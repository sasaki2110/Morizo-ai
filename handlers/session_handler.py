"""
セッション管理ハンドラー
"""

import logging
from fastapi import FastAPI, HTTPException, Depends
from session_manager import session_manager
from auth.authentication import verify_token

logger = logging.getLogger('morizo_ai.session_handler')


def setup_session_routes(app: FastAPI):
    """セッション管理のルートを設定"""
    
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
            
            from agents.mcp_client import MCPClient
            mcp_client = MCPClient()
            
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
