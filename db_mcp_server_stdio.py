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
    
    🎯 使用場面: 「入れる」「追加」「保管」等のキーワードでユーザーが新たに在庫を作成する場合
    
    ⚠️ 重要: item_idは自動採番されるため、パラメータには不要です。
    データベース側でUUIDが自動生成されます。
    
    📋 JSON形式:
    {{
        "description": "アイテムを在庫に追加する",
        "tool": "inventory_add",
        "parameters": {{
            "item_name": "アイテム名",
            "quantity": 数量,
            "unit": "単位",
            "storage_location": "保管場所",
            "expiry_date": "消費期限（オプション）"
        }},
        "priority": 1,
        "dependencies": []
    }}
    
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
async def inventory_update_by_id(
    token: str,
    item_name: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    storage_location: Optional[str] = None,
    expiry_date: Optional[str] = None,
    item_id: Optional[str] = None
) -> Dict[str, Any]:
    """ID指定での在庫アイテム1件更新
    
    個別在庫法に従い、1つのアイテムを1件として更新します。
    複数のアイテムを更新する場合は、このツールを複数回呼び出してください。
    
    🎯 使用場面: 「変更」「変える」「替える」「かえる」「更新」「クリア」等のキーワードでユーザーが在庫を更新する場合
    
    ⚠️ 重要: item_idは**必須です**。必ず在庫情報のitem_idを確認して、設定してください。
    item_idを指定しない場合は、inventory_update_by_nameを利用して名前でまとめて更新してください。
    
    📋 JSON形式:
    {{
        "description": "アイテムを更新する",
        "tool": "inventory_update_by_id",
        "parameters": {{
            "item_id": "対象のID（必須）",
            "item_name": "アイテム名",
            "quantity": 数量,
            "unit": "単位",
            "storage_location": "保管場所",
            "expiry_date": "消費期限"
        }},
        "priority": 1,
        "dependencies": []
    }}
    
    Args:
        token: 認証トークン
        item_name: アイテム名（必須）
        quantity: 数量（オプション）
        unit: 単位（オプション）
        storage_location: 保管場所（オプション）
        expiry_date: 消費期限（オプション）
        item_id: アイテムID（必須）
    
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
async def inventory_delete_by_id(token: str, item_id: str) -> Dict[str, Any]:
    """ID指定での在庫アイテム1件削除
    
    個別在庫法に従い、1つのアイテムを1件として削除します。
    複数のアイテムを削除する場合は、このツールを複数回呼び出してください。
    
    🎯 使用場面: 「削除」「消す」「捨てる」「処分」等のキーワードでユーザーが特定のアイテムを削除する場合
    
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

@mcp.tool()
async def inventory_delete_by_name(token: str, item_name: str) -> Dict[str, Any]:
    """名前指定での在庫アイテム一括削除
    
    指定された名前のアイテムを全て削除します。
    例: "牛乳"を指定すると、牛乳の全アイテムが削除されます。
    
    Args:
        token: 認証トークン
        item_name: アイテム名（必須）
    
    Returns:
        削除結果のメッセージと削除件数
    """
    try:
        user_id = db_client.authenticate(token)
        
        # まず削除対象のアイテム数を確認
        count_result = db_client.get_client().table("inventory").select("id", count="exact").eq("item_name", item_name).eq("user_id", user_id).execute()
        if not count_result.data:
            return {"success": False, "error": f"'{item_name}'が見つかりません"}
        
        # 削除実行
        result = db_client.get_client().table("inventory").delete().eq("item_name", item_name).eq("user_id", user_id).execute()
        
        if result.data is not None:
            deleted_count = len(result.data) if result.data else 0
            return {"success": True, "message": f"'{item_name}'を{deleted_count}件削除しました"}
        else:
            return {"success": False, "error": result.error.message if result.error else "Unknown error"}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"データベース操作エラー: {str(e)}"}

