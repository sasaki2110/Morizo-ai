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
import logging
import shutil
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from session_manager import session_manager, SessionContext

def setup_log_rotation():
    """ログローテーション設定"""
    log_file = 'morizo_ai.log'
    backup_file = 'morizo_ai.log.1'
    
    # 既存のログファイルがある場合、バックアップを作成
    if os.path.exists(log_file):
        try:
            # 既存のバックアップファイルがある場合は削除
            if os.path.exists(backup_file):
                os.remove(backup_file)
                print(f"🗑️ 古いバックアップログを削除: {backup_file}")
            
            # 現在のログファイルをバックアップに移動
            shutil.move(log_file, backup_file)
            print(f"📦 ログファイルをバックアップ: {log_file} → {backup_file}")
            
        except Exception as e:
            print(f"⚠️ ログローテーション失敗: {str(e)}")
    else:
        print(f"📝 新しいログファイルを作成: {log_file}")
    
    return log_file

# ログローテーション実行
log_file = setup_log_rotation()

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8', mode='a'),
        logging.StreamHandler()  # コンソール出力も残す
    ],
    force=True  # 既存の設定を上書き
)

# FastMCPのログを抑制
logging.getLogger('mcp').setLevel(logging.WARNING)
logging.getLogger('mcp.client').setLevel(logging.WARNING)
logging.getLogger('mcp.server').setLevel(logging.WARNING)

# HTTP関連のログを抑制
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('hpack').setLevel(logging.WARNING)

logger = logging.getLogger('morizo_ai')

# ログテスト
logger.info("🚀 Morizo AI アプリケーション起動 - ログテスト")

def _is_complex_request(message: str) -> bool:
    """
    複雑な要求かどうかを判定する
    
    Args:
        message: ユーザーのメッセージ
        
    Returns:
        複雑な要求かどうか
    """
    # 複数アイテムのキーワード
    multi_item_keywords = [
        "と", "も", "および", "それから", "さらに", "また", "加えて",
        "1パックと", "2本と", "3個と", "1袋と"
    ]
    
    # 複数操作のキーワード
    multi_operation_keywords = [
        "その後", "それから", "次に", "さらに", "また", "加えて",
        "変更して", "削除して", "更新して"
    ]
    
    # 複数アイテムの判定
    for keyword in multi_item_keywords:
        if keyword in message:
            return True
    
    # 複数操作の判定
    for keyword in multi_operation_keywords:
        if keyword in message:
            return True
    
    return False

async def _process_with_true_react(request, user_session, raw_token):
    """
    真のReActエージェントで処理する
    
    Args:
        request: リクエスト
        user_session: ユーザーセッション
        raw_token: 認証トークン
        
    Returns:
        処理結果
    """
    try:
        # 真のReActエージェントのインポート
        from true_react_agent import TrueReactAgent
        from action_planner import ActionPlanner
        from task_manager import TaskManager
        
        logger.info("🤖 [真のAIエージェント] 行動計画立案を開始")
        
        # OpenAIクライアントの初期化
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # 真のReActエージェントの初期化
        true_react_agent = TrueReactAgent(client)
        
        # MCPから動的にツール一覧を取得
        available_tools = await _get_available_tools_from_mcp()
        
        # 真のReActエージェントで処理
        result = await true_react_agent.process_request(
            request.message,
            user_session,
            available_tools
        )
        
        logger.info("🤖 [真のAIエージェント] 処理完了")
        return {"response": result}
        
    except Exception as e:
        logger.error(f"❌ [真のAIエージェント] エラー: {str(e)}")
        return {"response": f"申し訳ありません。処理中にエラーが発生しました: {str(e)}"}

async def _get_available_tools_from_mcp() -> List[str]:
    """
    MCPから利用可能なツール一覧を取得する
    
    Returns:
        利用可能なツール一覧
    """
    try:
        available_tools = []
        async with stdio_client(mcp_client.server_params) as (read, write):
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

def mask_email(email: str) -> str:
    """メールアドレスをマスク"""
    if "@" not in email:
        return email
    
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "*" * (len(local) - 1)
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    
    return f"{masked_local}@{domain}"

