"""
Morizo AI - 統一された真のReActエージェント
リファクタリング後のメインアプリケーション
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

# ハンドラー
from handlers.chat_handler import handle_chat_request
from handlers.session_handler import setup_session_routes

# ログ設定
logger = setup_logging()

# インポートテスト
try:
    logger.info("🔍 [MAIN] モジュールインポートテスト開始")
    from handlers.chat_handler import handle_chat_request
    logger.info("✅ [MAIN] chat_handler インポート成功")
    from auth.authentication import verify_token
    logger.info("✅ [MAIN] authentication インポート成功")
    from models.requests import ChatRequest, ChatResponse
    logger.info("✅ [MAIN] models インポート成功")
    from agents.mcp_client import get_available_tools_from_mcp
    logger.info("✅ [MAIN] agents インポート成功")
    from utils.session_utils import update_session_inventory
    logger.info("✅ [MAIN] utils インポート成功")
    logger.info("✅ [MAIN] 全モジュールインポート成功")
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
        result = await handle_chat_request(request, dummy_auth_data)
        logger.info("✅ [MAIN] 認証なしチャットテスト完了")
        return result
        
    except Exception as e:
        logger.error(f"❌ [MAIN] 認証なしチャットテストエラー: {str(e)}")
        logger.error(f"❌ [MAIN] エラータイプ: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [MAIN] トレースバック: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")

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

# セッション管理ルート
setup_session_routes(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
