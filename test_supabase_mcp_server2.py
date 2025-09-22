#!/usr/bin/env python3
"""
Supabase MCP Server 2 (Annotation-based) テスト
公式チュートリアルに従ったアノテーション方式のMCPサーバーのテスト
FastMCPクライアントを使用
"""

import asyncio
import json
from typing import Dict, Any
from fastmcp import Client

async def test_annotation_mcp_server():
    """アノテーション方式のMCPサーバーをテスト（FastMCPクライアント）"""
    
    print("🧪 FastMCPサーバー（アノテーション方式）包括テスト開始")
    print("🌐 FastMCPクライアントでテストします")
    
    # FastMCPクライアントでサーバーに接続
    server_url = "http://localhost:8002/mcp"
    
    try:
        # FastMCPクライアントの初期化
        mcp_client = Client(server_url)
        await mcp_client.__aenter__()
        
        print("✅ FastMCPサーバー（アノテーション方式）接続成功")
        
        # 利用可能なツール一覧を取得
        tools = await mcp_client.list_tools()
        print(f"📡 利用可能ツール数: {len(tools)}")
        
        # ツール名を表示
        for tool in tools:
            tool_name = getattr(tool, 'name', 'Unknown')
            tool_desc = getattr(tool, 'description', 'No description')
            print(f"  - {tool_name}: {tool_desc}")
            
        # テスト用の認証トークンをユーザー入力で取得
        print("\n🔑 Supabase認証トークンの入力が必要です")
        print("💡 ヒント: Next.js側で以下のコードを実行してトークンを取得してください")
        print("   const { data: { session } } = await supabase.auth.getSession();")
        print("   console.log('Access Token:', session?.access_token);")
        print()
        
        test_token = input("Supabase Access Token を入力してください: ").strip()
        
        if not test_token:
            print("❌ トークンが入力されませんでした。テストを終了します。")
            await mcp_client.__aexit__(None, None, None)
            return
        
        print(f"✅ トークンを受け取りました（長さ: {len(test_token)}文字）")
        
        # 1. 在庫追加テスト
        print("\n📦 在庫追加テスト...")
        try:
            add_result = await mcp_client.call_tool(
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
            if add_result and hasattr(add_result, 'data') and add_result.data:
                result_data = add_result.data
                if result_data.get("success"):
                    print("✅ 在庫追加成功")
                    item_id = result_data["data"]["id"]
                    
                    # 2. 在庫一覧取得テスト
                    print("\n📋 在庫一覧取得テスト...")
                    list_result = await mcp_client.call_tool(
                        "inventory_list",
                        arguments={"token": test_token}
                    )
                    print(f"在庫一覧結果: {list_result}")
                    
                    if list_result and hasattr(list_result, 'data') and list_result.data:
                        list_data = list_result.data
                        if list_data.get("success"):
                            print(f"✅ 在庫一覧取得成功: {len(list_data['data'])}件")
                            
                            # 3. 在庫取得テスト
                            print("\n🔍 在庫取得テスト...")
                            get_result = await mcp_client.call_tool(
                                "inventory_get",
                                arguments={
                                    "token": test_token,
                                    "item_id": item_id
                                }
                            )
                            print(f"在庫取得結果: {get_result}")
                            
                            if get_result and hasattr(get_result, 'data') and get_result.data:
                                get_data = get_result.data
                                if get_data.get("success"):
                                    print("✅ 在庫取得成功")
                                    
                                    # 4. 在庫更新テスト
                                    print("\n✏️ 在庫更新テスト...")
                                    update_result = await mcp_client.call_tool(
                                        "inventory_update",
                                        arguments={
                                            "token": test_token,
                                            "item_id": item_id,
                                            "quantity": 5.0,
                                            "storage_location": "冷凍庫"
                                        }
                                    )
                                    print(f"在庫更新結果: {update_result}")
                                    
                                    if update_result and hasattr(update_result, 'data') and update_result.data:
                                        update_data = update_result.data
                                        if update_data.get("success"):
                                            print("✅ 在庫更新成功")
                                            
                                            # 5. 在庫削除テスト
                                            print("\n🗑️ 在庫削除テスト...")
                                            delete_result = await mcp_client.call_tool(
                                                "inventory_delete",
                                                arguments={
                                                    "token": test_token,
                                                    "item_id": item_id
                                                }
                                            )
                                            print(f"在庫削除結果: {delete_result}")
                                            
                                            if delete_result and hasattr(delete_result, 'data') and delete_result.data:
                                                delete_data = delete_result.data
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
        
        # クライアントのクリーンアップ
        await mcp_client.__aexit__(None, None, None)
                
    except Exception as e:
        print(f"❌ テスト実行エラー: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Supabase MCP Server 2 (Annotation-based) テスト開始")
    print("⚠️  注意: テスト前に.envファイルでSupabase認証情報を設定してください")
    print("⚠️  注意: python supabase_mcp_server2.py を別ターミナルで起動してください")
    print("⚠️  注意: テスト実行時にSupabaseトークンの入力が求められます")
    print()
    
    asyncio.run(test_annotation_mcp_server())
