"""
Morizo AI - Smart Pantry AI Agent
Copyright (c) 2024 Morizo AI Project. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, modification,
distribution, or use is strictly prohibited without explicit written permission.

For licensing inquiries, contact: [contact@morizo-ai.com]
"""

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

# 動的MCPエージェントがすべての在庫操作を処理するため、
# 個別のPydanticモデルは不要になりました。
# すべての操作は /chat エンドポイント経由で自然言語で実行されます。

@app.get("/")
async def root():
    return {"message": "Morizo AI is running!", "mcp_integration": "enabled"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Morizo AI", "mcp_integration": "enabled"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, auth_data = Depends(verify_token)):
    """
    Morizo AI ReAct Agent - 観察→思考→決定→行動のループでユーザーメッセージを処理
    """
    try:
        current_user = auth_data["user"]
        raw_token = auth_data["raw_token"]
        
        print(f"\n=== Morizo AI ReAct Agent 開始 ===")
        print(f"🔍 [観察] ユーザー入力: {request.message}")
        print(f"   User: {current_user.email}")
        print(f"   User ID: {current_user.id}")
        
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # === 思考フェーズ ===
        print(f"🧠 [思考] MCPサーバーから動的にツールリストを取得中...")
        
        # MCPサーバーから動的にツールリストを取得
        available_tools = []
        try:
            async with stdio_client(mcp_client.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # ツールリストを取得
                    tools_response = await session.list_tools()
                    
                    if tools_response and hasattr(tools_response, 'tools'):
                        for tool in tools_response.tools:
                            available_tools.append(f"- {tool.name}: {tool.description}")
                    
                    print(f"🧠 [思考] 利用可能なツール: {len(available_tools)}個")
                    
        except Exception as e:
            print(f"❌ [エラー] ツールリスト取得失敗: {str(e)}")
            # フォールバック: 基本的なツールリスト
            available_tools = [
                "- inventory_list: 在庫一覧を取得",
                "- inventory_add: 在庫にアイテムを追加",
                "- inventory_get: 特定のアイテムの詳細を取得",
                "- inventory_update: 在庫アイテムを更新",
                "- inventory_delete: 在庫アイテムを削除"
            ]
        
        # LLMにツール選択を依頼
        tools_list = "\n".join(available_tools)
        tool_selection_prompt = f"""
あなたはMorizoというスマートパントリーアシスタントです。
ユーザーの要求を分析し、適切なツールを選択してください。

利用可能なツール:
{tools_list}
- llm_chat: 一般的な会話や質問

ユーザーの要求: "{request.message}"

以下のJSON形式で回答してください:
{{
    "tool": "ツール名",
    "reasoning": "選択理由",
    "parameters": {{
        "item_name": "アイテム名（該当する場合）",
        "quantity": 数量（該当する場合）,
        "unit": "単位（該当する場合）",
        "storage_location": "保管場所（該当する場合）"
    }}
}}
"""
        
        try:
            tool_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": tool_selection_prompt}],
                max_tokens=200,
                temperature=0.1
            )
            
            tool_decision = tool_response.choices[0].message.content
            print(f"🧠 [思考] LLM判断: {tool_decision}")
            
            # JSON解析
            import json
            try:
                tool_data = json.loads(tool_decision)
                selected_tool = tool_data.get("tool", "llm_chat")
                reasoning = tool_data.get("reasoning", "")
                parameters = tool_data.get("parameters", {})
                
                print(f"🎯 [決定] 選択されたツール: {selected_tool}")
                print(f"🎯 [決定] 理由: {reasoning}")
                
            except json.JSONDecodeError:
                print(f"⚠️ [警告] JSON解析失敗、LLMチャットを使用")
                selected_tool = "llm_chat"
                parameters = {}
                
        except Exception as e:
            print(f"❌ [エラー] LLM呼び出し失敗: {str(e)}")
            selected_tool = "llm_chat"
            parameters = {}
        
        # === 行動フェーズ ===
        print(f"🔍 [行動] {selected_tool}を実行中...")
        
        if selected_tool == "llm_chat":
            print(f"🔍 [行動] LLMチャットを実行")
            ai_response = await get_llm_response(request.message, current_user)
            
        elif selected_tool != "llm_chat":
            print(f"🔍 [行動] MCPで{selected_tool}を実行")
            try:
                # 動的にMCPツールを呼び出し
                mcp_arguments = {"token": raw_token}
                
                # LLMが抽出したパラメータを追加
                if parameters:
                    mcp_arguments.update(parameters)
                
                print(f"🔍 [行動] 引数: {mcp_arguments}")
                
                mcp_result = await mcp_client.call_tool(
                    selected_tool,
                    arguments=mcp_arguments
                )
                
                if mcp_result.get("success"):
                    print(f"✅ [成功] {selected_tool}実行完了")
                    
                    # 動的な結果処理
                    if mcp_result.get("data"):
                        # データがある場合は、LLMに結果を整形してもらう
                        data_str = json.dumps(mcp_result["data"], ensure_ascii=False, indent=2)
                        formatting_prompt = f"""
以下の{selected_tool}の実行結果を、ユーザーにとって分かりやすい日本語で整形してください。

実行結果:
{data_str}

ユーザーの要求: "{request.message}"

自然で親しみやすい日本語で回答してください。
"""
                        
                        try:
                            format_response = client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[{"role": "user", "content": formatting_prompt}],
                                max_tokens=500,
                                temperature=0.3
                            )
                            ai_response = format_response.choices[0].message.content
                        except Exception as e:
                            print(f"⚠️ [警告] 結果整形失敗: {str(e)}")
                            ai_response = mcp_result.get("message", f"{selected_tool}が正常に実行されました。")
                    else:
                        # データがない場合はメッセージをそのまま表示
                        ai_response = mcp_result.get("message", f"{selected_tool}が正常に実行されました。")
                else:
                    print(f"❌ [エラー] MCP失敗: {mcp_result.get('error')}")
                    ai_response = f"申し訳ありません。{selected_tool}の実行でエラーが発生しました: {mcp_result.get('error')}"
                    
            except Exception as e:
                print(f"❌ [エラー] MCP実行エラー: {str(e)}")
                ai_response = f"申し訳ありません。{selected_tool}の実行でエラーが発生しました: {str(e)}"
        
        else:
            print(f"🔍 [行動] LLMチャットを実行")
            ai_response = await get_llm_response(request.message, current_user)
        
        print(f"✅ [完了] 最終応答: {ai_response}")
        print(f"=== Morizo AI ReAct Agent 終了 ===\n")
        
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

# 動的MCPエージェントがすべての在庫操作を処理するため、
# 個別のエンドポイントは不要になりました。
# すべての操作は /chat エンドポイント経由で実行されます。

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)