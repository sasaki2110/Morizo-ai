"""
Morizo AI - Smart Pantry AI Agent
Copyright (c) 2024 Morizo AI Project. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, modification,
distribution, or use is strictly prohibited without explicit written permission.

For licensing inquiries, contact: [contact@morizo-ai.com]
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import logging
import os

# ログ設定
logger = logging.getLogger('morizo_ai.session')


class SessionContext:
    """ユーザーセッションのコンテキスト管理"""
    
    def __init__(self, user_id: str, token: str = None):
        self.user_id = user_id
        self.token = token  # 認証トークンを追加
        self.session_id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
        
        # 操作履歴（最大10件）
        self.operation_history = []
        self.max_history = 10
        
        # ユーザー設定
        self.user_preferences = {}
        
        # 会話コンテキスト
        self.conversation_context = []
        
        # 最後の操作
        self.last_operation = None
        
        # 保留中の確認
        self.pending_confirmation = None
        
        # Phase 4.4.3: 確認プロセス用の拡張
        self.pending_confirmation_context = None  # 保留中の確認コンテキスト
        self.task_chain_state = None  # タスクチェーンの状態
        self.executed_tasks = []  # 実行済みタスク
        self.remaining_tasks = []  # 残りタスク
        self.confirmation_timeout = 300  # 確認タイムアウト（5分）
        
        # ストリーミング状態管理
        self.is_streaming = False  # ストリーミング中かどうか
        self.streaming_start_time = None  # ストリーミング開始時刻
        self.streaming_timeout = 60  # ストリーミングタイムアウト（60秒）
        
        # 新規追加: TrueReactAgentとTaskChainManagerの管理
        self.react_agent: Optional[Any] = None  # TrueReactAgentインスタンス
        self.task_chain_manager: Optional[Any] = None  # TaskChainManagerインスタンス
        
        
    def add_operation(self, operation_type: str, details: Dict[str, Any]):
        """操作履歴を追加（最大10件制限）"""
        operation = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "operation": operation_type,
            "details": details,
            "before_state": self.current_inventory.copy(),
            "after_state": None  # 操作後に更新
        }
        
        self.operation_history.append(operation)
        
        # 履歴の上限管理（10件制限）
        if len(self.operation_history) > self.max_history:
            removed_operation = self.operation_history.pop(0)
            print(f"📝 履歴上限に達したため、古い操作を削除: {removed_operation['operation']}")
        
        self.last_activity = datetime.now()
        
    def update_last_operation_after_state(self, after_state: List[Dict]):
        """最後の操作のafter_stateを更新"""
        if self.operation_history:
            self.operation_history[-1]["after_state"] = after_state.copy()
            
    def get_recent_operations(self, count: int = 5) -> List[Dict]:
        """最近の操作を取得"""
        return self.operation_history[-count:] if count <= len(self.operation_history) else self.operation_history
        
    def get_session_duration(self) -> timedelta:
        """セッションの継続時間を取得"""
        return datetime.now() - self.created_at
        
    def clear_history(self):
        """操作履歴をクリア"""
        self.operation_history = []
        print(f"🧹 ユーザー {self.user_id} の操作履歴をクリアしました")
        
    def clear_conversation_context(self):
        """会話コンテキストをクリア"""
        self.conversation_context = []
        print(f"💬 ユーザー {self.user_id} の会話コンテキストをクリアしました")
        
    # Phase 4.4.3: 確認プロセス管理メソッド
    def save_confirmation_context(self, confirmation_context: dict):
        """確認コンテキストを保存"""
        self.pending_confirmation_context = confirmation_context
        self.last_activity = datetime.now()
        logger.debug(f"💾 [セッション] 確認コンテキストを保存: {self.user_id}")
        
    def get_confirmation_context(self) -> Optional[dict]:
        """確認コンテキストを取得"""
        return self.pending_confirmation_context
        
    def clear_confirmation_context(self):
        """確認コンテキストをクリア"""
        self.pending_confirmation_context = None
        self.task_chain_state = None
        self.executed_tasks = []
        self.remaining_tasks = []
        logger.debug(f"🧹 [セッション] 確認コンテキストをクリア: {self.user_id}")
        
    def is_confirmation_context_valid(self) -> bool:
        """確認コンテキストが有効かチェック"""
        if not self.pending_confirmation_context:
            return False
        
        # 確認コンテキストのタイムアウトチェック
        time_diff = datetime.now() - self.last_activity
        return time_diff.total_seconds() < self.confirmation_timeout
        
    def save_task_chain_state(self, executed_tasks: List[Any], remaining_tasks: List[Any]):
        """タスクチェーン状態を保存"""
        self.executed_tasks = executed_tasks.copy()
        self.remaining_tasks = remaining_tasks.copy()
        self.task_chain_state = {
            "executed_count": len(executed_tasks),
            "remaining_count": len(remaining_tasks),
            "timestamp": datetime.now().isoformat()
        }
        logger.debug(f"📊 [セッション] タスクチェーン状態を保存: 実行済み{len(executed_tasks)}件, 残り{len(remaining_tasks)}件")
        
    # ストリーミング状態管理メソッド
    def set_streaming_state(self, is_streaming: bool):
        """ストリーミング状態を設定"""
        self.is_streaming = is_streaming
        if is_streaming:
            self.streaming_start_time = datetime.now()
            logger.debug(f"📡 [セッション] ストリーミング開始: {self.user_id}")
        else:
            self.streaming_start_time = None
            logger.debug(f"📡 [セッション] ストリーミング終了: {self.user_id}")
    
    def is_streaming_active(self) -> bool:
        """ストリーミングがアクティブかチェック"""
        if not self.is_streaming or not self.streaming_start_time:
            return False
        
        # ストリーミングタイムアウトチェック
        time_diff = datetime.now() - self.streaming_start_time
        return time_diff.total_seconds() < self.streaming_timeout
    
    def get_streaming_duration(self) -> float:
        """ストリーミング継続時間を取得（秒）"""
        if not self.streaming_start_time:
            return 0.0
        time_diff = datetime.now() - self.streaming_start_time
        return time_diff.total_seconds()
        
    def to_dict(self) -> Dict[str, Any]:
        """セッション情報を辞書形式で取得"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "operation_history_count": len(self.operation_history),
            "conversation_context_count": len(self.conversation_context),
            "session_duration_minutes": self.get_session_duration().total_seconds() / 60,
            "is_streaming": self.is_streaming,
            "streaming_duration_seconds": self.get_streaming_duration()
        }


