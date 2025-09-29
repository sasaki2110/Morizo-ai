#!/usr/bin/env python3
"""
Phase 4.5: 並列提示システム検証テスト（2025/9/29責任分離設計対応）
斬新な提案（AI生成）と伝統的な提案（RAG検索）の併立提示機能の検証

新しい責任分離設計:
- task1: 在庫チェック
- task2: LLM推論で献立タイトル生成
- task3: RAG検索で献立タイトル生成
- task4: Web検索でレシピURL取得
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
    
    return logging.getLogger('morizo_ai.parallel_proposal_test')

# ログ設定を実行
logger = setup_logging()


class ParallelProposalTester:
    """並列提示システム検証テストクラス"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=120.0)  # 120秒タイムアウト
        
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
            logger.info(f"✅ [並列提示テスト] 自動ログインで認証トークン取得完了: {self.supabase_token[:20]}...")
        except Exception as e:
            logger.warning(f"⚠️ [並列提示テスト] 自動ログイン失敗: {str(e)}")
            # フォールバック: 環境変数から取得
            self.supabase_token = os.getenv("SUPABASE_ANON_KEY")
            if not self.supabase_token:
                logger.warning("⚠️ [並列提示テスト] SUPABASE_ANON_KEYも設定されていません")
            else:
                logger.info(f"✅ [並列提示テスト] 環境変数から認証トークン取得完了: {self.supabase_token[:20]}...")
        
        logger.info("🚀 [並列提示テスト] Phase 4.5 並列提示システム検証開始")
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def test_server_health(self) -> bool:
        """サーバーのヘルスチェック"""
        logger.info("🔍 [並列提示テスト] サーバーヘルスチェック")
        
        try:
            response = await self.client.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                logger.info("✅ [並列提示テスト] サーバー正常")
                return True
            else:
                logger.error(f"❌ [並列提示テスト] サーバーエラー: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ [並列提示テスト] サーバー接続エラー: {str(e)}")
            return False
    
    async def test_parallel_proposal_response(self) -> bool:
        """並列提示レスポンスの検証"""
        logger.info("🧪 [並列提示テスト] 並列提示レスポンス検証開始")
        
        try:
            # Step 1: 並列提示要求を送信
            logger.info("📤 [並列提示テスト] Step 1: 並列提示要求を送信")
            headers = {"Authorization": f"Bearer {self.supabase_token}"} if self.supabase_token else {}
            
            proposal_request = "在庫で作れる献立とレシピを教えて"
            logger.info(f"📤 [並列提示テスト] リクエスト: {proposal_request}")
            
            response = await self.client.post(
                f"{self.base_url}/chat",
                json={"message": proposal_request},
                headers=headers
            )
            
            # 認証エラーの場合は認証なしでテスト
            if response.status_code == 401 and self.supabase_token:
                logger.warning("⚠️ [並列提示テスト] 認証エラー、認証なしでテスト")
                response = await self.client.post(
                    f"{self.base_url}/chat-test",
                    json={"message": proposal_request}
                )
            
            if response.status_code != 200:
                logger.error(f"❌ [並列提示テスト] Step 1 エラー: {response.status_code}")
                return False
            
            data = response.json()
            response_text = data.get("response", "")
            
            logger.info(f"📥 [並列提示テスト] Step 1 レスポンス: {response_text}")
            
            # 責任分離設計の並列提示システム検証指標
            success_indicators = [
                "献立提案（2つの選択肢）",  # 並列提示のタイトル
                "斬新な提案（AI生成）",     # LLM生成提案
                "伝統的な提案（蓄積レシピ）", # RAG検索提案
                "どちらの提案",             # ユーザー選択ヒント
                "http",                     # レシピURL
                "主菜",                     # 献立構成
                "副菜",                     # 献立構成
                "汁物",                     # 献立構成
            ]
            
            found_indicators = []
            for indicator in success_indicators:
                if indicator in response_text:
                    found_indicators.append(indicator)
                    logger.info(f"✅ [並列提示テスト] 成功指標発見: {indicator}")
            
            # 成功基準: 少なくとも6つの指標が見つかること（責任分離設計ではより詳細な検証）
            if len(found_indicators) >= 6:
                logger.info(f"✅ [並列提示テスト] 並列提示レスポンスが正常に動作しました")
                logger.info(f"📊 [並列提示テスト] 発見された指標: {len(found_indicators)}/{len(success_indicators)}")
                return True
            else:
                logger.warning(f"⚠️ [並列提示テスト] 並列提示レスポンスの動作が不十分です")
                logger.warning(f"📊 [並列提示テスト] 発見された指標: {len(found_indicators)}/{len(success_indicators)}")
                logger.warning(f"📊 [並列提示テスト] 発見された指標: {found_indicators}")
                return False
                
        except Exception as e:
            logger.error(f"❌ [並列提示テスト] 並列提示レスポンス例外: {str(e)}")
            logger.error(f"❌ [並列提示テスト] 例外タイプ: {type(e).__name__}")
            import traceback
            logger.error(f"❌ [並列提示テスト] トレースバック: {traceback.format_exc()}")
            return False


    async def test_fallback_behavior(self) -> bool:
        """従来処理へのフォールバック検証"""
        logger.info("🧪 [並列提示テスト] フォールバック検証開始")
        
        try:
            # Step 1: 通常の挨拶を送信（並列提示が発動しないケース）
            logger.info("📤 [並列提示テスト] Step 1: 通常の挨拶を送信")
            headers = {"Authorization": f"Bearer {self.supabase_token}"} if self.supabase_token else {}
            
            greeting_request = "こんにちは"
            logger.info(f"📤 [並列提示テスト] リクエスト: {greeting_request}")
            
            response = await self.client.post(
                f"{self.base_url}/chat",
                json={"message": greeting_request},
                headers=headers
            )
            
            # 認証エラーの場合は認証なしでテスト
            if response.status_code == 401 and self.supabase_token:
                logger.warning("⚠️ [並列提示テスト] 認証エラー、認証なしでテスト")
                response = await self.client.post(
                    f"{self.base_url}/chat-test",
                    json={"message": greeting_request}
                )
            
            if response.status_code != 200:
                logger.error(f"❌ [並列提示テスト] Step 1 エラー: {response.status_code}")
                return False
            
            data = response.json()
            response_text = data.get("response", "")
            
            logger.info(f"📥 [並列提示テスト] Step 1 レスポンス: {response_text}")
            
            # フォールバック処理の検証指標
            # 挨拶に対しては並列提示が発動せず、通常の挨拶レスポンスが返される
            unexpected_indicators = [
                "献立提案（2つの選択肢）",  # 並列提示のタイトル
                "斬新な提案（AI生成）",     # LLM生成提案
                "伝統的な提案（蓄積レシピ）", # RAG検索提案
                "どちらの提案",             # ユーザー選択ヒント
            ]
            
            # これらの指標が含まれていないことを確認
            found_unexpected = []
            for indicator in unexpected_indicators:
                if indicator in response_text:
                    found_unexpected.append(indicator)
                    logger.warning(f"⚠️ [並列提示テスト] 予期しない指標発見: {indicator}")
            
            # 成功基準: 予期しない指標が含まれていないこと
            if len(found_unexpected) == 0:
                logger.info(f"✅ [並列提示テスト] フォールバックが正常に動作しました")
                return True
            else:
                logger.warning(f"⚠️ [並列提示テスト] フォールバックの動作が不適切です")
                logger.warning(f"📊 [並列提示テスト] 予期しない指標: {found_unexpected}")
                return False
                
        except Exception as e:
            logger.error(f"❌ [並列提示テスト] フォールバック例外: {str(e)}")
            logger.error(f"❌ [並列提示テスト] 例外タイプ: {type(e).__name__}")
            import traceback
            logger.error(f"❌ [並列提示テスト] トレースバック: {traceback.format_exc()}")
            return False


