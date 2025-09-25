"""
Morizo AI - Smart Pantry AI Agent
Copyright (c) 2024 Morizo AI Project. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, modification,
distribution, or use is strictly prohibited without explicit written permission.

For licensing inquiries, contact: [contact@morizo-ai.com]
"""

import json
import logging
import os
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
    
    async def create_plan(self, user_request: str, available_tools: List[str]) -> List[Task]:
        """
        ユーザーの要求を分析し、実行可能なタスクに分解する
        
        Args:
            user_request: ユーザーの要求
            available_tools: 利用可能なツール一覧
            
        Returns:
            実行可能なタスクのリスト
        """
        logger.info(f"🧠 [計画立案] ユーザー要求を分析: {user_request}")
        
        # MCPツールの説明を動的に取得（関連ツールのみ）
        tools_description = await self._get_tools_description(available_tools, user_request)
        
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

2. **在庫管理に関連するユーザー指示の確認**: 適切なツールを選択
   - **ユーザー指定（最新）**: ユーザー要求に「最新の」「新しい方の」「最近買った」キーワードがあるか確認
   - 最新を指示するキーワードがあれば、最新アイテムを更新/削除。

   - **ユーザー指定（全て）**: ユーザー要求に「全ての」「全部の」キーワードがあるか確認
   - 全てを指示するキーワードがあれば、全アイテムを更新/削除。

   - **ユーザー指定なし**: ユーザー要求に最新や全ての指定がない場合は最古アイテムを更新/削除

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
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
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
    
    async def _get_tools_description(self, available_tools: List[str], user_request: str = "") -> str:
        """MCPツールの説明を動的に取得（関連ツールのみ）"""
        try:
            # ユーザー要求に基づいて関連ツールをフィルタリング
            relevant_tools = self._filter_relevant_tools(available_tools, user_request)
            logger.info(f"🔧 [計画立案] 関連ツール: {len(relevant_tools)}/{len(available_tools)}個")
            
            # FastMCPクライアントから動的にツール詳細を取得
            from agents.mcp_client import MCPClient
            mcp_client = MCPClient()
            tool_details = await mcp_client.get_tool_details()
            
            if not tool_details:
                logger.warning("⚠️ [計画立案] ツール詳細取得失敗、フォールバック使用")
                return self._get_fallback_tools_description(relevant_tools)
            
            # 動的に取得したツール説明をフォーマット（パラメータ情報含む）
            descriptions = []
            for tool_name in relevant_tools:
                if tool_name in tool_details:
                    tool_info = tool_details[tool_name]
                    # 説明文を短縮（100文字以内、トークン節約）
                    full_description = tool_info["description"]
                    # 最初の文のみ抽出（。で区切る）
                    first_sentence = full_description.split('。')[0] if '。' in full_description else full_description
                    # 100文字以内に制限（FIFO関連情報を含めるため拡張）
                    short_description = first_sentence[:100] + "..." if len(first_sentence) > 100 else first_sentence
                    
                    # パラメータ情報を追加
                    param_info = self._extract_parameter_info(tool_info.get("input_schema", {}))
                    if param_info:
                        descriptions.append(f"{tool_name}: {short_description}\n  パラメータ: {param_info}")
                    else:
                        descriptions.append(f"{tool_name}: {short_description}")
                else:
                    logger.warning(f"⚠️ [計画立案] ツール {tool_name} の詳細情報が見つかりません")
            
            return "\n".join(descriptions)
            
        except Exception as e:
            logger.error(f"❌ [計画立案] 動的ツール説明取得エラー: {str(e)}")
            return self._get_fallback_tools_description(available_tools)
    
    def _filter_relevant_tools(self, available_tools: List[str], user_request: str) -> List[str]:
        """ユーザー要求に基づいて関連ツールをフィルタリング"""
        if not user_request:
            return available_tools
        
        # キーワードベースのフィルタリング
        user_lower = user_request.lower()
        
        # 追加関連キーワード
        add_keywords = ["追加", "入れる", "保管", "新規", "増やす"]
        if any(keyword in user_lower for keyword in add_keywords):
            return [tool for tool in available_tools if "add" in tool]
        
        # 更新関連キーワード
        update_keywords = ["変更", "変える", "替える", "更新", "修正", "本数", "数量"]
        if any(keyword in user_lower for keyword in update_keywords):
            return [tool for tool in available_tools if "update" in tool]
        
        # 削除関連キーワード
        delete_keywords = ["削除", "消す", "捨てる", "処分", "なくす"]
        if any(keyword in user_lower for keyword in delete_keywords):
            return [tool for tool in available_tools if "delete" in tool]
        
        # 確認関連キーワード
        list_keywords = ["一覧", "確認", "見る", "表示", "教えて"]
        if any(keyword in user_lower for keyword in list_keywords):
            return [tool for tool in available_tools if "list" in tool or "get" in tool]
        
        # デフォルト: 全ツールを返す
        return available_tools
    
    def _extract_parameter_info(self, input_schema: dict) -> str:
        """入力スキーマからパラメータ情報を抽出"""
        try:
            if not input_schema or "properties" not in input_schema:
                return ""
            
            properties = input_schema["properties"]
            required = input_schema.get("required", [])
            
            param_list = []
            for param_name, param_info in properties.items():
                if param_name == "token":  # tokenは除外
                    continue
                
                param_type = param_info.get("type", "unknown")
                is_required = param_name in required
                
                if is_required:
                    param_list.append(f"{param_name}({param_type}, 必須)")
                else:
                    param_list.append(f"{param_name}({param_type}, オプション)")
            
            return ", ".join(param_list) if param_list else ""
            
        except Exception as e:
            logger.warning(f"⚠️ [計画立案] パラメータ情報抽出エラー: {str(e)}")
            return ""
    
    def _get_fallback_tools_description(self, available_tools: List[str]) -> str:
        """フォールバック用のツール説明"""
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
