#!/usr/bin/env python3
"""
SSE送信機能の統一管理
Server-Sent Eventsによるリアルタイム進捗表示の送信機能
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime

logger = logging.getLogger("morizo_ai.sse_sender")

class SSESender:
    """SSE送信機能の統一管理クラス"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.connections: Dict[str, asyncio.Queue] = {}
        self.is_active = True
        logger.info(f"📡 [SSESender] 初期化完了: session_id={session_id}, connections={len(self.connections)}")
    
    def add_connection(self, connection_id: str, queue: asyncio.Queue):
        """SSE接続を追加"""
        self.connections[connection_id] = queue
        logger.info(f"📡 [SSE] 接続追加: session_id={self.session_id}, connection_id={connection_id}")
    
    def remove_connection(self, connection_id: str):
        """SSE接続を削除"""
        if connection_id in self.connections:
            del self.connections[connection_id]
            logger.info(f"📡 [SSE] 接続削除: session_id={self.session_id}, connection_id={connection_id}")
    
    def send_progress(self, progress_info: Dict[str, Any]):
        """進捗情報を送信"""
        if not self.connections or not self.is_active:
            return
        
        progress_data = {
            "type": "progress",
            "sse_session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "message": self._generate_progress_message(progress_info),
            "progress": progress_info
        }
        
        # 全接続に送信
        self._send_to_all_connections(progress_data)
    
    def send_error(self, error_message: str, error_code: str = "TASK_FAILED", details: str = ""):
        """エラー情報を送信"""
        if not self.connections or not self.is_active:
            return
        
        error_data = {
            "type": "error",
            "sse_session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "message": error_message,
            "error": {
                "code": error_code,
                "message": error_message,
                "details": details or "タスク実行中にエラーが発生しました"
            },
            "progress": {
                "completed_tasks": 0,
                "total_tasks": 0,
                "progress_percentage": 0,
                "current_task": "エラー発生",
                "remaining_tasks": 0,
                "is_complete": False
            }
        }
        
        self._send_to_all_connections(error_data)
    
    def send_complete(self, result: Dict[str, Any]):
        """完了情報を送信"""
        if not self.connections or not self.is_active:
            return
        
        complete_data = {
            "type": "complete",
            "sse_session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "message": "処理が完了しました",
            "progress": {
                "completed_tasks": result.get("total_tasks", 0),
                "total_tasks": result.get("total_tasks", 0),
                "progress_percentage": 100,
                "current_task": "完了",
                "remaining_tasks": 0,
                "is_complete": True
            },
            "result": result
        }
        
        self._send_to_all_connections(complete_data)
    
    def send_start(self, total_tasks: int = 0):
        """開始情報を送信"""
        if not self.connections or not self.is_active:
            return
        
        start_data = {
            "type": "start",
            "sse_session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "message": "処理を開始します...",
            "progress": {
                "completed_tasks": 0,
                "total_tasks": total_tasks,
                "progress_percentage": 0,
                "current_task": "タスクを分析中...",
                "remaining_tasks": total_tasks,
                "is_complete": False
            }
        }
        
        self._send_to_all_connections(start_data)
    
    def _send_to_all_connections(self, data: Dict[str, Any]):
        """全接続にデータを送信"""
        if not self.connections:
            return
        
        message = f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
        
        # 接続が切断されたものを削除
        disconnected_connections = set()
        
        for connection_id, queue in self.connections.items():
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                logger.warning(f"⚠️ [SSE] キューが満杯: session_id={self.session_id}, connection_id={connection_id}")
            except Exception as e:
                logger.warning(f"⚠️ [SSE] 送信エラー: session_id={self.session_id}, connection_id={connection_id}, error={str(e)}")
                disconnected_connections.add(connection_id)
        
        # 切断された接続を削除
        for connection_id in disconnected_connections:
            self.remove_connection(connection_id)
    
    def _generate_progress_message(self, progress_info: Dict[str, Any]) -> str:
        """進捗メッセージを生成"""
        completed = progress_info.get("completed_tasks", 0)
        total = progress_info.get("total_tasks", 0)
        current_task = progress_info.get("current_task", "待機中")
        
        if total > 0:
            percentage = int((completed / total) * 100)
            return f"進捗: {completed}/{total} 完了 ({percentage}%)\n\n{current_task}"
        else:
            return f"進捗: {current_task}"
    
    def close(self):
        """SSE送信機能を終了"""
        self.is_active = False
        self.connections.clear()
        logger.info(f"📡 [SSE] 送信機能終了: session_id={self.session_id}")


# グローバルなSSE送信機能管理
_sse_senders: Dict[str, SSESender] = {}

def get_sse_sender(session_id: str) -> SSESender:
    """SSE送信機能を取得（シングルトン）"""
    logger.info(f"📡 [SSESender] get_sse_sender呼び出し: session_id={session_id}")
    if session_id not in _sse_senders:
        logger.info(f"📡 [SSESender] 新しいSSESenderを作成: session_id={session_id}")
        _sse_senders[session_id] = SSESender(session_id)
    else:
        logger.info(f"📡 [SSESender] 既存のSSESenderを取得: session_id={session_id}")
    return _sse_senders[session_id]

def remove_sse_sender(session_id: str):
    """SSE送信機能を削除"""
    if session_id in _sse_senders:
        _sse_senders[session_id].close()
        del _sse_senders[session_id]
        logger.info(f"📡 [SSE] 送信機能削除: session_id={session_id}")

def cleanup_sse_senders():
    """全てのSSE送信機能をクリーンアップ"""
    for session_id in list(_sse_senders.keys()):
        remove_sse_sender(session_id)
