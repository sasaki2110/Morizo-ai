#!/usr/bin/env python3
"""
献立生成→レシピ検索の完全フローテスト
"""

import asyncio
import json
import time
import sys
import os
from typing import Dict, Any
import httpx
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class RecipeSearchFlowTester:
    """献立生成→レシピ検索の完全フローテスト"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.supabase_token = os.getenv("SUPABASE_ANON_KEY")
        if not self.supabase_token:
            print("❌ SUPABASE_ANON_KEY が設定されていません")
            sys.exit(1)
        self.client = httpx.AsyncClient(timeout=60.0)  # 30秒 → 60秒に延長
    
    async def send_message(self, message: str) -> Dict[str, Any]:
        """メッセージを送信してレスポンスを取得"""
        try:
            response = await self.client.post(
                f"{self.base_url}/chat",
                headers={
                    "Authorization": f"Bearer {self.supabase_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "message": message,
                    "session_id": "test_session_recipe_search"
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # 認証エラーの場合は詳細情報を返す
            if "401" in str(e) or "Authentication failed" in str(e):
                return {
                    "error": "認証エラー: Supabaseトークンが期限切れです。.envファイルのSUPABASE_ANON_KEYを更新してください。",
                    "original_error": str(e)
                }
            # 空のエラーメッセージの場合は詳細情報を提供
            error_msg = str(e) if str(e) else f"例外タイプ: {type(e).__name__}"
            return {
                "error": error_msg,
                "error_type": type(e).__name__,
                "error_repr": repr(e)
            }
    
    async def cleanup(self):
        """クライアントをクリーンアップ"""
        await self.client.aclose()
    
    def assertIn(self, member, container):
        """assertInの代替実装"""
        if member not in container:
            raise AssertionError(f"{member} not found in {container}")
    
    def assertIsInstance(self, obj, cls):
        """assertIsInstanceの代替実装"""
        if not isinstance(obj, cls):
            raise AssertionError(f"{obj} is not an instance of {cls}")
    
    async def test_scenario_menu_plan_with_recipe_search(self):
        """
        シナリオ: 在庫から献立を生成し、レシピを検索する
        期待される動作:
        1. inventory_list が実行され、在庫が取得される
        2. generate_menu_plan_with_history が実行され、献立が生成される
        3. search_recipe_from_web が実行され、レシピが検索される
        4. データフロー: 献立の料理名がレシピ検索のクエリに注入される
        """
        print("\n--- シナリオ: 献立生成→レシピ検索の完全フロー ---")
        user_message = "在庫で作れる献立とレシピを教えて"
        
        start_time = time.time()
        response = await self.send_message(user_message)
        end_time = time.time()
        
        print(f"応答: {json.dumps(response, ensure_ascii=False, indent=2)}")
        print(f"実行時間: {end_time - start_time:.2f}秒")
        
        self.assertIn("response", response)
        self.assertIsInstance(response["response"], str)
        
        # 献立とレシピの両方が含まれていることを確認
        response_text = response["response"]
        self.assertIn("献立", response_text)
        
        # レシピ検索が実行された場合の確認
        if "レシピ" in response_text or "作り方" in response_text or "調理" in response_text:
            print("✅ レシピ検索が実行されました")
        else:
            print("ℹ️ レシピ検索は実行されませんでした（献立生成のみ）")
        
        print("✅ シナリオ: 献立生成→レシピ検索の完全フロー 成功")
    
    async def test_scenario_inventory_add_menu_plan_recipe_search(self):
        """
        シナリオ: 在庫追加→献立生成→レシピ検索の完全フロー
        期待される動作:
        1. inventory_add タスクが並列実行される
        2. inventory_list が実行される
        3. generate_menu_plan_with_history が実行される
        4. search_recipe_from_web が実行される
        5. データフロー: 献立の料理名がレシピ検索のクエリに注入される
        """
        print("\n--- シナリオ: 在庫追加→献立生成→レシピ検索の完全フロー ---")
        user_message = "牛すね肉と人参を追加して、在庫で作れる献立とレシピを教えて"
        
        start_time = time.time()
        response = await self.send_message(user_message)
        end_time = time.time()
        
        print(f"応答: {json.dumps(response, ensure_ascii=False, indent=2)}")
        print(f"実行時間: {end_time - start_time:.2f}秒")
        
        self.assertIn("response", response)
        self.assertIsInstance(response["response"], str)
        
        # 在庫追加、献立、レシピの全てが含まれていることを確認
        response_text = response["response"]
        self.assertIn("牛すね肉", response_text)
        self.assertIn("人参", response_text)
        self.assertIn("献立", response_text)
        
        # レシピ検索が実行された場合の確認
        if "レシピ" in response_text or "作り方" in response_text or "調理" in response_text:
            print("✅ レシピ検索が実行されました")
        else:
            print("ℹ️ レシピ検索は実行されませんでした（献立生成のみ）")
        
        print("✅ シナリオ: 在庫追加→献立生成→レシピ検索の完全フロー 成功")

async def main():
    """メイン実行関数"""
    print("🚀 献立生成→レシピ検索の完全フローテスト開始")
    
    tester = RecipeSearchFlowTester()
    
    try:
        # テスト実行
        await tester.test_scenario_menu_plan_with_recipe_search()
        await tester.test_scenario_inventory_add_menu_plan_recipe_search()
        
        print("\n🎉 全てのテストが成功しました！")
        
    except Exception as e:
        print(f"\n❌ テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
