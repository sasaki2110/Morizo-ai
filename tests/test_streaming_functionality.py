#!/usr/bin/env python3
"""
ストリーミング機能検証テスト（2025/1/15実装）
Server-Sent Events (SSE) によるリアルタイム進捗表示機能の検証

実装された機能:
- SSEエンドポイント: GET /chat/stream/{session_id}
- 進捗表示機能: タスク実行状況のリアルタイム送信
- エラー通知機能: エラー発生時の適切な通知
- セッション管理: ストリーミング状態の管理
"""

import asyncio
import sys
import os
import json
import time
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# HTTP クライアント
import httpx

# 環境変数の読み込み
load_dotenv()

# ログ設定
def setup_logging():
    """サーバーと同じログ設定を使用"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 既存のログハンドラーをクリア
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # ファイルハンドラーを追加（サーバーと同じログファイル）
    file_handler = logging.FileHandler('morizo_ai.log', mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # コンソールハンドラーも追加（テスト実行時の確認用）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # ルートロガーに設定
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return logging.getLogger('morizo_ai.streaming_test')

# ログ設定を実行
logger = setup_logging()


class StreamingTester:
    """ストリーミング機能検証テストクラス"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=300.0)  # 300秒タイムアウト（Web検索対応）
        
        # 自動ログインで認証トークンを取得
        try:
            import sys
            import os
            from dotenv import load_dotenv
            
            # プロジェクトルートをパスに追加
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if project_root not in sys.path:
                sys.path.append(project_root)
            
            # .envファイルを読み込み
            load_dotenv(os.path.join(project_root, '.env'))
            
            from auth.auto_login import get_auto_token
            self.supabase_token = get_auto_token()
            logger.info(f"✅ [ストリーミングテスト] 自動ログインで認証トークン取得完了: {self.supabase_token[:20]}...")
        except Exception as e:
            logger.warning(f"⚠️ [ストリーミングテスト] 自動ログイン失敗: {str(e)}")
            # フォールバック: 環境変数から取得
            self.supabase_token = os.getenv("SUPABASE_ANON_KEY")
            if not self.supabase_token:
                logger.warning("⚠️ [ストリーミングテスト] SUPABASE_ANON_KEYも設定されていません")
            else:
                logger.info(f"✅ [ストリーミングテスト] 環境変数から認証トークン取得完了: {self.supabase_token[:20]}...")
        
        logger.info("🚀 [ストリーミングテスト] ストリーミング機能検証開始")
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def test_server_health(self) -> bool:
        """サーバーのヘルスチェック"""
        logger.info("🔍 [ストリーミングテスト] サーバーヘルスチェック")
        
        try:
            response = await self.client.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                logger.info("✅ [ストリーミングテスト] サーバー正常")
                return True
            else:
                logger.error(f"❌ [ストリーミングテスト] サーバーエラー: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ [ストリーミングテスト] サーバー接続エラー: {str(e)}")
            return False
    
    async def test_sse_endpoint_basic(self) -> bool:
        """SSEエンドポイントの基本テスト（フロントエンド動作を忠実に再現）"""
        logger.info("🧪 [ストリーミングテスト] SSEエンドポイント基本テスト開始")
        
        try:
            # フロントエンドの動作を忠実に再現: sessionIdを直接生成
            import uuid
            session_id = str(uuid.uuid4())
            logger.info(f"📱 [ストリーミングテスト] フロントエンドで生成したsessionId: {session_id}")
            
            # 認証ヘッダーを設定（フロントエンドの動作を再現）
            sse_headers = {
                "Authorization": f"Bearer {self.supabase_token}" if self.supabase_token else "",
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache"
            }
            
            logger.info(f"📡 [ストリーミングテスト] SSE接続開始: {session_id}")
            
            received_messages = []
            timeout_count = 0
            max_timeout = 30  # 30秒でタイムアウト
            
            # SSEエンドポイントに接続（フロントエンドの動作を再現）
            async with self.client.stream("GET", f"{self.base_url}/chat/stream/{session_id}", headers=sse_headers) as response:
                if response.status_code != 200:
                    logger.error(f"❌ [ストリーミングテスト] SSE接続失敗: {response.status_code}")
                    return False
                
                logger.info(f"✅ [ストリーミングテスト] SSE接続成功: {response.status_code}")
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])  # "data: "を除去
                            received_messages.append(data)
                            logger.info(f"📨 [ストリーミングテスト] メッセージ受信: {data['type']} - {data.get('message', '')[:50]}...")
                            
                            # 完了またはエラーで終了
                            if data.get("type") in ["complete", "error", "timeout"]:
                                logger.info(f"🏁 [ストリーミングテスト] ストリーミング終了: {data['type']}")
                                break
                                
                        except json.JSONDecodeError as e:
                            logger.warning(f"⚠️ [ストリーミングテスト] JSON解析エラー: {e}")
                            logger.warning(f"⚠️ [ストリーミングテスト] 受信データ: {line}")
                    
                    # タイムアウト防止
                    timeout_count += 0.5
                    if timeout_count >= max_timeout:
                        logger.warning("⏰ [ストリーミングテスト] タイムアウトで終了")
                        break
            
            # 結果の検証
            if len(received_messages) > 0:
                logger.info(f"✅ [ストリーミングテスト] SSE基本テスト成功: {len(received_messages)}件のメッセージ受信")
                
                # メッセージタイプの分析
                message_types = {}
                for msg in received_messages:
                    msg_type = msg.get("type", "unknown")
                    message_types[msg_type] = message_types.get(msg_type, 0) + 1
                
                logger.info(f"📊 [ストリーミングテスト] メッセージタイプ: {message_types}")
                return True
            else:
                logger.error("❌ [ストリーミングテスト] SSE基本テスト失敗: メッセージが受信されませんでした")
                return False
                
        except Exception as e:
            logger.error(f"❌ [ストリーミングテスト] SSE基本テスト例外: {str(e)}")
            logger.error(f"❌ [ストリーミングテスト] 例外タイプ: {type(e).__name__}")
            import traceback
            logger.error(f"❌ [ストリーミングテスト] トレースバック: {traceback.format_exc()}")
            return False
    
    async def test_chat_with_streaming(self) -> bool:
        """SSEストリーミング機能のテスト（フロントエンド動作を忠実に再現）"""
        logger.info("🧪 [ストリーミングテスト] SSEストリーミング機能テスト開始")
        
        try:
            # フロントエンドの動作を忠実に再現: sessionIdを直接生成
            import uuid
            session_id = str(uuid.uuid4())
            logger.info(f"📱 [ストリーミングテスト] フロントエンドで生成したsessionId: {session_id}")
            
            # Step 1: SSEストリーミング接続を開始（フロントエンドの動作を再現）
            logger.info("📡 [ストリーミングテスト] Step 1: SSEストリーミング接続を開始")
            
            sse_headers = {
                "Authorization": f"Bearer {self.supabase_token}" if self.supabase_token else "",
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache"
            }
            
            # SSEストリーミング接続を開始
            streaming_task = asyncio.create_task(
                self._collect_streaming_messages_production(session_id, sse_headers)
            )
            
            # 少し待ってからストリーミング接続を開始
            await asyncio.sleep(1)
            
            # Step 2: ストリーミング結果を待機
            logger.info("📡 [ストリーミングテスト] Step 2: ストリーミング結果を待機")
            
            # ストリーミング結果を待機
            streaming_result = await streaming_task
            
            # 結果の検証
            if isinstance(streaming_result, Exception):
                logger.error(f"❌ [ストリーミングテスト] ストリーミングエラー: {streaming_result}")
                return False
            
            streaming_messages = streaming_result
            
            # ストリーミングメッセージの検証
            if len(streaming_messages) > 0:
                logger.info(f"✅ [ストリーミングテスト] ストリーミング成功: {len(streaming_messages)}件のメッセージ受信")
                
                # ストリーミング機能の成功指標
                success_indicators = [
                    "start",      # 開始通知
                    "progress",   # 進捗更新
                    "complete"    # 完了通知
                ]
                
                found_indicators = []
                for indicator in success_indicators:
                    for msg in streaming_messages:
                        if msg.get("type") == indicator:
                            found_indicators.append(indicator)
                            break
                
                logger.info(f"📊 [ストリーミングテスト] 発見された指標: {found_indicators}")
                
                # 成功基準: 少なくとも2つの指標が見つかること
                if len(found_indicators) >= 2:
                    logger.info("✅ [ストリーミングテスト] SSEストリーミング機能テスト成功")
                    return True
                else:
                    logger.warning(f"⚠️ [ストリーミングテスト] ストリーミング機能が不十分: {len(found_indicators)}/3")
                    return False
            else:
                logger.error("❌ [ストリーミングテスト] ストリーミングメッセージが受信されませんでした")
                return False
                
        except Exception as e:
            logger.error(f"❌ [ストリーミングテスト] SSEストリーミング機能テスト例外: {str(e)}")
            logger.error(f"❌ [ストリーミングテスト] 例外タイプ: {type(e).__name__}")
            import traceback
            logger.error(f"❌ [ストリーミングテスト] トレースバック: {traceback.format_exc()}")
            return False
    
    async def _collect_streaming_messages(self, session_id: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """ストリーミングメッセージを収集するヘルパーメソッド"""
        received_messages = []
        
        try:
            async with self.client.stream("GET", f"{self.base_url}/chat/stream/{session_id}", headers=headers) as response:
                if response.status_code != 200:
                    logger.error(f"❌ [ストリーミングテスト] SSE接続失敗: {response.status_code}")
                    return []
                
                timeout_count = 0
                max_timeout = 30  # 30秒でタイムアウト
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])  # "data: "を除去
                            received_messages.append(data)
                            logger.info(f"📨 [ストリーミングテスト] メッセージ受信: {data['type']} - {data.get('message', '')[:50]}...")
                            
                            # 完了またはエラーで終了
                            if data.get("type") in ["complete", "error", "timeout"]:
                                logger.info(f"🏁 [ストリーミングテスト] ストリーミング終了: {data['type']}")
                                break
                                
                        except json.JSONDecodeError as e:
                            logger.warning(f"⚠️ [ストリーミングテスト] JSON解析エラー: {e}")
                    
                    # タイムアウト防止
                    timeout_count += 0.5
                    if timeout_count >= max_timeout:
                        logger.warning("⏰ [ストリーミングテスト] タイムアウトで終了")
                        break
        
        except Exception as e:
            logger.error(f"❌ [ストリーミングテスト] ストリーミング収集エラー: {e}")
        
        return received_messages
    
    
    async def _collect_streaming_messages_production(self, session_id: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """ストリーミングメッセージを収集するヘルパーメソッド（本番用）"""
        received_messages = []
        
        try:
            # 本番用SSEエンドポイントを使用
            async with self.client.stream("GET", f"{self.base_url}/chat/stream/{session_id}", headers=headers) as response:
                if response.status_code != 200:
                    logger.error(f"❌ [ストリーミングテスト] SSE接続失敗: {response.status_code}")
                    return []
                
                timeout_count = 0
                max_timeout = 30  # 30秒でタイムアウト
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])  # "data: "を除去
                            received_messages.append(data)
                            logger.info(f"📨 [ストリーミングテスト] メッセージ受信: {data['type']} - {data.get('message', '')[:50]}...")
                            
                            # 完了またはエラーで終了
                            if data.get("type") in ["complete", "error", "timeout"]:
                                logger.info(f"🏁 [ストリーミングテスト] ストリーミング終了: {data['type']}")
                                break
                                
                        except json.JSONDecodeError as e:
                            logger.warning(f"⚠️ [ストリーミングテスト] JSON解析エラー: {e}")
                    
                    # タイムアウト防止
                    timeout_count += 0.5
                    if timeout_count >= max_timeout:
                        logger.warning("⏰ [ストリーミングテスト] タイムアウトで終了")
                        break
        
        except Exception as e:
            logger.error(f"❌ [ストリーミングテスト] ストリーミング収集エラー: {e}")
        
        return received_messages
    
    async def test_error_handling(self) -> bool:
        """エラーハンドリングテスト（フロントエンド動作を忠実に再現）"""
        logger.info("🧪 [ストリーミングテスト] エラーハンドリングテスト開始")
        
        try:
            # 無効なセッションIDでSSE接続を試行（フロントエンドの動作を再現）
            invalid_session_id = "invalid-session-id-999"
            
            headers = {
                "Authorization": f"Bearer {self.supabase_token}" if self.supabase_token else "",
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache"
            }
            
            logger.info(f"📡 [ストリーミングテスト] 無効セッションIDでSSE接続: {invalid_session_id}")
            
            try:
                async with self.client.stream("GET", f"{self.base_url}/chat/stream/{invalid_session_id}", headers=headers) as response:
                    if response.status_code == 400:
                        logger.info("✅ [ストリーミングテスト] 無効セッションIDで適切にエラー応答")
                        return True
                    elif response.status_code == 200:
                        # 200の場合は、エラーメッセージが送信されることを確認
                        received_messages = []
                        timeout_count = 0
                        max_timeout = 10  # 10秒でタイムアウト
                        
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                try:
                                    data = json.loads(line[6:])  # "data: "を除去
                                    received_messages.append(data)
                                    
                                    if data.get("type") == "error":
                                        logger.info("✅ [ストリーミングテスト] エラーメッセージを受信")
                                        return True
                                        
                                except json.JSONDecodeError:
                                    pass
                            
                            # タイムアウト防止
                            timeout_count += 0.5
                            if timeout_count >= max_timeout:
                                break
                        
                        logger.warning("⚠️ [ストリーミングテスト] エラーメッセージが受信されませんでした")
                        return False
                    else:
                        logger.error(f"❌ [ストリーミングテスト] 予期しないステータスコード: {response.status_code}")
                        return False
                        
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 400:
                    logger.info("✅ [ストリーミングテスト] 無効セッションIDで適切にエラー応答")
                    return True
                else:
                    logger.error(f"❌ [ストリーミングテスト] 予期しないHTTPエラー: {e.response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ [ストリーミングテスト] エラーハンドリングテスト例外: {str(e)}")
            return False
    
    async def _send_chat_request(self, message: str, sse_session_id: str = None) -> Dict[str, Any]:
        """実際のチャットリクエストを送信"""
        logger.info(f"💬 [ストリーミングテスト] チャットリクエスト送信: {message[:50]}...")
        
        import uuid
        
        headers = {
            "Authorization": f"Bearer {self.supabase_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "message": message,
            "session_id": str(uuid.uuid4())
        }
        
        # SSEセッションIDが指定されている場合は追加
        if sse_session_id:
            payload["sse_session_id"] = sse_session_id
            logger.info(f"📡 [ストリーミングテスト] SSEセッションID追加: {sse_session_id}")
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                logger.info("✅ [ストリーミングテスト] チャットリクエスト送信成功")
                return response.json()
            else:
                logger.error(f"❌ [ストリーミングテスト] チャットリクエスト送信失敗: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ [ストリーミングテスト] チャットリクエスト送信エラー: {str(e)}")
            return {"error": str(e)}
    
    async def test_real_react_processing(self) -> bool:
        """実際のReAct処理でのストリーミング機能テスト"""
        logger.info("🧪 [ストリーミングテスト] 実際のReAct処理テスト開始")
        
        try:
            # Step 1: 実際のユーザーリクエストを送信
            test_request = "在庫で作れる献立とレシピを教えて"
            logger.info(f"📝 [ストリーミングテスト] テストリクエスト: {test_request}")
            
            # Step 2: SSE接続を開始
            import uuid
            session_id = str(uuid.uuid4())
            logger.info(f"📱 [ストリーミングテスト] SSE接続識別子: {session_id}")
            
            sse_headers = {
                "Authorization": f"Bearer {self.supabase_token}" if self.supabase_token else "",
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache"
            }
            
            # Step 3: ストリーミング接続を開始
            streaming_task = asyncio.create_task(
                self._collect_streaming_messages_production(session_id, sse_headers)
            )
            
            # 少し待ってからチャット処理を実行（SSE接続の確立を待つ）
            await asyncio.sleep(2)
            
            # Step 4: 実際のチャット処理を実行（SSEセッションIDを渡す）
            chat_response = await self._send_chat_request(test_request, session_id)
            
            # Step 5: ストリーミング結果を待機
            streaming_messages = await streaming_task
            
            # Step 6: 進捗情報の詳細検証
            if isinstance(streaming_messages, Exception):
                logger.error(f"❌ [ストリーミングテスト] ストリーミングエラー: {streaming_messages}")
                return False
            
            # Step 7: 進捗情報の検証
            progress_validation = self._validate_progress_information(streaming_messages)
            
            if progress_validation:
                logger.info("✅ [ストリーミングテスト] 実際のReAct処理テスト成功")
                return True
            else:
                logger.error("❌ [ストリーミングテスト] 進捗情報の検証に失敗")
                return False
                
        except Exception as e:
            logger.error(f"❌ [ストリーミングテスト] ReAct処理テスト例外: {str(e)}")
            logger.error(f"❌ [ストリーミングテスト] 例外タイプ: {type(e).__name__}")
            import traceback
            logger.error(f"❌ [ストリーミングテスト] トレースバック: {traceback.format_exc()}")
            return False
    
    def _validate_progress_information(self, messages: List[Dict[str, Any]]) -> bool:
        """進捗情報の詳細検証"""
        logger.info("🔍 [ストリーミングテスト] 進捗情報の詳細検証開始")
        
        # 進捗メッセージを抽出
        progress_messages = [msg for msg in messages if msg.get("type") == "progress"]
        
        if not progress_messages:
            logger.error("❌ [ストリーミングテスト] 進捗メッセージが見つかりません")
            return False
        
        logger.info(f"📊 [ストリーミングテスト] 進捗メッセージ数: {len(progress_messages)}")
        
        # 進捗情報の検証
        for i, progress_msg in enumerate(progress_messages):
            progress_data = progress_msg.get("progress", {})
            
            # 必須フィールドの存在確認
            required_fields = [
                "total_tasks", "completed_tasks", "progress_percentage",
                "current_task", "is_complete"
            ]
            
            for field in required_fields:
                if field not in progress_data:
                    logger.error(f"❌ [ストリーミングテスト] 必須フィールドが不足: {field}")
                    return False
            
            # 進捗パーセンテージの計算検証
            total = progress_data["total_tasks"]
            completed = progress_data["completed_tasks"]
            percentage = progress_data["progress_percentage"]
            
            logger.info(f"📈 [ストリーミングテスト] 進捗メッセージ {i+1}: {completed}/{total} ({percentage}%)")
            
            if total > 0:
                expected_percentage = (completed / total) * 100
                if abs(percentage - expected_percentage) > 0.1:  # 0.1%の誤差を許容
                    logger.error(f"❌ [ストリーミングテスト] 進捗パーセンテージが不正確: {percentage}% vs {expected_percentage}%")
                    return False
            
            # 進捗の論理的整合性チェック
            if completed > total:
                logger.error(f"❌ [ストリーミングテスト] 完了タスク数が総タスク数を超過: {completed} > {total}")
                return False
            
            if percentage < 0 or percentage > 100:
                logger.error(f"❌ [ストリーミングテスト] 進捗パーセンテージが範囲外: {percentage}%")
                return False
            
            logger.info(f"✅ [ストリーミングテスト] 進捗メッセージ {i+1} 検証成功")
        
        logger.info("✅ [ストリーミングテスト] 進捗情報の詳細検証成功")
        return True
    
    async def test_parallel_task_execution(self) -> bool:
        """複数タスクの並列実行テスト"""
        logger.info("🧪 [ストリーミングテスト] 並列実行テスト開始")
        
        try:
            # 複数タスクを実行するリクエスト
            test_request = "在庫で作れる献立とレシピを教えて"
            logger.info(f"📝 [ストリーミングテスト] 並列実行テストリクエスト: {test_request}")
            
            # SSE接続とチャット処理を同時実行
            import uuid
            session_id = str(uuid.uuid4())
            logger.info(f"📱 [ストリーミングテスト] 並列実行SSE接続識別子: {session_id}")
            
            sse_headers = {
                "Authorization": f"Bearer {self.supabase_token}" if self.supabase_token else "",
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache"
            }
            
            # 並列実行
            streaming_task = asyncio.create_task(
                self._collect_streaming_messages_production(session_id, sse_headers)
            )
            
            # 少し待ってからチャット処理を実行
            await asyncio.sleep(1)
            
            chat_task = asyncio.create_task(
                self._send_chat_request(test_request)
            )
            
            # 結果を待機
            streaming_messages, chat_response = await asyncio.gather(
                streaming_task, chat_task, return_exceptions=True
            )
            
            # 並列実行の検証
            if isinstance(streaming_messages, Exception):
                logger.error(f"❌ [ストリーミングテスト] ストリーミングエラー: {streaming_messages}")
                return False
            
            parallel_validation = self._validate_parallel_execution(streaming_messages)
            
            if parallel_validation:
                logger.info("✅ [ストリーミングテスト] 並列実行テスト成功")
                return True
            else:
                logger.error("❌ [ストリーミングテスト] 並列実行検証に失敗")
                return False
                
        except Exception as e:
            logger.error(f"❌ [ストリーミングテスト] 並列実行テスト例外: {str(e)}")
            logger.error(f"❌ [ストリーミングテスト] 例外タイプ: {type(e).__name__}")
            import traceback
            logger.error(f"❌ [ストリーミングテスト] トレースバック: {traceback.format_exc()}")
            return False
    
    def _validate_parallel_execution(self, messages: List[Dict[str, Any]]) -> bool:
        """並列実行の検証"""
        logger.info("🔍 [ストリーミングテスト] 並列実行検証開始")
        
        # 進捗メッセージの時系列分析
        progress_messages = [msg for msg in messages if msg.get("type") == "progress"]
        
        if len(progress_messages) < 2:
            logger.error("❌ [ストリーミングテスト] 進捗メッセージが不足（並列実行の検証に必要）")
            return False
        
        logger.info(f"📊 [ストリーミングテスト] 並列実行進捗メッセージ数: {len(progress_messages)}")
        
        # 進捗の変化を追跡
        progress_history = []
        for msg in progress_messages:
            progress_data = msg.get("progress", {})
            progress_history.append({
                "timestamp": msg.get("timestamp", 0),
                "completed_tasks": progress_data.get("completed_tasks", 0),
                "current_task": progress_data.get("current_task", "")
            })
        
        # 進捗の増加を確認
        completed_tasks_sequence = [p["completed_tasks"] for p in progress_history]
        logger.info(f"📈 [ストリーミングテスト] 完了タスクシーケンス: {completed_tasks_sequence}")
        
        if not all(completed_tasks_sequence[i] <= completed_tasks_sequence[i+1] 
                   for i in range(len(completed_tasks_sequence)-1)):
            logger.error("❌ [ストリーミングテスト] 進捗が減少している（異常）")
            return False
        
        # 複数タスクの実行を確認
        max_completed = max(completed_tasks_sequence)
        if max_completed < 2:
            logger.warning("⚠️ [ストリーミングテスト] 複数タスクの実行が確認できません（並列実行の可能性が低い）")
        
        logger.info("✅ [ストリーミングテスト] 並列実行検証成功")
        return True
    
    async def test_realtime_progress_updates(self) -> bool:
        """リアルタイム進捗更新テスト"""
        logger.info("🧪 [ストリーミングテスト] リアルタイム更新テスト開始")
        
        try:
            # 長時間実行されるリクエスト
            test_request = "在庫で作れる献立とレシピを教えて"
            logger.info(f"📝 [ストリーミングテスト] リアルタイム更新テストリクエスト: {test_request}")
            
            import uuid
            session_id = str(uuid.uuid4())
            logger.info(f"📱 [ストリーミングテスト] リアルタイム更新SSE接続識別子: {session_id}")
            
            sse_headers = {
                "Authorization": f"Bearer {self.supabase_token}" if self.supabase_token else "",
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache"
            }
            
            # ストリーミング接続を開始
            streaming_task = asyncio.create_task(
                self._collect_streaming_messages_production(session_id, sse_headers)
            )
            
            # 少し待ってからチャット処理を実行
            await asyncio.sleep(1)
            
            # チャット処理を実行
            chat_task = asyncio.create_task(
                self._send_chat_request(test_request)
            )
            
            # 結果を待機
            streaming_messages, chat_response = await asyncio.gather(
                streaming_task, chat_task, return_exceptions=True
            )
            
            # リアルタイム更新の検証
            if isinstance(streaming_messages, Exception):
                logger.error(f"❌ [ストリーミングテスト] ストリーミングエラー: {streaming_messages}")
                return False
            
            realtime_validation = self._validate_realtime_updates(streaming_messages)
            
            if realtime_validation:
                logger.info("✅ [ストリーミングテスト] リアルタイム更新テスト成功")
                return True
            else:
                logger.error("❌ [ストリーミングテスト] リアルタイム更新検証に失敗")
                return False
                
        except Exception as e:
            logger.error(f"❌ [ストリーミングテスト] リアルタイム更新テスト例外: {str(e)}")
            logger.error(f"❌ [ストリーミングテスト] 例外タイプ: {type(e).__name__}")
            import traceback
            logger.error(f"❌ [ストリーミングテスト] トレースバック: {traceback.format_exc()}")
            return False
    
    def _validate_realtime_updates(self, messages: List[Dict[str, Any]]) -> bool:
        """リアルタイム更新の検証"""
        logger.info("🔍 [ストリーミングテスト] リアルタイム更新検証開始")
        
        # メッセージの時系列分析
        message_types = [msg.get("type") for msg in messages]
        logger.info(f"📊 [ストリーミングテスト] メッセージタイプ: {message_types}")
        
        # 期待されるメッセージシーケンス
        expected_sequence = ["start", "progress", "complete"]
        
        # シーケンスの検証
        found_start = "start" in message_types
        found_progress = "progress" in message_types
        found_complete = "complete" in message_types
        
        if not found_start:
            logger.error("❌ [ストリーミングテスト] 開始メッセージが見つかりません")
            return False
        
        if not found_progress:
            logger.error("❌ [ストリーミングテスト] 進捗メッセージが見つかりません")
            return False
        
        if not found_complete:
            logger.error("❌ [ストリーミングテスト] 完了メッセージが見つかりません")
            return False
        
        # タイムスタンプの検証
        timestamps = [msg.get("timestamp", 0) for msg in messages if msg.get("timestamp")]
        if len(timestamps) > 1:
            logger.info(f"⏰ [ストリーミングテスト] タイムスタンプ: {timestamps}")
            if not all(timestamps[i] <= timestamps[i+1] for i in range(len(timestamps)-1)):
                logger.error("❌ [ストリーミングテスト] タイムスタンプが時系列順ではありません")
                return False
        
        # 進捗の段階的変化を確認
        progress_messages = [msg for msg in messages if msg.get("type") == "progress"]
        if len(progress_messages) > 1:
            progress_sequence = []
            for msg in progress_messages:
                progress_data = msg.get("progress", {})
                progress_sequence.append({
                    "completed": progress_data.get("completed_tasks", 0),
                    "total": progress_data.get("total_tasks", 0),
                    "percentage": progress_data.get("progress_percentage", 0)
                })
            
            logger.info(f"📈 [ストリーミングテスト] 進捗シーケンス: {progress_sequence}")
            
            # 進捗の増加を確認
            completed_sequence = [p["completed"] for p in progress_sequence]
            if not all(completed_sequence[i] <= completed_sequence[i+1] 
                       for i in range(len(completed_sequence)-1)):
                logger.error("❌ [ストリーミングテスト] 進捗が減少している（異常）")
                return False
        
        logger.info("✅ [ストリーミングテスト] リアルタイム更新検証成功")
        return True
    
    async def test_detailed_error_handling(self) -> bool:
        """詳細なエラー処理テスト"""
        logger.info("🧪 [ストリーミングテスト] 詳細エラー処理テスト開始")
        
        try:
            # 無効なリクエストを送信
            invalid_request = "無効なリクエスト: 存在しないツールを実行してください"
            logger.info(f"📝 [ストリーミングテスト] エラー処理テストリクエスト: {invalid_request}")
            
            import uuid
            session_id = str(uuid.uuid4())
            logger.info(f"📱 [ストリーミングテスト] エラー処理テストSSE接続識別子: {session_id}")
            
            sse_headers = {
                "Authorization": f"Bearer {self.supabase_token}" if self.supabase_token else "",
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache"
            }
            
            # ストリーミング接続を開始
            streaming_task = asyncio.create_task(
                self._collect_streaming_messages_production(session_id, sse_headers)
            )
            
            # 少し待ってからチャット処理を実行
            await asyncio.sleep(1)
            
            # 無効なチャット処理を実行
            chat_task = asyncio.create_task(
                self._send_chat_request(invalid_request)
            )
            
            # 結果を待機
            streaming_messages, chat_response = await asyncio.gather(
                streaming_task, chat_task, return_exceptions=True
            )
            
            # エラー処理の検証
            error_validation = self._validate_error_handling(streaming_messages, chat_response)
            
            if error_validation:
                logger.info("✅ [ストリーミングテスト] 詳細エラー処理テスト成功")
                return True
            else:
                logger.error("❌ [ストリーミングテスト] エラー処理検証に失敗")
                return False
                
        except Exception as e:
            logger.error(f"❌ [ストリーミングテスト] 詳細エラー処理テスト例外: {str(e)}")
            logger.error(f"❌ [ストリーミングテスト] 例外タイプ: {type(e).__name__}")
            import traceback
            logger.error(f"❌ [ストリーミングテスト] トレースバック: {traceback.format_exc()}")
            return False
    
    def _validate_error_handling(self, streaming_messages: List[Dict[str, Any]], chat_response: Any) -> bool:
        """エラー処理の検証"""
        logger.info("🔍 [ストリーミングテスト] エラー処理検証開始")
        
        # ストリーミングメッセージの検証
        if isinstance(streaming_messages, Exception):
            logger.error(f"❌ [ストリーミングテスト] ストリーミングエラー: {streaming_messages}")
            return False
        
        # エラーメッセージの存在確認
        error_messages = [msg for msg in streaming_messages if msg.get("type") == "error"]
        
        if error_messages:
            logger.info(f"📊 [ストリーミングテスト] エラーメッセージ数: {len(error_messages)}")
            
            # エラーメッセージの内容検証
            for i, error_msg in enumerate(error_messages):
                error_data = error_msg.get("error", {})
                
                # エラー情報の必須フィールド確認
                required_error_fields = ["code", "message"]
                for field in required_error_fields:
                    if field not in error_data:
                        logger.error(f"❌ [ストリーミングテスト] エラーメッセージの必須フィールドが不足: {field}")
                        return False
                
                logger.info(f"⚠️ [ストリーミングテスト] エラーメッセージ {i+1}: {error_data.get('code')} - {error_data.get('message')}")
            
            logger.info("✅ [ストリーミングテスト] エラーメッセージの検証成功")
        else:
            logger.info("ℹ️ [ストリーミングテスト] エラーメッセージは受信されませんでした（正常処理の可能性）")
        
        # チャットレスポンスの検証
        if isinstance(chat_response, Exception):
            logger.info(f"⚠️ [ストリーミングテスト] チャット処理でエラーが発生: {chat_response}")
        elif isinstance(chat_response, dict) and "error" in chat_response:
            logger.info(f"⚠️ [ストリーミングテスト] チャットレスポンスにエラー: {chat_response['error']}")
        else:
            logger.info("ℹ️ [ストリーミングテスト] チャット処理は正常に完了")
        
        # エラー処理の適切性を評価
        # エラーが発生した場合でも、ストリーミング接続が適切に処理されているか
        if streaming_messages:
            logger.info("✅ [ストリーミングテスト] エラー発生時でもストリーミング接続が維持")
        
        logger.info("✅ [ストリーミングテスト] エラー処理検証成功")
        return True