@mcp.tool()
async def inventory_update_by_name(
    token: str,
    item_name: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    storage_location: Optional[str] = None,
    expiry_date: Optional[str] = None
) -> Dict[str, Any]:
    """名前指定での在庫アイテム一括更新
    
    指定された名前のアイテムを全て更新します。
    例: "パン"の賞味期限を全てnullにする場合など。
    
    🎯 使用場面: 「全部」「一括」「全て」等のキーワードで複数のアイテムを同時に更新する場合
    
    ⚠️ 重要: quantityパラメータは更新する値です。
    更新対象件数ではありません。件数を指定する必要はありません。
    例: パンの賞味期限をクリアする場合、quantityは指定不要。
    
    Args:
        token: 認証トークン
        item_name: アイテム名（必須）
        quantity: 更新後の数量（オプション、件数ではない）
        unit: 単位（オプション）
        storage_location: 保管場所（オプション）
        expiry_date: 消費期限（オプション、nullを指定する場合は空文字を渡す）
    
    Returns:
        更新結果のメッセージと更新件数
    """
    try:
        user_id = db_client.authenticate(token)
        
        update_data = {}
        if quantity is not None: update_data["quantity"] = quantity
        if unit: update_data["unit"] = unit
        if storage_location: update_data["storage_location"] = storage_location
        if expiry_date is not None: 
            update_data["expiry_date"] = expiry_date if expiry_date else None

        if not update_data:
            return {"success": False, "error": "更新するデータがありません"}

        # まず更新対象のアイテム数を確認
        count_result = db_client.get_client().table("inventory").select("id", count="exact").eq("item_name", item_name).eq("user_id", user_id).execute()
        if not count_result.data:
            return {"success": False, "error": f"'{item_name}'が見つかりません"}

        # 更新実行
        result = db_client.get_client().table("inventory").update(update_data).eq("item_name", item_name).eq("user_id", user_id).execute()
        
        if result.data is not None:
            updated_count = len(result.data) if result.data else 0
            return {"success": True, "message": f"'{item_name}'を{updated_count}件更新しました", "data": result.data}
        else:
            return {"success": False, "error": result.error.message if result.error else "Unknown error"}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"データベース操作エラー: {str(e)}"}


@mcp.tool()
async def inventory_update_by_name_oldest(
    token: str,
    item_name: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    storage_location: Optional[str] = None,
    expiry_date: Optional[str] = None
) -> Dict[str, Any]:
    """名前指定での最古アイテム更新（FIFO原則）
    
    このツールは、指定された名前のアイテムの中で最も古いもの（created_atが最も古い）を更新します。
    FIFO（First In, First Out）原則に従い、デフォルトで最古のアイテムを対象とします。
    
    🎯 使用場面: 
    - 「牛乳の数量を3本に変更して」→ 最古の牛乳を更新
    - 「パンの賞味期限を来週に変更して」→ 最古のパンを更新
    - 明示的な指定がない場合のデフォルト動作
    
    ⚠️ 重要: 同名アイテムが複数ある場合、最も古いもの（created_atが最も古い）のみが更新されます。
    
    Args:
        token: 認証トークン
        item_name: 更新対象のアイテム名（必須）
        quantity: 新しい数量（オプション）
        unit: 新しい単位（オプション）
        storage_location: 新しい保管場所（オプション）
        expiry_date: 新しい賞味期限（オプション、YYYY-MM-DD形式）
    
    Returns:
        更新されたアイテムの情報
    """
    try:
        user_id = db_client.authenticate(token)
        
        update_data = {}
        if quantity is not None: update_data["quantity"] = quantity
        if unit: update_data["unit"] = unit
        if storage_location: update_data["storage_location"] = storage_location
        if expiry_date is not None: 
            update_data["expiry_date"] = expiry_date if expiry_date else None

        if not update_data:
            return {"success": False, "error": "更新するデータがありません"}

        # 最古のアイテムを取得（created_at ASC）
        oldest_item = db_client.get_client().table("inventory").select("id").eq("item_name", item_name).eq("user_id", user_id).order("created_at", desc=False).limit(1).execute()
        
        if not oldest_item.data:
            return {"success": False, "error": f"'{item_name}'が見つかりません"}

        item_id = oldest_item.data[0]["id"]

        # 更新実行
        result = db_client.get_client().table("inventory").update(update_data).eq("id", item_id).eq("user_id", user_id).execute()
        
        if result.data:
            return {"success": True, "message": f"'{item_name}'の最古アイテムを更新しました", "data": result.data[0]}
        else:
            return {"success": False, "error": result.error.message if result.error else "Unknown error"}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"データベース操作エラー: {str(e)}"}


@mcp.tool()
async def inventory_update_by_name_latest(
    token: str,
    item_name: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    storage_location: Optional[str] = None,
    expiry_date: Optional[str] = None
) -> Dict[str, Any]:
    """名前指定での最新アイテム更新（ユーザー指定）
    
    このツールは、指定された名前のアイテムの中で最も新しいもの（created_atが最も新しい）を更新します。
    ユーザーが「最新の」「新しい方の」と明示的に指定した場合に使用されます。
    
    🎯 使用場面:
    - 「最新の牛乳の本数を3本に変えて」→ 最新の牛乳を更新
    - 「新しい方のパンの賞味期限を来週に変更して」→ 最新のパンを更新
    - ユーザーが明示的に「最新」を指定した場合
    
    ⚠️ 重要: 同名アイテムが複数ある場合、最も新しいもの（created_atが最も新しい）のみが更新されます。
    
    Args:
        token: 認証トークン
        item_name: 更新対象のアイテム名（必須）
        quantity: 新しい数量（オプション）
        unit: 新しい単位（オプション）
        storage_location: 新しい保管場所（オプション）
        expiry_date: 新しい賞味期限（オプション、YYYY-MM-DD形式）
    
    Returns:
        更新されたアイテムの情報
    """
    try:
        user_id = db_client.authenticate(token)
        
        update_data = {}
        if quantity is not None: update_data["quantity"] = quantity
        if unit: update_data["unit"] = unit
        if storage_location: update_data["storage_location"] = storage_location
        if expiry_date is not None: 
            update_data["expiry_date"] = expiry_date if expiry_date else None

        if not update_data:
            return {"success": False, "error": "更新するデータがありません"}

        # 最新のアイテムを取得（created_at DESC）
        latest_item = db_client.get_client().table("inventory").select("id").eq("item_name", item_name).eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
        
        if not latest_item.data:
            return {"success": False, "error": f"'{item_name}'が見つかりません"}

        item_id = latest_item.data[0]["id"]

        # 更新実行
        result = db_client.get_client().table("inventory").update(update_data).eq("id", item_id).eq("user_id", user_id).execute()
        
        if result.data:
            return {"success": True, "message": f"'{item_name}'の最新アイテムを更新しました", "data": result.data[0]}
        else:
            return {"success": False, "error": result.error.message if result.error else "Unknown error"}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"データベース操作エラー: {str(e)}"}

