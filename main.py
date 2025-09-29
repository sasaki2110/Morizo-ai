"""
Morizo AI - Smart Pantry AI Agent
Copyright (c) 2024 Morizo AI Project. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, modification,
distribution, or use is strictly prohibited without explicit written permission.

For licensing inquiries, contact: [contact@morizo-ai.com]
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# 環境変数の読み込み
load_dotenv()

# 設定とログ
from config.logging_config import setup_logging
from config.cors_config import setup_cors

# 認証
from auth.authentication import verify_token

# モデル
from models.requests import ChatRequest, ChatResponse
from confirmation_processor import ConfirmationProcessor

# ハンドラー
from handlers.chat_handler import handle_chat_request
from handlers.session_handler import setup_session_routes

# ログ設定
logger = setup_logging()

# インポートテスト
try:
    logger.debug("🔍 [MAIN] モジュールインポートテスト開始")
    from handlers.chat_handler import handle_chat_request
    logger.debug("✅ [MAIN] chat_handler インポート成功")
    from auth.authentication import verify_token
    logger.debug("✅ [MAIN] authentication インポート成功")
    from models.requests import ChatRequest, ChatResponse
    logger.debug("✅ [MAIN] models インポート成功")
    from agents.mcp_client import get_available_tools_from_mcp
    logger.debug("✅ [MAIN] agents インポート成功")
    logger.debug("✅ [MAIN] utils インポート成功")
    logger.debug("✅ [MAIN] 全モジュールインポート成功")
except Exception as e:
    logger.error(f"❌ [MAIN] インポートエラー: {str(e)}")
    import traceback
    logger.error(f"❌ [MAIN] トレースバック: {traceback.format_exc()}")

# FastAPIアプリケーションの初期化
app = FastAPI(
    title="Morizo AI",
    description="音声駆動型スマートパントリーAIエージェント",
    version="2.0.0"
)

# CORS設定
setup_cors(app)

# ルート設定
@app.get("/")
async def root():
    """ルートエンドポイント"""
    logger.info("🔍 [MAIN] ルートエンドポイントアクセス")
    return {
        "message": "Morizo AI - 統一された真のReActエージェント",
        "version": "2.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    logger.info("🔍 [MAIN] ヘルスチェックエンドポイントアクセス")
    return {"status": "healthy", "message": "Morizo AI is running"}

@app.get("/test")
async def test_endpoint():
    """テストエンドポイント"""
    logger.info("🔍 [MAIN] テストエンドポイントアクセス")
    return {"message": "Test endpoint working", "timestamp": "2025-09-23"}

@app.post("/chat-test", response_model=ChatResponse)
async def chat_test(request: ChatRequest):
    """
    認証なしのテスト用チャットエンドポイント
    """
    logger.info("🔍 [MAIN] 認証なしチャットテスト開始")
    logger.info(f"🔍 [MAIN] テストリクエスト: {request.message}")
    
    try:
        # ダミーの認証データを作成
        class DummyUser:
            def __init__(self):
                self.id = "test-user-id"
                self.email = "test@example.com"
        
        dummy_auth_data = {
            "user": DummyUser(),
            "raw_token": "dummy-token"
        }
        
        logger.info("🔍 [MAIN] ダミー認証データ作成完了")
        
        # テスト用のSupabaseクライアントを作成（認証バイパス）
        from supabase import create_client
        import os
        
        # 実際のSupabase設定を使用
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if supabase_url and supabase_key:
            # 実際のSupabaseクライアントを作成
            supabase_client = create_client(supabase_url, supabase_key)
            logger.info("✅ [MAIN] 実際のSupabaseクライアントを作成")
        else:
            logger.warning("⚠️ [MAIN] Supabase設定が見つかりません")
            supabase_client = None
        
        # テスト用のセッション管理（認証バイパス）
        from session_manager import session_manager
        user_session = session_manager.get_or_create_session(dummy_auth_data["user"].id, dummy_auth_data["raw_token"])
        
        # Supabaseクライアントをセッションに設定
        if supabase_client:
            user_session.supabase_client = supabase_client
        
        result = await handle_chat_request(request, dummy_auth_data)
        logger.info("✅ [MAIN] 認証なしチャットテスト完了")
        return result
        
    except Exception as e:
        logger.error(f"❌ [MAIN] 認証なしチャットテストエラー: {str(e)}")
        logger.error(f"❌ [MAIN] エラータイプ: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [MAIN] トレースバック: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")

# 認証なしの確認応答エンドポイント（テスト用）
@app.post("/chat-test/confirm", response_model=ChatResponse)
async def confirm_chat_test(request: ChatRequest):
    """
    認証なしの確認応答エンドポイント（テスト用）
    """
    try:
        logger.info(f"🤔 [MAIN] 認証なし確認応答リクエスト受信: {request.message}")
        
        # ダミーの認証データを作成
        class DummyUser:
            def __init__(self):
                self.id = "test-user-id"
                self.email = "test@example.com"
        
        dummy_auth_data = {
            "user": DummyUser(),
            "raw_token": "dummy-token"
        }
        
        # セッション管理
        from session_manager import session_manager
        user_session = session_manager.get_or_create_session(dummy_auth_data["user"].id, dummy_auth_data["raw_token"])
        
        # 確認コンテキストを取得
        confirmation_context = user_session.get_confirmation_context()
        if not confirmation_context:
            logger.warning(f"⚠️ [MAIN] 確認コンテキストが見つかりません: {dummy_auth_data['user'].id}")
            raise HTTPException(status_code=400, detail="確認コンテキストが見つかりません。確認プロセスが開始されていないか、期限切れの可能性があります。")
        
        # 確認コンテキストから実際のコンテキストを抽出
        actual_context = confirmation_context.get('confirmation_context', confirmation_context)
        logger.info(f"🤔 [MAIN] 確認コンテキスト取得完了: {actual_context.get('action', 'unknown')}")
        
        # 確認プロセッサーで応答を処理
        confirmation_processor = ConfirmationProcessor()
        execution_plan = confirmation_processor.process_confirmation_response(
            request.message, 
            actual_context
        )
        
        logger.info(f"🤔 [MAIN] 確認応答処理完了: cancel={execution_plan.cancel}, continue={execution_plan.continue_execution}")
        
        if execution_plan.cancel:
            # キャンセル処理
            user_session.clear_confirmation_context()
            logger.info(f"🚫 [MAIN] 操作をキャンセル: {dummy_auth_data['user'].id}")
            return ChatResponse(
                response="操作をキャンセルしました。",
                success=True,
                model_used=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                user_id=user_session.user_id
            )
        
        # タスクチェーン再開処理
        if execution_plan.continue_execution:
            logger.info(f"🔄 [MAIN] タスクチェーン再開開始: {len(execution_plan.tasks)}個のタスク")
            
            # TrueReactAgentでタスクチェーン再開
            from true_react_agent import TrueReactAgent
            from openai import OpenAI
            
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            true_react_agent = TrueReactAgent(client)
            
            # タスクチェーン再開
            result = await true_react_agent.resume_task_chain(
                execution_plan.tasks,
                user_session,
                confirmation_context
            )
            
            # 確認コンテキストをクリア
            user_session.clear_confirmation_context()
            
            logger.info(f"✅ [MAIN] タスクチェーン再開完了: {dummy_auth_data['user'].id}")
            
            return ChatResponse(
                response=result,
                success=True,
                model_used=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                user_id=user_session.user_id
            )
        
        # 予期しない状況
        logger.warning(f"⚠️ [MAIN] 予期しない実行計画: {execution_plan}")
        return ChatResponse(
            response="申し訳ありません。処理中に予期しない状況が発生しました。",
            success=False,
            model_used=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            user_id=user_session.user_id
        )
        
    except HTTPException:
        # HTTPExceptionはそのまま再発生
        raise
    except Exception as e:
        logger.error(f"❌ [MAIN] 認証なし確認応答処理エラー: {str(e)}")
        logger.error(f"❌ [MAIN] エラータイプ: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [MAIN] トレースバック: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Confirmation processing error: {str(e)}")

# チャットエンドポイント
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, auth_data = Depends(verify_token)):
    """
    Morizo AI - 統一された真のReActエージェント
    単純な要求も複雑な要求も同じフローで処理
    """
    try:
        logger.info(f"🔍 [MAIN] チャットリクエスト受信: {request.message}")
        logger.info(f"🔍 [MAIN] リクエスト詳細: message={request.message}, user_id={request.user_id}")
        logger.info(f"🔍 [MAIN] 認証データ: {type(auth_data)}")
        
        logger.info(f"🔍 [MAIN] handle_chat_request呼び出し開始")
        result = await handle_chat_request(request, auth_data)
        logger.info(f"✅ [MAIN] handle_chat_request呼び出し完了")
        logger.info(f"✅ [MAIN] チャットリクエスト処理完了")
        return result
    except Exception as e:
        logger.error(f"❌ [MAIN] チャットリクエスト処理エラー: {str(e)}")
        logger.error(f"❌ [MAIN] エラータイプ: {type(e).__name__}")
        logger.error(f"❌ [MAIN] エラー詳細: {repr(e)}")
        import traceback
        logger.error(f"❌ [MAIN] トレースバック: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# 確認応答エンドポイント
@app.post("/chat/confirm", response_model=ChatResponse)
async def confirm_chat(request: ChatRequest, auth_data = Depends(verify_token)):
    """
    Phase 4.4.3: 確認応答を処理するエンドポイント（完全実装）
    ユーザーが確認プロセスで選択した内容を処理し、タスクチェーンを再開
    """
    try:
        logger.info(f"🤔 [MAIN] 確認応答リクエスト受信: {request.message}")
        
        current_user = auth_data["user"]
        raw_token = auth_data["raw_token"]
        
        # セッション管理
        from session_manager import session_manager
        user_session = session_manager.get_or_create_session(current_user.id, raw_token)
        
        # 確認コンテキストを取得
        confirmation_context = user_session.get_confirmation_context()
        if not confirmation_context:
            logger.warning(f"⚠️ [MAIN] 確認コンテキストが見つかりません: {current_user.id}")
            raise HTTPException(status_code=400, detail="確認コンテキストが見つかりません。確認プロセスが開始されていないか、期限切れの可能性があります。")
        
        # 確認コンテキストから実際のコンテキストを抽出
        actual_context = confirmation_context.get('confirmation_context', confirmation_context)
        logger.info(f"🤔 [MAIN] 確認コンテキスト取得完了: {actual_context.get('action', 'unknown')}")
        
        # 確認プロセッサーで応答を処理
        confirmation_processor = ConfirmationProcessor()
        execution_plan = confirmation_processor.process_confirmation_response(
            request.message, 
            actual_context
        )
        
        logger.info(f"🤔 [MAIN] 確認応答処理完了: cancel={execution_plan.cancel}, continue={execution_plan.continue_execution}")
        
        if execution_plan.cancel:
            # キャンセル処理
            user_session.clear_confirmation_context()
            logger.info(f"🚫 [MAIN] 操作をキャンセル: {current_user.id}")
            return ChatResponse(
                response="操作をキャンセルしました。",
                success=True,
                model_used=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                user_id=user_session.user_id
            )
        
        # タスクチェーン再開処理
        if execution_plan.continue_execution:
            logger.info(f"🔄 [MAIN] タスクチェーン再開開始: {len(execution_plan.tasks)}個のタスク")
            
            # TrueReactAgentでタスクチェーン再開
            from true_react_agent import TrueReactAgent
            from openai import OpenAI
            
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            true_react_agent = TrueReactAgent(client)
            
            # タスクチェーン再開
            result = await true_react_agent.resume_task_chain(
                execution_plan.tasks,
                user_session,
                confirmation_context
            )
            
            # 確認コンテキストをクリア
            user_session.clear_confirmation_context()
            
            logger.info(f"✅ [MAIN] タスクチェーン再開完了: {current_user.id}")
            
            return ChatResponse(
                response=result,
                success=True,
                model_used=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                user_id=user_session.user_id
            )
        
        # 予期しない状況
        logger.warning(f"⚠️ [MAIN] 予期しない実行計画: {execution_plan}")
        return ChatResponse(
            response="申し訳ありません。処理中に予期しない状況が発生しました。",
            success=False,
            model_used=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            user_id=user_session.user_id
        )
        
    except HTTPException:
        # HTTPExceptionはそのまま再発生
        raise
    except Exception as e:
        logger.error(f"❌ [MAIN] 確認応答処理エラー: {str(e)}")
        logger.error(f"❌ [MAIN] エラータイプ: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [MAIN] トレースバック: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Confirmation processing error: {str(e)}")

# セッション管理ルート
setup_session_routes(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
