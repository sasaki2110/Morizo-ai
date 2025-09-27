"""
Morizo AI - Smart Pantry AI Agent
Copyright (c) 2024 Morizo AI Project. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, modification,
distribution, or use is strictly prohibited without explicit written permission.

For licensing inquiries, contact: [contact@morizo-ai.com]
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from action_planner import Task

logger = logging.getLogger("morizo_ai.task_manager")

class TaskManager:
    """タスク管理クラス"""
    
    def __init__(self):
        self.tasks: List[Task] = []
        self.current_task_index = 0
        self.completed_tasks: List[Task] = []
        self.failed_tasks: List[Task] = []
    
    def add_tasks(self, tasks: List[Task]):
        """
        タスクを追加する
        
        Args:
            tasks: 追加するタスクリスト
        """
        self.tasks.extend(tasks)
        logger.info(f"📋 [タスク管理] {len(tasks)}個のタスクを追加")
    
    def get_next_task(self) -> Optional[Task]:
        """
        次の実行可能なタスクを取得する
        
        Returns:
            次のタスク（実行可能なものがない場合はNone）
        """
        # 依存関係を満たしているタスクを探す
        for i, task in enumerate(self.tasks):
            if task.status == "pending" and self._are_dependencies_met(task):
                logger.info(f"📋 [タスク管理] 次のタスクを取得: {task.description}")
                return task
        
        logger.info("📋 [タスク管理] 実行可能なタスクがありません")
        return None
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """
        タスクIDでタスクを取得する
        
        Args:
            task_id: タスクID
            
        Returns:
            該当するタスク（見つからない場合はNone）
        """
        # 全タスクリストから検索
        all_tasks = self.tasks + self.completed_tasks + self.failed_tasks
        
        for task in all_tasks:
            if task.id == task_id:
                return task
        
        logger.warning(f"⚠️ [タスク管理] タスクIDが見つかりません: {task_id}")
        return None
    
    def mark_task_in_progress(self, task: Task):
        """
        タスクを実行中にマークする
        
        Args:
            task: マークするタスク
        """
        task.status = "in_progress"
        logger.info(f"📋 [タスク管理] タスク実行開始: {task.description}")
    
    def mark_task_completed(self, task: Task, result: Dict[str, Any] = None):
        """
        タスクを完了にマークする
        
        Args:
            task: マークするタスク
            result: 実行結果
        """
        task.status = "completed"
        if result:
            task.result = result
        self.completed_tasks.append(task)
        logger.info(f"📋 [タスク管理] タスク完了: {task.description}")
    
    def mark_task_failed(self, task: Task, error: str = None):
        """
        タスクを失敗にマークする
        
        Args:
            task: マークするタスク
            error: エラーメッセージ
        """
        task.status = "failed"
        if error:
            task.error = error
        self.failed_tasks.append(task)
        logger.error(f"📋 [タスク管理] タスク失敗: {task.description} - {error}")
    
    def has_remaining_tasks(self) -> bool:
        """
        実行可能なタスクが残っているかチェック
        
        Returns:
            実行可能なタスクがあるかどうか
        """
        for task in self.tasks:
            if task.status == "pending" and self._are_dependencies_met(task):
                return True
        return False
    
    def get_task_status(self) -> Dict[str, Any]:
        """
        タスクの状態を取得する
        
        Returns:
            タスクの状態情報
        """
        total_tasks = len(self.tasks)
        completed_count = len(self.completed_tasks)
        failed_count = len(self.failed_tasks)
        pending_count = total_tasks - completed_count - failed_count
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_count,
            "failed_tasks": failed_count,
            "pending_tasks": pending_count,
            "completion_rate": completed_count / total_tasks if total_tasks > 0 else 0
        }
    
    def get_task_summary(self) -> str:
        """
        タスクの要約を取得する
        
        Returns:
            タスクの要約文字列
        """
        status = self.get_task_status()
        summary = f"""
📋 タスク実行状況:
- 総タスク数: {status['total_tasks']}
- 完了: {status['completed_tasks']}
- 失敗: {status['failed_tasks']}
- 待機中: {status['pending_tasks']}
- 完了率: {status['completion_rate']:.1%}
"""
        return summary
    
    def _are_dependencies_met(self, task: Task) -> bool:
        """
        タスクの依存関係が満たされているかチェック
        
        Args:
            task: チェックするタスク
            
        Returns:
            依存関係が満たされているかどうか
        """
        if not task.dependencies:
            return True
        
        # 依存するタスクが完了しているかチェック
        for dep_id in task.dependencies:
            dep_task = self._find_task_by_id(dep_id)
            if not dep_task or dep_task.status != "completed":
                logger.debug(f"📋 [依存関係] タスク {task.id} の依存関係 {dep_id} が未完了")
                return False
        
        logger.debug(f"📋 [依存関係] タスク {task.id} の依存関係が満たされています")
        return True
    
    def _find_task_by_id(self, task_id: str) -> Optional[Task]:
        """
        IDでタスクを検索する
        
        Args:
            task_id: 検索するタスクID
            
        Returns:
            見つかったタスク（見つからない場合はNone）
        """
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def reset(self):
        """タスクマネージャーをリセットする"""
        self.tasks = []
        self.current_task_index = 0
        self.completed_tasks = []
        self.failed_tasks = []
        logger.info("📋 [タスク管理] タスクマネージャーをリセット")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        タスクマネージャーの状態を辞書形式で返す
        
        Returns:
            タスクマネージャーの状態
        """
        return {
            "tasks": [asdict(task) for task in self.tasks],
            "completed_tasks": [asdict(task) for task in self.completed_tasks],
            "failed_tasks": [asdict(task) for task in self.failed_tasks],
            "current_task_index": self.current_task_index,
            "status": self.get_task_status()
        }
