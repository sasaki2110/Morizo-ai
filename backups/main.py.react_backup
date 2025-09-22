from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from supabase import create_client, Client
import os
import json
import asyncio
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 環境変数の読み込み
load_dotenv()

app = FastAPI(title="Morizo AI", description="Smart Pantry AI Agent with MCP Integration")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なドメインに制限
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI API設定
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Supabase設定
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None

# MCPクライアント設定
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
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments=arguments)
                    
                    if result and hasattr(result, 'content') and result.content:
                        return json.loads(result.content[0].text)
                    else:
                        return {"success": False, "error": "No result from MCP tool"}
        except Exception as e:
            return {"success": False, "error": f"MCP tool error: {str(e)}"}

# グローバルMCPクライアントインスタンス
mcp_client = MCPClient()

# サーバー起動時にモデル情報を表示
print(f"🚀 Morizo AI Server starting...")
print(f"📋 Using OpenAI Model: {model_name}")
print(f"🔑 OpenAI API Key configured: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
print(f"🔐 Supabase configured: {'Yes' if supabase else 'No'}")
print(f"🔗 MCP Integration: Enabled")

# 認証設定
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Supabaseトークンを検証し、ユーザー情報を返す
    """
    if not supabase:
        raise HTTPException(
            status_code=500, 
            detail="Supabase not configured"
        )
    
    try:
        # トークンの前処理（角括弧の除去）
        raw_token = credentials.credentials
        if raw_token.startswith('[') and raw_token.endswith(']'):
            raw_token = raw_token[1:-1]
        
        print(f"🔍 [DEBUG] Raw token received: {raw_token[:50]}...")
        print(f"🔍 [DEBUG] Token length: {len(raw_token)}")
        
        # トークンからユーザー情報を取得
        response = supabase.auth.get_user(raw_token)
        
        if response.user is None:
            print(f"❌ [ERROR] User is None in response")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )
        
        print(f"✅ [SUCCESS] User authenticated: {response.user.email}")
        
        # ユーザー情報とトークンを辞書で返す
        return {
            "user": response.user,
            "raw_token": raw_token
        }
    except Exception as e:
        print(f"❌ [ERROR] Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    response: str
    success: bool
    model_used: str
    user_id: Optional[str] = None

class InventoryRequest(BaseModel):
    item_name: str
    quantity: float
    unit: str = "個"
    storage_location: str = "冷蔵庫"
    expiry_date: Optional[str] = None

class InventoryUpdateRequest(BaseModel):
    item_id: str
    item_name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    storage_location: Optional[str] = None
    expiry_date: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "Morizo AI is running!", "mcp_integration": "enabled"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Morizo AI", "mcp_integration": "enabled"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, auth_data = Depends(verify_token)):
    """
    ユーザーのメッセージをLLMに送信し、レスポンスを返す
    """
    try:
        current_user = auth_data["user"]
        raw_token = auth_data["raw_token"]
        
        print(f"\n🔍 [DEBUG] Chat request received:")
        print(f"   User: {current_user.email}")
        print(f"   Message: {request.message}")
        print(f"   User ID: {current_user.id}")
        
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # 在庫管理関連のキーワードをチェック
        inventory_keywords = ["追加", "加える", "入れる", "在庫", "冷蔵庫", "冷凍庫", "牛乳", "卵", "肉", "野菜", "果物"]
        is_inventory_request = any(keyword in request.message for keyword in inventory_keywords)
        
        print(f"🔍 [DEBUG] Inventory keywords detected: {is_inventory_request}")
        
        if is_inventory_request:
            print(f"🔍 [DEBUG] Attempting to parse inventory request...")
            
            # 簡単な在庫追加のパターンマッチング
            if "牛乳" in request.message and ("追加" in request.message or "加える" in request.message or "入れる" in request.message):
                print(f"🔍 [DEBUG] Detected milk addition request")
                
                # 数量を抽出（簡単なパターン）
                import re
                quantity_match = re.search(r'(\d+)本', request.message)
                quantity = float(quantity_match.group(1)) if quantity_match else 2.0
                
                print(f"🔍 [DEBUG] Extracted quantity: {quantity}")
                
                # MCP経由で在庫追加を試行
                try:
                    print(f"🔍 [DEBUG] Using token: {raw_token[:50]}...")
                    mcp_result = await mcp_client.call_tool(
                        "inventory_add",
                        arguments={
                            "token": raw_token,  # 生のJWTトークンを使用
                            "item_name": "牛乳",
                            "quantity": quantity,
                            "unit": "本",
                            "storage_location": "冷蔵庫"
                        }
                    )
                    
                    print(f"🔍 [DEBUG] MCP result: {mcp_result}")
                    
                    if mcp_result.get("success"):
                        print(f"✅ [SUCCESS] Inventory added successfully")
                        ai_response = f"牛乳を{quantity}本、冷蔵庫に追加しました！在庫管理が完了しました。"
                    else:
                        print(f"❌ [ERROR] MCP failed: {mcp_result.get('error')}")
                        ai_response = f"申し訳ありません。在庫の追加でエラーが発生しました: {mcp_result.get('error')}"
                        
                except Exception as mcp_error:
                    print(f"❌ [ERROR] MCP call failed: {str(mcp_error)}")
                    ai_response = f"申し訳ありません。在庫管理システムでエラーが発生しました: {str(mcp_error)}"
            else:
                print(f"🔍 [DEBUG] No specific inventory pattern matched, using LLM")
                ai_response = await get_llm_response(request.message, current_user)
        else:
            print(f"🔍 [DEBUG] No inventory keywords, using LLM directly")
            ai_response = await get_llm_response(request.message, current_user)
        
        print(f"🔍 [DEBUG] Final response: {ai_response}")
        
        return ChatResponse(
            response=ai_response,
            success=True,
            model_used="gpt-4o-mini",
            user_id=current_user.id
        )
        
    except Exception as e:
        print(f"❌ [ERROR] Chat processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")

async def get_llm_response(message: str, current_user) -> str:
    """LLMからレスポンスを取得"""
    try:
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "あなたはMorizoという名前のスマートパントリーアシスタントです。食材管理とレシピ提案を手伝います。日本語で親しみやすく回答してください。"},
                {"role": "user", "content": message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ [ERROR] LLM response error: {str(e)}")
        return f"申し訳ありません。AI応答でエラーが発生しました: {str(e)}"

# MCP統合エンドポイント
@app.post("/inventory/add")
async def add_inventory_item(request: InventoryRequest, auth_data = Depends(verify_token)):
    """在庫アイテムを追加"""
    try:
        current_user = auth_data["user"]
        raw_token = auth_data["raw_token"]
        
        result = await mcp_client.call_tool(
            "inventory_add",
            arguments={
                "token": raw_token,  # 生のJWTトークンを使用
                "item_name": request.item_name,
                "quantity": request.quantity,
                "unit": request.unit,
                "storage_location": request.storage_location,
                "expiry_date": request.expiry_date
            }
        )
        
        if result.get("success"):
            return {"success": True, "data": result["data"]}
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inventory add error: {str(e)}")

@app.get("/inventory/list")
async def list_inventory_items(auth_data = Depends(verify_token)):
    """在庫一覧を取得"""
    try:
        current_user = auth_data["user"]
        raw_token = auth_data["raw_token"]
        
        result = await mcp_client.call_tool(
            "inventory_list",
            arguments={"token": raw_token}
        )
        
        if result.get("success"):
            return {"success": True, "data": result["data"]}
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inventory list error: {str(e)}")

@app.get("/inventory/{item_id}")
async def get_inventory_item(item_id: str, auth_data = Depends(verify_token)):
    """特定の在庫アイテムを取得"""
    try:
        current_user = auth_data["user"]
        raw_token = auth_data["raw_token"]
        
        result = await mcp_client.call_tool(
            "inventory_get",
            arguments={
                "token": raw_token,
                "item_id": item_id
            }
        )
        
        if result.get("success"):
            return {"success": True, "data": result["data"]}
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inventory get error: {str(e)}")

@app.put("/inventory/update")
async def update_inventory_item(request: InventoryUpdateRequest, auth_data = Depends(verify_token)):
    """在庫アイテムを更新"""
    try:
        current_user = auth_data["user"]
        raw_token = auth_data["raw_token"]
        
        arguments = {
            "token": raw_token,
            "item_id": request.item_id
        }
        
        if request.item_name: arguments["item_name"] = request.item_name
        if request.quantity is not None: arguments["quantity"] = request.quantity
        if request.unit: arguments["unit"] = request.unit
        if request.storage_location: arguments["storage_location"] = request.storage_location
        if request.expiry_date: arguments["expiry_date"] = request.expiry_date
        
        result = await mcp_client.call_tool(
            "inventory_update",
            arguments=arguments
        )
        
        if result.get("success"):
            return {"success": True, "data": result["data"]}
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inventory update error: {str(e)}")

@app.delete("/inventory/{item_id}")
async def delete_inventory_item(item_id: str, auth_data = Depends(verify_token)):
    """在庫アイテムを削除"""
    try:
        current_user = auth_data["user"]
        raw_token = auth_data["raw_token"]
        
        result = await mcp_client.call_tool(
            "inventory_delete",
            arguments={
                "token": raw_token,
                "item_id": item_id
            }
        )
        
        if result.get("success"):
            return {"success": True, "message": result["message"]}
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inventory delete error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)