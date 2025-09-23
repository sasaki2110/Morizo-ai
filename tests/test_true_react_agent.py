"""
真のReActエージェントのテストプログラム
複数タスクの処理と行動計画立案をテストする
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
logger = logging.getLogger("test_true_react")

class TrueReactAgentTester:
    """真のReActエージェントのテスター"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.supabase_token = None
    
    async def setup(self):
        """テストのセットアップ"""
        logger.info("🧪 真のReActエージェントテスト開始")
        
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
        
        test_cases = [
            "牛乳1本買ってきたから、冷蔵庫に入れておいて",
            "りんご3個買ってきたから、冷蔵庫に入れておいて",
            "パン1袋買ってきたから、冷蔵庫に入れておいて"
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"🧪 テスト1-{i}: {test_case}")
            
            try:
                response = await self._send_chat_request(test_case)
                logger.info(f"✅ レスポンス: {response}")
                
                # 成功の確認
                if "完了" in response or "登録" in response:
                    logger.info(f"✅ テスト1-{i} 成功")
                else:
                    logger.warning(f"⚠️ テスト1-{i} 不明な結果")
                
            except Exception as e:
                logger.error(f"❌ テスト1-{i} エラー: {str(e)}")
                logger.error(traceback.format_exc())
            
            await asyncio.sleep(1)  # 1秒待機
    
    async def test_multiple_items_registration(self):
        """複数アイテム登録のテスト（真のAIエージェントの核心）"""
        logger.info("🧪 テスト2: 複数アイテム登録（真のAIエージェントテスト）")
        
        test_cases = [
            "鶏もも肉1パックともやし1袋買ってきたから、冷蔵庫に入れておいて",
            "牛乳2本とパン1袋買ってきたから、冷蔵庫に入れておいて",
            "りんご3個とバナナ1房とオレンジ2個買ってきたから、冷蔵庫に入れておいて"
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"🧪 テスト2-{i}: {test_case}")
            
            try:
                response = await self._send_chat_request(test_case)
                logger.info(f"✅ レスポンス: {response}")
                
                # 複数タスク処理の確認
                if "一連の作業が完了" in response or "完了しました" in response:
                    logger.info(f"✅ テスト2-{i} 成功: 複数タスク処理完了")
                elif "登録" in response and "完了" in response:
                    logger.info(f"✅ テスト2-{i} 成功: 複数タスク処理完了")
                else:
                    logger.warning(f"⚠️ テスト2-{i} 不明な結果: {response[:100]}...")
                
            except Exception as e:
                logger.error(f"❌ テスト2-{i} エラー: {str(e)}")
                logger.error(traceback.format_exc())
            
            await asyncio.sleep(2)  # 2秒待機
    
    async def test_mixed_operations(self):
        """混合操作のテスト"""
        logger.info("🧪 テスト3: 混合操作（登録・更新・削除）")
        
        test_cases = [
            "牛乳1本とパン1袋買ってきたから、冷蔵庫に入れておいて。その後、牛乳の数量を2本に変更して",
            "りんご3個買ってきたから、冷蔵庫に入れておいて。その後、りんご1個を削除して"
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"🧪 テスト3-{i}: {test_case}")
            
            try:
                response = await self._send_chat_request(test_case)
                logger.info(f"✅ レスポンス: {response}")
                
                # 混合操作の確認
                if "一連の作業が完了" in response:
                    logger.info(f"✅ テスト3-{i} 成功: 混合操作完了")
                else:
                    logger.warning(f"⚠️ テスト3-{i} 不明な結果: {response[:100]}...")
                
            except Exception as e:
                logger.error(f"❌ テスト3-{i} エラー: {str(e)}")
                logger.error(traceback.format_exc())
            
            await asyncio.sleep(2)  # 2秒待機
    
    async def test_inventory_status(self):
        """在庫状況確認のテスト"""
        logger.info("🧪 テスト4: 在庫状況確認")
        
        try:
            response = await self._send_chat_request("今の在庫を教えて")
            logger.info(f"✅ レスポンス: {response}")
            
            if "在庫" in response or "牛乳" in response or "パン" in response:
                logger.info("✅ テスト4 成功: 在庫状況取得完了")
            else:
                logger.warning(f"⚠️ テスト4 不明な結果: {response[:100]}...")
                
        except Exception as e:
            logger.error(f"❌ テスト4 エラー: {str(e)}")
            logger.error(traceback.format_exc())
    
    async def _send_chat_request(self, message: str) -> str:
        """チャットリクエストを送信"""
        try:
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
                return result.get("response", "レスポンスが空です")
            else:
                logger.error(f"❌ HTTPエラー: {response.status_code}")
                return f"HTTPエラー: {response.status_code}"
                
        except Exception as e:
            logger.error(f"❌ リクエストエラー: {str(e)}")
            return f"リクエストエラー: {str(e)}"
    
    async def cleanup(self):
        """テストのクリーンアップ"""
        logger.info("🧹 テストクリーンアップ")
        
        # テスト用データの削除
        cleanup_requests = [
            "テスト用の牛乳をすべて削除して",
            "テスト用のパンをすべて削除して",
            "テスト用のりんごをすべて削除して",
            "テスト用のバナナをすべて削除して",
            "テスト用のオレンジをすべて削除して",
            "テスト用の鶏もも肉をすべて削除して",
            "テスト用のもやしをすべて削除して"
        ]
        
        for request in cleanup_requests:
            try:
                await self._send_chat_request(request)
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"⚠️ クリーンアップエラー: {str(e)}")
        
        await self.client.aclose()
        logger.info("✅ クリーンアップ完了")
    
    async def run_all_tests(self):
        """全テストを実行"""
        logger.info("🚀 真のReActエージェントテスト開始")
        
        # セットアップ
        if not await self.setup():
            logger.error("❌ セットアップに失敗しました")
            return
        
        try:
            # テスト実行
            await self.test_single_item_registration()
            await asyncio.sleep(2)
            
            await self.test_multiple_items_registration()
            await asyncio.sleep(2)
            
            await self.test_mixed_operations()
            await asyncio.sleep(2)
            
            await self.test_inventory_status()
            
        except Exception as e:
            logger.error(f"❌ テスト実行エラー: {str(e)}")
            logger.error(traceback.format_exc())
        
        finally:
            # クリーンアップ
            await self.cleanup()
        
        logger.info("🎉 真のReActエージェントテスト完了")

async def main():
    """メイン関数"""
    tester = TrueReactAgentTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
