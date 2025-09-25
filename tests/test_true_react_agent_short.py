"""
真のReActエージェント短めテスト（シンプル版）
"""

import asyncio
import json
import logging
import traceback
from typing import List, Dict, Any
import httpx
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_true_react_agent_short")

class TrueReactAgentShortTester:
    """真のReActエージェント短めテストクラス（シンプル版）"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.supabase_token = None
    
    async def setup(self):
        """テストのセットアップ"""
        logger.info("🧪 真のReActエージェント短めテスト開始（シンプル版）")
        
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
        """テスト1: 単純な挨拶"""
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
    
    async def test_single_item_registration(self):
        """テスト2: 単一アイテム登録"""
        logger.info("🧪 テスト2: 単一アイテム登録")
        test_case = "牛乳1本買ってきたから、冷蔵庫に入れておいて"
        logger.info(f"🧪 テスト2: {test_case}")
        
        try:
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # 登録成功の確認
            if "完了" in response or "登録" in response or "追加" in response:
                logger.info(f"✅ テスト2 成功: 単一アイテム登録完了")
            else:
                logger.warning(f"⚠️ テスト2 不明な結果: {response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト2 エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(2)  # 2秒待機
    
    async def test_multiple_items_registration(self):
        """テスト3: 複数アイテム登録"""
        logger.info("🧪 テスト3: 複数アイテム登録")
        test_case = "鶏もも肉1パックともやし1袋買ってきたから、冷蔵庫に入れておいて"
        logger.info(f"🧪 テスト3: {test_case}")
        
        try:
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # 複数登録成功の確認
            if "完了" in response or "登録" in response or "追加" in response:
                logger.info(f"✅ テスト3 成功: 複数アイテム登録完了")
            else:
                logger.warning(f"⚠️ テスト3 不明な結果: {response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト3 エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(2)  # 2秒待機
    
    async def test_bulk_delete_by_name(self):
        """テスト4: 一括削除（by_name）"""
        logger.info("🧪 テスト4: 一括削除（by_name）")
        test_case = "実は牛乳腐っちゃったから、全部削除して"
        logger.info(f"🧪 テスト4: {test_case}")
        
        try:
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # 一括削除の確認
            if "削除" in response and ("完了" in response or "削除しました" in response):
                logger.info(f"✅ テスト4 成功: 一括削除完了")
            else:
                logger.warning(f"⚠️ テスト4 不明な結果: {response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト4 エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(2)  # 2秒待機
    
    async def test_prepare_fifo_data(self):
        """テスト4.5: FIFO/最新削除テスト用データ準備"""
        logger.info("🧪 テスト4.5: FIFO/最新削除テスト用データ準備")
        
        try:
            # 牛乳を3つ追加（異なる作成日時でFIFOテスト用）
            test_cases = [
                "牛乳を1本追加して",
                "牛乳を2本追加して", 
                "牛乳を3本追加して"
            ]
            
            for i, test_case in enumerate(test_cases, 1):
                logger.info(f"🧪 テスト4.5-{i}: {test_case}")
                response = await self._send_chat_request(test_case)
                logger.info(f"✅ レスポンス: {response}")
                
                if "追加" in response and ("完了" in response or "追加しました" in response):
                    logger.info(f"✅ テスト4.5-{i} 成功: 牛乳{i}本追加完了")
                else:
                    logger.warning(f"⚠️ テスト4.5-{i} 不明な結果: {response[:100]}...")
                
                await asyncio.sleep(1)  # 作成日時を分けるため1秒待機
            
            logger.info(f"✅ テスト4.5 成功: FIFO/最新削除テスト用データ準備完了")
            
        except Exception as e:
            logger.error(f"❌ テスト4.5 エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(2)  # 2秒待機
    
    async def test_inventory_status(self):
        """テスト5: 在庫状況確認"""
        logger.info("🧪 テスト5: 在庫状況確認")
        test_case = "今の在庫を教えて"
        logger.info(f"🧪 テスト5: {test_case}")
        
        try:
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # 在庫状況の確認
            if "在庫" in response:
                logger.info(f"✅ テスト5 成功: 在庫状況確認完了")
            else:
                logger.warning(f"⚠️ テスト5 不明な結果: {response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト5 エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(1)  # 1秒待機
    
    async def test_fifo_update_oldest(self):
        """テスト6: FIFO原則による最古アイテム更新"""
        logger.info("🧪 テスト6: FIFO原則による最古アイテム更新")
        test_case = "牛乳の数量を3本に変更して"
        logger.info(f"🧪 テスト6: {test_case}")
        
        try:
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # FIFO更新の確認
            if "更新" in response and ("完了" in response or "変更" in response):
                logger.info(f"✅ テスト6 成功: FIFO原則による最古アイテム更新完了")
            else:
                logger.warning(f"⚠️ テスト6 不明な結果: {response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト6 エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(2)  # 2秒待機
    
    async def test_user_specified_latest(self):
        """テスト7: ユーザー指定による最新アイテム更新"""
        logger.info("🧪 テスト7: ユーザー指定による最新アイテム更新")
        test_case = "最新の牛乳の本数を3本に変えて"
        logger.info(f"🧪 テスト7: {test_case}")
        
        try:
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # ユーザー指定更新の確認
            if "更新" in response and ("完了" in response or "変更" in response):
                logger.info(f"✅ テスト7 成功: ユーザー指定による最新アイテム更新完了")
            else:
                logger.warning(f"⚠️ テスト7 不明な結果: {response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト7 エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(2)  # 2秒待機
    
    async def test_fifo_delete_oldest(self):
        """テスト8: FIFO原則による最古アイテム削除"""
        logger.info("🧪 テスト8: FIFO原則による最古アイテム削除")
        test_case = "牛乳の古い方を削除して"
        logger.info(f"🧪 テスト8: {test_case}")
        
        try:
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # FIFO削除の確認
            if "削除" in response and ("完了" in response or "処分" in response):
                logger.info(f"✅ テスト8 成功: FIFO原則による最古アイテム削除完了")
            else:
                logger.warning(f"⚠️ テスト8 不明な結果: {response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト8 エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(2)  # 2秒待機
    
    async def test_user_specified_delete_latest(self):
        """テスト9: ユーザー指定による最新アイテム削除"""
        logger.info("🧪 テスト9: ユーザー指定による最新アイテム削除")
        test_case = "最新の牛乳を削除して"
        logger.info(f"🧪 テスト9: {test_case}")
        
        try:
            response = await self._send_chat_request(test_case)
            logger.info(f"✅ レスポンス: {response}")
            
            # ユーザー指定削除の確認
            if "削除" in response and ("完了" in response or "処分" in response):
                logger.info(f"✅ テスト9 成功: ユーザー指定による最新アイテム削除完了")
            else:
                logger.warning(f"⚠️ テスト9 不明な結果: {response[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ テスト9 エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        await asyncio.sleep(2)  # 2秒待機
    
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
        logger.info("🚀 真のReActエージェント短めテスト開始（シンプル版）")
        
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
            
            await self.test_bulk_delete_by_name()
            await asyncio.sleep(2)
            
            await self.test_prepare_fifo_data()
            await asyncio.sleep(2)
            
            await self.test_inventory_status()
            await asyncio.sleep(2)
            
            await self.test_fifo_update_oldest()
            await asyncio.sleep(2)
            
            await self.test_user_specified_latest()
            await asyncio.sleep(2)
            
            await self.test_fifo_delete_oldest()
            await asyncio.sleep(2)
            
            await self.test_user_specified_delete_latest()
        
        except Exception as e:
            logger.error(f"❌ テスト実行エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        finally:
            # クリーンアップ
            await self.cleanup()
    
    logger.info("🎉 真のReActエージェント短めテスト完了（シンプル版）")

async def main():
    """メイン関数"""
    tester = TrueReactAgentShortTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())