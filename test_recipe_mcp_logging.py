#!/usr/bin/env python3
"""
recipe_mcp_server_stdio.pyのロギング検証テスト
"""

import asyncio
import sys
import os
import logging
import json
from typing import List, Dict, Any

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

# プロジェクトのログ設定を使用
from config.logging_config import setup_logging

# ログ設定を初期化
logger = setup_logging()

async def test_generate_menu_with_llm_logging():
    """generate_menu_with_llmのロギング検証テスト"""
    logger.info("🧪 [ロギングテスト] generate_menu_with_llm 開始")
    
    try:
        # 必要なモジュールをモックしてインポート
        import importlib.util
        
        # fastmcpのモック
        class MockFastMCP:
            def tool(self, func):
                return func
        
        # モジュールを動的に読み込み
        spec = importlib.util.spec_from_file_location("recipe_mcp", "/app/Morizo-ai/recipe_mcp_server_stdio.py")
        recipe_mcp = importlib.util.module_from_spec(spec)
        
        # 依存関係をモック
        recipe_mcp.mcp = MockFastMCP()
        
        # OpenAIクライアントのモック
        recipe_mcp.openai_client = type('MockOpenAIClient', (), {
            'get_client': lambda: type('MockClient', (), {
                'chat': type('MockChat', (), {
                    'completions': type('MockCompletions', (), {
                        'create': lambda **kwargs: type('MockResponse', (), {
                            'choices': [type('MockChoice', (), {
                                'message': type('MockMessage', (), {
                                    'content': json.dumps({
                                        "candidates": [
                                            {
                                                "candidate_id": 1,
                                                "main_dish": {"title": "豚バラの煮込み", "ingredients": ["豚バラ", "玉ねぎ"]},
                                                "side_dish": {"title": "ほうれん草のごま和え", "ingredients": ["ほうれん草", "ごま"]},
                                                "soup": {"title": "味噌汁", "ingredients": ["豆腐", "わかめ"]}
                                            },
                                            {
                                                "candidate_id": 2,
                                                "main_dish": {"title": "鶏もも肉の照り焼き", "ingredients": ["鶏もも肉", "玉ねぎ"]},
                                                "side_dish": {"title": "キャベツのサラダ", "ingredients": ["キャベツ"]},
                                                "soup": {"title": "わかめスープ", "ingredients": ["わかめ"]}
                                            },
                                            {
                                                "candidate_id": 3,
                                                "main_dish": {"title": "牛すね肉の煮込み", "ingredients": ["牛すね肉", "人参"]},
                                                "side_dish": {"title": "もやしのナムル", "ingredients": ["もやし"]},
                                                "soup": {"title": "コンソメスープ", "ingredients": ["人参"]}
                                            }
                                        ]
                                    }, ensure_ascii=False)
                                })()
                            })]
                        })()
                    })()
                })()
            })()
        })()
        
        # ベクトル検索のモック
        recipe_mcp.get_vector_search = lambda: type('MockVectorSearch', (), {
            '_load_vector_db': lambda: None,
            'search_similar_recipes': lambda query, k: [
                {"title": "肉じゃが", "ingredients": ["豚肉", "じゃがいも", "玉ねぎ"]},
                {"title": "ほうれん草のおひたし", "ingredients": ["ほうれん草"]},
                {"title": "味噌汁", "ingredients": ["豆腐", "わかめ"]}
            ]
        })()
        
        # ログ設定のモック（プロジェクトのログ設定を使用）
        recipe_mcp.setup_logging = lambda: logger
        
        # モジュールを実行
        spec.loader.exec_module(recipe_mcp)
        
        # テストデータ
        inventory_items = ["ほうれん草", "豚バラブロック", "鶏もも肉", "牛すね肉", "もやし", "人参", "牛乳", "パン"]
        menu_type = "和食"
        excluded_recipes = []
        use_constraint_solver = True
        
        logger.info(f"📋 [ロギングテスト] パラメータ: 食材{len(inventory_items)}件, 制約解決={use_constraint_solver}")
        
        # 関数を直接呼び出し
        result = await recipe_mcp.generate_menu_with_llm(
            inventory_items=inventory_items,
            menu_type=menu_type,
            excluded_recipes=excluded_recipes,
            use_constraint_solver=use_constraint_solver
        )
        
        logger.info(f"✅ [ロギングテスト] generate_menu_with_llm 完了")
        logger.info(f"📊 [ロギングテスト] 結果: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ [ロギングテスト] generate_menu_with_llm エラー: {e}")
        import traceback
        logger.error(f"❌ [ロギングテスト] トレースバック: {traceback.format_exc()}")
        return None

