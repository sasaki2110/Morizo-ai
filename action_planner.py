"""
Morizo AI - Smart Pantry AI Agent
Copyright (c) 2024 Morizo AI Project. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, modification,
distribution, or use is strictly prohibited without explicit written permission.

For licensing inquiries, contact: [contact@morizo-ai.com]
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from openai import OpenAI

logger = logging.getLogger("morizo_ai.planner")

# 定数定義
MAX_TOKENS = 1500

def estimate_tokens(text: str) -> int:
    """テキストのトークン数を概算する（日本語は1文字=1トークン、英語は4文字=1トークン）"""
    japanese_chars = sum(1 for c in text if '\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF' or '\u4E00' <= c <= '\u9FAF')
    other_chars = len(text) - japanese_chars
    return japanese_chars + (other_chars // 4)

@dataclass
class Task:
    """実行可能なタスクを表現するクラス"""
    id: str
    description: str
    tool: str
    parameters: Dict[str, Any]
    status: str = "pending"  # pending, in_progress, completed, failed
    priority: int = 1  # 1=高, 2=中, 3=低
    dependencies: List[str] = None  # 依存するタスクのID
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

class ActionPlanner:
    """行動計画立案クラス"""
    
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        self.task_counter = 0
    
    def create_plan(self, user_request: str, available_tools: List[str]) -> List[Task]:
        """
        ユーザーの要求を分析し、実行可能なタスクに分解する
        
        Args:
            user_request: ユーザーの要求
            available_tools: 利用可能なツール一覧
            
        Returns:
            実行可能なタスクのリスト
        """
        logger.info(f"🧠 [計画立案] ユーザー要求を分析: {user_request}")
        
        # MCPツールの説明を取得
        tools_description = self._get_tools_description(available_tools)
        
        # LLMにタスク分解を依頼
        
        planning_prompt = f"""
ユーザー要求を分析し、適切なタスクに分解してください。

ユーザー要求: "{user_request}"

利用可能なツール: {', '.join(available_tools)}

{tools_description}

重要な判断基準:
1. **挨拶や一般的な会話の場合**: タスクは生成せず、空の配列を返す
   - 例: "こんにちは", "おはよう", "こんばんは", "お疲れ様", "ありがとう"
   - 例: "調子はどう？", "元気？", "今日はいい天気ですね"

2. **在庫管理に関連する要求の場合**: 適切なツールを選択
   - 在庫確認: inventory_list
   - 在庫追加: inventory_add
   - 在庫更新: inventory_update_by_id (item_id必須)
   - 在庫削除: inventory_delete_by_id (item_id必須)
   - 一括更新: inventory_update_by_name (item_nameのみ)
   - 一括削除: inventory_delete_by_name (item_nameのみ)

3. **タスク生成のルール**:
   - 削除・更新は必ずitem_idを指定
   - 在庫状況から適切なIDを選択
   - 異なるアイテムは個別タスクに分解
   - 同一アイテムでも個別IDで処理

**重要**: 必ず以下のJSON形式で回答してください：

{{
    "tasks": [
        {{
            "description": "タスクの説明",
            "tool": "使用するツール名",
            "parameters": {{
                // ツールが求めるJSON形式で記述
            }},
            "priority": 1,
            "dependencies": []
        }}
    ]
}}

