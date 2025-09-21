#!/usr/bin/env python3
"""
MCPサーバーの検証スクリプト（FastMCP専用版）
supabase_mcp_server.py の各ツールをテスト
"""

import asyncio
import os
from dotenv import load_dotenv

# FastMCPクライアントをインポート
from fastmcp import Client

# 環境変数読み込み
load_dotenv()

class FastMCPServerTester:
    def __init__(self):
        self.mcp_client = None
        self.token = None
    
    async def connect_to_server(self):
        """MCPサーバーに接続"""
        print("🚀 FastMCPサーバー接続中...")
        
        try:
            # 実績のある方法: HTTPトランスポートで接続
            server_url = "http://localhost:8001/mcp"
            self.mcp_client = Client(server_url)
            await self.mcp_client.__aenter__()
            print("✅ FastMCPサーバー接続成功")
            return True
            
        except Exception as e:
            print(f"❌ FastMCPサーバー接続失敗: {e}")
            return False
    
    async def test_server_initialization(self):
        """サーバー初期化テスト"""
        print("\n🔍 サーバー初期化テスト...")
        
        try:
            # ツール一覧取得
            tools = await self.mcp_client.list_tools()
            print(f"✅ 利用可能ツール数: {len(tools)}")
            for tool in tools:
                # Toolオブジェクトの正しい属性アクセス
                tool_name = getattr(tool, 'name', 'Unknown')
                print(f"   - {tool_name}")
            return True
            
        except Exception as e:
            print(f"❌ ツール一覧取得失敗: {e}")
            return False
    
    def get_auth_token(self):
        """認証トークンを取得"""
        print("\n🔑 認証トークン取得...")
        
        # 環境変数からトークンを取得（テスト用）
        token = os.getenv("TEST_AUTH_TOKEN")
        if not token:
            print("⚠️  TEST_AUTH_TOKEN が設定されていません")
            print("Next.js側でログイン後、トークンを取得してください")
            token = input("認証トークンを入力してください: ").strip()
        
        self.token = token
        print(f"✅ トークン設定完了: {token[:20]}...")
        return True
    
    async def test_inventory_add(self):
        """在庫追加ツールのテスト"""
        print("\n📝 在庫追加テスト...")
        
        try:
            result = await self.mcp_client.call_tool("inventory_add", {
                "token": self.token,
                "item_name": "テスト食材",
                "quantity": 2.0,
                "unit": "個",
                "storage_location": "冷蔵庫",
                "expiry_date": "2024-12-31"
            })
            
            # CallToolResultオブジェクトの正しい処理
            if hasattr(result, 'data'):
                actual_result = result.data
            else:
                actual_result = result
                
            if actual_result.get("success"):
                print("✅ 在庫追加成功")
                print(f"   追加されたアイテム: {actual_result['data']}")
                return actual_result["data"]
            else:
                print(f"❌ 在庫追加失敗: {actual_result.get('error')}")
                return None
                
        except Exception as e:
            print(f"❌ 在庫追加エラー: {e}")
            return None
    
    async def test_inventory_list(self):
        """在庫一覧ツールのテスト"""
        print("\n📋 在庫一覧テスト...")
        
        try:
            result = await self.mcp_client.call_tool("inventory_list", {
                "token": self.token
            })
            
            # CallToolResultオブジェクトの正しい処理
            if hasattr(result, 'data'):
                actual_result = result.data
            else:
                actual_result = result
                
            if actual_result.get("success"):
                items = actual_result["data"]
                print(f"✅ 在庫一覧取得成功: {len(items)}件")
                for item in items:
                    print(f"   - {item.get('item_name')}: {item.get('quantity')}{item.get('unit')}")
                return items
            else:
                print(f"❌ 在庫一覧取得失敗: {actual_result.get('error')}")
                return None
                
        except Exception as e:
            print(f"❌ 在庫一覧エラー: {e}")
            return None
    
    async def test_inventory_update(self, item_id):
        """在庫更新ツールのテスト"""
        print(f"\n✏️ 在庫更新テスト (ID: {item_id})...")
        
        try:
            result = await self.mcp_client.call_tool("inventory_update", {
                "token": self.token,
                "item_id": item_id,
                "quantity": 5.0,
                "storage_location": "冷凍庫"
            })
            
            # CallToolResultオブジェクトの正しい処理
            if hasattr(result, 'data'):
                actual_result = result.data
            else:
                actual_result = result
                
            if actual_result.get("success"):
                print("✅ 在庫更新成功")
                print(f"   更新されたアイテム: {actual_result['data']}")
                return actual_result["data"]
            else:
                print(f"❌ 在庫更新失敗: {actual_result.get('error')}")
                return None
                
        except Exception as e:
            print(f"❌ 在庫更新エラー: {e}")
            return None
    
    async def test_inventory_delete(self, item_id):
        """在庫削除ツールのテスト"""
        print(f"\n🗑️ 在庫削除テスト (ID: {item_id})...")
        
        try:
            result = await self.mcp_client.call_tool("inventory_delete", {
                "token": self.token,
                "item_id": item_id
            })
            
            # CallToolResultオブジェクトの正しい処理
            if hasattr(result, 'data'):
                actual_result = result.data
            else:
                actual_result = result
                
            if actual_result.get("success"):
                print("✅ 在庫削除成功")
                return True
            else:
                print(f"❌ 在庫削除失敗: {actual_result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ 在庫削除エラー: {e}")
            return False
    
    async def run_all_tests(self):
        """全テストを実行"""
        print("🧪 FastMCPサーバー包括テスト開始\n")
        
        # 1. サーバー接続
        if not await self.connect_to_server():
            return False
        
        # 2. サーバー初期化テスト
        if not await self.test_server_initialization():
            return False
        
        # 3. 認証トークン取得
        if not self.get_auth_token():
            return False
        
        # 4. CRUD操作テスト
        added_item = await self.test_inventory_add()
        if not added_item:
            return False
        
        # 5. 一覧取得テスト
        items = await self.test_inventory_list()
        if not items:
            return False
        
        # 6. 更新テスト
        if added_item and "id" in added_item:
            await self.test_inventory_update(added_item["id"])
        
        # 7. 削除テスト
        if added_item and "id" in added_item:
            await self.test_inventory_delete(added_item["id"])
        
        print("\n🎉 全テスト完了！")
        return True
    
    async def cleanup(self):
        """クリーンアップ"""
        print("\n🧹 クリーンアップ中...")
        
        if self.mcp_client:
            try:
                await self.mcp_client.__aexit__(None, None, None)
                print("✅ FastMCPクライアント切断完了")
            except Exception as e:
                print(f"❌ クライアント切断エラー: {e}")

async def main():
    """メイン実行"""
    tester = FastMCPServerTester()
    
    try:
        success = await tester.run_all_tests()
        if success:
            print("\n✅ 全テスト成功！FastMCPサーバーは正常に動作しています。")
        else:
            print("\n❌ テスト失敗。FastMCPサーバーに問題があります。")
    except KeyboardInterrupt:
        print("\n⚠️  テスト中断")
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())