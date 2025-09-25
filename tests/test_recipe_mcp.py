#!/usr/bin/env python3
"""
Recipe MCP Server テスト
generate_menu_plan_with_historyの動作確認
"""

import asyncio
import json
from typing import Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_recipe_mcp():
    """Recipe MCP Serverの動作をテスト"""
    
    print("🧪 Recipe MCP Server テスト開始")
    print("🔗 stdio接続でテストします")
    
    # 疎結合設計では認証トークンは不要
    print("\n✅ 疎結合設計: 認証トークンは不要です")
    
    # テスト実行の確認
    print("\n⚠️  このテストはOpenAI APIに接続します")
    print("以下の操作が実行されます:")
    print("  1. LLMによる献立タイトル生成")
    print("  2. 除外レシピの考慮")
    print("  3. 献立提案の生成")
    
    confirm = input("\n続行しますか？ (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ テストをキャンセルしました")
        return
    
    print("🚀 テストを開始します...")
    
    try:
        # stdio接続でMCPサーバーを自動起動
        server_params = StdioServerParameters(
            command="python",
            args=["recipe_mcp_server_stdio.py"]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # サーバー初期化
                await session.initialize()
                
                # テストケース1: 基本的な献立生成
                print("\n=== テストケース1: 基本的な献立生成 ===")
                test_inventory_1 = [
                    "牛乳", "卵", "パン", "バター", "ほうれん草", "胡麻", 
                    "豆腐", "わかめ", "味噌", "だし", "醤油", "酒"
                ]
                
                try:
                    result = await session.call_tool(
                        "generate_menu_plan_with_history",
                        arguments={
                            "inventory_items": test_inventory_1,
                            "excluded_recipes": ["フレンチトースト", "オムレツ", "ハンバーグ"],
                            "menu_type": "和食"
                        }
                    )
                    
                    response_data = json.loads(result.content[0].text)
                    print(f"✅ テストケース1 結果:")
                    print(f"   成功: {response_data.get('success', False)}")
                    
                    if response_data.get('success'):
                        data = response_data.get('data', {})
                        print(f"   主菜: {data.get('main_dish', {}).get('title', 'N/A')}")
                        print(f"   副菜: {data.get('side_dish', {}).get('title', 'N/A')}")
                        print(f"   味噌汁: {data.get('soup', {}).get('title', 'N/A')}")
                        print(f"   使用食材数: {len(data.get('ingredient_usage', {}).get('used', []))}")
                        print(f"   残り食材数: {len(data.get('ingredient_usage', {}).get('remaining', []))}")
                        print(f"   除外レシピ数: {len(data.get('excluded_recipes', []))}")
                        print(f"   代替案使用: {data.get('fallback_used', False)}")
                    else:
                        print(f"   エラー: {response_data.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    print(f"❌ テストケース1 エラー: {e}")
                
                # テストケース2: 限られた食材での献立生成
                print("\n=== テストケース2: 限られた食材での献立生成 ===")
                test_inventory_2 = [
                    "卵", "豆腐", "わかめ", "味噌", "だし", "醤油"
                ]
                
                try:
                    result = await session.call_tool(
                        "generate_menu_plan_with_history",
                        arguments={
                            "inventory_items": test_inventory_2,
                            "excluded_recipes": ["豆腐の卵とじ", "わかめの和え物"],
                            "menu_type": "和食"
                        }
                    )
                    
                    response_data = json.loads(result.content[0].text)
                    print(f"✅ テストケース2 結果:")
                    print(f"   成功: {response_data.get('success', False)}")
                    
                    if response_data.get('success'):
                        data = response_data.get('data', {})
                        print(f"   主菜: {data.get('main_dish', {}).get('title', 'N/A')}")
                        print(f"   副菜: {data.get('side_dish', {}).get('title', 'N/A')}")
                        print(f"   味噌汁: {data.get('soup', {}).get('title', 'N/A')}")
                        print(f"   使用食材数: {len(data.get('ingredient_usage', {}).get('used', []))}")
                        print(f"   残り食材数: {len(data.get('ingredient_usage', {}).get('remaining', []))}")
                    else:
                        print(f"   エラー: {response_data.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    print(f"❌ テストケース2 エラー: {e}")
                
                # テストケース3: 洋食での献立生成
                print("\n=== テストケース3: 洋食での献立生成 ===")
                test_inventory_3 = [
                    "鶏肉", "玉ねぎ", "にんにく", "トマト", "パスタ", 
                    "オリーブオイル", "バジル", "チーズ", "パン", "バター"
                ]
                
                try:
                    result = await session.call_tool(
                        "generate_menu_plan_with_history",
                        arguments={
                            "inventory_items": test_inventory_3,
                            "excluded_recipes": ["鶏肉とトマトのバジルソテー", "オニオンチーズトースト"],
                            "menu_type": "洋食"
                        }
                    )
                    
                    response_data = json.loads(result.content[0].text)
                    print(f"✅ テストケース3 結果:")
                    print(f"   成功: {response_data.get('success', False)}")
                    
                    if response_data.get('success'):
                        data = response_data.get('data', {})
                        print(f"   主菜: {data.get('main_dish', {}).get('title', 'N/A')}")
                        print(f"   副菜: {data.get('side_dish', {}).get('title', 'N/A')}")
                        print(f"   味噌汁: {data.get('soup', {}).get('title', 'N/A')}")
                        print(f"   使用食材数: {len(data.get('ingredient_usage', {}).get('used', []))}")
                        print(f"   残り食材数: {len(data.get('ingredient_usage', {}).get('remaining', []))}")
                    else:
                        print(f"   エラー: {response_data.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    print(f"❌ テストケース3 エラー: {e}")
                
                print("\n🎉 Recipe MCP Server テスト完了")
                
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Recipe MCP Server テスト")
    print("=" * 60)
    print("このテストは以下の機能を確認します:")
    print("  • generate_menu_plan_with_history: 献立生成（疎結合設計）")
    print("  • LLMによる献立タイトル生成")
    print("  • 除外レシピの考慮")
    print("  • 献立タイプ（和食・洋食）の対応")
    print("")
    print("⚠️  注意: OpenAI APIに接続します")
    print("   コストが発生する可能性があります")
    print("=" * 60)
    
    asyncio.run(test_recipe_mcp())
