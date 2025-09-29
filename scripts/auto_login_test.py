#!/usr/bin/env python3
"""
自動ログイン機能のテストスクリプト
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# .envファイルを読み込み
load_dotenv(os.path.join(project_root, '.env'))

from auth.auto_login import get_auto_token, refresh_auto_token

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_auto_login():
    """自動ログイン機能をテスト"""
    try:
        logger.info("🔐 自動ログイン機能テスト開始")
        
        # 環境変数チェック
        required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_EMAIL", "SUPABASE_PASSWORD"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"❌ 必要な環境変数が設定されていません: {missing_vars}")
            logger.info("💡 .envファイルに以下を設定してください:")
            for var in missing_vars:
                logger.info(f"   {var}=your_value_here")
            return False
        
        # 自動ログインでトークン取得
        token = get_auto_token()
        logger.info(f"✅ 自動ログイン成功: {token[:20]}...")
        
        # トークン更新テスト
        new_token = refresh_auto_token()
        logger.info(f"✅ トークン更新成功: {new_token[:20]}...")
        
        logger.info("🎉 自動ログイン機能テスト完了")
        return True
        
    except Exception as e:
        logger.error(f"❌ 自動ログイン機能テスト失敗: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_auto_login())
    sys.exit(0 if success else 1)
