#!/usr/bin/env python3
"""
Supabase MCP Server
Supabase CRUD操作をMCPツールとして提供
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import BaseModel
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# MCPサーバーの初期化
server = Server("supabase-crud")

class SupabaseClient:
    """Supabaseクライアントのラッパークラス"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase設定が不足しています")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
    
    def authenticate(self, token: str) -> str:
        """認証トークンを検証し、ユーザーIDを返す"""
        try:
            user = self.client.auth.get_user(token)
            if not user.user:
                raise ValueError("認証に失敗しました")
            
            # DB認証を設定
            self.client.postgrest.auth(token)
            
            return user.user.id
        except Exception as e:
            raise ValueError(f"認証エラー: {str(e)}")

# グローバルクライアントインスタンス
supabase_client = SupabaseClient()

# MCPツール定義
@server.list_tools()
async def list_tools() -> List[Tool]:
    """利用可能なツール一覧を返す"""
    return [
        Tool(
            name="inventory_add",
            description="在庫にアイテムを追加",
            inputSchema={
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "認証トークン"},
                    "item_name": {"type": "string", "description": "アイテム名"},
                    "quantity": {"type": "number", "description": "数量"},
                    "unit": {"type": "string", "description": "単位", "default": "個"},
                    "storage_location": {"type": "string", "description": "保管場所", "default": "冷蔵庫"},
                    "expiry_date": {"type": "string", "description": "消費期限", "nullable": True}
                },
                "required": ["token", "item_name", "quantity"]
            }
        ),
        Tool(
            name="inventory_list",
            description="在庫一覧を取得",
            inputSchema={
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "認証トークン"}
                },
                "required": ["token"]
            }
        ),
        Tool(
            name="inventory_get",
            description="特定の在庫アイテムを取得",
            inputSchema={
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "認証トークン"},
                    "item_id": {"type": "string", "description": "アイテムID"}
                },
                "required": ["token", "item_id"]
            }
        ),
        Tool(
            name="inventory_update",
            description="在庫アイテムを更新",
            inputSchema={
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "認証トークン"},
                    "item_id": {"type": "string", "description": "アイテムID"},
                    "quantity": {"type": "number", "description": "数量", "nullable": True},
                    "unit": {"type": "string", "description": "単位", "nullable": True},
                    "storage_location": {"type": "string", "description": "保管場所", "nullable": True},
                    "expiry_date": {"type": "string", "description": "消費期限", "nullable": True}
                },
                "required": ["token", "item_id"]
            }
        ),
        Tool(
            name="inventory_delete",
            description="在庫アイテムを削除",
            inputSchema={
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "認証トークン"},
                    "item_id": {"type": "string", "description": "アイテムID"}
                },
                "required": ["token", "item_id"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """ツール呼び出しのハンドラー"""
    
    if name == "inventory_add":
        result = await inventory_add(**arguments)
    elif name == "inventory_list":
        result = await inventory_list(**arguments)
    elif name == "inventory_get":
        result = await inventory_get(**arguments)
    elif name == "inventory_update":
        result = await inventory_update(**arguments)
    elif name == "inventory_delete":
        result = await inventory_delete(**arguments)
    else:
        result = {"success": False, "message": f"未知のツール: {name}"}
    
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

async def inventory_add(
    token: str,
    item_name: str,
    quantity: float,
    unit: str = "個",
    storage_location: str = "冷蔵庫",
    expiry_date: Optional[str] = None
) -> Dict[str, Any]:
    """在庫にアイテムを追加"""
    try:
        user_id = supabase_client.authenticate(token)
        
        item_data = {
            "user_id": user_id,
            "item_name": item_name,
            "quantity": quantity,
            "unit": unit,
            "storage_location": storage_location,
            "expiry_date": expiry_date
        }
        
        result = supabase_client.client.table("inventory").insert(item_data).execute()
        
        if result.data:
            return {
                "success": True,
                "message": f"{item_name} を {quantity}{unit} 追加しました",
                "data": result.data[0]
            }
        else:
            return {"success": False, "message": "追加に失敗しました"}
            
    except Exception as e:
        return {"success": False, "message": f"エラー: {str(e)}"}

async def inventory_list(token: str) -> Dict[str, Any]:
    """在庫一覧を取得"""
    try:
        user_id = supabase_client.authenticate(token)
        
        result = supabase_client.client.table("inventory").select("*").execute()
        
        return {
            "success": True,
            "message": f"{len(result.data)}件の在庫が見つかりました",
            "data": result.data
        }
        
    except Exception as e:
        return {"success": False, "message": f"エラー: {str(e)}"}

async def inventory_get(token: str, item_id: str) -> Dict[str, Any]:
    """特定の在庫アイテムを取得"""
    try:
        user_id = supabase_client.authenticate(token)
        
        result = supabase_client.client.table("inventory").select("*").eq("id", item_id).execute()
        
        if result.data:
            return {
                "success": True,
                "message": "在庫アイテムを取得しました",
                "data": result.data[0]
            }
        else:
            return {"success": False, "message": "アイテムが見つかりませんでした"}
            
    except Exception as e:
        return {"success": False, "message": f"エラー: {str(e)}"}

async def inventory_update(
    token: str,
    item_id: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    storage_location: Optional[str] = None,
    expiry_date: Optional[str] = None
) -> Dict[str, Any]:
    """在庫アイテムを更新"""
    try:
        user_id = supabase_client.authenticate(token)
        
        update_data = {}
        if quantity is not None:
            update_data["quantity"] = quantity
        if unit is not None:
            update_data["unit"] = unit
        if storage_location is not None:
            update_data["storage_location"] = storage_location
        if expiry_date is not None:
            update_data["expiry_date"] = expiry_date
        
        if not update_data:
            return {"success": False, "message": "更新するデータがありません"}
        
        result = supabase_client.client.table("inventory").update(update_data).eq("id", item_id).execute()
        
        if result.data:
            return {
                "success": True,
                "message": "在庫アイテムを更新しました",
                "data": result.data[0]
            }
        else:
            return {"success": False, "message": "更新に失敗しました"}
            
    except Exception as e:
        return {"success": False, "message": f"エラー: {str(e)}"}

async def inventory_delete(token: str, item_id: str) -> Dict[str, Any]:
    """在庫アイテムを削除"""
    try:
        user_id = supabase_client.authenticate(token)
        
        result = supabase_client.client.table("inventory").delete().eq("id", item_id).execute()
        
        if result.data:
            return {
                "success": True,
                "message": "在庫アイテムを削除しました",
                "data": result.data[0]
            }
        else:
            return {"success": False, "message": "削除に失敗しました"}
            
    except Exception as e:
        return {"success": False, "message": f"エラー: {str(e)}"}

async def main():
    """MCPサーバーを起動"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())