ツールを利用しない場合は、親しみやすい自然言語で回答してください。
"""
        
        try:
            # トークン数予測
            estimated_tokens = estimate_tokens(planning_prompt)
            overage_rate = (estimated_tokens / MAX_TOKENS) * 100
            
            logger.info(f"🧠 [計画立案] プロンプト全文 (総トークン数: {estimated_tokens}/{MAX_TOKENS}, 超過率: {overage_rate:.1f}%):")
            logger.info(f"🧠 [計画立案] {planning_prompt}")
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": planning_prompt}],
                max_tokens=MAX_TOKENS,
                temperature=0.3
            )
            
            result = response.choices[0].message.content
            logger.info(f"🧠 [計画立案] LLM応答: {result}")
            
            # JSON解析（マークダウンのコードブロックを除去）
            if "```json" in result:
                # マークダウンのコードブロックを除去
                json_start = result.find("```json") + 7
                json_end = result.find("```", json_start)
                if json_end != -1:
                    result = result[json_start:json_end].strip()
                else:
                    # 終了の```がない場合
                    result = result[json_start:].strip()
            
            # JSON解析
            plan_data = json.loads(result)
            tasks = []
            
            for task_data in plan_data.get("tasks", []):
                # パラメータ名を正規化
                parameters = task_data["parameters"]
                if "item" in parameters:
                    parameters["item_name"] = parameters.pop("item")
                
                task = Task(
                    id=f"task_{self.task_counter}",
                    description=task_data["description"],
                    tool=task_data["tool"],
                    parameters=parameters,
                    priority=task_data.get("priority", 1),
                    dependencies=task_data.get("dependencies", [])
                )
                tasks.append(task)
                self.task_counter += 1
            
            logger.info(f"🧠 [計画立案] {len(tasks)}個のタスクを生成")
            
            # 不適切なタスク生成のチェック
            if self._is_inappropriate_task_generation(user_request, tasks):
                logger.warning(f"⚠️ [計画立案] 不適切なタスク生成を検出: {user_request}")
                logger.warning(f"⚠️ [計画立案] 生成されたタスク数: {len(tasks)}")
                return []  # 空のタスクリストを返す
            
            return tasks
            
        except json.JSONDecodeError as e:
            logger.info(f"🧠 [計画立案] LLMがシンプルなメッセージと判断: {str(e)}")
            logger.info(f"🧠 [計画立案] LLM応答: {result[:100]}...")
            
            # JSON解析エラー = LLMがシンプルなメッセージと判断
            # 空のタスク配列を返す（TrueReactAgentで_generate_simple_responseに流れる）
            return []
            
        except Exception as e:
            logger.error(f"❌ [計画立案] エラー: {str(e)}")
            # その他のエラーの場合
            fallback_task = Task(
                id=f"task_{self.task_counter}",
                description=f"ユーザー要求の処理: {user_request}",
                tool="llm_chat",
                parameters={"message": user_request},
                priority=1
            )
            self.task_counter += 1
            return [fallback_task]
    
    def _get_tools_description(self, available_tools: List[str]) -> str:
        """MCPツールの説明を取得"""
        # 簡易的なツール説明（実際のMCPツールから動的に取得する場合は、MCPクライアントを使用）
        tool_descriptions = {
            "inventory_add": """
📋 inventory_add: 在庫にアイテムを1件追加
🎯 使用場面: 「入れる」「追加」「保管」等のキーワードでユーザーが新たに在庫を作成する場合
⚠️ 重要: item_idは自動採番されるため、パラメータには不要です。
📋 JSON形式:
{
    "description": "アイテムを在庫に追加する",
    "tool": "inventory_add",
    "parameters": {
        "item_name": "アイテム名",
        "quantity": 数量,
        "unit": "単位",
        "storage_location": "保管場所",
        "expiry_date": "消費期限（オプション）"
    },
    "priority": 1,
    "dependencies": []
}
""",
            "inventory_update_by_id": """
📋 inventory_update_by_id: ID指定での在庫アイテム1件更新
🎯 使用場面: 「変更」「変える」「替える」「かえる」「更新」「クリア」等のキーワードでユーザーが在庫を更新する場合
⚠️ 重要: item_idは**必須です**。必ず在庫情報のitem_idを確認して、設定してください。
📋 JSON形式:
{
    "description": "アイテムを更新する",
    "tool": "inventory_update_by_id",
    "parameters": {
        "item_id": "対象のID（必須）",
        "item_name": "アイテム名",
        "quantity": 数量,
        "unit": "単位",
        "storage_location": "保管場所",
        "expiry_date": "消費期限"
    },
    "priority": 1,
    "dependencies": []
}
""",
            "inventory_delete_by_id": """
📋 inventory_delete_by_id: ID指定での在庫アイテム1件削除
🎯 使用場面: 「削除」「消す」「捨てる」「処分」等のキーワードでユーザーが特定のアイテムを削除する場合
⚠️ 重要: item_idパラメータは必須です。
📋 JSON形式:
{
    "description": "アイテムを削除する",
    "tool": "inventory_delete_by_id",
    "parameters": {
        "item_id": "対象のID（必須）"
    },
    "priority": 1,
    "dependencies": []
}
""",
            "inventory_update_by_name": """
📋 inventory_update_by_name: 名前指定での在庫アイテム一括更新
🎯 使用場面: 「全部」「一括」「全て」等のキーワードで複数のアイテムを同時に更新する場合
⚠️ 重要: quantityパラメータは更新する値です。更新対象件数ではありません。
📋 JSON形式:
{
    "description": "アイテムを一括更新する",
    "tool": "inventory_update_by_name",
    "parameters": {
        "item_name": "アイテム名（必須）",
        "quantity": "更新後の数量（オプション）",
        "unit": "単位（オプション）",
        "storage_location": "保管場所（オプション）",
        "expiry_date": "消費期限（オプション）"
    },
    "priority": 1,
    "dependencies": []
}
""",
            "inventory_delete_by_name": """
📋 inventory_delete_by_name: 名前指定での在庫アイテム一括削除
🎯 使用場面: 「全部」「一括」「全て」等のキーワードで複数のアイテムを同時に削除する場合
📋 JSON形式:
{
    "description": "アイテムを一括削除する",
    "tool": "inventory_delete_by_name",
    "parameters": {
        "item_name": "アイテム名（必須）"
    },
    "priority": 1,
    "dependencies": []
}
""",
            "inventory_list": """
