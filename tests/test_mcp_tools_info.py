#!/usr/bin/env python3
"""
MCPツールの詳細情報取得テスト
list_tools()のレスポンス構造を確認する
"""

import asyncio
import json
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_mcp_tools_info")

async def test_mcp_tools_info():
    """MCPツールの詳細情報を取得してテスト"""
    try:
        server_params = StdioServerParameters(
            command="python",
            args=["db_mcp_server_stdio.py"]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as mcp_session:
                await mcp_session.initialize()
                
                # ツールリストを取得
                tools_response = await mcp_session.list_tools()
                
                print("🔧 MCPツール詳細情報:")
                print("=" * 50)
                
                if tools_response and hasattr(tools_response, 'tools'):
                    print(f"📊 ツール数: {len(tools_response.tools)}")
                    print()
                    
                    for i, tool in enumerate(tools_response.tools):
                        print(f"🔧 ツール {i+1}: {tool.name}")
                        print(f"   📝 説明: {tool.description}")
                        print(f"   📋 入力スキーマ: {json.dumps(tool.inputSchema, indent=2, ensure_ascii=False)}")
                        print("-" * 30)
                else:
                    print("❌ ツール情報の取得に失敗")
                
    except Exception as e:
        logger.error(f"❌ エラー: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_tools_info())