# 環境変数の読み込み
load_dotenv()

app = FastAPI(title="Morizo AI", description="Smart Pantry AI Agent with MCP Integration")

# バックグラウンドタスク: 期限切れセッションの自動クリア
async def cleanup_expired_sessions():
    """期限切れセッションを定期的にクリア"""
    while True:
        try:
            session_manager.clear_expired_sessions()
            await asyncio.sleep(300)  # 5分ごとにチェック
        except Exception as e:
            print(f"❌ [エラー] セッションクリーンアップエラー: {str(e)}")
            await asyncio.sleep(60)  # エラー時は1分後に再試行

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    logger.info("🚀 Morizo AI セッション管理システム起動")
    # バックグラウンドタスクを開始
    asyncio.create_task(cleanup_expired_sessions())

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
                async with ClientSession(read, write) as mcp_session:
                    await mcp_session.initialize()
                    result = await mcp_session.call_tool(tool_name, arguments=arguments)
                    
                    if result and hasattr(result, 'content') and result.content:
                        return json.loads(result.content[0].text)
                    else:
                        return {"success": False, "error": "No result from MCP tool"}
        except Exception as e:
            return {"success": False, "error": f"MCP tool error: {str(e)}"}

# グローバルMCPクライアントインスタンス
mcp_client = MCPClient()

# サーバー起動時にモデル情報を表示
logger.info(f"🚀 Morizo AI Server starting...")
logger.info(f"📋 Using OpenAI Model: {model_name}")
logger.info(f"🔑 OpenAI API Key configured: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
logger.info(f"🔐 Supabase configured: {'Yes' if supabase else 'No'}")
logger.info(f"🔗 MCP Integration: Enabled")

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
        
        # トークンを省略表示
        token_preview = f"{raw_token[:20]}...{raw_token[-20:]}" if len(raw_token) > 40 else raw_token
        logger.info(f"🔍 [AUTH] Token received: {token_preview}")
        logger.info(f"🔍 [AUTH] Token length: {len(raw_token)}")
        
        # トークンからユーザー情報を取得
        response = supabase.auth.get_user(raw_token)
        
        if response.user is None:
            print(f"❌ [ERROR] User is None in response")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )
        
        # メールアドレスをマスク
        email = response.user.email
        if '@' in email:
            local, domain = email.split('@', 1)
            masked_email = f"{local[:3]}*****@{domain}"
        else:
            masked_email = email
        logger.info(f"✅ [SUCCESS] User authenticated: {masked_email}")
        
        # ユーザー情報とトークンを辞書で返す
        return {
            "user": response.user,
            "raw_token": raw_token
        }
    except Exception as e:
        logger.error(f"❌ [ERROR] Authentication failed: {str(e)}")
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

