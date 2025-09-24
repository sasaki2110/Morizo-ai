#!/usr/bin/env python3
"""
Morizo AI - Database MCP Server
Copyright (c) 2024 Morizo AI Project. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, modification,
distribution, or use is strictly prohibited without explicit written permission.

For licensing inquiries, contact: [contact@morizo-ai.com]

Database MCP Server (stdio transport)
DB操作用のMCPサーバー（アノテーション方式、stdio接続）
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

# FastMCPロゴを非表示にする（環境変数で制御）
os.environ["FASTMCP_DISABLE_BANNER"] = "1"

# MCPサーバーの初期化
mcp = FastMCP("Database CRUD Server")

class DatabaseClient:
    """データベースクライアントのラッパークラス"""
    
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
db_client = DatabaseClient()

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
    """在庫にアイテムを1件追加
    
    個別在庫法に従い、1つのアイテムを1件として登録します。
    複数のアイテムを追加する場合は、このツールを複数回呼び出してください。
    
    Args:
        token: 認証トークン
        item_name: アイテム名
        quantity: 数量
        unit: 単位（デフォルト: 個）
        storage_location: 保管場所（デフォルト: 冷蔵庫）
        expiry_date: 消費期限（オプション）
    
    Returns:
        追加されたアイテムの情報
    """
    try:
        user_id = db_client.authenticate(token)
        
        item_data = {
            "user_id": user_id,
            "item_name": item_name,
            "quantity": quantity,
            "unit": unit,
            "storage_location": storage_location
        }
        if expiry_date:
            item_data["expiry_date"] = expiry_date

        result = db_client.get_client().table("inventory").insert(item_data).execute()
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
    
    ユーザーの全在庫アイテムを取得します。
    個別在庫法に従い、各アイテムが個別に表示されます。
    
    Args:
        token: 認証トークン
    
    Returns:
        在庫一覧のデータ
    """
    try:
        user_id = db_client.authenticate(token)
        result = db_client.get_client().table("inventory").select("*").eq("user_id", user_id).execute()
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
    """特定の在庫アイテムを1件取得
    
    個別在庫法に従い、指定されたIDのアイテムを1件取得します。
    
    Args:
        token: 認証トークン
        item_id: アイテムID
    
    Returns:
        指定されたアイテムの情報
    """
    try:
        user_id = db_client.authenticate(token)
        result = db_client.get_client().table("inventory").select("*").eq("id", item_id).eq("user_id", user_id).execute()
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
    item_name: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    storage_location: Optional[str] = None,
    expiry_date: Optional[str] = None,
    item_id: Optional[str] = None
) -> Dict[str, Any]:
    """在庫アイテムを1件更新
    
    個別在庫法に従い、1つのアイテムを1件として更新します。
    複数のアイテムを更新する場合は、このツールを複数回呼び出してください。
    
    ⚠️ 重要: item_idパラメータの指定を強く推奨します。
    item_idを指定しない場合は、item_nameで最新のアイテムを更新しますが、
    意図しないアイテムが更新される可能性があります。
    
    Args:
        token: 認証トークン
        item_name: アイテム名（必須）
        quantity: 数量（オプション）
        unit: 単位（オプション）
        storage_location: 保管場所（オプション）
        expiry_date: 消費期限（オプション）
        item_id: アイテムID（推奨、指定しない場合は最新のアイテムを更新）
    
    Returns:
        更新されたアイテムの情報
    """
    try:
        user_id = db_client.authenticate(token)
        
        update_data = {}
        if item_name: update_data["item_name"] = item_name
        if quantity is not None: update_data["quantity"] = quantity
        if unit: update_data["unit"] = unit
        if storage_location: update_data["storage_location"] = storage_location
        if expiry_date: update_data["expiry_date"] = expiry_date

        if not update_data:
            return {"success": False, "error": "更新するデータがありません"}

        # item_idが指定されていない場合は、item_nameで最新のアイテムを取得
        if not item_id:
            # 同じitem_nameの最新のアイテムを取得
            existing_items = db_client.get_client().table("inventory").select("id").eq("item_name", item_name).eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
            if not existing_items.data:
                return {"success": False, "error": f"'{item_name}'が見つかりません"}
            item_id = existing_items.data[0]["id"]

        result = db_client.get_client().table("inventory").update(update_data).eq("id", item_id).eq("user_id", user_id).execute()
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
    """在庫アイテムを1件削除
    
    個別在庫法に従い、1つのアイテムを1件として削除します。
    複数のアイテムを削除する場合は、このツールを複数回呼び出してください。
    
    ⚠️ 重要: item_idパラメータは必須です。
    削除対象を特定するために、必ずitem_idを指定してください。
    
    Args:
        token: 認証トークン
        item_id: アイテムID（必須）
    
    Returns:
        削除結果のメッセージ
    """
    try:
        user_id = db_client.authenticate(token)
        result = db_client.get_client().table("inventory").delete().eq("id", item_id).eq("user_id", user_id).execute()
        if result.data:
            return {"success": True, "message": "Item deleted successfully"}
        else:
            return {"success": False, "error": result.error.message if result.error else "Unknown error"}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"データベース操作エラー: {str(e)}"}

if __name__ == "__main__":
    print("🚀 Database MCP Server (stdio transport) starting...")
    print("📡 Available tools: inventory_add, inventory_list, inventory_get, inventory_update, inventory_delete")
    print("🔗 Transport: stdio")
    print("Press Ctrl+C to stop the server")
    
    # stdioトランスポートで起動
    mcp.run(transport="stdio")
