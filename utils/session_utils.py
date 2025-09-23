"""
セッション関連のユーティリティ関数
"""

import logging
from session_manager import SessionContext
from agents.mcp_client import MCPClient

logger = logging.getLogger('morizo_ai.session_utils')

# グローバルMCPクライアントインスタンス
mcp_client = MCPClient()


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
