#!/usr/bin/env python3
"""
ユーザー指定による最新アイテム削除のテスト
inventory_delete_by_name_latestツールの動作確認
"""

import asyncio
import httpx
import logging
import traceback
from dotenv import load_dotenv
import os

# 環境変数を読み込み
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_delete_latest")

class DeleteLatestTester:
    """ユーザー指定による最新アイテム削除のテストクラス"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.supabase_token = self._get_supabase_token()
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _get_supabase_token(self) -> str:
        """Supabaseトークンを取得"""
        token = os.getenv("SUPABASE_TOKEN")
        if not token:
            print("🔑 Supabaseトークンが設定されていません")
            print("💡 環境変数 SUPABASE_TOKEN を設定するか、以下を入力してください:")
            token = input("Supabaseトークンを入力: ").strip()
            if not token:
                raise ValueError("Supabaseトークンが必要です")
        return token
        
    async def cleanup(self):
        """クリーンアップ"""
        try:
            await self.client.aclose()
        except Exception as e:
            logger.warning(f"⚠️ クリーンアップエラー: {str(e)}")
    
    async def test_user_specified_delete_latest(self):
        """ユーザー指定による最新アイテム削除のテスト"""
        logger.info("🧪 ユーザー指定による最新アイテム削除テスト開始")
        
        try:
            # テストデータの準備（複数の牛乳アイテムを追加）
            await self._prepare_test_data()
            
            # ユーザー指定削除のテスト
            test_case = "最新の牛乳を削除して"
            logger.info(f"🧪 テストケース: {test_case}")
            
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # 結果の確認
            if "削除" in response and ("完了" in response or "処分" in response):
                logger.info(f"✅ ユーザー指定削除テスト成功: 最新アイテムの削除完了")
            else:
                logger.warning(f"⚠️ 不明な結果: {response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ ユーザー指定削除テストエラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        finally:
            # クリーンアップ
            await self.cleanup()
        
        logger.info("🎉 ユーザー指定による最新アイテム削除テスト完了")
    
    async def _prepare_test_data(self):
        """テストデータの準備"""
        logger.info("📋 テストデータの準備開始")
        
        # 複数の牛乳アイテムを追加
        test_items = [
            {"item_name": "牛乳", "quantity": 1, "unit": "本", "storage_location": "冷蔵庫"},
            {"item_name": "牛乳", "quantity": 2, "unit": "本", "storage_location": "冷蔵庫"},
            {"item_name": "牛乳", "quantity": 3, "unit": "本", "storage_location": "冷蔵庫"}
        ]
        
        for item in test_items:
            try:
                await self._send_chat_request(f"{item['item_name']}を{item['quantity']}{item['unit']}追加して")
                await asyncio.sleep(1)  # 作成時間の差を作るため
            except Exception as e:
                logger.warning(f"⚠️ テストデータ準備エラー: {str(e)}")
        
        logger.info("📋 テストデータの準備完了")
    
    async def _send_chat_request(self, message: str) -> str:
        """チャットリクエストを送信"""
        try:
            print(f"\n📤 リクエスト送信: {message}")
            
            response = await self.client.post(
                f"{self.base_url}/chat",
                headers={
                    "Authorization": f"Bearer {self.supabase_token}",
                    "Content-Type": "application/json"
                },
                json={"message": message}
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "応答なし")
                print(f"📥 レスポンス受信: {response_text}")
                return response_text
            else:
                error_msg = f"HTTPエラー: {response.status_code} - {response.text}"
                logger.error(f"❌ {error_msg}")
                return error_msg
                
        except Exception as e:
            error_msg = f"リクエストエラー: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return error_msg

async def main():
    """メイン関数"""
    tester = DeleteLatestTester()
    await tester.test_user_specified_delete_latest()

if __name__ == "__main__":
    asyncio.run(main())
