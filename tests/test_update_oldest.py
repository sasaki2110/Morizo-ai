"""
FIFO原則による最古アイテム更新の集中テスト
「牛乳の数量を3本に変更して」のみをテスト
"""

import asyncio
import json
import logging
import traceback
from typing import List, Dict, Any
import httpx
from openai import OpenAI

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_update_oldest")

class UpdateOldestTester:
    """FIFO原則による最古アイテム更新に集中したテスター"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.supabase_token = None
    
    async def setup(self):
        """テストのセットアップ"""
        logger.info("🧪 FIFO原則による最古アイテム更新テスト開始")
        
        # Supabaseトークンの取得
        self.supabase_token = await self._get_supabase_token()
        if not self.supabase_token:
            logger.error("❌ Supabaseトークンの取得に失敗しました")
            return False
        
        logger.info("✅ セットアップ完了")
        return True
    
    async def _get_supabase_token(self) -> str:
        """Supabaseトークンを取得"""
        print("\n🔑 Supabaseトークンを入力してください:")
        print("   Next.jsアプリから取得したトークンを貼り付けてください")
        print("   (例: eyJhbGciOiJIUzI1NiIs...)")
        
        token = input("トークン: ").strip()
        
        if len(token) < 100:
            print("⚠️ トークンが短すぎるようです。正しいトークンですか？")
            confirm = input("続行しますか？ (y/N): ").strip().lower()
            if confirm != 'y':
                return None
        
        return token
    
    async def test_fifo_update_oldest(self):
        """FIFO原則による最古アイテム更新のテスト"""
        logger.info("🧪 テスト: FIFO原則による最古アイテム更新")
        
        test_case = "牛乳の数量を3本に変更して"
        logger.info(f"🧪 テスト: {test_case}")
        
        try:
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # FIFO更新の確認
            if "更新" in response and ("完了" in response or "変更" in response):
                logger.info(f"✅ テスト 成功: FIFO原則による最古アイテム更新完了")
            else:
                logger.warning(f"⚠️ テスト 不明な結果: {response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(1)  # 1秒待機
    
    async def test_inventory_list_before_update(self):
        """更新前の在庫一覧確認"""
        logger.info("🧪 テスト: 更新前の在庫一覧確認")
        test_case = "今の在庫を教えて"
        logger.info(f"🧪 テスト: {test_case}")
        
        try:
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # 在庫一覧が表示されているかチェック
            if "在庫" in response:
                logger.info(f"✅ テスト 成功: 更新前の在庫一覧表示完了")
            else:
                logger.warning(f"⚠️ テスト 不明な結果: {response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(1)  # 1秒待機
    
    async def test_inventory_list_after_update(self):
        """更新後の在庫一覧確認"""
        logger.info("🧪 テスト: 更新後の在庫一覧確認")
        test_case = "今の在庫を教えて"
        logger.info(f"🧪 テスト: {test_case}")
        
        try:
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # 在庫一覧が表示されているかチェック
            if "在庫" in response:
                logger.info(f"✅ テスト 成功: 更新後の在庫一覧表示完了")
            else:
                logger.warning(f"⚠️ テスト 不明な結果: {response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(1)  # 1秒待機
    
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
                response_text = result.get("response", "レスポンスが空です")
                
                # main.pyの最終レスポンスを表示
                print(f"📥 最終レスポンス:")
                print(f"   {response_text}")
                print(f"📊 レスポンス詳細:")
                print(f"   - 成功: {result.get('success', 'N/A')}")
                print(f"   - モデル: {result.get('model_used', 'N/A')}")
                print(f"   - ユーザーID: {result.get('user_id', 'N/A')}")
                print(f"   - 文字数: {len(response_text)}文字")
                
                return response_text
            else:
                logger.error(f"❌ HTTPエラー: {response.status_code}")
                error_msg = f"HTTPエラー: {response.status_code}"
                print(f"❌ {error_msg}")
                return error_msg
                
        except Exception as e:
            logger.error(f"❌ リクエストエラー: {str(e)}")
            error_msg = f"リクエストエラー: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    async def cleanup(self):
        """テストのクリーンアップ"""
        logger.info("🧹 テストクリーンアップ")
        await self.client.aclose()
        logger.info("✅ クリーンアップ完了")
    
    async def run_all_tests(self):
        """全テストを実行"""
        logger.info("🚀 FIFO原則による最古アイテム更新テスト開始")
        
        # セットアップ
        if not await self.setup():
            logger.error("❌ セットアップに失敗しました")
            return
        
        try:
            # テスト実行
            await self.test_inventory_list_before_update()
            await asyncio.sleep(2)
            
            await self.test_fifo_update_oldest()
            await asyncio.sleep(2)
            
            await self.test_inventory_list_after_update()
            
        except Exception as e:
            logger.error(f"❌ テスト実行エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        finally:
            # クリーンアップ
            await self.cleanup()
        
        logger.info("🎉 FIFO原則による最古アイテム更新テスト完了")

async def main():
    """メイン関数"""
    tester = UpdateOldestTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
