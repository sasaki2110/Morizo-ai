"""
複数アイテム登録テスト（真のAIエージェントの核心）
"""

import asyncio
import json
import logging
import traceback
from typing import List, Dict, Any
import httpx
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_insert_twice")

class InsertTwiceTester:
    """複数アイテム登録テストクラス"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.supabase_token = None
    
    async def setup(self):
        """テストのセットアップ"""
        logger.info("🧪 InsertTwiceテスト開始")
        
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
                return ""
        
        return token
    
    async def test_simple_greeting(self):
        """テスト1: 単純な挨拶（ツール不要パターン）"""
        logger.info("🧪 テスト1: 単純な挨拶")
        test_case = "こんにちは"
        logger.info(f"🧪 テスト1: {test_case}")
        
        try:
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # 挨拶応答のチェック
            if "こんにちは" in response or "おはよう" in response or "こんばんは" in response:
                logger.info(f"✅ テスト1 成功: 挨拶応答完了")
            else:
                logger.warning(f"⚠️ テスト1 不明な結果: {response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト1 エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(1)  # 1秒待機
    
    async def test_multiple_item_registration(self):
        """テスト2: 複数アイテム登録（真のAIエージェントの核心）"""
        logger.info("🧪 テスト2: 複数アイテム登録（真のAIエージェントテスト）")
        test_case = "鶏もも肉1パックともやし1袋買ってきたから、冷蔵庫に入れておいて"
        logger.info(f"🧪 テスト2: {test_case}")
        
        try:
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # 複数アイテム登録の成功チェック
            if ("完了" in response or "登録" in response or "追加" in response) and ("鶏もも肉" in response or "もやし" in response):
                logger.info(f"✅ テスト2 成功: 複数アイテム登録完了")
            else:
                logger.warning(f"⚠️ テスト2 不明な結果: {response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト2 エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(1)  # 1秒待機
    
    async def test_inventory_status(self):
        """テスト3: 在庫状況確認（複数アイテム登録後の確認）"""
        logger.info("🧪 テスト3: 在庫状況確認")
        test_case = "今の在庫状況を教えて"
        logger.info(f"🧪 テスト3: {test_case}")
        
        try:
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # 在庫状況が表示されているかチェック
            if "在庫" in response and ("鶏もも肉" in response or "もやし" in response):
                logger.info(f"✅ テスト3 成功: 在庫状況表示完了")
            else:
                logger.warning(f"⚠️ テスト3 不明な結果: {response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト3 エラー: {str(e)}")
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
        logger.info("🚀 InsertTwiceテスト開始")
        
        # セットアップ
        if not await self.setup():
            logger.error("❌ セットアップに失敗しました")
            return
        
        try:
            # テスト実行
            await self.test_simple_greeting()
            await asyncio.sleep(2)
            
            await self.test_multiple_item_registration()
            await asyncio.sleep(2)
            
            await self.test_inventory_status()
            
        except Exception as e:
            logger.error(f"❌ テスト実行エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        finally:
            # クリーンアップ
            await self.cleanup()
        
        logger.info("🎉 InsertTwiceテスト完了")

async def main():
    """メイン関数"""
    tester = InsertTwiceTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