async def test_generate_menu_with_rag_logging():
    """generate_menu_with_ragのロギング検証テスト"""
    logger.info("🧪 [ロギングテスト] generate_menu_with_rag 開始")
    
    try:
        # 必要なモジュールをモックしてインポート
        import importlib.util
        
        # fastmcpのモック
        class MockFastMCP:
            def tool(self, func):
                return func
        
        # モジュールを動的に読み込み
        spec = importlib.util.spec_from_file_location("recipe_mcp", "/app/Morizo-ai/recipe_mcp_server_stdio.py")
        recipe_mcp = importlib.util.module_from_spec(spec)
        
        # 依存関係をモック
        recipe_mcp.mcp = MockFastMCP()
        
        # OpenAIクライアントのモック
        recipe_mcp.openai_client = type('MockOpenAIClient', (), {
            'get_client': lambda: type('MockClient', (), {
                'chat': type('MockChat', (), {
                    'completions': type('MockCompletions', (), {
                        'create': lambda **kwargs: type('MockResponse', (), {
                            'choices': [type('MockChoice', (), {
                                'message': type('MockMessage', (), {
                                    'content': json.dumps({
                                        "selected_menu": {
                                            "main_dish": {"title": "肉じゃが", "ingredients": ["豚肉", "じゃがいも", "玉ねぎ"], "source": "RAG"},
                                            "side_dish": {"title": "キャベツのサラダ", "ingredients": ["キャベツ"], "source": "RAG"},
                                            "soup": {"title": "味噌汁", "ingredients": ["豆腐", "わかめ"], "source": "RAG"}
                                        },
                                        "constraint_check": {
                                            "ingredient_duplication": False,
                                            "inventory_compliance": True,
                                            "reasoning": "食材重複を回避した最適な組み合わせを選択"
                                        }
                                    }, ensure_ascii=False)
                                })()
                            })]
                        })()
                    })()
                })()
            })()
        })()
        
        # ベクトル検索のモック
        recipe_mcp.get_vector_search = lambda: type('MockVectorSearch', (), {
            '_load_vector_db': lambda: None,
            'search_similar_recipes': lambda query, k: [
                {"title": "肉じゃが", "ingredients": ["豚肉", "じゃがいも", "玉ねぎ"]},
                {"title": "ほうれん草のおひたし", "ingredients": ["ほうれん草"]},
                {"title": "味噌汁", "ingredients": ["豆腐", "わかめ"]}
            ]
        })()
        
        # ログ設定のモック（プロジェクトのログ設定を使用）
        recipe_mcp.setup_logging = lambda: logger
        
        # モジュールを実行
        spec.loader.exec_module(recipe_mcp)
        
        # テストデータ
        inventory_items = ["ほうれん草", "豚バラブロック", "鶏もも肉", "牛すね肉", "もやし", "人参", "牛乳", "パン"]
        menu_type = "和食"
        excluded_recipes = []
        max_results = 3
        use_constraint_solver = True
        
        logger.info(f"📋 [ロギングテスト] パラメータ: 食材{len(inventory_items)}件, 制約解決={use_constraint_solver}")
        
        # 関数を直接呼び出し
        result = await recipe_mcp.generate_menu_with_rag(
            inventory_items=inventory_items,
            menu_type=menu_type,
            excluded_recipes=excluded_recipes,
            max_results=max_results,
            use_constraint_solver=use_constraint_solver
        )
        
        logger.info(f"✅ [ロギングテスト] generate_menu_with_rag 完了")
        logger.info(f"📊 [ロギングテスト] 結果: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ [ロギングテスト] generate_menu_with_rag エラー: {e}")
        import traceback
        logger.error(f"❌ [ロギングテスト] トレースバック: {traceback.format_exc()}")
        return None

async def main():
    """メインテスト関数"""
    logger.info("🚀 [recipe_mcpロギングテスト] 開始")
    
    # テスト1: generate_menu_with_llm
    logger.info("=" * 50)
    logger.info("🧪 [ロギングテスト1] generate_menu_with_llm")
    logger.info("=" * 50)
    result1 = await test_generate_menu_with_llm_logging()
    
    # テスト2: generate_menu_with_rag
    logger.info("=" * 50)
    logger.info("🧪 [ロギングテスト2] generate_menu_with_rag")
    logger.info("=" * 50)
    result2 = await test_generate_menu_with_rag_logging()
    
    # 結果サマリー
    logger.info("=" * 50)
    logger.info("📊 [ロギングテスト結果サマリー]")
    logger.info("=" * 50)
    logger.info(f"✅ generate_menu_with_llm: {'成功' if result1 else '失敗'}")
    logger.info(f"✅ generate_menu_with_rag: {'成功' if result2 else '失敗'}")
    
    if result1:
        logger.info(f"📝 LLM生成結果: {result1.get('main_dish', {}).get('title', 'N/A')}")
        logger.info(f"📝 制約満足: {result1.get('constraint_satisfied', 'N/A')}")
    
    if result2:
        logger.info(f"📝 RAG検索結果: {result2.get('main_dish', {}).get('title', 'N/A')}")
        logger.info(f"📝 制約満足: {result2.get('constraint_satisfied', 'N/A')}")
    
    logger.info("🎉 [recipe_mcpロギングテスト] 完了")
    logger.info("📝 [ロギングテスト] morizo_ai.logにログが出力されているか確認してください")

if __name__ == "__main__":
    asyncio.run(main())
