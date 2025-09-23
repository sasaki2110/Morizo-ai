"""
MCPクライアントとツール管理
"""

import json
import logging
from typing import Dict, Any, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger('morizo_ai.mcp')


class MCPClient:
    """MCPクライアントのラッパークラス"""
    
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="python",
            args=["db_mcp_server_stdio.py"]
        )
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """MCPツールを呼び出し"""
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as mcp_session:
                    await mcp_session.initialize()
                    result = await mcp_session.call_tool(tool_name, arguments=arguments)
                    
                    if result and hasattr(result, 'content') and result.content:
                        return json.loads(result.content[0].text)
                    else:
                        return {"success": False, "error": "No result from MCP tool"}
        except Exception as e:
            return {"success": False, "error": f"MCP tool error: {str(e)}"}


async def get_available_tools_from_mcp() -> List[str]:
    """
    MCPから利用可能なツール一覧を取得する
    
    Returns:
        利用可能なツール一覧
    """
    try:
        available_tools = []
        server_params = StdioServerParameters(
            command="python",
            args=["db_mcp_server_stdio.py"]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as mcp_session:
                await mcp_session.initialize()
                
                # ツールリストを取得
                tools_response = await mcp_session.list_tools()
                
                if tools_response and hasattr(tools_response, 'tools'):
                    for tool in tools_response.tools:
                        available_tools.append(tool.name)
                    logger.info(f"🔧 [MCP] 利用可能なツール: {available_tools}")
                else:
                    logger.warning("⚠️ [MCP] ツールリストの取得に失敗、フォールバックを使用")
                    available_tools = ["inventory_add", "inventory_list", "inventory_get", "inventory_update", "inventory_delete", "llm_chat"]
        
        return available_tools
        
    except Exception as e:
        logger.error(f"❌ [MCP] ツール一覧取得エラー: {str(e)}")
        # フォールバック
        return ["inventory_add", "inventory_list", "inventory_get", "inventory_update", "inventory_delete", "llm_chat"]
