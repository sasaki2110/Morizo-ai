#!/usr/bin/env python3
"""
Phase 4.4.3: レシピ検索統合専用テスト（2025/9/29更新）
サーバー起動状態でのレシピ検索統合機能の動作確認のみ
配列対応レシピ検索機能のテスト
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
    
    return logging.getLogger('morizo_ai.recipe_integration_test')

# ログ設定を実行
logger = setup_logging()


class RecipeIntegrationTester:
    """レシピ検索統合専用テストクラス"""
    
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
            logger.info(f"✅ [レシピ統合テスト] 自動ログインで認証トークン取得完了: {self.supabase_token[:20]}...")
        except Exception as e:
            logger.warning(f"⚠️ [レシピ統合テスト] 自動ログイン失敗: {str(e)}")
            # フォールバック: 環境変数から取得
            self.supabase_token = os.getenv("SUPABASE_ANON_KEY")
            if not self.supabase_token:
                logger.warning("⚠️ [レシピ統合テスト] SUPABASE_ANON_KEYも設定されていません")
            else:
                logger.info(f"✅ [レシピ統合テスト] 環境変数から認証トークン取得完了: {self.supabase_token[:20]}...")
        
        logger.info("🚀 [レシピ統合テスト] Phase 4.4.3 レシピ検索統合検証開始")
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def test_server_health(self) -> bool:
        """サーバーのヘルスチェック"""
        logger.info("🔍 [レシピ統合テスト] サーバーヘルスチェック")
        
        try:
            response = await self.client.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                logger.info("✅ [レシピ統合テスト] サーバー正常")
                return True
            else:
                logger.error(f"❌ [レシピ統合テスト] サーバーエラー: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ [レシピ統合テスト] サーバー接続エラー: {str(e)}")
            return False
    
    async def test_recipe_integration(self) -> bool:
        """レシピ検索統合機能の検証"""
        logger.info("🧪 [レシピ統合テスト] レシピ検索統合機能検証開始")
        
        try:
            # Step 1: レシピ検索要求を送信
            logger.info("📤 [レシピ統合テスト] Step 1: レシピ検索要求を送信")
            headers = {"Authorization": f"Bearer {self.supabase_token}"} if self.supabase_token else {}
            
            recipe_request = "在庫で作れる献立とレシピを教えて"
            logger.info(f"📤 [レシピ統合テスト] リクエスト: {recipe_request}")
            
            response = await self.client.post(
                f"{self.base_url}/chat",
                json={"message": recipe_request},
                headers=headers
            )
            
            # 認証エラーの場合は認証なしでテスト
            if response.status_code == 401 and self.supabase_token:
                logger.warning("⚠️ [レシピ統合テスト] 認証エラー、認証なしでテスト")
                response = await self.client.post(
                    f"{self.base_url}/chat-test",
                    json={"message": recipe_request}
                )
            
            if response.status_code != 200:
                logger.error(f"❌ [レシピ統合テスト] Step 1 エラー: {response.status_code}")
                return False
            
            data = response.json()
            response_text = data.get("response", "")
            
            logger.info(f"📥 [レシピ統合テスト] Step 1 レスポンス: {response_text}")
            
            # レシピ検索統合機能の検証
            success_indicators = [
                "🍽️ **生成された献立**",  # 献立データの表示
                "🔗 **レシピリンク**",    # レシピデータの表示
                "http",                   # URLの存在
                "主菜",                   # 献立の詳細
                "副菜",                   # 献立の詳細
                "汁物"                    # 献立の詳細
            ]
            
            # 配列対応レシピ検索の追加確認
            url_count = response_text.count("http")
            if url_count >= 3:
                logger.info(f"✅ [レシピ統合テスト] 複数レシピURL検出: {url_count}個")
            else:
                logger.warning(f"⚠️ [レシピ統合テスト] レシピURL数が不足: {url_count}個")
            
            found_indicators = []
            for indicator in success_indicators:
                if indicator in response_text:
                    found_indicators.append(indicator)
                    logger.info(f"✅ [レシピ統合テスト] 成功指標発見: {indicator}")
            
            # 成功基準: 少なくとも3つの指標が見つかり、複数URLが存在すること
            if len(found_indicators) >= 3 and url_count >= 3:
                logger.info(f"✅ [レシピ統合テスト] レシピ検索統合機能が正常に動作しました（配列対応）")
                logger.info(f"📊 [レシピ統合テスト] 発見された指標: {len(found_indicators)}/{len(success_indicators)}")
                logger.info(f"📊 [レシピ統合テスト] レシピURL数: {url_count}個")
                return True
            else:
                logger.warning(f"⚠️ [レシピ統合テスト] レシピ検索統合機能の動作が不十分です")
                logger.warning(f"📊 [レシピ統合テスト] 発見された指標: {len(found_indicators)}/{len(success_indicators)}")
                logger.warning(f"📊 [レシピ統合テスト] レシピURL数: {url_count}個")
                logger.warning(f"📊 [レシピ統合テスト] 発見された指標: {found_indicators}")
                return False
                
        except Exception as e:
            logger.error(f"❌ [レシピ統合テスト] レシピ検索統合機能例外: {str(e)}")
            logger.error(f"❌ [レシピ統合テスト] 例外タイプ: {type(e).__name__}")
            import traceback
            logger.error(f"❌ [レシピ統合テスト] トレースバック: {traceback.format_exc()}")
            return False

    async def test_specific_recipe_search(self) -> bool:
        """具体的なレシピ検索の検証"""
        logger.info("🧪 [レシピ統合テスト] 具体的なレシピ検索検証開始")
        
        try:
            # Step 1: 具体的な料理名でのレシピ検索
            logger.info("📤 [レシピ統合テスト] Step 1: 具体的な料理名でのレシピ検索")
            headers = {"Authorization": f"Bearer {self.supabase_token}"} if self.supabase_token else {}
            
            specific_request = "カレーライスのレシピを教えて"
            logger.info(f"📤 [レシピ統合テスト] リクエスト: {specific_request}")
            
            response = await self.client.post(
                f"{self.base_url}/chat",
                json={"message": specific_request},
                headers=headers
            )
            
            # 認証エラーの場合は認証なしでテスト
            if response.status_code == 401 and self.supabase_token:
                logger.warning("⚠️ [レシピ統合テスト] 認証エラー、認証なしでテスト")
                response = await self.client.post(
                    f"{self.base_url}/chat-test",
                    json={"message": specific_request}
                )
            
            if response.status_code != 200:
                logger.error(f"❌ [レシピ統合テスト] Step 1 エラー: {response.status_code}")
                return False
            
            data = response.json()
            response_text = data.get("response", "")
            
            logger.info(f"📥 [レシピ統合テスト] Step 1 レスポンス: {response_text}")
            
            # 具体的なレシピ検索の成功指標
            success_indicators = [
                "カレー",                 # 料理名の含まれ
                "http",                   # URLの存在
                "レシピ",                 # レシピ情報
                "調理時間",               # 調理情報
                "分量"                    # 調理情報
            ]
            
            found_indicators = []
            for indicator in success_indicators:
                if indicator in response_text:
                    found_indicators.append(indicator)
                    logger.info(f"✅ [レシピ統合テスト] 成功指標発見: {indicator}")
            
            # 成功基準: 少なくとも3つの指標が見つかること
            if len(found_indicators) >= 3:
                logger.info(f"✅ [レシピ統合テスト] 具体的なレシピ検索が正常に動作しました")
                logger.info(f"📊 [レシピ統合テスト] 発見された指標: {len(found_indicators)}/{len(success_indicators)}")
                return True
            else:
                logger.warning(f"⚠️ [レシピ統合テスト] 具体的なレシピ検索の動作が不十分です")
                logger.warning(f"📊 [レシピ統合テスト] 発見された指標: {len(found_indicators)}/{len(success_indicators)}")
                logger.warning(f"📊 [レシピ統合テスト] 発見された指標: {found_indicators}")
                return False
                
        except Exception as e:
            logger.error(f"❌ [レシピ統合テスト] 具体的なレシピ検索例外: {str(e)}")
            logger.error(f"❌ [レシピ統合テスト] 例外タイプ: {type(e).__name__}")
            import traceback
            logger.error(f"❌ [レシピ統合テスト] トレースバック: {traceback.format_exc()}")
            return False


async def run_recipe_integration_test():
    """レシピ検索統合検証テストを実行"""
    logger.info("🚀 [レシピ統合テスト] Phase 4.4.3 レシピ検索統合検証開始")
    logger.info("=" * 50)
    
    async with RecipeIntegrationTester() as tester:
        # テスト実行
        tests = [
            ("サーバーヘルスチェック", tester.test_server_health),
            ("レシピ検索統合機能検証", tester.test_recipe_integration),
            ("具体的なレシピ検索検証", tester.test_specific_recipe_search)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                logger.info(f"🧪 [レシピ統合テスト] {test_name} 開始")
                result = await test_func()
                if result:
                    logger.info(f"✅ [レシピ統合テスト] {test_name} 成功")
                    passed += 1
                else:
                    logger.error(f"❌ [レシピ統合テスト] {test_name} 失敗")
            except Exception as e:
                logger.error(f"❌ [レシピ統合テスト] {test_name} エラー: {str(e)}")
        
        logger.info("=" * 50)
        logger.info(f"📊 [レシピ統合テスト] 結果: {passed}/{total} 成功")
        
        if passed == total:
            logger.info("🎉 [レシピ統合テスト] Phase 4.4.3 レシピ検索統合検証成功！")
            return True
        else:
            logger.error(f"❌ [レシピ統合テスト] Phase 4.4.3 レシピ検索統合検証失敗: {total - passed}件")
            return False


if __name__ == "__main__":
    # レシピ検索統合検証テスト実行
    result = asyncio.run(run_recipe_integration_test())
    if not result:
        sys.exit(1)
