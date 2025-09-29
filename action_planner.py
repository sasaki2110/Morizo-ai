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
MAX_TOKENS = 4000

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
    result: Dict[str, Any] = None  # 実行結果
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.result is None:
            self.result = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Taskオブジェクトを辞書に変換"""
        return {
            "id": self.id,
            "description": self.description,
            "tool": self.tool,
            "parameters": self.parameters,
            "status": self.status,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "result": self.result
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """辞書からTaskオブジェクトを復元"""
        return cls(
            id=data['id'],
            description=data['description'],
            tool=data['tool'],
            parameters=data['parameters'],
            status=data.get('status', 'pending'),
            priority=data.get('priority', 1),
            dependencies=data.get('dependencies', []),
            result=data.get('result', {})
        )

class ActionPlanner:
    """行動計画立案クラス"""
    
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        self.task_counter = 0
    
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
            
            # 動的に取得したツール説明をフォーマット（大幅短縮版）
            descriptions = []
            for tool_name in relevant_tools:
                if tool_name in tool_details:
                    tool_info = tool_details[tool_name]
                    # 説明文を大幅短縮（30文字以内、トークン大幅節約）
                    full_description = tool_info["description"]
                    # 最初の文のみ抽出（。で区切る）
                    first_sentence = full_description.split('。')[0] if '。' in full_description else full_description
                    # 30文字以内に制限（大幅短縮）
                    short_description = first_sentence[:30] + "..." if len(first_sentence) > 30 else first_sentence
                    
                    # パラメータ情報は削除（トークン節約のため）
                    descriptions.append(f"{tool_name}: {short_description}")
                else:
                    logger.warning(f"⚠️ [計画立案] ツール {tool_name} の詳細情報が見つかりません")
            
            return "\n".join(descriptions)
            
        except Exception as e:
            logger.error(f"❌ [計画立案] 動的ツール説明取得エラー: {str(e)}")
            return self._get_fallback_tools_description(available_tools)
    
    def _filter_relevant_tools(self, available_tools: List[str], user_request: str) -> List[str]:
        """ユーザー要求に基づいて関連ツールをフィルタリング（階層的アプローチ）"""
        if not user_request:
            return []
        
        # ステップ1: シンプル応答パターンの検出（最優先）
        if self._is_simple_response_pattern(user_request):
            logger.info(f"🔍 [フィルタ] シンプル応答パターン検出: {user_request}")
            return []
        
        # ステップ2: 在庫・レシピ関連の検出
        user_lower = user_request.lower()
        relevant_tools = []
        
        # 在庫管理関連キーワード
        inventory_tools = self._filter_inventory_tools(available_tools, user_lower)
        relevant_tools.extend(inventory_tools)
        
        # レシピ・献立関連キーワード
        recipe_tools = self._filter_recipe_tools(available_tools, user_lower)
        relevant_tools.extend(recipe_tools)
        
        # ステップ3: 結果の統合
        if not relevant_tools:
            logger.info(f"🔍 [フィルタ] 関連ツールなし、シンプル応答: {user_request}")
            return []
        
        logger.info(f"🔧 [計画立案] 関連ツール: {len(relevant_tools)}/{len(available_tools)}個")
        return relevant_tools
    
    def _is_simple_response_pattern(self, user_request: str) -> bool:
        """シンプル応答が必要なパターンを検出（キーワードマッチング版）"""
        patterns = {
            "greeting": ["こんにちは", "おはよう", "こんばんは", "お疲れ様", "ありがとう", "よろしく"],
            "weather": ["天気", "雨", "晴れ", "曇り", "寒い", "暑い", "気温"],
            "health": ["元気", "調子", "疲れ", "具合", "体調", "健康"],
            "time": ["何時", "時間", "今日", "明日", "昨日", "今"],
            "casual": ["どう", "いかが", "すみません", "お願い", "よろしくお願いします"],
            "thanks": ["ありがとう", "感謝", "助かった", "助かりました"]
        }
        
        user_lower = user_request.lower()
        return any(
            any(keyword in user_lower for keyword in keywords)
            for keywords in patterns.values()
        )
    
    
    def _filter_inventory_tools(self, available_tools: List[str], user_lower: str) -> List[str]:
        """在庫管理関連ツールをフィルタリング"""
        inventory_tools = []
        
        # 追加関連キーワード
        add_keywords = ["追加", "入れる", "保管", "新規", "増やす", "買った", "購入"]
        if any(keyword in user_lower for keyword in add_keywords):
            inventory_tools.extend([tool for tool in available_tools if "add" in tool])
        
        # 更新関連キーワード
        update_keywords = ["変更", "変える", "替える", "更新", "修正", "本数", "数量", "クリア"]
        if any(keyword in user_lower for keyword in update_keywords):
            inventory_tools.extend([tool for tool in available_tools if "update" in tool])
        
        # 削除関連キーワード
        delete_keywords = ["削除", "消す", "捨てる", "処分", "なくす", "使った", "消費"]
        if any(keyword in user_lower for keyword in delete_keywords):
            inventory_tools.extend([tool for tool in available_tools if "delete" in tool])
        
        # 確認関連キーワード
        list_keywords = ["一覧", "確認", "見る", "表示", "教えて", "在庫", "冷蔵庫", "中身"]
        if any(keyword in user_lower for keyword in list_keywords):
            inventory_tools.extend([tool for tool in available_tools if "list" in tool or "get" in tool])
        
        return list(set(inventory_tools))  # 重複除去
    
    def _filter_recipe_tools(self, available_tools: List[str], user_lower: str) -> List[str]:
        """レシピ・献立関連ツールをフィルタリング"""
        recipe_tools = []
        
        # レシピ・献立関連キーワード
        recipe_keywords = [
            "献立", "レシピ", "料理", "メニュー", "食事", "夕飯", "昼飯", "朝飯", "ご飯",
            "作る", "調理", "クッキング", "提案", "考えて", "何ができる", "作れる"
        ]
        if any(keyword in user_lower for keyword in recipe_keywords):
            recipe_tools.extend([tool for tool in available_tools if "generate_menu" in tool or "search_recipe" in tool])
        
        return list(set(recipe_tools))  # 重複除去
    
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
        """フォールバック用のツール説明（大幅短縮版）"""
        tool_descriptions = {
            "inventory_add": "inventory_add: 在庫追加",
            "inventory_update_by_id": "inventory_update_by_id: ID指定更新",
            "inventory_delete_by_id": "inventory_delete_by_id: ID指定削除",
            "inventory_update_by_name": "inventory_update_by_name: 名前指定一括更新",
            "inventory_delete_by_name": "inventory_delete_by_name: 名前指定一括削除",
            "inventory_list": "inventory_list: 在庫一覧取得",
            "generate_menu_plan_with_history": "generate_menu_plan_with_history: 献立生成"
        }
        
        # 利用可能なツールの説明を結合（簡潔版）
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
        
        # Phase A: LLMが直接タスクIDを生成するため、変換処理は不要
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
    
    def _add_prerequisite_tasks(self, tasks: List[Task]) -> List[Task]:
        """
        Phase 2: 削除・更新タスクの前に在庫確認タスクを自動生成
        
        Args:
            tasks: 元のタスクリスト
            
        Returns:
            前提タスクが追加されたタスクリスト
        """
        # 削除・更新操作のツール
        inventory_operation_tools = [
            "inventory_delete_by_name",
            "inventory_update_by_name", 
            "inventory_delete_by_name_oldest",
            "inventory_delete_by_name_latest",
            "inventory_update_by_name_oldest",
            "inventory_update_by_name_latest"
        ]
        
        enhanced_tasks = []
        prerequisite_tasks = {}  # item_name -> prerequisite_task_id
        
        for task in tasks:
            # 削除・更新タスクかチェック
            if task.tool in inventory_operation_tools:
                item_name = task.parameters.get("item_name")
                if item_name:
                    # 既に前提タスクが生成されているかチェック
                    if item_name not in prerequisite_tasks:
                        # 前提タスクを生成
                        prerequisite_task = Task(
                            id=f"prerequisite_{item_name}_{self.task_counter}",
                            description=f"{item_name}の在庫状況を確認",
                            tool="inventory_list_by_name",
                            parameters={"item_name": item_name},
                            priority=task.priority - 1,  # より高い優先度
                            dependencies=[]
                        )
                        prerequisite_tasks[item_name] = prerequisite_task.id
                        enhanced_tasks.append(prerequisite_task)
                        self.task_counter += 1
                        logger.info(f"🔧 [前提タスク] {item_name}の在庫確認タスクを生成: {prerequisite_task.id}")
                    
                    # 元のタスクの依存関係を更新
                    task.dependencies.append(prerequisite_tasks[item_name])
                    logger.info(f"🔧 [前提タスク] {task.id}の依存関係を更新: {task.dependencies}")
            
            enhanced_tasks.append(task)
        
        if prerequisite_tasks:
            logger.info(f"🔧 [前提タスク] {len(prerequisite_tasks)}個の前提タスクを追加")
        
        return enhanced_tasks

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

**🚨 重要: 献立生成要求の場合は必ず4タスク構成を使用してください**

**献立生成要求の判定基準**:
- ユーザー要求に「献立」「レシピ」「料理」「メニュー」などのキーワードが含まれる場合
- 在庫から料理を提案する要求の場合

**献立生成要求の場合は以下の4タスク構成を必ず使用**:
{{
  "tasks": [
    {{
      "id": "task1",
      "description": "最新の在庫を取得",
      "tool": "inventory_list",
      "parameters": {{}},
      "priority": 1,
      "dependencies": []
    }},
    {{
      "id": "task2",
      "description": "LLM推論で献立タイトル生成",
      "tool": "generate_menu_plan_with_history",
      "parameters": {{"inventory_items": [], "excluded_recipes": [], "menu_type": "和食"}},
      "priority": 2,
      "dependencies": ["task1"]
    }},
    {{
      "id": "task3",
      "description": "RAG検索で献立タイトル生成",
      "tool": "search_menu_from_rag_with_history",
      "parameters": {{"inventory_items": [], "excluded_recipes": [], "menu_type": "和食", "max_results": 3}},
      "priority": 3,
      "dependencies": ["task1"]
    }},
    {{
      "id": "task4",
      "description": "Web検索でレシピURL取得",
      "tool": "search_recipe_from_web",
      "parameters": {{"menu_titles": ["動的に注入される"], "max_results": 3}},
      "priority": 4,
      "dependencies": ["task2", "task3"]
    }}
  ]
}}

**重要**: 献立生成要求の場合は、上記の4タスク構成を必ず使用してください。3タスク構成は使用禁止です。

重要な判定基準:
1. **挨拶や一般的な会話の場合**: タスクは生成せず、空の配列を返す
   - 例: "こんにちは", "おはよう", "こんばんは", "お疲れ様", "ありがとう"
   - 例: "調子はどう？", "元気？", "今日はいい天気ですね"

2. **在庫管理に関するユーザー指示の確認**: 適切なツールを選択
   - **ユーザー指定（古い方）**: ユーザー要求に「古い方の」「古い」「最初の」キーワードがあるか確認
   - 古い方を指示するキーワードがあれば、最古アイテムを更新/削除。

   - **ユーザー指定（最新）**: ユーザー要求に「最新の」「新しい方の」「最近買った」キーワードがあるか確認
   - 最新を指示するキーワードがあれば、最新アイテムを更新/削除。

   - **ユーザー指定（全て）**: ユーザー要求に「全ての」「全部の」キーワードがあるか確認
   - 全てを指示するキーワードがあれば、全アイテムを更新/削除。

   - **ユーザー指定なし**: ユーザー要求に「古い方」「最新」「全て」の指定がない場合は、必ず`inventory_delete_by_name`または`inventory_update_by_name`を使用する。`inventory_delete_by_name_latest`、`inventory_delete_by_name_oldest`、`inventory_update_by_name_latest`、`inventory_update_by_name_oldest`は使用禁止。

**重要**: 「牛乳を削除して」のような曖昧な要求では、絶対に`inventory_delete_by_name_latest`や`inventory_delete_by_name_oldest`を選択してはいけません。

**具体例**:
- 「牛乳を削除して」→ `inventory_delete_by_name`（確認プロセス発動）
- 「古い牛乳を削除して」→ `inventory_delete_by_name_oldest`（直接削除）
- 「最新の牛乳を削除して」→ `inventory_delete_by_name_latest`（直接削除）
- 「全ての牛乳を削除して」→ `inventory_delete_by_name`（全削除）

**禁止事項**: 曖昧な要求で`inventory_delete_by_name_latest`や`inventory_delete_by_name_oldest`を選択することは絶対に禁止です。

3. **タスク生成のルール**:
   - 削除・更新は必ずitem_idを指定
   - 在庫状況から適切なIDを選択
   - 異なるアイテムは個別タスクに分解
   - 同一アイテムでも個別IDで処理

**重要**: 必ず以下のJSON形式で回答してください（コメントは禁止）：

{{
    "tasks": [
        {{
            "id": "task1",
            "description": "タスクの説明",
            "tool": "使用するツール名",
            "parameters": {{
                "key": "value"
            }},
            "priority": 1,
            "dependencies": []
        }}
    ]
}}

**依存関係のルール**:
- 各タスクには一意のIDを付与してください（task1, task2, task3...）
- 依存関係は他のタスクのIDで指定してください
- 依存関係がない場合は空配列[]を指定
- 複数のタスクが同じ依存関係を持つ場合は並列実行可能です

**例**:
- 在庫取得 → 献立生成: dependencies: ["inventory_fetch"]
- 在庫取得 → 献立生成 + 買い物リスト: 献立生成と買い物リストは並列実行可能

**在庫追加後の献立生成のルール**:
- 在庫追加（inventory_add）を行った後、献立生成（generate_menu_plan_with_history）を実行する場合は、必ず在庫一覧取得（inventory_list）を間に挟む
- 例: inventory_add → inventory_list → generate_menu_plan_with_history
- 在庫追加と献立生成を同時に要求された場合:
  1. inventory_add タスク（並列実行可能）
  2. inventory_list タスク（在庫追加の依存関係）
  3. generate_menu_plan_with_history タスク（在庫一覧の依存関係）

**重要なパラメータ名**:
- generate_menu_plan_with_history: inventory_items (必須), excluded_recipes, menu_type
- inventory_list: パラメータなし
- その他のツール: 各ツールの仕様に従って正しいパラメータ名を使用

**パラメータ例**:
- 献立生成: {{"inventory_items": ["鶏もも肉", "もやし", "パン"], "excluded_recipes": [], "menu_type": "和食"}}
- 在庫一覧: {{}} (パラメータなし)

**在庫追加+献立生成の具体例**:
ユーザー要求: "牛すね肉と人参を追加して献立を教えて"
正しいタスク構造:
{{
  "tasks": [
    {{
      "id": "task1",
      "description": "牛すね肉を在庫に追加",
      "tool": "inventory_add",
      "parameters": {{"item_name": "牛すね肉", "quantity": 1}},
      "priority": 1,
      "dependencies": []
    }},
    {{
      "id": "task2", 
      "description": "人参を在庫に追加",
      "tool": "inventory_add",
      "parameters": {{"item_name": "人参", "quantity": 3}},
      "priority": 1,
      "dependencies": []
    }},
    {{
      "id": "task3",
      "description": "最新の在庫を取得",
      "tool": "inventory_list", 
      "parameters": {{}},
      "priority": 2,
      "dependencies": ["task1", "task2"]
    }},
    {{
      "id": "task4",
      "description": "在庫から献立を生成",
      "tool": "generate_menu_plan_with_history",
      "parameters": {{"inventory_items": [], "excluded_recipes": [], "menu_type": "和食"}},
      "priority": 3,
      "dependencies": ["task3"]
    }}
  ]
}}

**🚀 レシピ検索の自動追加ルール**:
- 献立生成（generate_menu_plan_with_history）を実行する場合、自動的にレシピ検索（search_recipe_from_web）を追加
- 献立生成の結果から料理名を抽出してレシピ検索のクエリに使用
- 例: 献立生成 → レシピ検索（肉じゃがの作り方、味噌汁の作り方など）

**レシピ検索の具体例**:
ユーザー要求: "在庫で作れる献立とレシピを教えて"
正しいタスク構造:
{{
  "tasks": [
    {{
      "id": "task1",
      "description": "最新の在庫を取得",
      "tool": "inventory_list",
      "parameters": {{}},
      "priority": 1,
      "dependencies": []
    }},
    {{
      "id": "task2",
      "description": "LLM推論で献立タイトル生成",
      "tool": "generate_menu_plan_with_history",
      "parameters": {{"inventory_items": [], "excluded_recipes": [], "menu_type": "和食"}},
      "priority": 2,
      "dependencies": ["task1"]
    }},
    {{
      "id": "task3",
      "description": "RAG検索で献立タイトル生成",
      "tool": "search_menu_from_rag_with_history",
      "parameters": {{"inventory_items": [], "excluded_recipes": [], "menu_type": "和食", "max_results": 3}},
      "priority": 3,
      "dependencies": ["task1"]
    }},
    {{
      "id": "task4",
      "description": "Web検索でレシピURL取得",
      "tool": "search_recipe_from_web",
      "parameters": {{"menu_titles": ["動的に注入される"], "max_results": 3}},
      "priority": 4,
      "dependencies": ["task2", "task3"]
    }}
  ]
}}

**JSONの注意事項**:
- コメント（//）は絶対に使用しない
- すべての文字列は二重引用符で囲む
- 有効なJSON形式のみを使用

ツールを利用しない場合は、親しみやすい自然言語で回答してください。
"""
        
        try:
            # トークン数予測
            estimated_tokens = estimate_tokens(planning_prompt)
            overage_rate = (estimated_tokens / MAX_TOKENS) * 100
            
            logger.info(f"🧠 [計画立案] プロンプト全文 (総トークン数: {estimated_tokens}/{MAX_TOKENS}, 超過率: {overage_rate:.1f}%):")
            # プロンプト表示を5行に制限
            prompt_lines = planning_prompt.split('\n')
            if len(prompt_lines) > 5:
                logger.info(f"🧠 [計画立案] {chr(10).join(prompt_lines[:5])}")
                logger.info(f"🧠 [計画立案] ... (残り{len(prompt_lines)-5}行を省略)")
            else:
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
                if "name" in parameters:
                    parameters["item_name"] = parameters.pop("name")
                
                task = Task(
                    id=task_data.get("id", f"task_{self.task_counter}"),
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
            
            # Phase 2: 前提タスクの自動生成
            tasks = self._add_prerequisite_tasks(tasks)
            
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
