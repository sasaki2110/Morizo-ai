#!/usr/bin/env python3
"""
タスクチェーン管理
確認プロセス中のタスクチェーンの保持と再開処理
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from action_planner import Task


@dataclass
class TaskChainState:
    """タスクチェーンの状態"""
    pending_tasks: List[Task]
    executed_tasks: List[Task]
    current_task_index: int
    confirmation_context: Optional[Dict[str, Any]] = None
    is_paused: bool = False


class TaskChainManager:
    """タスクチェーン管理クラス"""
    
    def __init__(self):
        self.state = TaskChainState(
            pending_tasks=[],
            executed_tasks=[],
            current_task_index=0
        )
    
    def set_task_chain(self, tasks: List[Task]):
        """タスクチェーンを設定"""
        self.state.pending_tasks = tasks
        self.state.executed_tasks = []
        self.state.current_task_index = 0
        self.state.is_paused = False
        self.state.confirmation_context = None
    
    def get_remaining_tasks(self) -> List[Task]:
        """残りのタスクを取得"""
        return self.state.pending_tasks[self.state.current_task_index:]
    
    def get_executed_tasks(self) -> List[Task]:
        """実行済みタスクを取得"""
        return self.state.executed_tasks
    
    def get_current_task(self) -> Optional[Task]:
        """現在のタスクを取得"""
        if self.state.current_task_index < len(self.state.pending_tasks):
            return self.state.pending_tasks[self.state.current_task_index]
        return None
    
    def advance_task_index(self):
        """タスクインデックスを進める"""
        if self.state.current_task_index < len(self.state.pending_tasks):
            # 現在のタスクを実行済みに移動
            current_task = self.state.pending_tasks[self.state.current_task_index]
            self.state.executed_tasks.append(current_task)
            self.state.current_task_index += 1
    
    def pause_for_confirmation(self, confirmation_context: Dict[str, Any]):
        """確認プロセスのために一時停止"""
        self.state.is_paused = True
        self.state.confirmation_context = confirmation_context
    
    def resume_after_confirmation(self):
        """確認プロセス後に再開"""
        self.state.is_paused = False
        self.state.confirmation_context = None
    
    def is_complete(self) -> bool:
        """タスクチェーンが完了したかどうか"""
        return self.state.current_task_index >= len(self.state.pending_tasks)
    
    def is_paused(self) -> bool:
        """一時停止中かどうか"""
        return self.state.is_paused
    
    def get_progress_info(self) -> Dict[str, Any]:
        """進捗情報を取得"""
        total_tasks = len(self.state.pending_tasks)
        completed_tasks = len(self.state.executed_tasks)
        remaining_tasks = len(self.get_remaining_tasks())
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "remaining_tasks": remaining_tasks,
            "progress_percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "is_complete": self.is_complete(),
            "is_paused": self.is_paused()
        }
    
    def generate_progress_message(self) -> str:
        """進捗メッセージを生成"""
        progress_info = self.get_progress_info()
        
        if progress_info["is_complete"]:
            return f"進捗: {progress_info['completed_tasks']}/{progress_info['total_tasks']} 完了\n\n全ての処理が完了しました。"
        
        message = f"進捗: {progress_info['completed_tasks']}/{progress_info['total_tasks']} 完了\n\n"
        
        if progress_info["remaining_tasks"] > 0:
            message += "残りの処理：\n"
            remaining_tasks = self.get_remaining_tasks()
            for i, task in enumerate(remaining_tasks, 1):
                message += f"{i}. {task.description}\n"
        
        return message
    
    def reset(self):
        """タスクチェーンをリセット"""
        self.state = TaskChainState(
            pending_tasks=[],
            executed_tasks=[],
            current_task_index=0
        )
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """状態のスナップショットを取得"""
        return {
            "pending_tasks": [
                {
                    "id": task.id if hasattr(task, 'id') else f"task_{i}",
                    "description": task.description,
                    "tool": task.tool,
                    "parameters": task.parameters
                }
                for i, task in enumerate(self.state.pending_tasks)
            ],
            "executed_tasks": [
                {
                    "id": task.id if hasattr(task, 'id') else f"task_{i}",
                    "description": task.description,
                    "tool": task.tool,
                    "parameters": task.parameters
                }
                for i, task in enumerate(self.state.executed_tasks)
            ],
            "current_task_index": self.state.current_task_index,
            "confirmation_context": self.state.confirmation_context,
            "is_paused": self.state.is_paused,
            "progress_info": self.get_progress_info()
        }