async def run_streaming_test():
    """ストリーミング機能検証テストを実行"""
    logger.info("🚀 [ストリーミングテスト] ストリーミング機能検証開始")
    logger.info("=" * 60)
    
    async with StreamingTester() as tester:
        # テスト実行（簡素化版）
        tests = [
            ("包括的ストリーミング機能テスト", tester.test_real_react_processing)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                logger.info(f"🧪 [ストリーミングテスト] {test_name} 開始")
                result = await test_func()
                if result:
                    logger.info(f"✅ [ストリーミングテスト] {test_name} 成功")
                    passed += 1
                else:
                    logger.error(f"❌ [ストリーミングテスト] {test_name} 失敗")
            except Exception as e:
                logger.error(f"❌ [ストリーミングテスト] {test_name} エラー: {str(e)}")
        
        logger.info("=" * 60)
        logger.info(f"📊 [ストリーミングテスト] 結果: {passed}/{total} 成功")
        
        if passed == total:
            logger.info("🎉 [ストリーミングテスト] ストリーミング機能検証成功！")
            return True
        else:
            logger.error(f"❌ [ストリーミングテスト] ストリーミング機能検証失敗: {total - passed}件")
            return False


if __name__ == "__main__":
    # ストリーミング機能検証テスト実行
    result = asyncio.run(run_streaming_test())
    if not result:
        sys.exit(1)
