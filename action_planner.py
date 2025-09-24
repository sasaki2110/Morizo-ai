"""
行動計画立案システム
ユーザーの要求を分析し、実行可能なタスクに分解する
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from openai import OpenAI

logger = logging.getLogger("morizo_ai.planner")

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
    
    def create_plan(self, user_request: str, available_tools: List[str], current_inventory: List[Dict[str, Any]] = None) -> List[Task]:
        """
        ユーザーの要求を分析し、実行可能なタスクに分解する
        
        Args:
            user_request: ユーザーの要求
            available_tools: 利用可能なツール一覧
            current_inventory: 現在の在庫状況（ID情報含む）
            
        Returns:
            実行可能なタスクのリスト
        """
        logger.info(f"🧠 [計画立案] ユーザー要求を分析: {user_request}")
        
        # LLMにタスク分解を依頼
        inventory_summary = ""
        if current_inventory:
            # 在庫状況を簡潔に要約
            item_counts = {}
            for item in current_inventory:
                name = item.get("item_name", "不明")
                if name not in item_counts:
                    item_counts[name] = []
                item_counts[name].append({
                    "id": item.get("id"),
                    "quantity": item.get("quantity", 1)
                })
            
            inventory_summary = f"""
現在の在庫要約:
{json.dumps(item_counts, ensure_ascii=False, indent=2)}
"""
        
        planning_prompt = f"""
ユーザー要求を分析し、適切なタスクに分解してください。

ユーザー要求: "{user_request}"

利用可能なツール: {', '.join(available_tools)}
{inventory_summary}

重要な判断基準:
1. **挨拶や一般的な会話の場合**: タスクは生成せず、空の配列を返す
   - 例: "こんにちは", "おはよう", "こんばんは", "お疲れ様", "ありがとう"
   - 例: "調子はどう？", "元気？", "今日はいい天気ですね"

2. **在庫管理に関連する要求の場合**: 適切なツールを選択
   - 在庫確認: inventory_list
   - 在庫追加: inventory_add
   - 在庫更新: inventory_update (item_id必須)
   - 在庫削除: inventory_delete (item_id必須)

3. **タスク生成のルール**:
   - 削除・更新は必ずitem_idを指定
   - 在庫状況から適切なIDを選択
   - 異なるアイテムは個別タスクに分解
   - 同一アイテムでも個別IDで処理

以下のJSON形式で回答してください:
{{
    "tasks": [
        {{
            "description": "タスクの説明",
            "tool": "使用するツール名",
            "parameters": {{
                "item_id": "対象のID",
                "item_name": "アイテム名",
                "quantity": 数量,
                "unit": "単位",
                "storage_location": "保管場所"
            }},
            "priority": 1,
            "dependencies": []
        }}
    ]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": planning_prompt}],
                max_tokens=1000,
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
            logger.error(f"❌ [計画立案] JSON解析エラー: {str(e)}")
            logger.error(f"❌ [計画立案] 不完全なJSON: {result[:200]}...")
            
            # JSON解析エラーの場合、適切なツールを推測してフォールバック
            if "在庫" in user_request or "教えて" in user_request:
                # 在庫確認の場合はinventory_listを使用
                fallback_task = Task(
                    id=f"task_{self.task_counter}",
                    description="在庫一覧を取得する",
                    tool="inventory_list",
                    parameters={},
                    priority=1
                )
            elif "削除" in user_request:
                # 削除の場合はエラーとして処理
                logger.error("❌ [計画立案] 削除要求でJSON解析エラー - 適切なタスクを生成できません")
                return []
            else:
                # その他の場合はllm_chatを使用
                fallback_task = Task(
                    id=f"task_{self.task_counter}",
                    description=f"ユーザー要求の処理: {user_request}",
                    tool="llm_chat",
                    parameters={"message": user_request},
                    priority=1
                )
            
            self.task_counter += 1
            return [fallback_task]
            
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
            inventory_tools = ["inventory_add", "inventory_update", "inventory_delete"]
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
