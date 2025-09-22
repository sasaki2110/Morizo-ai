#!/usr/bin/env python3
"""
Supabase MCP Server (stdio transport)
アノテーション方式のMCPサーバーをstdio接続に移行
"""

import os
import json
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
from fastmcp import FastMCP
from pydantic import BaseModel
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# MCPサーバーの初期化
mcp = FastMCP("Supabase CRUD Server")

class SupabaseClient:
    """Supabaseクライアントのラッパークラス"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        self._client: Optional[Client] = None

    def get_client(self) -> Client:
        if self._client is None:
            self._client = create_client(self.supabase_url, self.supabase_key)
        return self._client

    def authenticate(self, token: str) -> str:
        """認証トークンを検証し、ユーザーIDを返す"""
        try:
            supabase = self.get_client()
            user_response = supabase.auth.get_user(token)
            if user_response.user is None:
                raise ValueError("Invalid authentication token")
            
            # PostgRESTクライアントに認証トークンを設定
            supabase.postgrest.auth(token)
            return user_response.user.id
        except Exception as e:
            raise ValueError(f"認証エラー: {str(e)}")

# グローバルクライアントインスタンス
supabase_client = SupabaseClient()

# Pydanticモデル定義
class InventoryItem(BaseModel):
    item_name: str
    quantity: float
    unit: str = "個"
    storage_location: str = "冷蔵庫"
    expiry_date: Optional[str] = None

class InventoryUpdate(BaseModel):
    item_name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    storage_location: Optional[str] = None
    expiry_date: Optional[str] = None

# MCPツール定義（アノテーション方式）
@mcp.tool()
async def inventory_add(
    token: str,
    item_name: str,
    quantity: float,
    unit: str = "個",
    storage_location: str = "冷蔵庫",
    expiry_date: Optional[str] = None
) -> Dict[str, Any]:
    """在庫にアイテムを追加
    
    Args:
        token: Supabase認証トークン
        item_name: アイテム名
        quantity: 数量
        unit: 単位（デフォルト: 個）
        storage_location: 保管場所（デフォルト: 冷蔵庫）
        expiry_date: 消費期限（オプション）
    
    Returns:
        追加されたアイテムの情報
    """
    try:
        user_id = supabase_client.authenticate(token)
        
        item_data = {
            "user_id": user_id,
            "item_name": item_name,
            "quantity": quantity,
            "unit": unit,
            "storage_location": storage_location
        }
        if expiry_date:
            item_data["expiry_date"] = expiry_date

        result = supabase_client.get_client().table("inventory").insert(item_data).execute()
        if result.data:
            return {"success": True, "data": result.data[0]}
        else:
            return {"success": False, "error": result.error.message if result.error else "Unknown error"}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"データベース操作エラー: {str(e)}"}

@mcp.tool()
async def inventory_list(token: str) -> Dict[str, Any]:
    """在庫一覧を取得
    
    Args:
        token: Supabase認証トークン
    
    Returns:
        在庫一覧のデータ
    """
    try:
        user_id = supabase_client.authenticate(token)
        result = supabase_client.get_client().table("inventory").select("*").eq("user_id", user_id).execute()
        if result.data:
            return {"success": True, "data": result.data}
        else:
            return {"success": False, "error": result.error.message if result.error else "Unknown error"}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"データベース操作エラー: {str(e)}"}

@mcp.tool()
async def inventory_get(token: str, item_id: str) -> Dict[str, Any]:
    """特定の在庫アイテムを取得
    
    Args:
        token: Supabase認証トークン
        item_id: アイテムID
    
    Returns:
        指定されたアイテムの情報
    """
    try:
        user_id = supabase_client.authenticate(token)
        result = supabase_client.get_client().table("inventory").select("*").eq("id", item_id).eq("user_id", user_id).execute()
        if result.data:
            return {"success": True, "data": result.data[0]}
        else:
            return {"success": False, "error": "Item not found or not authorized"}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"データベース操作エラー: {str(e)}"}

@mcp.tool()
async def inventory_update(
    token: str,
    item_id: str,
    item_name: Optional[str] = None,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    storage_location: Optional[str] = None,
    expiry_date: Optional[str] = None
) -> Dict[str, Any]:
    """在庫アイテムを更新
    
    Args:
        token: Supabase認証トークン
        item_id: アイテムID
        item_name: アイテム名（オプション）
        quantity: 数量（オプション）
        unit: 単位（オプション）
        storage_location: 保管場所（オプション）
        expiry_date: 消費期限（オプション）
    
    Returns:
        更新されたアイテムの情報
    """
    try:
        user_id = supabase_client.authenticate(token)
        
        update_data = {}
        if item_name: update_data["item_name"] = item_name
        if quantity is not None: update_data["quantity"] = quantity
        if unit: update_data["unit"] = unit
        if storage_location: update_data["storage_location"] = storage_location
        if expiry_date: update_data["expiry_date"] = expiry_date

        if not update_data:
            return {"success": False, "error": "更新するデータがありません"}

        result = supabase_client.get_client().table("inventory").update(update_data).eq("id", item_id).eq("user_id", user_id).execute()
        if result.data:
            return {"success": True, "data": result.data[0]}
        else:
            return {"success": False, "error": result.error.message if result.error else "Unknown error"}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"データベース操作エラー: {str(e)}"}

@mcp.tool()
async def inventory_delete(token: str, item_id: str) -> Dict[str, Any]:
    """在庫アイテムを削除
    
    Args:
        token: Supabase認証トークン
        item_id: アイテムID
    
    Returns:
        削除結果のメッセージ
    """
    try:
        user_id = supabase_client.authenticate(token)
        result = supabase_client.get_client().table("inventory").delete().eq("id", item_id).eq("user_id", user_id).execute()
        if result.data:
            return {"success": True, "message": "Item deleted successfully"}
        else:
            return {"success": False, "error": result.error.message if result.error else "Unknown error"}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"データベース操作エラー: {str(e)}"}

if __name__ == "__main__":
    print("🚀 Supabase MCP Server (stdio transport) starting...")
    print("📡 Available tools: inventory_add, inventory_list, inventory_get, inventory_update, inventory_delete")
    print("🔗 Transport: stdio")
    print("Press Ctrl+C to stop the server")
    
    # stdioトランスポートで起動
    mcp.run(transport="stdio")
