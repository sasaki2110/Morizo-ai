#!/usr/bin/env python3
"""
トークン最適化のテスト
説明文短縮と関連ツールフィルタリングの効果を確認
"""

import asyncio
import logging
from agents.mcp_client import MCPClient
from action_planner import ActionPlanner
from openai import OpenAI
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_token_optimization")

async def test_token_optimization():
    """トークン最適化のテスト"""
    try:
        print("🔧 トークン最適化テスト開始")
        print("=" * 50)
        
        # 環境変数確認
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY環境変数が設定されていません")
            return
        
        print(f"✅ OpenAI API Key: {api_key[:10]}...")
        
        # OpenAIクライアント初期化
        openai_client = OpenAI(api_key=api_key)
        
        # ActionPlanner初期化
        planner = ActionPlanner(openai_client)
        
        # 利用可能なツール一覧
        available_tools = [
            "inventory_add",
            "inventory_list", 
            "inventory_get",
            "inventory_update_by_id",
            "inventory_delete_by_id",
            "inventory_update_by_name",
            "inventory_delete_by_name",
            "inventory_update_by_name_oldest",
            "inventory_update_by_name_latest"
        ]
        
        # テストケース
        test_cases = [
            {
                "request": "牛乳の数量を3本に変更して",
                "expected_tools": "update系ツールのみ",
                "description": "更新要求（FIFO関連）"
            },
            {
                "request": "新しい牛乳を追加して",
                "expected_tools": "add系ツールのみ", 
                "description": "追加要求"
            },
            {
                "request": "在庫一覧を確認して",
                "expected_tools": "list/get系ツールのみ",
                "description": "確認要求"
            },
            {
                "request": "古いパンを削除して",
                "expected_tools": "delete系ツールのみ",
                "description": "削除要求"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 テストケース {i}: {test_case['description']}")
            print(f"🔤 要求: {test_case['request']}")
            
            # 関連ツールフィルタリングテスト
            relevant_tools = planner._filter_relevant_tools(available_tools, test_case['request'])
            print(f"🔧 関連ツール: {len(relevant_tools)}/{len(available_tools)}個")
            print(f"📝 ツール一覧: {relevant_tools}")
            
            # 動的ツール説明取得テスト
            tools_description = await planner._get_tools_description(available_tools, test_case['request'])
            print(f"📊 説明文の長さ: {len(tools_description)}文字")
            
            # 説明文の内容確認（最初の100文字のみ表示）
            print(f"📝 説明文（最初の100文字）: {tools_description[:100]}...")
            
            # 実際のタスク分解テスト
            tasks = await planner.create_plan(test_case['request'], available_tools)
            print(f"📊 生成されたタスク数: {len(tasks)}")
            for j, task in enumerate(tasks):
                print(f"🔧 タスク {j+1}: {task.tool} - {task.description}")
            
            print("-" * 30)
        
        print("\n✅ トークン最適化テスト完了")
        
    except Exception as e:
        logger.error(f"❌ トークン最適化テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_token_optimization())
