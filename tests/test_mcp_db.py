#!/usr/bin/env python3
"""
DB MCP Server テスト
在庫管理機能の各ツール動作確認
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 環境変数を読み込み
load_dotenv()

async def test_db_mcp_tools():
    """DB MCP Serverの各ツール動作確認"""
    
    print("🧪 DB MCP Server ツール動作確認テスト開始")
    print("=" * 60)
    
    # 認証トークンの取得
    token = os.getenv("SUPABASE_ANON_KEY")
    if not token:
        print("❌ エラー: SUPABASE_ANON_KEY が設定されていません")
        print("💡 ヒント: .env ファイルに SUPABASE_ANON_KEY=your-token を追加してください")
        return False
    
    print(f"✅ 認証トークン取得完了: {token[:20]}...")
    print("=" * 60)
    
    try:
        # stdio接続でMCPサーバーを自動起動
        server_params = StdioServerParameters(
            command="python",
            args=["db_mcp_server_stdio.py"]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 初期化
                await session.initialize()
                
                print("✅ MCPサーバー接続成功")
                
                # 利用可能ツールの確認
                tools = await session.list_tools()
                print(f"📋 利用可能ツール: {len(tools.tools)}個")
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                print("\n" + "=" * 60)
                
                # テスト1: 在庫一覧取得
                print("🔍 テスト1: 在庫一覧取得")
                try:
                    result = await session.call_tool("inventory_list", {"token": token})
                    print(f"✅ 在庫一覧取得成功")
                    print(f"📊 結果: {result.content}")
                except Exception as e:
                    print(f"❌ 在庫一覧取得失敗: {e}")
                
                print("\n" + "-" * 40)
                
                # テスト2: 在庫追加（単一アイテム）
                print("🔍 テスト2: 在庫追加（単一アイテム）")
                try:
                    result = await session.call_tool("inventory_add", {
                        "token": token,
                        "item_name": "テスト用卵",
                        "quantity": 1,
                        "unit": "個"
                    })
                    print(f"✅ 在庫追加成功")
                    print(f"📊 結果: {result.content}")
                except Exception as e:
                    print(f"❌ 在庫追加失敗: {e}")
                
                print("\n" + "-" * 40)
                
                # テスト3: 在庫追加（複数アイテム）
                print("🔍 テスト3: 在庫追加（複数アイテム）")
                try:
                    result = await session.call_tool("inventory_add", {
                        "token": token,
                        "item_name": "テスト用牛乳",
                        "quantity": 2,
                        "unit": "本"
                    })
                    print(f"✅ 在庫追加成功")
                    print(f"📊 結果: {result.content}")
                except Exception as e:
                    print(f"❌ 在庫追加失敗: {e}")
                
                print("\n" + "-" * 40)
                
                # テスト4: 在庫一覧取得（追加後）
                print("🔍 テスト4: 在庫一覧取得（追加後）")
                try:
                    result = await session.call_tool("inventory_list", {"token": token})
                    print(f"✅ 在庫一覧取得成功")
                    print(f"📊 結果: {result.content}")
                except Exception as e:
                    print(f"❌ 在庫一覧取得失敗: {e}")
                
                print("\n" + "-" * 40)
                
                # テスト5: 在庫更新（名前指定）
                print("🔍 テスト5: 在庫更新（名前指定）")
                try:
                    result = await session.call_tool("inventory_update_by_name", {
                        "token": token,
                        "item_name": "テスト用卵",
                        "quantity": 3,
                        "unit": "個"
                    })
                    print(f"✅ 在庫更新成功")
                    print(f"📊 結果: {result.content}")
                except Exception as e:
                    print(f"❌ 在庫更新失敗: {e}")
                
                print("\n" + "-" * 40)
                
                # テスト6: 在庫削除（名前指定）
                print("🔍 テスト6: 在庫削除（名前指定）")
                try:
                    result = await session.call_tool("inventory_delete_by_name", {
                        "token": token,
                        "item_name": "テスト用牛乳"
                    })
                    print(f"✅ 在庫削除成功")
                    print(f"📊 結果: {result.content}")
                except Exception as e:
                    print(f"❌ 在庫削除失敗: {e}")
                
                print("\n" + "-" * 40)
                
                # テスト7: 最終在庫一覧取得
                print("🔍 テスト7: 最終在庫一覧取得")
                try:
                    result = await session.call_tool("inventory_list", {"token": token})
                    print(f"✅ 在庫一覧取得成功")
                    print(f"📊 結果: {result.content}")
                except Exception as e:
                    print(f"❌ 在庫一覧取得失敗: {e}")
                
                print("\n" + "=" * 60)
                print("🎉 DB MCP Server ツール動作確認テスト完了")
                
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db_mcp_tools())