class SessionManager:
    """セッション管理システム（メモリ内）"""
    
    def __init__(self, session_timeout_minutes: int = 30):
        self.active_sessions: Dict[str, SessionContext] = {}
        self.session_timeout = session_timeout_minutes
        
    def get_or_create_session(self, user_id: str, token: str = None, sse_session_id: str = None) -> SessionContext:
        """セッションを取得または作成"""
        # 既存セッションをチェック
        if user_id in self.active_sessions:
            session = self.active_sessions[user_id]
            if self._is_session_valid(session):
                print(f"✅ 既存セッションを取得: {user_id}")
                # トークンを更新
                if token:
                    session.token = token
                # SSEセッションIDを設定
                if sse_session_id and hasattr(session, 'react_agent') and session.react_agent:
                    logger.info(f"📡 [セッション管理] 既存セッションにSSEセッションID設定: {sse_session_id}")
                    session.react_agent.set_sse_session_id(sse_session_id)
                return session
            else:
                # タイムアウトしたセッションをクリア
                print(f"⏰ セッションタイムアウト: {user_id}")
                self.clear_session(user_id)
        
        # 新規セッション作成
        session = SessionContext(user_id, token)
        
        # 新規追加: TrueReactAgentとTaskChainManagerを初期化
        try:
            from true_react_agent import TrueReactAgent
            from openai import OpenAI
            
            openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            session.react_agent = TrueReactAgent(openai_client, sse_session_id)
            session.task_chain_manager = session.react_agent.task_chain_manager
            logger.info(f"🤖 [セッション管理] TrueReactAgent初期化完了: {user_id}")
            if sse_session_id:
                logger.info(f"📡 [セッション管理] 新規セッションにSSEセッションID設定: {sse_session_id}")
        except Exception as e:
            logger.error(f"❌ [セッション管理] TrueReactAgent初期化エラー: {str(e)}")
            # エラーが発生してもセッションは作成する
        
        self.active_sessions[user_id] = session
        print(f"🆕 新規セッション作成: {user_id}")
        return session
        
    def clear_session(self, user_id: str, reason: str = "manual"):
        """セッションをクリア（方法A: 明示的なクリア）"""
        if user_id in self.active_sessions:
            session_info = self.active_sessions[user_id].to_dict()
            del self.active_sessions[user_id]
            print(f"🧹 セッションクリア ({reason}): {user_id}")
            print(f"   - セッション継続時間: {session_info['session_duration_minutes']:.1f}分")
            print(f"   - 操作履歴: {session_info['operation_history_count']}件")
            print(f"   - 在庫アイテム: {session_info['current_inventory_count']}件")
        else:
            print(f"⚠️ セッションが見つかりません: {user_id}")
            
    def clear_expired_sessions(self):
        """期限切れセッションを自動クリア（方法B: 自動タイムアウト）"""
        expired_users = []
        current_time = datetime.now()
        
        for user_id, session in self.active_sessions.items():
            if not self._is_session_valid(session):
                expired_users.append(user_id)
                
        for user_id in expired_users:
            # TaskChainManagerのリセット
            session = self.active_sessions.get(user_id)
            if session and session.task_chain_manager:
                try:
                    session.task_chain_manager.reset()
                    logger.info(f"🧹 [セッション管理] TaskChainManagerをリセット: {user_id}")
                except Exception as e:
                    logger.error(f"❌ [セッション管理] TaskChainManagerリセットエラー: {str(e)}")
            
            self.clear_session(user_id, reason="timeout")
            
        if expired_users:
            print(f"🕐 {len(expired_users)}件の期限切れセッションをクリアしました")
            
        # Phase 4.4.3: 期限切れの確認コンテキストもクリア
        self.clear_expired_confirmation_contexts()
            
    def clear_old_history(self, user_id: str):
        """古い履歴をクリア（方法C: 操作履歴の制限）"""
        if user_id in self.active_sessions:
            session = self.active_sessions[user_id]
            if len(session.operation_history) >= session.max_history:
                # 古い履歴を削除（既にSessionContextで自動管理されているが、明示的に実行）
                old_count = len(session.operation_history)
                session.operation_history = session.operation_history[-5:]  # 最新5件のみ保持
                removed_count = old_count - len(session.operation_history)
                print(f"📝 古い履歴をクリア: {user_id} ({removed_count}件削除)")
                
    def _is_session_valid(self, session: SessionContext) -> bool:
        """セッションが有効かチェック"""
        if not session.last_activity:
            return False
            
        time_diff = datetime.now() - session.last_activity
        return time_diff.total_seconds() < (self.session_timeout * 60)
        
    def get_session_status(self, user_id: str) -> Dict[str, Any]:
        """セッション状態を取得"""
        if user_id in self.active_sessions:
            session = self.active_sessions[user_id]
            return session.to_dict()
        else:
            return {"error": "セッションが見つかりません"}
            
    def get_all_sessions_info(self) -> Dict[str, Any]:
        """全セッションの情報を取得"""
        return {
            "total_sessions": len(self.active_sessions),
            "sessions": {
                user_id: session.to_dict() 
                for user_id, session in self.active_sessions.items()
            }
        }
        
    def clear_all_sessions(self):
        """全セッションをクリア（開発・テスト用）"""
        session_count = len(self.active_sessions)
        self.active_sessions.clear()
        print(f"🧹 全セッションをクリアしました ({session_count}件)")
        
    # Phase 4.4.3: 確認プロセス管理メソッド
    def clear_expired_confirmation_contexts(self):
        """期限切れの確認コンテキストをクリア"""
        expired_users = []
        
        for user_id, session in self.active_sessions.items():
            if session.pending_confirmation_context and not session.is_confirmation_context_valid():
                expired_users.append(user_id)
                session.clear_confirmation_context()
                
        if expired_users:
            logger.info(f"⏰ {len(expired_users)}件の期限切れ確認コンテキストをクリアしました")
            
    def get_confirmation_context(self, user_id: str) -> Optional[dict]:
        """ユーザーの確認コンテキストを取得"""
        if user_id in self.active_sessions:
            session = self.active_sessions[user_id]
            if session.is_confirmation_context_valid():
                return session.get_confirmation_context()
            else:
                # 期限切れの場合はクリア
                session.clear_confirmation_context()
        return None


