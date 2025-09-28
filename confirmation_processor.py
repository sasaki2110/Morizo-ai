#!/usr/bin/env python3
"""
確認プロセス処理
曖昧性検出後の確認プロセスとユーザー選択の処理
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from action_planner import Task
from ambiguity_detector import AmbiguityInfo
import logging

# ログ設定
logger = logging.getLogger('morizo_ai.confirmation')


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
                "original_task": ambiguity_info.task,
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
        
        # ユーザー選択に基づいて具体的なタスクを生成
        current_task = self._create_task_from_choice(user_input, context)
        
        # 残りのタスクチェーンを取得（Taskオブジェクトに変換）
        remaining_task_dicts = context.get("remaining_task_chain", [])
        remaining_tasks = []
        for task_dict in remaining_task_dicts:
            try:
                task = Task.from_dict(task_dict)
                remaining_tasks.append(task)
            except Exception as e:
                logger.warning(f"⚠️ [確認プロセス] タスク変換エラー: {e}")
                continue
        
        # 元の曖昧なタスクを除外（置換済みのため）
        original_task = context.get("original_task")
        if original_task:
            remaining_tasks = self._filter_out_ambiguous_task(remaining_tasks, original_task)
            logger.info(f"🔄 [確認プロセス] 元の曖昧なタスクを除外: {original_task.id}")
        
        return TaskExecutionPlan(
            tasks=[current_task] + remaining_tasks,
            continue_execution=True
        )
    
    def _filter_out_ambiguous_task(self, remaining_tasks: List[Task], original_task) -> List[Task]:
        """元の曖昧なタスクを除外し、依存関係を修正"""
        filtered_tasks = []
        for task in remaining_tasks:
            # 元のタスクと同じIDまたは同じツール・パラメータのタスクを除外
            if (task.id == original_task.id or 
                (task.tool == original_task.tool and task.parameters == original_task.parameters)):
                logger.info(f"🔄 [確認プロセス] 曖昧なタスクを除外: {task.id}")
                continue
            
            # 依存関係から元のタスクを除外
            if original_task.id in task.dependencies:
                task.dependencies = [dep for dep in task.dependencies if dep != original_task.id]
                logger.info(f"🔄 [確認プロセス] 依存関係を修正: {task.id} - {task.dependencies}")
            
            filtered_tasks.append(task)
        return filtered_tasks
    
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
            logger.error(f"❌ [確認プロセス] 無効な確認コンテキスト: item_name={item_name}, original_task={original_task}")
            logger.error(f"❌ [確認プロセス] コンテキスト内容: {context}")
            raise ValueError("Invalid confirmation context")
        
        # 自然言語での選択処理
        if any(word in user_input for word in ["古い", "最古", "oldest"]):
            if "delete" in original_task.tool:
                return Task(
                    id=f"{original_task.id}_oldest",
                    tool="inventory_delete_by_name_oldest",
                    parameters={"item_name": item_name},
                    description=f"最古の{item_name}を削除"
                )
            elif "update" in original_task.tool:
                return Task(
                    id=f"{original_task.id}_oldest",
                    tool="inventory_update_by_name_oldest",
                    parameters={**original_task.parameters},
                    description=f"最古の{item_name}を更新"
                )
        
        elif any(word in user_input for word in ["新しい", "最新", "latest"]):
            if "delete" in original_task.tool:
                return Task(
                    id=f"{original_task.id}_latest",
                    tool="inventory_delete_by_name_latest",
                    parameters={"item_name": item_name},
                    description=f"最新の{item_name}を削除"
                )
            elif "update" in original_task.tool:
                return Task(
                    id=f"{original_task.id}_latest",
                    tool="inventory_update_by_name_latest",
                    parameters={**original_task.parameters},
                    description=f"最新の{item_name}を更新"
                )
        
        elif any(word in user_input for word in ["全部", "全て", "all"]):
            return Task(
                id=f"{original_task.id}_all",
                tool=original_task.tool,
                parameters={**original_task.parameters},
                description=f"全ての{item_name}を{self._get_action_description(original_task)}"
            )
        
        elif any(word in user_input for word in ["確認", "confirm"]):
            return Task(
                id=f"{original_task.id}_confirm",
                tool=original_task.tool,
                parameters={**original_task.parameters},
                description=original_task.description
            )
        
        # 不明な選択の場合は明確化を求める
        logger.warning(f"⚠️ [確認プロセス] 不明な選択肢: {user_input}")
        return self._handle_unknown_choice(user_input, context)
    
    def _handle_unknown_choice(self, user_input: str, context: dict) -> Task:
        """不明な選択肢の処理"""
        logger.warning(f"⚠️ [確認プロセス] 不明な選択肢を処理: {user_input}")
        
        # デフォルトの選択肢を提案
        return Task(
            id="clarify_choice",
            tool="clarify_confirmation",
            parameters={
                "message": f"選択肢が分からないようです。'{user_input}' は理解できませんでした。\n\n以下のいずれかでお答えください：\n- 古いアイテムを操作\n- 新しいアイテムを操作\n- 全部操作\n- キャンセル",
                "original_context": context,
                "user_input": user_input
            },
            description="選択肢の明確化"
        )