async def run_parallel_proposal_test():
    """責任分離設計の並列提示システム検証テストを実行"""
    logger.info("🚀 [並列提示テスト] Phase 4.5 責任分離設計並列提示システム検証開始")
    logger.info("=" * 60)
    
    async with ParallelProposalTester() as tester:
        # テスト実行
        tests = [
            ("サーバーヘルスチェック", tester.test_server_health),
            ("並列提示レスポンス検証", tester.test_parallel_proposal_response),
            ("フォールバック検証", tester.test_fallback_behavior)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                logger.info(f"🧪 [並列提示テスト] {test_name} 開始")
                result = await test_func()
                if result:
                    logger.info(f"✅ [並列提示テスト] {test_name} 成功")
                    passed += 1
                else:
                    logger.error(f"❌ [並列提示テスト] {test_name} 失敗")
            except Exception as e:
                logger.error(f"❌ [並列提示テスト] {test_name} エラー: {str(e)}")
        
        logger.info("=" * 60)
        logger.info(f"📊 [並列提示テスト] 結果: {passed}/{total} 成功")
        
        if passed == total:
            logger.info("🎉 [並列提示テスト] Phase 4.5 責任分離設計並列提示システム検証成功！")
            return True
        else:
            logger.error(f"❌ [並列提示テスト] Phase 4.5 責任分離設計並列提示システム検証失敗: {total - passed}件")
            return False


if __name__ == "__main__":
    # 責任分離設計の並列提示システム検証テスト実行
    result = asyncio.run(run_parallel_proposal_test())
    if not result:
        sys.exit(1)
