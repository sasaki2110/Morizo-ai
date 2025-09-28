"""
チャット処理ハンドラー
"""

import logging
from fastapi import HTTPException
from models.requests import ChatRequest, ChatResponse
from auth.authentication import verify_token
from session_manager import session_manager
from agents.mcp_client import get_available_tools_from_mcp
from true_react_agent import TrueReactAgent
from confirmation_exceptions import UserConfirmationRequired
from openai import OpenAI
import os

logger = logging.getLogger('morizo_ai.chat_handler')


async def process_with_unified_react(request: ChatRequest, user_session, raw_token: str) -> ChatResponse:
    """
    統一されたReActエージェントで処理する
    単純な要求も複雑な要求も同じフローで処理
    """
    try:
        logger.info("🤖 [統一ReActエージェント] 処理開始")
        
        # OpenAIクライアントの初期化
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # 真のReActエージェントの初期化
        true_react_agent = TrueReactAgent(client)
        
        # MCPから動的にツール一覧を取得
        available_tools = await get_available_tools_from_mcp()
        
        # 真のReActエージェントで処理
        result = await true_react_agent.process_request(
            request.message,
            user_session,
            available_tools
        )
        
        
        return ChatResponse(
            response=result,
            success=True,
            model_used=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            user_id=user_session.user_id
        )
        
    except UserConfirmationRequired as e:
        # Phase 4.4: ユーザー確認が必要な場合の処理
        logger.info(f"🤔 [確認プロセス] ユーザー確認が必要: {request.message}")
        
        # 確認レスポンスを生成
        confirmation_response = e.confirmation_context
        
        return ChatResponse(
            response=confirmation_response["response"],
            success=True,
            model_used=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            user_id=user_session.user_id,
            confirmation_required=True,
            confirmation_context=confirmation_response
        )
        
    except Exception as e:
        logger.error(f"❌ [統一ReActエージェント] 処理エラー: {str(e)}")
        logger.error(f"❌ [統一ReActエージェント] エラータイプ: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [統一ReActエージェント] トレースバック: {traceback.format_exc()}")
        return ChatResponse(
            response=f"申し訳ありません。処理中にエラーが発生しました: {str(e)}",
            success=False,
            model_used=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            user_id=user_session.user_id
        )


async def handle_chat_request(request: ChatRequest, auth_data) -> ChatResponse:
    """
    チャットリクエストを処理するメインハンドラー
    """
    try:
        logger.info(f"🔍 [CHAT_HANDLER] 処理開始")
        logger.info(f"🔍 [CHAT_HANDLER] リクエスト: {request.message}")
        logger.info(f"🔍 [CHAT_HANDLER] 認証データタイプ: {type(auth_data)}")
        
        current_user = auth_data["user"]
        raw_token = auth_data["raw_token"]
        
        logger.info(f"🔍 [CHAT_HANDLER] ユーザー情報取得完了: {current_user.email}")
        logger.info(f"🔍 [CHAT_HANDLER] トークン取得完了: {raw_token[:20]}...")
        
        # === セッション管理 ===
        logger.info(f"🔍 [CHAT_HANDLER] セッション管理開始")
        user_session = session_manager.get_or_create_session(current_user.id, raw_token)
        logger.info(f"📱 [セッション] セッションID: {user_session.session_id}")
        logger.info(f"📱 [セッション] 継続時間: {user_session.get_session_duration().total_seconds()/60:.1f}分")
        logger.info(f"📱 [セッション] 操作履歴: {len(user_session.operation_history)}件")
        logger.info(f"✅ [CHAT_HANDLER] セッション管理完了")
        
        logger.info(f"\n=== Morizo AI 統一ReActエージェント 開始 ===")
        logger.info(f"🔍 [観察] ユーザー入力: {request.message}")
        logger.info(f"   User: {current_user.email}")
        logger.info(f"   User ID: {current_user.id}")
        logger.info(f"   Session ID: {user_session.session_id}")
        
        # 統一されたReActエージェントで処理
        result = await process_with_unified_react(request, user_session, raw_token)
        
        logger.info(f"\n=== Morizo AI 統一ReActエージェント 完了 ===")
        logger.info(f"✅ [完了] レスポンス生成完了")
        logger.info(f"📊 [統計] セッション継続時間: {user_session.get_session_duration().total_seconds()/60:.1f}分")
        logger.info(f"📊 [統計] 操作履歴件数: {len(user_session.operation_history)}件")
        
        # 最終レスポンスをログに出力
        logger.info(f"✅ [レスポンス] {result.response}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ [ERROR] Chat processing error: {str(e)}")
        logger.error(f"❌ [ERROR] エラータイプ: {type(e).__name__}")
        import traceback
        logger.error(f"❌ [ERROR] トレースバック: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")
