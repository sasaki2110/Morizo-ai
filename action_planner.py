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
        
        # LLMにタスク分解を依頼
        planning_prompt = f"""
以下のユーザー要求を分析し、実行可能なタスクに分解してください。

ユーザー要求: "{user_request}"

利用可能なツール:
{json.dumps(available_tools, ensure_ascii=False, indent=2)}

タスク分解のルール:
1. 複数のアイテムがある場合は、個別のタスクに分解
2. 個別在庫法に従い、各アイテムを個別に登録
3. 依存関係がある場合は、dependenciesに記録
4. 優先度を適切に設定（1=高, 2=中, 3=低）

以下のJSON形式で回答してください（マークダウンのコードブロックは使用しないでください）:
{{
    "tasks": [
        {{
            "description": "タスクの説明",
            "tool": "使用するツール名",
            "parameters": {{
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
            return tasks
            
        except Exception as e:
            logger.error(f"❌ [計画立案] エラー: {str(e)}")
            # フォールバック: 単一タスクとして処理
            fallback_task = Task(
                id=f"task_{self.task_counter}",
                description=f"ユーザー要求の処理: {user_request}",
                tool="llm_chat",
                parameters={"message": user_request},
                priority=1
            )
            self.task_counter += 1
            return [fallback_task]
    
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