📋 inventory_list: 在庫一覧を取得
🎯 使用場面: 「在庫を教えて」「今の在庫は？」等のキーワードでユーザーが在庫状況を確認する場合
📋 JSON形式:
{
    "description": "在庫一覧を取得する",
    "tool": "inventory_list",
    "parameters": {},
    "priority": 1,
    "dependencies": []
}
"""
        }
        
        # 利用可能なツールの説明を結合
        descriptions = []
        for tool in available_tools:
            if tool in tool_descriptions:
                descriptions.append(tool_descriptions[tool])
        
        return "\n".join(descriptions)
    
    def _is_inappropriate_task_generation(self, user_request: str, tasks: List[Task]) -> bool:
        """
        不適切なタスク生成を判定する
        
        Args:
            user_request: ユーザーの要求
            tasks: 生成されたタスクリスト
            
        Returns:
            True if inappropriate, False otherwise
        """
        # 1. 挨拶パターンのチェック
        greeting_patterns = ["こんにちは", "おはよう", "こんばんは", "お疲れ様", "ありがとう", "調子はどう", "元気", "天気"]
        if any(pattern in user_request for pattern in greeting_patterns):
            # 挨拶なのに在庫操作タスクがある場合は不適切
            inventory_tools = ["inventory_add", "inventory_update", "inventory_delete", "inventory_update_by_name", "inventory_delete_by_name"]
            if any(task.tool in inventory_tools for task in tasks):
                logger.warning(f"⚠️ [判定] 挨拶なのに在庫操作タスクを生成: {user_request}")
                return True
        
        # 2. タスク数の妥当性チェック
        if len(tasks) > 2 and len(user_request) < 10:  # 短い要求なのに多数のタスク
            logger.warning(f"⚠️ [判定] 短い要求なのに多数のタスク: {len(tasks)}個")
            return True
        
        # 3. 存在しないIDのチェック
        fake_ids = ["001", "002", "003", "商品A", "商品B", "商品C"]
        for task in tasks:
            if task.tool in ["inventory_update", "inventory_delete"]:
                item_id = task.parameters.get("item_id", "")
                if item_id in fake_ids:
                    logger.warning(f"⚠️ [判定] 存在しないIDを使用: {item_id}")
                    return True
        
        # 4. 在庫状況にないアイテム名のチェック
        fake_items = ["商品A", "商品B", "商品C"]
        for task in tasks:
            item_name = task.parameters.get("item_name", "")
            if item_name in fake_items:
                logger.warning(f"⚠️ [判定] 存在しないアイテム名を使用: {item_name}")
                return True
        
        return False
    
    def validate_plan(self, tasks: List[Task]) -> bool:
        """
        生成されたタスクプランを検証する
        
        Args:
            tasks: 検証するタスクリスト
            
        Returns:
            プランが有効かどうか
        """
        if not tasks:
            logger.warning("⚠️ [計画検証] タスクが空です")
            return False
        
        # 依存関係を説明文からタスクIDに変換
        for task in tasks:
            if task.dependencies:
                converted_deps = []
                for dep_description in task.dependencies:
                    # 説明文でタスクを検索
                    dep_task = self._find_task_by_description(tasks, dep_description)
                    if dep_task:
                        converted_deps.append(dep_task.id)
                    else:
                        logger.warning(f"⚠️ [計画検証] 依存関係エラー: {dep_description}が見つかりません")
                        return False
                task.dependencies = converted_deps
        
        # 依存関係の検証
        task_ids = {task.id for task in tasks}
        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id not in task_ids:
                    logger.warning(f"⚠️ [計画検証] 依存関係エラー: {dep_id}が見つかりません")
                    return False
        
        logger.info(f"✅ [計画検証] {len(tasks)}個のタスクが有効です")
        return True
    
    def _find_task_by_description(self, tasks: List[Task], description: str) -> Optional[Task]:
        """
        説明文でタスクを検索する
        
        Args:
            tasks: 検索対象のタスクリスト
            description: 検索する説明文
            
        Returns:
            見つかったタスク（見つからない場合はNone）
        """
        for task in tasks:
            if task.description == description:
                return task
        return None
    
    def optimize_plan(self, tasks: List[Task]) -> List[Task]:
        """
        タスクプランを最適化する（優先度順にソート）
        
        Args:
            tasks: 最適化するタスクリスト
            
        Returns:
            最適化されたタスクリスト
        """
        # 優先度順にソート
        sorted_tasks = sorted(tasks, key=lambda x: x.priority)
        
        logger.info(f"🔧 [計画最適化] {len(sorted_tasks)}個のタスクを優先度順にソート")
        return sorted_tasks
