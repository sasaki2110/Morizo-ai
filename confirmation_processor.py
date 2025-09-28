#!/usr/bin/env python3
"""
確認プロセス処理
曖昧性検出後の確認プロセスとユーザー選択の処理
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from action_planner import Task
from ambiguity_detector import AmbiguityInfo


@dataclass
class TaskExecutionPlan:
    """タスク実行計画"""
    tasks: List[Task]
    cancel: bool = False
    continue_execution: bool = True


class ConfirmationProcessor:
    """確認プロセス処理クラス"""
    
    def __init__(self):
        self.ambiguity_detector = None  # 後で注入
    
    def generate_confirmation_response(self, ambiguity_info: AmbiguityInfo, remaining_tasks: List[Task] = None) -> Dict[str, Any]:
        """確認レスポンスを生成"""
        response = f"{ambiguity_info.item_name}の{self._get_action_description(ambiguity_info.task)}について確認させてください。\n"
        response += f"現在、{ambiguity_info.item_name}が{len(ambiguity_info.items)}個あります。\n\n"
        
        # 残りのタスクチェーンを説明
        if remaining_tasks and len(remaining_tasks) > 0:
            response += f"この操作の後、以下の処理も予定されています：\n"
            for i, task in enumerate(remaining_tasks, 1):
                response += f"{i}. {task.description}\n"
            response += "\n"
        
        # アイテムの詳細情報を表示
        response += self._format_items_info(ambiguity_info.items)
        response += "\n"
        
        # 選択肢を表示
        response += "以下のいずれかでお答えください：\n"
        suggestions = self._generate_suggestions(ambiguity_info)
        for suggestion in suggestions:
            response += f"- {suggestion['description']}\n"
        
        # 辞書形式で返す
        return {
            "response": response,
            "confirmation_context": {
                "action": self._get_action_from_tool(ambiguity_info.task.tool),
                "item_name": ambiguity_info.item_name,
                "remaining_task_chain": [t.to_dict() for t in remaining_tasks] if remaining_tasks else [],
                "options": suggestions,
                "items": ambiguity_info.items
            }
        }
    
    def process_confirmation_response(self, user_input: str, context: dict) -> TaskExecutionPlan:
        """確認応答の処理とタスクチェーン再開"""
        user_input = user_input.strip().lower()
        
        if any(word in user_input for word in ["キャンセル", "やめる", "cancel"]):
            return TaskExecutionPlan(tasks=[], cancel=True)
        
        # 現在のタスクを実行
        current_task = self._create_task_from_choice(user_input, context)
        
        # 残りのタスクチェーンを取得
        remaining_tasks = context.get("remaining_task_chain", [])
        
        return TaskExecutionPlan(
            tasks=[current_task] + remaining_tasks,
            continue_execution=True
        )
    
    def _get_action_description(self, task: Task) -> str:
        """操作の説明を取得"""
        action_map = {
            "inventory_delete_by_name": "削除",
            "inventory_update_by_name": "更新",
            "inventory_delete_by_name_oldest": "削除（最古）",
            "inventory_delete_by_name_latest": "削除（最新）",
            "inventory_update_by_name_oldest": "更新（最古）",
            "inventory_update_by_name_latest": "更新（最新）"
        }
        return action_map.get(task.tool, "操作")
    
    def _format_items_info(self, items: List[Dict[str, Any]]) -> str:
        """アイテム情報を整形"""
        if len(items) <= 3:
            # 少ない場合は詳細表示
            info = "アイテム詳細：\n"
            for i, item in enumerate(items, 1):
                created_at = item.get("created_at", "不明")
                info += f"{i}. ID: {item.get('id', 'N/A')[:8]}... (登録日: {created_at})\n"
        else:
            # 多い場合は概要表示
            info = f"アイテム数: {len(items)}個\n"
        
        return info
    
    def _generate_suggestions(self, ambiguity_info: AmbiguityInfo) -> List[Dict[str, str]]:
        """選択肢を生成"""
        if ambiguity_info.type == "multiple_items":
            return [
                {"value": "oldest", "description": "古いアイテムを操作"},
                {"value": "latest", "description": "新しいアイテムを操作"},
                {"value": "all", "description": "全部操作"},
                {"value": "cancel", "description": "キャンセル"}
            ]
        elif ambiguity_info.type == "fifo_operation":
            if "oldest" in ambiguity_info.task.tool:
                return [
                    {"value": "confirm", "description": "最古のアイテムを操作"},
                    {"value": "cancel", "description": "キャンセル"}
                ]
            elif "latest" in ambiguity_info.task.tool:
                return [
                    {"value": "confirm", "description": "最新のアイテムを操作"},
                    {"value": "cancel", "description": "キャンセル"}
                ]
        
        return [
            {"value": "confirm", "description": "操作を実行"},
            {"value": "cancel", "description": "キャンセル"}
        ]
    
    def _get_action_from_tool(self, tool: str) -> str:
        """ツール名からアクションを取得"""
        if "delete" in tool:
            return "delete"
        elif "update" in tool:
            return "update"
        else:
            return "unknown"
    
    def _create_task_from_choice(self, user_input: str, context: dict) -> Task:
        """ユーザーの選択からタスクを作成"""
        item_name = context.get("item_name")
        original_task = context.get("original_task")
        
        if not item_name or not original_task:
            raise ValueError("Invalid confirmation context")
        
        # 自然言語での選択処理
        if any(word in user_input for word in ["古い", "最古", "oldest"]):
            if "delete" in original_task.tool:
                return Task(
                    id=f"{original_task.id}_oldest",
                    tool="inventory_delete_by_name_oldest",
                    parameters={"item_name": item_name, "token": context.get("token")},
                    description=f"最古の{item_name}を削除"
                )
            elif "update" in original_task.tool:
                return Task(
                    id=f"{original_task.id}_oldest",
                    tool="inventory_update_by_name_oldest",
                    parameters={**original_task.parameters, "token": context.get("token")},
                    description=f"最古の{item_name}を更新"
                )
        
        elif any(word in user_input for word in ["新しい", "最新", "latest"]):
            if "delete" in original_task.tool:
                return Task(
                    id=f"{original_task.id}_latest",
                    tool="inventory_delete_by_name_latest",
                    parameters={"item_name": item_name, "token": context.get("token")},
                    description=f"最新の{item_name}を削除"
                )
            elif "update" in original_task.tool:
                return Task(
                    id=f"{original_task.id}_latest",
                    tool="inventory_update_by_name_latest",
                    parameters={**original_task.parameters, "token": context.get("token")},
                    description=f"最新の{item_name}を更新"
                )
        
        elif any(word in user_input for word in ["全部", "全て", "all"]):
            return Task(
                id=f"{original_task.id}_all",
                tool=original_task.tool,
                parameters={**original_task.parameters, "token": context.get("token")},
                description=f"全ての{item_name}を{self._get_action_description(original_task)}"
            )
        
        elif any(word in user_input for word in ["確認", "confirm"]):
            return Task(
                id=f"{original_task.id}_confirm",
                tool=original_task.tool,
                parameters={**original_task.parameters, "token": context.get("token")},
                description=original_task.description
            )
        
        # 不明な選択の場合は元のタスクを返す
        return Task(
            id=f"{original_task.id}_unknown",
            tool=original_task.tool,
            parameters={**original_task.parameters, "token": context.get("token")},
            description=original_task.description
        )
