#!/usr/bin/env python3
"""
Recipe MCP Server テスト
レシピ検索・献立生成機能の各ツール動作確認
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 環境変数を読み込み
load_dotenv()

async def test_recipe_mcp_tools():
    """Recipe MCP Serverの各ツール動作確認"""
    
    print("🧪 Recipe MCP Server ツール動作確認テスト開始")
    print("=" * 60)
    
    # 認証トークンの取得
    token = os.getenv("SUPABASE_ANON_KEY")
    if not token:
        print("❌ エラー: SUPABASE_ANON_KEY が設定されていません")
        print("💡 ヒント: .env ファイルに SUPABASE_ANON_KEY=your-token を追加してください")
        return False
    
    print(f"✅ 認証トークン取得完了: {token[:20]}...")
    print("=" * 60)
    
    try:
        # stdio接続でMCPサーバーを自動起動
        server_params = StdioServerParameters(
            command="python",
            args=["recipe_mcp_server_stdio.py"]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 初期化
                await session.initialize()
                
                print("✅ MCPサーバー接続成功")
                
                # 利用可能ツールの確認
                tools = await session.list_tools()
                print(f"📋 利用可能ツール: {len(tools.tools)}個")
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                print("\n" + "=" * 60)
                
                # テスト1: 献立生成（基本）
                print("🔍 テスト1: 献立生成（基本）")
                try:
                    result = await session.call_tool("generate_menu_plan_with_history", {
                        "inventory_items": ["卵", "牛乳", "パン"],
                        "excluded_recipes": []
                    })
                    print(f"✅ 献立生成成功")
                    print(f"📊 結果: {result.content}")
                except Exception as e:
                    print(f"❌ 献立生成失敗: {e}")
                
                print("\n" + "-" * 40)
                
                # テスト2: RAG検索（基本）
                print("🔍 テスト2: RAG検索（基本）")
                try:
                    result = await session.call_tool("search_recipe_from_rag", {
                        "query": "卵料理",
                        "max_results": 3,
                        "similarity_threshold": 0.2  # 0.3 → 0.2に下げる
                    })
                    print(f"✅ RAG検索成功")
                    print(f"📊 結果: {result.content}")
                except Exception as e:
                    print(f"❌ RAG検索失敗: {e}")
                
                print("\n" + "-" * 40)
                
                # テスト3: RAG検索（フィルタリング）
                print("🔍 テスト3: RAG検索（フィルタリング）")
                try:
                    result = await session.call_tool("search_recipe_from_rag", {
                        "query": "卵料理",
                        "max_results": 3,
                        "category_filter": "副菜",  # 主菜 → 副菜に変更
                        "include_ingredients": ["卵"],
                        "exclude_ingredients": ["肉"],
                        "similarity_threshold": 0.2  # 0.3 → 0.2に下げる
                    })
                    print(f"✅ RAG検索（フィルタリング）成功")
                    print(f"📊 結果: {result.content}")
                except Exception as e:
                    print(f"❌ RAG検索（フィルタリング）失敗: {e}")
                
                print("\n" + "-" * 40)
                
                # テスト4: Web検索（Perplexity API）
                print("🔍 テスト4: Web検索（Perplexity API）")
                try:
                    result = await session.call_tool("search_recipe_from_web", {
                        "query": "肉じゃが 作り方",
                        "max_results": 2
                    })
                    print(f"✅ Web検索成功")
                    print(f"📊 結果: {result.content}")
                except Exception as e:
                    print(f"❌ Web検索失敗: {e}")
                
                print("\n" + "-" * 40)
                
                # テスト5: 献立生成（在庫活用）
                print("🔍 テスト5: 献立生成（在庫活用）")
                try:
                    result = await session.call_tool("generate_menu_plan_with_history", {
                        "inventory_items": ["豚バラブロック", "ほうれん草", "玉ねぎ", "じゃがいも"],
                        "excluded_recipes": []
                    })
                    print(f"✅ 献立生成（在庫活用）成功")
                    print(f"📊 結果: {result.content}")
                except Exception as e:
                    print(f"❌ 献立生成（在庫活用）失敗: {e}")
                
                print("\n" + "=" * 60)
                print("🎉 Recipe MCP Server ツール動作確認テスト完了")
                
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_recipe_mcp_tools())
