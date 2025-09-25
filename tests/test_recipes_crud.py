#!/usr/bin/env python3
"""
Recipes CRUD Operations テスト
recipesテーブルのCRUD操作をテストする
"""

import asyncio
import json
from typing import Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_recipes_crud():
    """recipesテーブルのCRUD操作をテスト"""
    
    print("🧪 Recipes CRUD Operations テスト開始")
    print("🔗 stdio接続でテストします")
    
    # 認証トークンの入力
    print("\n🔐 認証トークンの入力が必要です")
    print("Supabaseの認証トークンを入力してください（Bearer は不要）:")
    test_token = input("Token: ").strip()
    
    if not test_token:
        print("❌ 認証トークンが入力されていません。テストを終了します。")
        return
    
    print(f"✅ 認証トークンが入力されました: {test_token[:10]}...")
    
    # テスト実行の確認
    print("\n⚠️  このテストは実際のSupabaseデータベースに接続します")
    print("以下の操作が実行されます:")
    print("  1. レシピの追加")
    print("  2. レシピ一覧の取得")
    print("  3. 最新レシピの更新")
    print("  4. 最新レシピの削除")
    
    confirm = input("\n続行しますか？ (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ テストをキャンセルしました")
        return
    
    print("🚀 テストを開始します...")
    
    try:
        # stdio接続でMCPサーバーを自動起動
        server_params = StdioServerParameters(
            command="python",
            args=["db_mcp_server_stdio.py"]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # サーバー初期化
                await session.initialize()
                
                print("\n=== 1. recipes_add テスト ===")
                try:
                    result = await session.call_tool(
                        "recipes_add",
                        arguments={
                            "token": test_token,
                            "title": "牛乳と卵のフレンチトースト",
                            "source": "web",
                            "url": "https://cookpad.com/recipe/123456",
                            "rating": 4,
                            "notes": "美味しかった！"
                        }
                    )
                    print(f"✅ recipes_add 結果: {json.dumps(result.content[0].text, indent=2, ensure_ascii=False)}")
                except Exception as e:
                    print(f"❌ recipes_add エラー: {e}")
                
                print("\n=== 2. recipes_list テスト ===")
                try:
                    result = await session.call_tool(
                        "recipes_list",
                        arguments={
                            "token": test_token,
                            "limit": 10
                        }
                    )
                    print(f"✅ recipes_list 結果: {json.dumps(result.content[0].text, indent=2, ensure_ascii=False)}")
                except Exception as e:
                    print(f"❌ recipes_list エラー: {e}")
                
                print("\n=== 3. recipes_update_latest テスト ===")
                try:
                    result = await session.call_tool(
                        "recipes_update_latest",
                        arguments={
                            "token": test_token,
                            "rating": 5,
                            "notes": "更新されたメモ"
                        }
                    )
                    print(f"✅ recipes_update_latest 結果: {json.dumps(result.content[0].text, indent=2, ensure_ascii=False)}")
                except Exception as e:
                    print(f"❌ recipes_update_latest エラー: {e}")
                
                print("\n=== 4. recipes_delete_latest テスト ===")
                try:
                    result = await session.call_tool(
                        "recipes_delete_latest",
                        arguments={
                            "token": test_token
                        }
                    )
                    print(f"✅ recipes_delete_latest 結果: {json.dumps(result.content[0].text, indent=2, ensure_ascii=False)}")
                except Exception as e:
                    print(f"❌ recipes_delete_latest エラー: {e}")
                
                print("\n=== 5. 最終確認: recipes_list テスト ===")
                try:
                    result = await session.call_tool(
                        "recipes_list",
                        arguments={
                            "token": test_token,
                            "limit": 10
                        }
                    )
                    print(f"✅ 最終確認結果: {json.dumps(result.content[0].text, indent=2, ensure_ascii=False)}")
                except Exception as e:
                    print(f"❌ 最終確認エラー: {e}")
                
                print("\n🎉 Recipes CRUD Operations テスト完了")
                
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Recipes CRUD Operations テスト")
    print("=" * 60)
    print("このテストは以下の操作を実行します:")
    print("  • recipes_add: レシピ履歴の追加")
    print("  • recipes_list: レシピ履歴一覧取得")
    print("  • recipes_update_latest: 最新レシピの更新")
    print("  • recipes_delete_latest: 最新レシピの削除")
    print("")
    print("⚠️  注意: 実際のSupabaseデータベースに接続します")
    print("   テスト用のレシピが追加・更新・削除されます")
    print("=" * 60)
    
    asyncio.run(test_recipes_crud())