@app.get("/session/status")
async def get_session_status(auth_data = Depends(verify_token)):
    """セッション状態を取得"""
    try:
        current_user = auth_data["user"]
        token = auth_data["raw_token"]
        user_session = session_manager.get_or_create_session(current_user.id, token)
        
        return {
            "success": True,
            "session_info": user_session.to_dict(),
            "recent_operations": user_session.get_recent_operations(5)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session status error: {str(e)}")

@app.post("/session/clear")
async def clear_session(auth_data = Depends(verify_token)):
    """セッションをクリア（方法A: 明示的なクリア）"""
    try:
        current_user = auth_data["user"]
        session_manager.clear_session(current_user.id, reason="user_request")
        
        return {
            "success": True,
            "message": "セッションをクリアしました。新しい会話を始めましょう！"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session clear error: {str(e)}")

@app.post("/session/clear-history")
async def clear_session_history(auth_data = Depends(verify_token)):
    """操作履歴のみをクリア（方法C: 操作履歴の制限）"""
    try:
        current_user = auth_data["user"]
        token = auth_data["raw_token"]
        user_session = session_manager.get_or_create_session(current_user.id, token)
        user_session.clear_history()
        
        return {
            "success": True,
            "message": "操作履歴をクリアしました。"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session history clear error: {str(e)}")

@app.get("/session/all")
async def get_all_sessions_info(auth_data = Depends(verify_token)):
    """全セッション情報を取得（開発・テスト用）"""
    try:
        all_info = session_manager.get_all_sessions_info()
        return {
            "success": True,
            "sessions_info": all_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"All sessions info error: {str(e)}")

@app.post("/session/clear-all")
async def clear_all_sessions(auth_data = Depends(verify_token)):
    """全セッションをクリア（開発・テスト用）"""
    try:
        session_manager.clear_all_sessions()
        return {
            "success": True,
            "message": "全セッションをクリアしました。"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear all sessions error: {str(e)}")

@app.post("/test/clear-inventory")
async def clear_test_inventory(auth_data = Depends(verify_token)):
    """テスト用: 在庫をクリア（開発・テスト用）"""
    try:
        current_user = auth_data["user"]
        raw_token = auth_data["raw_token"]
        
        # テスト用の在庫クリア（牛乳を削除）
        mcp_result = await mcp_client.call_tool(
            "inventory_delete",
            arguments={
                "token": raw_token,
                "item_name": "牛乳"
            }
        )
        
        return {
            "success": True,
            "message": "テスト用在庫をクリアしました。",
            "mcp_result": mcp_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear test inventory error: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, auth_data = Depends(verify_token)):
    """
    Morizo AI ReAct Agent - 観察→思考→決定→行動のループでユーザーメッセージを処理
    """
    try:
        current_user = auth_data["user"]
        raw_token = auth_data["raw_token"]
        
        # === セッション管理 ===
        user_session = session_manager.get_or_create_session(current_user.id, raw_token)
        logger.info(f"📱 [セッション] セッションID: {user_session.session_id}")
        logger.info(f"📱 [セッション] 継続時間: {user_session.get_session_duration().total_seconds()/60:.1f}分")
        logger.info(f"📱 [セッション] 操作履歴: {len(user_session.operation_history)}件")
        
        logger.info(f"\n=== Morizo AI ReAct Agent 開始 ===")
        logger.info(f"🔍 [観察] ユーザー入力: {request.message}")
        logger.info(f"   User: {mask_email(current_user.email)}")
        logger.info(f"   User ID: {current_user.id}")
        
        # 真のAIエージェント化の判定
        if _is_complex_request(request.message):
            logger.info("🤖 [真のAIエージェント] 複雑な要求を検出、行動計画立案を開始")
            return await _process_with_true_react(request, user_session, raw_token)
        
        logger.info(f"🧠 [思考] MCPサーバーから動的にツールリストを取得中...")
        
        # MCPサーバーから動的にツールリストを取得
        available_tools = []
        try:
            async with stdio_client(mcp_client.server_params) as (read, write):
                async with ClientSession(read, write) as mcp_session:
                    await mcp_session.initialize()
                    
                    # ツールリストを取得
                    tools_response = await mcp_session.list_tools()
                    
                    if tools_response and hasattr(tools_response, 'tools'):
                        for tool in tools_response.tools:
                            available_tools.append(f"- {tool.name}: {tool.description}")
                    
                    logger.info(f"🧠 [思考] 利用可能なツール: {len(available_tools)}個")
                    
        except Exception as e:
            logger.error(f"❌ [エラー] ツールリスト取得失敗: {str(e)}")
            # フォールバック: 基本的なツールリスト
            available_tools = [
                "- inventory_list: 在庫一覧を取得",
                "- inventory_add: 在庫にアイテムを追加",
                "- inventory_get: 特定のアイテムの詳細を取得",
                "- inventory_update: 在庫アイテムを更新",
                "- inventory_delete: 在庫アイテムを削除"
            ]
        
        # LLMにツール選択を依頼（セッションコンテキストを含む）
        tools_list = "\n".join(available_tools)
        
        # セッションの在庫一覧をコンテキストに追加
        inventory_context = ""
        if user_session.current_inventory:
            try:
                inventory_context = f"""
現在の在庫状況:
{json.dumps(user_session.current_inventory, ensure_ascii=False, indent=2)}
"""
            except TypeError as e:
                logger.warning(f"⚠️ 在庫一覧のJSONシリアライズ失敗: {str(e)}")
                # シンプルな文字列表現にフォールバック
                inventory_context = f"""
現在の在庫状況:
{user_session.current_inventory}
"""
        
        # 最近の操作履歴をコンテキストに追加
        recent_operations = user_session.get_recent_operations(3)
        operation_context = ""
        if recent_operations:
            try:
                operation_context = f"""
最近の操作履歴:
{json.dumps(recent_operations, ensure_ascii=False, indent=2)}
"""
            except TypeError as e:
                logger.warning(f"⚠️ 操作履歴のJSONシリアライズ失敗: {str(e)}")
                # シンプルな文字列表現にフォールバック
                operation_context = f"""
最近の操作履歴:
{recent_operations}
"""
        
        tool_selection_prompt = f"""
あなたはMorizoというスマートパントリーアシスタントです。
ユーザーの要求を分析し、適切なツールを選択してください。

{inventory_context}
{operation_context}

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
        "storage_location": "保管場所（該当する場合）",
        "item_id": "アイテムID（更新・削除の場合、セッションから取得）"
    }},
    "fifo_preference": "latest" or "oldest" or "auto"
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
            logger.info(f"🧠 [思考] LLM判断: {tool_decision}")
            
            # JSON解析
            try:
                tool_data = json.loads(tool_decision)
                selected_tool = tool_data.get("tool", "llm_chat")
                reasoning = tool_data.get("reasoning", "")
                parameters = tool_data.get("parameters", {})
                fifo_preference = tool_data.get("fifo_preference", "auto")
                
                logger.info(f"🎯 [決定] 選択されたツール: {selected_tool}")
                logger.info(f"🎯 [決定] 理由: {reasoning}")
                logger.info(f"🎯 [決定] FIFO設定: {fifo_preference}")
                
                # 更新・削除操作でitem_idが必要な場合、セッションから取得
                if selected_tool in ["inventory_update", "inventory_delete"] and "item_name" in parameters:
                    item_name = parameters["item_name"]
                    
                    # FIFO原則でIDを取得
                    prefer_latest = fifo_preference == "latest"
                    item_id = user_session.get_item_id_by_fifo(item_name, prefer_latest)
                    
                    if item_id:
                        parameters["item_id"] = item_id
                        logger.info(f"🔍 [FIFO] '{item_name}'のIDを取得: {item_id}")
                    else:
                        logger.warning(f"⚠️ [警告] '{item_name}'のIDが見つかりません")
                        # IDが見つからない場合は、item_nameのみでMCPサーバーに任せる
                
            except json.JSONDecodeError:
                logger.warning(f"⚠️ [警告] JSON解析失敗、LLMチャットを使用")
                selected_tool = "llm_chat"
                parameters = {}
                
        except Exception as e:
            logger.error(f"❌ [エラー] LLM呼び出し失敗: {str(e)}")
            selected_tool = "llm_chat"
            parameters = {}
        
        # === 行動フェーズ ===
        logger.info(f"🔍 [行動] {selected_tool}を実行中...")
        
        if selected_tool == "llm_chat":
            logger.info(f"🔍 [行動] LLMチャットを実行")
            ai_response = await get_llm_response(request.message, current_user)
            
        elif selected_tool != "llm_chat":
            logger.info(f"🔍 [行動] MCPで{selected_tool}を実行")
            try:
                # 動的にMCPツールを呼び出し
                mcp_arguments = {"token": raw_token}
                
                # LLMが抽出したパラメータを追加
                if parameters:
                    mcp_arguments.update(parameters)
                
                # 引数からトークンを省略表示
                display_args = mcp_arguments.copy()
                if 'token' in display_args:
                    token = display_args['token']
                    display_args['token'] = f"{token[:20]}...{token[-20:]}" if len(token) > 40 else token
                logger.info(f"🔍 [行動] 引数: {display_args}")
                
                mcp_result = await mcp_client.call_tool(
                    selected_tool,
                    arguments=mcp_arguments
                )
                
                if mcp_result.get("success"):
                    logger.info(f"✅ [成功] {selected_tool}実行完了")
                    
                    # セッションに操作履歴を記録
                    user_session.add_operation(selected_tool, {
                        "parameters": mcp_arguments,
                        "result": mcp_result.get("data", {}),
                        "user_request": request.message
                    })
                    
                    # 在庫操作の場合は、セッションの在庫一覧を更新
                    if selected_tool in ["inventory_add", "inventory_update", "inventory_delete"]:
                        await update_session_inventory(user_session, raw_token)
                    
                    # 動的な結果処理
                    if mcp_result.get("data") or selected_tool in ["inventory_delete", "inventory_update"]:
                        # データがある場合、または削除・更新操作の場合は、LLMに結果を整形してもらう
                        data_str = ""
                        if mcp_result.get("data"):
                            data_str = json.dumps(mcp_result["data"], ensure_ascii=False, indent=2)
                        
                        # 削除・更新操作の場合は、セッション情報も含める
                        session_context = ""
                        if selected_tool in ["inventory_delete", "inventory_update"]:
                            session_context = f"""
現在の在庫状況:
{json.dumps(user_session.current_inventory, ensure_ascii=False, indent=2)}
"""
                        
                        formatting_prompt = f"""
以下の{selected_tool}の実行結果を、ユーザーにとって分かりやすい日本語で整形してください。

実行結果:
{data_str if data_str else mcp_result.get("message", "操作が正常に完了しました")}

{session_context}
ユーザーの要求: "{request.message}"

自然で親しみやすい日本語で回答してください。削除や更新の場合は、現在の在庫状況も含めて説明してください。
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
                            logger.warning(f"⚠️ [警告] 結果整形失敗: {str(e)}")
                            ai_response = mcp_result.get("message", f"{selected_tool}が正常に実行されました。")
                    else:
                        # データがない場合はメッセージをそのまま表示
                        ai_response = mcp_result.get("message", f"{selected_tool}が正常に実行されました。")
                else:
                    logger.error(f"❌ [エラー] MCP失敗: {mcp_result.get('error')}")
                    ai_response = f"申し訳ありません。{selected_tool}の実行でエラーが発生しました: {mcp_result.get('error')}"
                    
            except Exception as e:
                logger.error(f"❌ [エラー] MCP実行エラー: {str(e)}")
                ai_response = f"申し訳ありません。{selected_tool}の実行でエラーが発生しました: {str(e)}"
        
        else:
            logger.info(f"🔍 [行動] LLMチャットを実行")
            ai_response = await get_llm_response(request.message, current_user)
        
        logger.info(f"✅ [完了] 最終応答: {ai_response}")
        logger.info(f"=== Morizo AI ReAct Agent 終了 ===\n")
        
        return ChatResponse(
            response=ai_response,
            success=True,
            model_used="gpt-4o-mini",
            user_id=current_user.id
        )
        
    except Exception as e:
        logger.error(f"❌ [ERROR] Chat processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")

async def update_session_inventory(user_session: SessionContext, raw_token: str):
    """セッションの在庫一覧を更新"""
    try:
        logger.info(f"📦 [セッション] 在庫一覧を更新中...")
        
        # MCPサーバーから在庫一覧を取得
        mcp_result = await mcp_client.call_tool(
            "inventory_list",
            arguments={"token": raw_token}
        )
        
        if mcp_result.get("success") and mcp_result.get("data"):
            inventory_data = mcp_result["data"]
            user_session.update_inventory_state(inventory_data)
            logger.info(f"📦 [セッション] 在庫一覧更新完了: {len(inventory_data)}件")
        else:
            logger.warning(f"⚠️ [警告] 在庫一覧取得失敗: {mcp_result.get('error')}")
            
    except Exception as e:
        logger.error(f"❌ [エラー] セッション在庫更新エラー: {str(e)}")

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