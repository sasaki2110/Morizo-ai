"""
MCPクライアントとツール管理（FastMCP版）
"""

import json
import logging
from typing import Dict, Any, List, Optional
from fastmcp import Client

logger = logging.getLogger('morizo_ai.mcp')


class MCPClient:
    """FastMCPクライアントのラッパークラス"""
    
    def __init__(self):
        self.client = Client("db_mcp_server_stdio.py")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """MCPツールを呼び出し"""
        try:
            async with self.client:
                result = await self.client.call_tool(tool_name, arguments=arguments)
                
                if result and hasattr(result, 'content') and result.content:
                    return json.loads(result.content[0].text)
                else:
                    return {"success": False, "error": "No result from MCP tool"}
        except Exception as e:
            return {"success": False, "error": f"MCP tool error: {str(e)}"}
    
    async def get_tool_details(self) -> Dict[str, Dict[str, Any]]:
        """MCPからツール詳細情報を動的に取得"""
        try:
            async with self.client:
                tools = await self.client.list_tools()
                tool_details = {}
                
                for tool in tools:
                    tool_details[tool.name] = {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    }
                
                logger.info(f"🔧 [FastMCP] {len(tool_details)}個のツール詳細情報を取得")
                return tool_details
                
        except Exception as e:
            logger.error(f"❌ [FastMCP] ツール詳細情報取得エラー: {str(e)}")
            return {}


async def get_available_tools_from_mcp() -> List[str]:
    """
    MCPから利用可能なツール一覧を取得する（FastMCP版）
    
    Returns:
        利用可能なツール一覧
    """
    try:
        client = Client("db_mcp_server_stdio.py")
        available_tools = []
        
        async with client:
            tools = await client.list_tools()
            
            for tool in tools:
                available_tools.append(tool.name)
            
            logger.info(f"🔧 [FastMCP] 利用可能なツール: {available_tools}")
        
        return available_tools
        
    except Exception as e:
        logger.error(f"❌ [FastMCP] ツール一覧取得エラー: {str(e)}")
        # フォールバック
        return ["inventory_add", "inventory_list", "inventory_get", "inventory_update_by_id", "inventory_delete_by_id", "inventory_update_by_name", "inventory_delete_by_name", "inventory_update_by_name_oldest", "inventory_update_by_name_latest"]
