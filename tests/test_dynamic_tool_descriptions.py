#!/usr/bin/env python3
"""
動的ツール説明取得のテスト
ActionPlannerがFastMCPから動的にツール説明を取得できるかテストする
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
logger = logging.getLogger("test_dynamic_tool_descriptions")

async def test_dynamic_tool_descriptions():
    """動的ツール説明取得のテスト"""
    try:
        print("🔧 動的ツール説明取得テスト開始")
        print("=" * 50)
        
        # 環境変数確認
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY環境変数が設定されていません")
            print("💡 .envファイルまたは環境変数を設定してください")
            return
        
        print(f"✅ OpenAI API Key: {api_key[:10]}...")
        
        # OpenAIクライアント初期化
        openai_client = OpenAI(api_key=api_key)
        
        # MCPクライアント単体テスト
        print("\n📋 MCPクライアント単体テスト:")
        mcp_client = MCPClient()
        tool_details = await mcp_client.get_tool_details()
        
        if tool_details:
            print(f"✅ MCPクライアント: {len(tool_details)}個のツール詳細を取得")
            for tool_name in ["inventory_update_by_name_oldest", "inventory_update_by_name_latest"]:
                if tool_name in tool_details:
                    print(f"✅ {tool_name}: 動的取得成功")
                else:
                    print(f"❌ {tool_name}: 見つかりません")
        else:
            print("❌ MCPクライアント: ツール詳細取得失敗")
            return
        
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
        
        print(f"📋 テスト対象ツール: {len(available_tools)}個")
        
        # 動的ツール説明取得テスト
        print("\n📋 動的ツール説明取得テスト:")
        tools_description = await planner._get_tools_description(available_tools)
        
        print(f"📊 取得した説明文の長さ: {len(tools_description)}文字")
        print("\n📝 取得したツール説明:")
        print("-" * 30)
        print(tools_description)
        print("-" * 30)
        
        # 新しいツール（FIFO関連）が含まれているかチェック
        fifo_tools = ["inventory_update_by_name_oldest", "inventory_update_by_name_latest"]
        for tool in fifo_tools:
            if tool in tools_description:
                print(f"✅ {tool} の説明が動的に取得されました")
            else:
                print(f"❌ {tool} の説明が見つかりません")
        
        # 実際のタスク分解テスト
        print("\n📋 タスク分解テスト:")
        test_request = "牛乳の数量を3本に変更して"
        tasks = await planner.create_plan(test_request, available_tools)
        
        print(f"📊 生成されたタスク数: {len(tasks)}")
        for i, task in enumerate(tasks):
            print(f"🔧 タスク {i+1}: {task.tool} - {task.description}")
        
        print("\n✅ 動的ツール説明取得テスト完了")
        
    except Exception as e:
        logger.error(f"❌ 動的ツール説明取得テストエラー: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_dynamic_tool_descriptions())
