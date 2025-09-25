#!/usr/bin/env python3
"""
FastMCPクライアントの実装確認テスト
mcp_client.pyのFastMCP化が可能かテストする
"""

import asyncio
import json
import logging
from fastmcp import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_fastmcp_client")

async def test_fastmcp_client():
    """FastMCPクライアントの動作確認"""
    try:
        print("🔧 FastMCPクライアントテスト開始")
        print("=" * 50)
        
        # FastMCPサーバーに接続
        # db_mcp_server_stdio.pyをFastMCPサーバーとして起動
        client = Client("db_mcp_server_stdio.py")
        
        async with client:
            print("✅ FastMCPクライアント接続成功")
            
            # ツールリストを取得
            print("\n📋 ツールリスト取得テスト:")
            tools = await client.list_tools()
            print(f"📊 ツール数: {len(tools)}")
            
            for i, tool in enumerate(tools):
                print(f"🔧 ツール {i+1}: {tool.name}")
                print(f"   📝 説明: {tool.description[:100]}...")
            
            # ツール詳細情報の取得テスト
            print("\n📋 ツール詳細情報取得テスト:")
            tool_details = {}
            for tool in tools:
                tool_details[tool.name] = {
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                    "name": tool.name
                }
            
            print(f"📊 ツール詳細情報: {len(tool_details)}件")
            for tool_name, details in tool_details.items():
                print(f"🔧 {tool_name}: {len(details['description'])}文字の説明")
            
            # 実際のツール呼び出しテスト
            print("\n📋 ツール呼び出しテスト:")
            try:
                # inventory_listツールを呼び出し
                result = await client.call_tool("inventory_list", {"token": "test-token"})
                print(f"✅ inventory_list呼び出し成功: {type(result)}")
            except Exception as e:
                print(f"⚠️ inventory_list呼び出しエラー: {str(e)}")
            
        print("\n✅ FastMCPクライアントテスト完了")
        
    except Exception as e:
        logger.error(f"❌ FastMCPクライアントテストエラー: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fastmcp_client())