# グローバルセッションマネージャー
session_manager = SessionManager()


# テスト用の関数
def test_session_manager():
    """セッション管理システムのテスト"""
    print("🧪 セッション管理システムテスト開始")
    
    # テストユーザー
    test_user = "test-user-123"
    
    # 1. 新規セッション作成
    session = session_manager.get_or_create_session(test_user)
    print(f"✅ セッション作成: {session.session_id}")
    
    # 2. 操作履歴の追加
    session.add_operation("CREATE", {"item_name": "牛乳", "quantity": 2})
    session.add_operation("READ", {"item_name": "牛乳"})
    session.add_operation("UPDATE", {"item_name": "牛乳", "quantity": 3})
    
    # 3. 履歴上限テスト（10件を超える追加）
    for i in range(8):  # 既に3件あるので、8件追加して11件にする
        session.add_operation("TEST", {"test_id": i})
    
    print(f"📝 操作履歴: {len(session.operation_history)}件")
    
    # 4. セッション状態確認
    status = session_manager.get_session_status(test_user)
    print(f"📊 セッション状態: {status}")
    
    # 5. 明示的クリア（方法A）
    session_manager.clear_session(test_user, reason="test")
    
    # 6. 全セッション情報
    all_info = session_manager.get_all_sessions_info()
    print(f"📋 全セッション情報: {all_info}")
    
    print("🎉 セッション管理システムテスト完了")


if __name__ == "__main__":
    test_session_manager()
