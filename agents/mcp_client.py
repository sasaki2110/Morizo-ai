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
    
    def __init__(self, server_type: str = "db"):
        """
        MCPクライアントの初期化
        
        Args:
            server_type: "db" (データベースMCP) または "recipe" (レシピMCP)
        """
        if server_type == "db":
            self.client = Client("db_mcp_server_stdio.py")
        elif server_type == "recipe":
            self.client = Client("recipe_mcp_server_stdio.py")
        else:
            raise ValueError(f"Unknown server type: {server_type}")
        
        self.server_type = server_type
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """MCPツールを呼び出し"""
        try:
            # テスト用の認証バイパス
            if arguments.get("token") == "dummy-token":
                # テスト用の場合は実際のSupabaseキーを使用
                import os
                supabase_key = os.getenv("SUPABASE_KEY")
                if supabase_key:
                    arguments["token"] = supabase_key
                    logger.info("🔧 [MCP] テスト用認証バイパス: 実際のSupabaseキーを使用")
            
            async with self.client:
                result = await self.client.call_tool(tool_name, arguments=arguments)
                
                if result and hasattr(result, 'content') and result.content:
                    return json.loads(result.content[0].text)
                else:
                    return {"success": False, "error": "No result from MCP tool"}
        except Exception as e:
            logger.error(f"❌ [MCP] ツール呼び出しエラー: {str(e)}")
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
        all_tools = []
        
        # DB MCPサーバーからツールを取得
        try:
            db_client = Client("db_mcp_server_stdio.py")
            async with db_client:
                tools = await db_client.list_tools()
                for tool in tools:
                    all_tools.append(tool.name)
            logger.info(f"🔧 [FastMCP] DB MCPツール: {len(tools)}個")
        except Exception as e:
            logger.warning(f"⚠️ [FastMCP] DB MCPツール取得エラー: {str(e)}")
        
        # レシピMCPサーバーからツールを取得
        try:
            recipe_client = Client("recipe_mcp_server_stdio.py")
            async with recipe_client:
                tools = await recipe_client.list_tools()
                for tool in tools:
                    all_tools.append(tool.name)
            logger.info(f"🔧 [FastMCP] Recipe MCPツール: {len(tools)}個")
        except Exception as e:
            logger.warning(f"⚠️ [FastMCP] Recipe MCPツール取得エラー: {str(e)}")
        
        logger.info(f"🔧 [FastMCP] 総利用可能ツール: {all_tools}")
        return all_tools
        
    except Exception as e:
        logger.error(f"❌ [FastMCP] ツール一覧取得エラー: {str(e)}")
        # フォールバック
        return ["inventory_add", "inventory_list", "inventory_get", "inventory_update_by_id", "inventory_delete_by_id", "inventory_update_by_name", "inventory_delete_by_name", "inventory_update_by_name_oldest", "inventory_update_by_name_latest", "generate_menu_plan_with_history"]


async def call_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    適切なMCPサーバーでツールを呼び出し
    
    Args:
        tool_name: 呼び出すツール名
        arguments: ツールの引数
    
    Returns:
        ツールの実行結果
    """
    try:
        # ツール名から適切なMCPサーバーを判定
        if tool_name.startswith("inventory_") or tool_name.startswith("recipes_"):
            server_type = "db"
        elif tool_name.startswith("generate_menu_") or tool_name.startswith("search_recipe_") or tool_name.startswith("search_menu_"):
            server_type = "recipe"
        else:
            # デフォルトはDB MCP
            server_type = "db"
        
        logger.info(f"🔧 [FastMCP] ツール {tool_name} を {server_type} MCPで実行")
        
        client = MCPClient(server_type)
        result = await client.call_tool(tool_name, arguments)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ [FastMCP] ツール呼び出しエラー: {str(e)}")
        return {"success": False, "error": f"MCP tool error: {str(e)}"}
