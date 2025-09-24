"""
真のReActエージェントの短めテストプログラム
複数タスクの処理と行動計画立案をテストする（DBクリーンアップなし）
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
logger = logging.getLogger("test_true_react_short")

class TrueReactAgentShortTester:
    """真のReActエージェントの短めテスター"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.supabase_token = None
    
    async def setup(self):
        """テストのセットアップ"""
        logger.info("🧪 真のReActエージェント短めテスト開始")
        
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
    
    async def test_single_item_registration(self):
        """単一アイテム登録のテスト"""
        logger.info("🧪 テスト1: 単一アイテム登録")
        
        test_case = "牛乳1本買ってきたから、冷蔵庫に入れておいて"
        logger.info(f"🧪 テスト1: {test_case}")
        
        try:
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # 成功の確認
            if "完了" in response or "登録" in response:
                logger.info(f"✅ テスト1 成功")
            else:
                logger.warning(f"⚠️ テスト1 不明な結果")
            
        except Exception as e:
            logger.error(f"❌ テスト1 エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(1)  # 1秒待機
    
    async def test_multiple_items_registration(self):
        """複数アイテム登録のテスト（真のAIエージェントの核心）"""
        logger.info("🧪 テスト2: 複数アイテム登録（真のAIエージェントテスト）")
        
        test_case = "鶏もも肉1パックともやし1袋買ってきたから、冷蔵庫に入れておいて"
        logger.info(f"🧪 テスト2: {test_case}")
        
        try:
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # 複数タスク処理の確認
            if "一連の作業が完了" in response or "完了しました" in response:
                logger.info(f"✅ テスト2 成功: 複数タスク処理完了")
            elif "登録" in response and "完了" in response:
                logger.info(f"✅ テスト2 成功: 複数タスク処理完了")
            else:
                logger.warning(f"⚠️ テスト2 不明な結果: {response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト2 エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(2)  # 2秒待機
    
    async def test_mixed_operations(self):
        """混合操作のテスト"""
        logger.info("🧪 テスト3: 混合操作（登録・更新・削除）")
        
        test_case = "牛乳1本とパン1袋買ってきたから、冷蔵庫に入れておいて。その後、牛乳の数量を2本に変更して"
        logger.info(f"🧪 テスト3: {test_case}")
        
        try:
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # 混合操作の確認
            if "一連の作業が完了" in response:
                logger.info(f"✅ テスト3 成功: 混合操作完了")
            else:
                logger.warning(f"⚠️ テスト3 不明な結果: {response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト3 エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(2)  # 2秒待機
    
    async def test_simple_greeting(self):
        """単純な挨拶のテスト（ツール不要パターン）"""
        logger.info("🧪 テスト4: 単純な挨拶（ツール不要パターン）")
        
        test_case = "こんにちは"
        logger.info(f"🧪 テスト4: {test_case}")
        
        try:
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # 挨拶の確認
            if "こんにちは" in response or "おはよう" in response or "こんばんは" in response:
                logger.info(f"✅ テスト4 成功: 挨拶応答完了")
            else:
                logger.warning(f"⚠️ テスト4 不明な結果: {response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト4 エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(1)  # 1秒待機
    
    async def test_inventory_status(self):
        """在庫状況確認のテスト"""
        logger.info("🧪 テスト5: 在庫状況確認")
        
        try:
            response = await self._send_chat_request("今の在庫を教えて")
            logger.info(f"✅ レスポンス: {response}")
            
            if "在庫" in response or "牛乳" in response or "パン" in response:
                logger.info("✅ テスト5 成功: 在庫状況取得完了")
            else:
                logger.warning(f"⚠️ テスト5 不明な結果: {response[:100]}...")
                
        except Exception as e:
            logger.error(f"❌ テスト5 エラー: {str(e)}")
            logger.error(traceback.format_exc())
    
    async def test_bulk_delete_by_name(self):
        """一括削除のテスト（by_name）"""
        logger.info("🧪 テスト6: 一括削除（by_name）")
        
        test_case = "牛乳9本全部削除"
        logger.info(f"🧪 テスト6: {test_case}")
        
        try:
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # 一括削除の確認
            if "削除" in response and "完了" in response:
                logger.info(f"✅ テスト6 成功: 一括削除完了")
            else:
                logger.warning(f"⚠️ テスト6 不明な結果: {response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト6 エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(1)
    
    async def test_bulk_update_by_name(self):
        """一括更新のテスト（by_name）"""
        logger.info("🧪 テスト7: 一括更新（by_name）")
        
        test_case = "パンは冷凍したから、賞味期限をクリアしておいて"
        logger.info(f"🧪 テスト7: {test_case}")
        
        try:
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # 一括更新の確認
            if "更新" in response and "完了" in response:
                logger.info(f"✅ テスト7 成功: 一括更新完了")
            else:
                logger.warning(f"⚠️ テスト7 不明な結果: {response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト7 エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(1)
    
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
        """テストのクリーンアップ（DBクリーンアップなし）"""
        logger.info("🧹 テストクリーンアップ（DBクリーンアップなし）")
        await self.client.aclose()
        logger.info("✅ クリーンアップ完了")
    
    async def run_all_tests(self):
        """全テストを実行"""
        logger.info("🚀 真のReActエージェント短めテスト開始")
        
        # セットアップ
        if not await self.setup():
            logger.error("❌ セットアップに失敗しました")
            return
        
        try:
            # テスト実行
            await self.test_simple_greeting()
            await asyncio.sleep(2)
            
            await self.test_single_item_registration()
            await asyncio.sleep(2)
            
            await self.test_multiple_items_registration()
            await asyncio.sleep(2)
            
            await self.test_mixed_operations()
            await asyncio.sleep(2)
            
            await self.test_inventory_status()
            await asyncio.sleep(2)
            
            await self.test_bulk_delete_by_name()
            await asyncio.sleep(2)
            
            await self.test_bulk_update_by_name()
            
        except Exception as e:
            logger.error(f"❌ テスト実行エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        finally:
            # クリーンアップ
            await self.cleanup()
        
        logger.info("🎉 真のReActエージェント短めテスト完了")

async def main():
    """メイン関数"""
    tester = TrueReactAgentShortTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
