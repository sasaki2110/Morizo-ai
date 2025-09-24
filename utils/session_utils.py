"""
セッション関連のユーティリティ関数
"""

import logging
from session_manager import SessionContext
from agents.mcp_client import MCPClient

logger = logging.getLogger('morizo_ai.session_utils')

# グローバルMCPクライアントインスタンス
mcp_client = MCPClient()


