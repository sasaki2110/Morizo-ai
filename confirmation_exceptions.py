#!/usr/bin/env python3
"""
確認プロセス用のカスタム例外
並列実行中のキャンセル処理とタスクチェーンの保持
"""

from typing import List, Dict, Any
from action_planner import Task


class UserConfirmationRequired(Exception):
    """ユーザー確認が必要な場合の例外"""
    
    def __init__(self, confirmation_context: dict, executed_tasks: List[Task] = None, remaining_tasks: List[Task] = None):
        self.confirmation_context = confirmation_context
        self.executed_tasks = executed_tasks or []
        self.remaining_tasks = remaining_tasks or []
        super().__init__("User confirmation required")


class TaskExecutionCancelled(Exception):
    """タスク実行がキャンセルされた場合の例外"""
    
    def __init__(self, reason: str, rollback_required: bool = False, executed_tasks: List[Task] = None):
        self.reason = reason
        self.rollback_required = rollback_required
        self.executed_tasks = executed_tasks or []
        super().__init__(f"Task execution cancelled: {reason}")


class ConfirmationTimeout(Exception):
    """確認プロセスのタイムアウト例外"""
    
    def __init__(self, timeout_seconds: int = 300):
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Confirmation timeout after {timeout_seconds} seconds")


class InvalidConfirmationResponse(Exception):
    """無効な確認応答の例外"""
    
    def __init__(self, user_input: str, expected_options: List[str]):
        self.user_input = user_input
        self.expected_options = expected_options
        super().__init__(f"Invalid confirmation response: '{user_input}'. Expected one of: {expected_options}")
