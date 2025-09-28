#!/usr/bin/env python3
"""
inventory_list_by_name ツールの単体テスト
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
logger = logging.getLogger('inventory_test')

async def test_inventory_list_by_name():
    """inventory_list_by_nameツールの単体テスト"""
    
    logger.info("🧪 [単体テスト] inventory_list_by_name テスト開始")
    
    try:
        # MCPクライアントをインポート
        from agents.mcp_client import call_mcp_tool
        
        # 認証トークンを取得
        token = os.getenv("SUPABASE_ANON_KEY")
        if not token:
            logger.error("❌ [単体テスト] SUPABASE_ANON_KEYが見つかりません")
            return False
        
        logger.info(f"🔑 [単体テスト] 認証トークン取得: {token[:20]}...")
        
        # 1. 全在庫を確認
        logger.info("📋 [単体テスト] 1. 全在庫を確認")
        all_inventory_result = await call_mcp_tool("inventory_list", {"token": token})
        
        if all_inventory_result.get("success"):
            all_items = all_inventory_result.get("result", {}).get("data", [])
            logger.info(f"📋 [単体テスト] 全在庫: {len(all_items)}件")
            
            # 牛乳のアイテムを探す
            milk_items = [item for item in all_items if item.get("item_name") == "牛乳"]
            logger.info(f"🥛 [単体テスト] 牛乳のアイテム: {len(milk_items)}件")
            
            for i, item in enumerate(milk_items):
                logger.info(f"🥛 [単体テスト] 牛乳 {i+1}: {item}")
        else:
            logger.error(f"❌ [単体テスト] 全在庫取得失敗: {all_inventory_result.get('error')}")
            return False
        
        # 2. inventory_list_by_nameで牛乳を検索
        logger.info("🔍 [単体テスト] 2. inventory_list_by_nameで牛乳を検索")
        milk_result = await call_mcp_tool("inventory_list_by_name", {
            "token": token,
            "item_name": "牛乳"
        })
        
        logger.info(f"🔍 [単体テスト] inventory_list_by_name結果: {milk_result}")
        
        if milk_result.get("success"):
            milk_data = milk_result.get("result", {}).get("data", [])
            logger.info(f"🥛 [単体テスト] inventory_list_by_nameで取得した牛乳: {len(milk_data)}件")
            
            for i, item in enumerate(milk_data):
                logger.info(f"🥛 [単体テスト] 取得した牛乳 {i+1}: {item}")
        else:
            logger.error(f"❌ [単体テスト] inventory_list_by_name失敗: {milk_result.get('error')}")
            return False
        
        # 3. 結果の比較
        logger.info("📊 [単体テスト] 3. 結果の比較")
        if len(milk_items) == len(milk_data):
            logger.info("✅ [単体テスト] 結果一致: inventory_list_by_nameは正常に動作しています")
            return True
        else:
            logger.error(f"❌ [単体テスト] 結果不一致: 全在庫={len(milk_items)}件, inventory_list_by_name={len(milk_data)}件")
            return False
            
    except Exception as e:
        logger.error(f"❌ [単体テスト] 例外発生: {str(e)}")
        import traceback
        logger.error(f"❌ [単体テスト] トレースバック: {traceback.format_exc()}")
        return False

async def main():
    """メイン関数"""
    logger.info("🚀 [単体テスト] inventory_list_by_name 単体テスト開始")
    
    success = await test_inventory_list_by_name()
    
    if success:
        logger.info("✅ [単体テスト] テスト成功")
    else:
        logger.error("❌ [単体テスト] テスト失敗")
    
    logger.info("🏁 [単体テスト] テスト完了")

if __name__ == "__main__":
    asyncio.run(main())
