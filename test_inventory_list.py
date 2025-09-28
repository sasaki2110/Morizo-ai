#!/usr/bin/env python3
"""
inventory_list ツールの単体テスト
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('inventory_list_test')

async def test_inventory_list():
    """inventory_listツールの単体テスト"""
    
    logger.info("🧪 [単体テスト] inventory_list テスト開始")
    
    try:
        # MCPクライアントをインポート
        from agents.mcp_client import call_mcp_tool
        
        # 認証トークンを取得
        token = os.getenv("SUPABASE_ANON_KEY")
        if not token:
            logger.error("❌ [単体テスト] SUPABASE_ANON_KEYが見つかりません")
            return False
        
        logger.info(f"🔑 [単体テスト] 認証トークン取得: {token[:20]}...")
        
        # inventory_listを実行
        logger.info("📋 [単体テスト] inventory_listを実行")
        result = await call_mcp_tool("inventory_list", {"token": token})
        
        logger.info(f"📋 [単体テスト] inventory_list結果: {result}")
        
        if result.get("success"):
            data = result.get("data", [])
            logger.info(f"📋 [単体テスト] 取得した在庫: {len(data)}件")
            
            # 各アイテムを表示
            for i, item in enumerate(data):
                logger.info(f"📦 [単体テスト] アイテム {i+1}: {item.get('item_name')} - {item.get('quantity')}{item.get('unit')}")
            
            # 牛乳のアイテムを探す
            milk_items = [item for item in data if item.get("item_name") == "牛乳"]
            logger.info(f"🥛 [単体テスト] 牛乳のアイテム: {len(milk_items)}件")
            
            for i, item in enumerate(milk_items):
                logger.info(f"🥛 [単体テスト] 牛乳 {i+1}: {item}")
            
            logger.info("✅ [単体テスト] inventory_listは正常に動作しています")
            return True
        else:
            logger.error(f"❌ [単体テスト] inventory_list失敗: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ [単体テスト] 例外発生: {str(e)}")
        import traceback
        logger.error(f"❌ [単体テスト] トレースバック: {traceback.format_exc()}")
        return False

async def main():
    """メイン関数"""
    logger.info("🚀 [単体テスト] inventory_list 単体テスト開始")
    
    success = await test_inventory_list()
    
    if success:
        logger.info("✅ [単体テスト] テスト成功")
    else:
        logger.error("❌ [単体テスト] テスト失敗")
    
    logger.info("🏁 [単体テスト] テスト完了")

if __name__ == "__main__":
    asyncio.run(main())
