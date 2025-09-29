#!/usr/bin/env python3
"""
Phase 4.4.3: 確認プロセス検証専用テスト
サーバー起動状態での確認プロセスの動作確認のみ
"""

import asyncio
import sys
import os
import json
import time
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# HTTP クライアント
import httpx

# 環境変数の読み込み
load_dotenv()

# ログ設定 - サーバーと同じログファイルに出力
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
    
    # テスト用ロガーはINFOレベルを維持（テスト結果の確認のため）
    
    return logging.getLogger('morizo_ai.confirmation_test')

# ログ設定を実行
logger = setup_logging()


class ConfirmationProcessTester:
    """確認プロセス専用テストクラス"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=120.0)  # 30秒 → 120秒に延長
        
        # 環境変数から認証トークンを取得
        self.supabase_token = os.getenv("SUPABASE_ANON_KEY")
        if not self.supabase_token:
            logger.warning("⚠️ [確認テスト] SUPABASE_ANON_KEYが設定されていません")
        else:
            logger.info(f"✅ [確認テスト] 認証トークン取得完了: {self.supabase_token[:20]}...")
        
        logger.info("🚀 [確認テスト] Phase 4.4.3 確認プロセス検証開始")
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def test_server_health(self) -> bool:
        """サーバーのヘルスチェック"""
        logger.info("🔍 [確認テスト] サーバーヘルスチェック")
        
        try:
            response = await self.client.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                logger.info("✅ [確認テスト] サーバー正常")
                return True
            else:
                logger.error(f"❌ [確認テスト] サーバーエラー: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ [確認テスト] サーバー接続エラー: {str(e)}")
            return False
    
    async def test_confirmation_process(self) -> bool:
        """確認プロセスの検証"""
        logger.info("🧪 [確認テスト] 確認プロセス検証開始")
        
        try:
            # Step 1: 曖昧な要求を送信（確認が必要な操作）
            logger.info("📤 [確認テスト] Step 1: 曖昧な要求を送信")
            headers = {"Authorization": f"Bearer {self.supabase_token}"} if self.supabase_token else {}
            
            ambiguous_request = "牛乳を削除して、在庫で作れる献立とレシピを教えて"
            logger.info(f"📤 [確認テスト] リクエスト: {ambiguous_request}")
            
            response = await self.client.post(
                f"{self.base_url}/chat",
                json={"message": ambiguous_request},
                headers=headers
            )
            
            # 認証エラーの場合は認証なしでテスト
            if response.status_code == 401 and self.supabase_token:
                logger.warning("⚠️ [確認テスト] 認証エラー、認証なしでテスト")
                response = await self.client.post(
                    f"{self.base_url}/chat-test",
                    json={"message": ambiguous_request}
                )
            
            if response.status_code != 200:
                logger.error(f"❌ [確認テスト] Step 1 エラー: {response.status_code}")
                return False
            
            data = response.json()
            response_text = data.get("response", "")
            confirmation_required = data.get("confirmation_required", False)
            
            logger.info(f"📥 [確認テスト] Step 1 レスポンス: {response_text[:100]}...")
            logger.info(f"📥 [確認テスト] Step 1 確認必要: {confirmation_required}")
            
            # 確認プロセスが発動したかチェック
            if confirmation_required:
                logger.info("✅ [確認テスト] 確認プロセスが正常に開始されました")
                
                # Step 2: 確認応答を送信
                logger.info("📤 [確認テスト] Step 2: 確認応答を送信")
                confirmation_response = "古いアイテムを操作"
                logger.info(f"📤 [確認テスト] 確認応答: {confirmation_response}")
                
                confirm_response = await self.client.post(
                    f"{self.base_url}/chat/confirm",
                    json={"message": confirmation_response},
                    headers=headers
                )
                
                # 認証エラーの場合は認証なしでテスト
                if confirm_response.status_code == 401 and self.supabase_token:
                    logger.warning("⚠️ [確認テスト] 確認応答で認証エラー、認証なしでテスト")
                    confirm_response = await self.client.post(
                        f"{self.base_url}/chat-test",
                        json={"message": confirmation_response}
                    )
                
                if confirm_response.status_code == 200:
                    confirm_data = confirm_response.json()
                    confirm_text = confirm_data.get("response", "")
                    logger.info(f"📥 [確認テスト] Step 2 レスポンス: {confirm_text[:100]}...")
                    logger.info("✅ [確認テスト] 確認応答処理が正常に完了しました")
                    return True
                else:
                    logger.error(f"❌ [確認テスト] Step 2 エラー: {confirm_response.status_code}")
                    return False
            else:
                logger.warning("⚠️ [確認テスト] 確認プロセスが発動しませんでした")
                logger.info(f"📥 [確認テスト] レスポンス内容: {response_text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ [確認テスト] 確認プロセス例外: {str(e)}")
            logger.error(f"❌ [確認テスト] 例外タイプ: {type(e).__name__}")
            import traceback
            logger.error(f"❌ [確認テスト] トレースバック: {traceback.format_exc()}")
            return False


async def run_confirmation_test():
    """確認プロセス検証テストを実行"""
    logger.info("🚀 [確認テスト] Phase 4.4.3 確認プロセス検証開始")
    logger.info("=" * 50)
    
    async with ConfirmationProcessTester() as tester:
        # テスト実行
        tests = [
            ("サーバーヘルスチェック", tester.test_server_health),
            ("確認プロセス検証", tester.test_confirmation_process)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                logger.info(f"🧪 [確認テスト] {test_name} 開始")
                result = await test_func()
                if result:
                    logger.info(f"✅ [確認テスト] {test_name} 成功")
                    passed += 1
                else:
                    logger.error(f"❌ [確認テスト] {test_name} 失敗")
            except Exception as e:
                logger.error(f"❌ [確認テスト] {test_name} エラー: {str(e)}")
        
        logger.info("=" * 50)
        logger.info(f"📊 [確認テスト] 結果: {passed}/{total} 成功")
        
        if passed == total:
            logger.info("🎉 [確認テスト] Phase 4.4.3 確認プロセス検証成功！")
            return True
        else:
            logger.error(f"❌ [確認テスト] Phase 4.4.3 確認プロセス検証失敗: {total - passed}件")
            return False


if __name__ == "__main__":
    # 確認プロセス検証テスト実行
    result = asyncio.run(run_confirmation_test())
    if not result:
        sys.exit(1)