@mcp.tool()
async def inventory_delete_by_name_oldest(
    token: str,
    item_name: str
) -> Dict[str, Any]:
    """名前指定での最古アイテム削除（FIFO原則）
    
    このツールは、指定された名前のアイテムの中で最も古いもの（created_atが最も古い）を削除します。
    FIFO（First In, First Out）原則に従い、デフォルトで最古のアイテムを対象とします。
    
    🎯 使用場面:
    - 「牛乳の古い方を削除して」→ 最古の牛乳を削除
    - 「古いパンを処分して」→ 最古のパンを削除
    - デフォルトでFIFO原則に従った削除
    
    Args:
        token: 認証トークン
        item_name: アイテム名（必須）
    
    Returns:
        削除結果のメッセージと削除されたアイテムの情報
    """
    try:
        user_id = db_client.authenticate(token)
        
        # 最古のアイテムを取得（created_at ASC）
        oldest_item = db_client.get_client().table("inventory").select("*").eq("item_name", item_name).eq("user_id", user_id).order("created_at", desc=False).limit(1).execute()
        
        if not oldest_item.data:
            return {"success": False, "error": f"'{item_name}'が見つかりません"}
        
        item_id = oldest_item.data[0]["id"]
        
        # 削除実行
        result = db_client.get_client().table("inventory").delete().eq("id", item_id).eq("user_id", user_id).execute()
        
        if result.data:
            return {"success": True, "message": f"'{item_name}'の最古アイテムを削除しました", "data": result.data[0]}
        else:
            return {"success": False, "error": result.error.message if result.error else "Unknown error"}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"データベース操作エラー: {str(e)}"}


@mcp.tool()
async def inventory_delete_by_name_latest(
    token: str,
    item_name: str
) -> Dict[str, Any]:
    """名前指定での最新アイテム削除（ユーザー指定）
    
    このツールは、指定された名前のアイテムの中で最も新しいもの（created_atが最も新しい）を削除します。
    ユーザーが「最新の」「新しい方の」と明示的に指定した場合に使用されます。
    
    🎯 使用場面:
    - 「最新の牛乳を削除して」→ 最新の牛乳を削除
    - 「新しい方のパンを処分して」→ 最新のパンを削除
    - ユーザーが明示的に「最新」を指定した場合
    
    Args:
        token: 認証トークン
        item_name: アイテム名（必須）
    
    Returns:
        削除結果のメッセージと削除されたアイテムの情報
    """
    try:
        user_id = db_client.authenticate(token)
        
        # 最新のアイテムを取得（created_at DESC）
        latest_item = db_client.get_client().table("inventory").select("*").eq("item_name", item_name).eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
        
        if not latest_item.data:
            return {"success": False, "error": f"'{item_name}'が見つかりません"}
        
        item_id = latest_item.data[0]["id"]
        
        # 削除実行
        result = db_client.get_client().table("inventory").delete().eq("id", item_id).eq("user_id", user_id).execute()
        
        if result.data:
            return {"success": True, "message": f"'{item_name}'の最新アイテムを削除しました", "data": result.data[0]}
        else:
            return {"success": False, "error": result.error.message if result.error else "Unknown error"}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"データベース操作エラー: {str(e)}"}


if __name__ == "__main__":
    print("🚀 Database MCP Server (stdio transport) starting...")
    print("📡 Available tools: inventory_add, inventory_list, inventory_get, inventory_update_by_id, inventory_delete_by_id, inventory_delete_by_name, inventory_update_by_name, inventory_update_by_name_oldest, inventory_update_by_name_latest, inventory_delete_by_name_oldest, inventory_delete_by_name_latest")
    print("🔗 Transport: stdio")
    print("Press Ctrl+C to stop the server")
    
    # stdioトランスポートで起動
    mcp.run(transport="stdio")
