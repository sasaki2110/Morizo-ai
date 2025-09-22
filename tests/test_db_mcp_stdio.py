#!/usr/bin/env python3
"""
Database MCP Server (stdio transport) テスト
stdio接続でMCPサーバーを自動起動してテスト
"""

import asyncio
import json
from typing import Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_stdio_mcp_server():
    """stdio接続でMCPサーバーをテスト"""
    
    print("🧪 Database MCP Server（stdio接続）包括テスト開始")
    print("🔗 stdio接続でテストします")
    
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
                
                print("✅ Database MCP Server（stdio接続）接続成功")
                
                # 利用可能なツール一覧を取得
                tools_result = await session.list_tools()
                print(f"📡 利用可能ツール数: {len(tools_result.tools)}")
                
                # ツール名を表示
                for tool in tools_result.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                # テスト用の認証トークンをユーザー入力で取得
                print("\n🔑 認証トークンの入力が必要です")
                print("💡 ヒント: Next.js側で以下のコードを実行してトークンを取得してください")
                print("   const { data: { session } } = await supabase.auth.getSession();")
                print("   console.log('Access Token:', session?.access_token);")
                print()
                
                test_token = input("Access Token を入力してください: ").strip()
                
                if not test_token:
                    print("❌ トークンが入力されませんでした。テストを終了します。")
                    return
                
                print(f"✅ トークンを受け取りました（長さ: {len(test_token)}文字）")
                
                # 1. 在庫追加テスト
                print("\n📦 在庫追加テスト...")
                try:
                    add_result = await session.call_tool(
                        "inventory_add",
                        arguments={
                            "token": test_token,
                            "item_name": "テスト牛乳",
                            "quantity": 2.0,
                            "unit": "本",
                            "storage_location": "冷蔵庫"
                        }
                    )
                    print(f"在庫追加結果: {add_result}")
                    
                    # CallToolResultオブジェクトからデータを取得
                    if add_result and hasattr(add_result, 'content') and add_result.content:
                        result_data = json.loads(add_result.content[0].text)
                        if result_data.get("success"):
                            print("✅ 在庫追加成功")
                            item_id = result_data["data"]["id"]
                            
                            # 2. 在庫一覧取得テスト
                            print("\n📋 在庫一覧取得テスト...")
                            list_result = await session.call_tool(
                                "inventory_list",
                                arguments={"token": test_token}
                            )
                            print(f"在庫一覧結果: {list_result}")
                            
                            if list_result and hasattr(list_result, 'content') and list_result.content:
                                list_data = json.loads(list_result.content[0].text)
                                if list_data.get("success"):
                                    print(f"✅ 在庫一覧取得成功: {len(list_data['data'])}件")
                                    
                                    # 3. 在庫取得テスト
                                    print("\n🔍 在庫取得テスト...")
                                    get_result = await session.call_tool(
                                        "inventory_get",
                                        arguments={
                                            "token": test_token,
                                            "item_id": item_id
                                        }
                                    )
                                    print(f"在庫取得結果: {get_result}")
                                    
                                    if get_result and hasattr(get_result, 'content') and get_result.content:
                                        get_data = json.loads(get_result.content[0].text)
                                        if get_data.get("success"):
                                            print("✅ 在庫取得成功")
                                            
                                            # 4. 在庫更新テスト
                                            print("\n✏️ 在庫更新テスト...")
                                            update_result = await session.call_tool(
                                                "inventory_update",
                                                arguments={
                                                    "token": test_token,
                                                    "item_id": item_id,
                                                    "quantity": 5.0,
                                                    "storage_location": "冷凍庫"
                                                }
                                            )
                                            print(f"在庫更新結果: {update_result}")
                                            
                                            if update_result and hasattr(update_result, 'content') and update_result.content:
                                                update_data = json.loads(update_result.content[0].text)
                                                if update_data.get("success"):
                                                    print("✅ 在庫更新成功")
                                                    
                                                    # 5. 在庫削除テスト
                                                    print("\n🗑️ 在庫削除テスト...")
                                                    delete_result = await session.call_tool(
                                                        "inventory_delete",
                                                        arguments={
                                                            "token": test_token,
                                                            "item_id": item_id
                                                        }
                                                    )
                                                    print(f"在庫削除結果: {delete_result}")
                                                    
                                                    if delete_result and hasattr(delete_result, 'content') and delete_result.content:
                                                        delete_data = json.loads(delete_result.content[0].text)
                                                        if delete_data.get("success"):
                                                            print("✅ 在庫削除成功")
                                                        else:
                                                            print(f"❌ 在庫削除失敗: {delete_data.get('error')}")
                                                    else:
                                                        print("❌ 在庫削除結果の解析に失敗")
                                                else:
                                                    print(f"❌ 在庫更新失敗: {update_data.get('error')}")
                                            else:
                                                print("❌ 在庫更新結果の解析に失敗")
                                        else:
                                            print(f"❌ 在庫取得失敗: {get_data.get('error')}")
                                    else:
                                        print("❌ 在庫取得結果の解析に失敗")
                                else:
                                    print(f"❌ 在庫一覧取得失敗: {list_data.get('error')}")
                            else:
                                print("❌ 在庫一覧取得結果の解析に失敗")
                        else:
                            print(f"❌ 在庫追加失敗: {result_data.get('error')}")
                    else:
                        print("❌ 在庫追加結果の解析に失敗")
                        
                except Exception as e:
                    print(f"❌ 在庫追加テストエラー: {str(e)}")
                
                print("\n🎉 全テスト完了！")
                
    except Exception as e:
        print(f"❌ テスト実行エラー: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Database MCP Server (stdio transport) テスト開始")
    print("⚠️  注意: テスト前に.envファイルで認証情報を設定してください")
    print("⚠️  注意: テスト実行時に認証トークンの入力が求められます")
    print("⚠️  注意: サーバーは自動起動されます")
    print()
    
    asyncio.run(test_stdio_mcp_server())
