#!/usr/bin/env python3
"""
Morizo AI - Recipe MCP Server
Copyright (c) 2024 Morizo AI Project. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, modification,
distribution, or use is strictly prohibited without explicit written permission.

For licensing inquiries, contact: [contact@morizo-ai.com]

Recipe MCP Server (stdio transport)
レシピ提案機能用のMCPサーバー（アノテーション方式、stdio接続）
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI

# LangChain関連のインポート（RAG検索用）
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# Perplexity API関連のインポート
from utils.perplexity_client import PerplexityAPIClient, RecipeSearchResult

# 環境変数の読み込み
load_dotenv()

# FastMCPロゴを非表示にする（環境変数で制御）
os.environ["FASTMCP_DISABLE_BANNER"] = "1"

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MCPサーバーの初期化
mcp = FastMCP("Recipe Suggestion Server")

class OpenAIClient:
    """OpenAIクライアントのラッパークラス"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be set in .env")
        self._client: Optional[AsyncOpenAI] = None

    def get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

# グローバルクライアントインスタンス
openai_client = OpenAIClient()

class RecipeVectorSearch:
    """レシピベクトル検索クラス"""
    
    def __init__(self, vector_db_path: str):
        """
        初期化
        
        Args:
            vector_db_path: ベクトルDBのパス
        """
        self.vector_db_path = vector_db_path
        self.vectorstore = None
        self.embeddings = None
        
    def _load_vector_db(self):
        """ベクトルDBを読み込む"""
        try:
            logger.info(f"ベクトルDB読み込み中: {self.vector_db_path}")
            
            # OpenAI Embeddingsの初期化
            self.embeddings = OpenAIEmbeddings()
            
            # ChromaDBベクトルストアを読み込み
            self.vectorstore = Chroma(
                persist_directory=self.vector_db_path,
                embedding_function=self.embeddings
            )
            
            logger.info("ベクトルDB読み込み完了")
            
        except Exception as e:
            logger.error(f"ベクトルDB読み込みエラー: {e}")
            raise
    
    def search_similar_recipes(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        類似レシピを検索
        
        Args:
            query: 検索クエリ
            k: 取得する件数
            
        Returns:
            検索結果のリスト
        """
        try:
            if self.vectorstore is None:
                self._load_vector_db()
            
            logger.info(f"レシピ検索: '{query}' (上位{k}件)")
            
            # 類似度検索を実行
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            
            # 結果を整形
            formatted_results = []
            for i, (doc, score) in enumerate(results, 1):
                # メタデータから情報を取得
                metadata = doc.metadata
                
                # テキストからレシピタイトルを抽出（最初の行をタイトルとする）
                text_lines = doc.page_content.split('\n')
                title = text_lines[0] if text_lines else "Unknown"
                
                formatted_result = {
                    "rank": i,
                    "title": title,
                    "category": metadata.get("recipe_category", "不明"),
                    "main_ingredients": metadata.get("main_ingredients", ""),
                    "similarity_score": round(score, 4),
                    "text_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                }
                formatted_results.append(formatted_result)
            
            logger.info(f"検索結果: {len(formatted_results)}件")
            return formatted_results
            
        except Exception as e:
            logger.error(f"レシピ検索エラー: {e}")
            raise

# グローバルインスタンス
vector_search = None
perplexity_client = None

def get_vector_search():
    """ベクトル検索インスタンスを取得（遅延初期化）"""
    global vector_search
    if vector_search is None:
        vector_db_path = "/app/Morizo-ai/recipe_vector_db"
        vector_search = RecipeVectorSearch(vector_db_path)
    return vector_search

def get_perplexity_client():
    """Perplexity API クライアントを取得（遅延初期化）"""
    global perplexity_client
    if perplexity_client is None:
        perplexity_client = PerplexityAPIClient()
    return perplexity_client

# Pydanticモデル定義（シンプル化）
class MenuPlan(BaseModel):
    main_dish: Dict[str, Any]
    side_dish: Dict[str, Any]
    soup: Dict[str, Any]
    excluded_recipes: List[str] = []

# 食材分類関数を削除（AIネイティブアプローチでは不要）

# get_recent_recipes関数を削除（疎結合設計では外部から受け取る）

async def generate_menu_with_llm(
    inventory_items: List[str],
    menu_type: str,
    excluded_recipes: List[str]
) -> Dict[str, Any]:
    """LLMを使って献立を生成（AIネイティブアプローチ）"""
    try:
        client = openai_client.get_client()
        
        # シンプルなプロンプト（食材を丸投げ）
        prompt = f"""
あなたは料理の専門家です。在庫食材から3品構成の献立（主菜・副菜・汁物）を提案してください。

【在庫食材】
{', '.join(inventory_items)}

【献立タイプ】: {menu_type}

【制約条件】
1. 各料理で同じ食材を使用しない（調味料は除く）
2. 過去のレシピを避ける: {', '.join(excluded_recipes)}
3. 在庫食材を最大活用する
4. 実用的で美味しい献立にする

【出力形式】
JSON形式で以下の構造で回答してください：
{{
    "main_dish": {{
        "title": "レシピタイトル",
        "ingredients": ["食材1", "食材2", "食材3"]
    }},
    "side_dish": {{
        "title": "レシピタイトル", 
        "ingredients": ["食材1", "食材2", "食材3"]
    }},
    "soup": {{
        "title": "レシピタイトル",
        "ingredients": ["食材1", "食材2", "食材3"]
    }}
}}
"""

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "あなたは料理の専門家です。在庫食材から実用的で美味しい献立を提案してください。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        content = response.choices[0].message.content
        logger.info(f"LLM応答: {content}")
        
        # JSON解析（マークダウンのコードブロックを除去）
        try:
            # コードブロック（```json ... ```）を除去
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()
            
            menu_data = json.loads(content)
            logger.info(f"JSON解析後の献立データ: {menu_data}")
            return menu_data
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析エラー: {e}")
            logger.error(f"解析対象テキスト: {content}")
            raise
        
    except Exception as e:
        logger.error(f"LLM献立生成エラー: {e}")
        raise

async def generate_menu_with_rag(
    inventory_items: List[str],
    menu_type: str,
    excluded_recipes: List[str],
    max_results: int = 3
) -> Dict[str, Any]:
    """RAG検索を使って献立を生成（伝統的アプローチ）"""
    try:
        # ベクトル検索インスタンスを取得
        vector_search = get_vector_search()
        vector_search._load_vector_db()  # ベクトルDBを読み込み
        
        # 在庫食材から検索クエリを生成
        rag_query = f"{menu_type} {' '.join(inventory_items[:5])} 献立 主菜 副菜 汁物"
        logger.info(f"🔍 [RAG献立] 検索クエリ生成: '{rag_query}'")
        
        # ベクトル検索実行
        search_results = vector_search.search_similar_recipes(rag_query, k=max_results * 3)
        
        logger.info(f"🔍 [RAG献立] ベクトル検索結果: {len(search_results)}件")
        
        # 検索結果から献立タイトルを抽出
        rag_titles = []
        for result in search_results:
            title = result.get("title", "レシピ")
            rag_titles.append(title)
            logger.info(f"🔍 [RAG献立] 発見: {title}")
        
        # 献立タイトルから主菜・副菜・汁物を分類
        main_dish_titles = [t for t in rag_titles if any(keyword in t for keyword in ["肉", "魚", "鶏", "豚", "牛", "カレー", "ハンバーグ", "唐揚げ"])]
        side_dish_titles = [t for t in rag_titles if any(keyword in t for keyword in ["サラダ", "和え物", "おひたし", "炒め物", "煮物"])]
        soup_titles = [t for t in rag_titles if any(keyword in t for keyword in ["汁", "スープ", "味噌汁", "豚汁"])]
        
        # デフォルト値の設定
        if not main_dish_titles:
            main_dish_titles = ["肉じゃが"]
        if not side_dish_titles:
            side_dish_titles = ["ほうれん草のおひたし"]
        if not soup_titles:
            soup_titles = ["味噌汁"]
        
        # 献立データ構築
        menu_data = {
            "main_dish": {
                "title": main_dish_titles[0],
                "ingredients": inventory_items[:3]  # 在庫から適当に選択
            },
            "side_dish": {
                "title": side_dish_titles[0],
                "ingredients": inventory_items[3:6] if len(inventory_items) > 3 else inventory_items[:3]
            },
            "soup": {
                "title": soup_titles[0],
                "ingredients": inventory_items[6:9] if len(inventory_items) > 6 else inventory_items[:3]
            }
        }
        
        logger.info(f"✅ [RAG献立] 生成完了: 主菜={menu_data['main_dish']['title']}")
        return menu_data
        
    except Exception as e:
        logger.error(f"❌ [RAG献立] 生成エラー: {e}")
        # フォールバック: デフォルト献立
        return {
            "main_dish": {"title": "肉じゃが", "ingredients": inventory_items[:3]},
            "side_dish": {"title": "ほうれん草のおひたし", "ingredients": inventory_items[3:6] if len(inventory_items) > 3 else inventory_items[:3]},
            "soup": {"title": "味噌汁", "ingredients": inventory_items[6:9] if len(inventory_items) > 6 else inventory_items[:3]}
        }

# 食材重複チェックと使用状況計算関数を削除（AIネイティブアプローチでは不要）

# MCPツール定義
@mcp.tool()
async def generate_menu_plan_with_history(
    inventory_items: List[str],
    excluded_recipes: List[str],
    menu_type: str = "和食"
) -> Dict[str, Any]:
    """在庫食材から献立構成を生成（疎結合設計）
    
    🎯 使用場面: 在庫食材から過去履歴を考慮した献立を提案する場合
    
    📋 パラメータ:
    - inventory_items: 在庫食材リスト
    - excluded_recipes: 除外する過去レシピのリスト
    - menu_type: 献立のタイプ（和食・洋食・中華）
    
    📋 JSON形式:
    {
        "success": true,
        "data": {
            "main_dish": {
                "title": "牛乳と卵のフレンチトースト",
                "ingredients": ["牛乳", "卵", "パン", "バター"]
            },
            "side_dish": {
                "title": "ほうれん草の胡麻和え",
                "ingredients": ["ほうれん草", "胡麻", "醤油"]
            },
            "soup": {
                "title": "白菜とハムのクリームスープ",
                "ingredients": ["白菜", "ハム", "牛乳", "バター", "小麦粉"]
            },
            "excluded_recipes": ["フレンチトースト", "オムレツ"]
        }
    }
    """
    try:
        logger.info(f"献立生成開始: 食材{len(inventory_items)}件, 除外レシピ{len(excluded_recipes)}件")
        
        # LLMによる献立生成（AIネイティブアプローチ）
        menu_data = await generate_menu_with_llm(
            inventory_items, 
            menu_type, 
            excluded_recipes
        )
        
        # レスポンス構築（シンプル化）
        response_data = {
            "main_dish": menu_data.get("main_dish", {}),
            "side_dish": menu_data.get("side_dish", {}),
            "soup": menu_data.get("soup", {}),
            "excluded_recipes": excluded_recipes
        }
        
        logger.info(f"献立生成完了: 主菜={response_data['main_dish'].get('title', 'N/A')}")
        
        return {
            "success": True,
            "data": response_data
        }
        
    except Exception as e:
        logger.error(f"献立生成エラー: {e}")
        return {
            "success": False,
            "error": f"献立生成エラー: {str(e)}"
        }

@mcp.tool()
async def search_menu_from_rag_with_history(
    inventory_items: List[str],
    excluded_recipes: List[str] = None,
    menu_type: str = "和食",
    max_results: int = 3,
    token: str = None
) -> Dict[str, Any]:
    """在庫食材からRAG検索で献立タイトルを生成（責任分離設計）
    
    🎯 使用場面: 在庫食材からRAG検索で伝統的な献立タイトルを提案する場合
    
    📋 パラメータ:
    - inventory_items: 在庫食材リスト
    - excluded_recipes: 除外する過去レシピのリスト
    - menu_type: 献立のタイプ（和食・洋食・中華）
    - max_results: 取得する最大件数（デフォルト: 3）
    
    📋 JSON形式:
    {
        "success": true,
        "data": {
            "main_dish": {
                "title": "肉じゃが",
                "ingredients": ["豚肉", "じゃがいも", "人参", "玉ねぎ"]
            },
            "side_dish": {
                "title": "ほうれん草のおひたし",
                "ingredients": ["ほうれん草", "醤油", "だし"]
            },
            "soup": {
                "title": "味噌汁",
                "ingredients": ["味噌", "豆腐", "わかめ"]
            },
            "excluded_recipes": []
        }
    }
    """
    try:
        logger.info(f"🔍 [RAG献立] 検索開始: 食材{len(inventory_items)}件")
        
        # RAG検索で献立タイトルを生成
        menu_data = await generate_menu_with_rag(
            inventory_items, 
            menu_type, 
            excluded_recipes or [],
            max_results
        )
        
        # レスポンス構築
        response_data = {
            "main_dish": menu_data.get("main_dish", {}),
            "side_dish": menu_data.get("side_dish", {}),
            "soup": menu_data.get("soup", {}),
            "excluded_recipes": excluded_recipes or []
        }
        
        logger.info(f"✅ [RAG献立] 検索完了: 主菜={response_data['main_dish'].get('title', 'N/A')}")
        
        return {
            "success": True,
            "data": response_data
        }
        
    except Exception as e:
        logger.error(f"❌ [RAG献立] 検索エラー: {e}")
        return {
            "success": False,
            "error": f"RAG献立検索エラー: {str(e)}"
        }

@mcp.tool()
async def search_recipe_from_rag(
    query: str,
    max_results: int = 5,
    category_filter: str = None,
    include_ingredients: List[str] = None,
    exclude_ingredients: List[str] = None,
    similarity_threshold: float = 0.3
) -> Dict[str, Any]:
    """RAG検索によるレシピ検索（高度版）
    
    🎯 使用場面: レシピタイトルや食材から類似レシピを検索する場合
    
    📋 パラメータ:
    - query: 検索クエリ（例: "牛乳と卵", "フレンチトースト", "肉じゃが"）
    - max_results: 取得する最大件数（デフォルト: 5）
    - category_filter: カテゴリフィルタ（例: "主菜", "副菜", "汁物"）
    - include_ingredients: 含める食材リスト（例: ["卵", "牛乳"]）
    - exclude_ingredients: 除外する食材リスト（例: ["肉", "魚"]）
    - similarity_threshold: 類似度閾値（0.0-1.0、デフォルト: 0.3）
    
    📋 JSON形式:
    {
        "success": true,
        "data": {
            "query": "牛乳と卵",
            "filters": {
                "category": "主菜",
                "include_ingredients": ["卵", "牛乳"],
                "exclude_ingredients": ["肉"],
                "similarity_threshold": 0.3
            },
            "total_found": 3,
            "recipes": [
                {
                    "rank": 1,
                    "title": "牛乳と卵のフレンチトースト",
                    "category": "主菜",
                    "main_ingredients": "卵",
                    "similarity_score": 0.1234,
                    "text_preview": "牛乳と卵のフレンチトースト 牛乳 卵 パン バター..."
                }
            ]
        }
    }
    """
    try:
        logger.info(f"RAG検索開始: '{query}' (最大{max_results}件)")
        logger.info(f"フィルタ: カテゴリ={category_filter}, 含める食材={include_ingredients}, 除外食材={exclude_ingredients}, 閾値={similarity_threshold}")
        
        # ベクトル検索インスタンスを取得
        vector_search = get_vector_search()
        
        # クエリを拡張（含める食材がある場合）
        enhanced_query = query
        if include_ingredients:
            ingredient_query = " ".join(include_ingredients)
            enhanced_query = f"{query} {ingredient_query}"
            logger.info(f"クエリ拡張: '{query}' → '{enhanced_query}'")
        
        # 検索戦略の動的調整
        if include_ingredients or exclude_ingredients:
            search_k = max(max_results * 5, 50)  # 食材フィルタがある場合は多めに
        else:
            search_k = max(max_results * 2, 15)  # 通常は少なめに
        
        logger.info(f"検索戦略: k={search_k} (フィルタ条件: 含める={bool(include_ingredients)}, 除外={bool(exclude_ingredients)})")
        
        # 類似レシピを検索
        results = vector_search.search_similar_recipes(enhanced_query, k=search_k)
        
        # フィルタリング処理
        filtered_results = []
        for result in results:
            # 類似度閾値チェック
            if result["similarity_score"] < similarity_threshold:
                continue
                
            # カテゴリフィルタ
            if category_filter and result["category"] != category_filter:
                continue
                
            # 含める食材チェック（柔軟化）
            if include_ingredients:
                main_ingredients = result["main_ingredients"].lower()
                text_preview = result["text_preview"].lower()
                
                # main_ingredientsまたはtext_previewに食材が含まれているかチェック
                ingredient_found = False
                for ingredient in include_ingredients:
                    ingredient_lower = ingredient.lower()
                    if (ingredient_lower in main_ingredients or 
                        ingredient_lower in text_preview):
                        ingredient_found = True
                        break
                
                if not ingredient_found:
                    continue
                    
            # 除外食材チェック（柔軟化）
            if exclude_ingredients:
                main_ingredients = result["main_ingredients"].lower()
                text_preview = result["text_preview"].lower()
                
                # main_ingredientsまたはtext_previewに除外食材が含まれているかチェック
                excluded_found = False
                for ingredient in exclude_ingredients:
                    ingredient_lower = ingredient.lower()
                    if (ingredient_lower in main_ingredients or 
                        ingredient_lower in text_preview):
                        excluded_found = True
                        break
                
                if excluded_found:
                    continue
                    
            # フィルタを通過した結果を追加
            filtered_results.append(result)
            
            # 最大件数に達したら終了
            if len(filtered_results) >= max_results:
                break
        
        # ランキングを再設定
        for i, result in enumerate(filtered_results, 1):
            result["rank"] = i
        
        # レスポンス構築
        response_data = {
            "query": query,
            "filters": {
                "category": category_filter,
                "include_ingredients": include_ingredients,
                "exclude_ingredients": exclude_ingredients,
                "similarity_threshold": similarity_threshold
            },
            "total_found": len(filtered_results),
            "recipes": filtered_results
        }
        
        logger.info(f"RAG検索完了: {len(filtered_results)}件のレシピを発見（フィルタ適用後）")
        
        return {
            "success": True,
            "data": response_data
        }
        
    except Exception as e:
        logger.error(f"RAG検索エラー: {e}")
        return {
            "success": False,
            "error": f"RAG検索エラー: {str(e)}"
        }

@mcp.tool()
async def search_recipe_from_web(
    menu_titles: List[str],
    max_results: int = 3
) -> Dict[str, Any]:
    """Web検索によるレシピ検索（責任分離設計）
    
    🎯 使用場面: 献立タイトルからレシピURLを取得する場合
    
    📋 パラメータ:
    - menu_titles: 献立タイトルの配列（例: ["肉じゃが", "ほうれん草のおひたし", "味噌汁"]）
    - max_results: 取得する最大件数（デフォルト: 3）
    
    📋 JSON形式:
    {
        "success": true,
        "data": {
            "query": "肉じゃが 作り方",
            "total_found": 3,
            "recipes": [
                {
                    "title": "基本の肉じゃが",
                    "url": "https://cookpad.com/recipe/123456",
                    "source": "クックパッド",
                    "ingredients": ["じゃがいも", "玉ねぎ", "牛肉", "だし汁"],
                    "instructions": "1. じゃがいもを一口大に切る...",
                    "cooking_time": "30分",
                    "servings": "4人分"
                }
            ]
        }
    }
    """
    try:
        # パラメータの検証
        if not menu_titles:
            return {
                "success": False,
                "error": "menu_titlesパラメータが必要です"
            }
        
        # 献立タイトルから検索クエリを生成
        queries = [f"{title} 作り方" for title in menu_titles]
        
        logger.info(f"🔍 [Web検索] 開始: {len(queries)}個の献立タイトル (最大{max_results}件/タイトル)")
        
        # Perplexity API クライアントを取得
        client = get_perplexity_client()
        
        # 全クエリの結果を格納
        all_recipes = []
        
        # 各献立タイトルで個別に検索
        for i, (menu_title, single_query) in enumerate(zip(menu_titles, queries)):
            logger.info(f"🔍 [Web検索] {i+1}/{len(queries)}: '{menu_title}' -> '{single_query}'")
            
            try:
                # レシピ検索を実行（タイムアウト処理付き）
                import asyncio
                recipes = await asyncio.wait_for(
                    asyncio.to_thread(client.search_recipe, single_query, max_results=max_results),
                    timeout=30.0  # 30秒でタイムアウト
                )
                
                # 結果に献立タイトル情報を追加
                for recipe in recipes:
                    recipe_data = {
                        "menu_title": menu_title,
                        "query": single_query,
                        "title": recipe.title,
                        "url": recipe.url,
                        "source": recipe.source,
                        "ingredients": recipe.ingredients,
                        "instructions": recipe.instructions,
                        "cooking_time": recipe.cooking_time,
                        "servings": recipe.servings,
                        "snippet": recipe.snippet
                    }
                    all_recipes.append(recipe_data)
                
                logger.info(f"✅ [Web検索] {i+1} 完了: {len(recipes)}件のレシピを発見")
                
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ [Web検索] {i+1} タイムアウト: '{menu_title}' (30秒)")
                # タイムアウトした献立タイトルの結果を追加
                all_recipes.append({
                    "menu_title": menu_title,
                    "query": single_query,
                    "title": f"{menu_title} (検索タイムアウト)",
                    "url": "",
                    "source": "エラー",
                    "ingredients": [],
                    "instructions": "検索がタイムアウトしました。しばらく時間をおいて再実行してください。",
                    "cooking_time": "",
                    "servings": "",
                    "snippet": ""
                })
            except Exception as e:
                logger.error(f"❌ [Web検索] {i+1} エラー: {e}")
                # エラーが発生した献立タイトルの結果を追加
                all_recipes.append({
                    "menu_title": menu_title,
                    "query": single_query,
                    "title": f"{menu_title} (検索エラー)",
                    "url": "",
                    "source": "エラー",
                    "ingredients": [],
                    "instructions": f"検索エラー: {str(e)}",
                    "cooking_time": "",
                    "servings": "",
                    "snippet": ""
                })
        
        # レスポンス構築
        response_data = {
            "menu_titles": menu_titles,
            "queries": queries,
            "total_titles": len(menu_titles),
            "total_found": len(all_recipes),
            "recipes": all_recipes
        }
        
        logger.info(f"✅ [Web検索] 完了: {len(all_recipes)}件のレシピを発見")
        
        return {
            "success": True,
            "data": response_data
        }
        
    except Exception as e:
        logger.error(f"Web検索エラー: {e}")
        return {
            "success": False,
            "error": f"Web検索エラー: {str(e)}"
        }

# RAG検索実行（オプション） - ベクトル検索を使用
        if rag_search and inventory_items:
            logger.info(f"🔍 [並列提示] RAG検索開始: {inventory_items}")
            
            try:
                # ベクトル検索インスタンスを取得
                vector_search = get_vector_search()
                vector_search._load_vector_db()  # ベクトルDBを読み込み
                
                # 在庫食材から検索クエリを生成
                rag_query = f"{' '.join(inventory_items)} レシピ"
                logger.info(f"🔍 [RAG検索] 検索クエリ生成: '{rag_query}'")
                logger.info(f"🔍 [RAG検索] 検索パラメータ: k={max_results * 3}, inventory_items={inventory_items[:5]}...")
                
                # ベクトル検索実行
                search_results = vector_search.search_similar_recipes(rag_query, k=max_results * 3)
                
                logger.info(f"🔍 [RAG検索] ベクトル検索結果: {len(search_results)}件")
                if search_results:
                    logger.info(f"🔍 [RAG検索] 最初の3件のタイトル: {[result.get('title', 'N/A') for result in search_results[:3]]}")
                
                rag_recipes = []
                if search_results:
                    rag_titles = []
                    for result in search_results:
                        title = result.get("title", "レシピ")
                        rag_titles.append(title)
                    
                    # RAG検索で取得したタイトルにWeb検索を実行
                    if rag_titles:
                        logger.info(f"🔍 [並列提示] RAGタイトルをWeb検索: {rag_titles}")
                        for title in rag_titles:
                            try:
                                web_recipes = await asyncio.wait_for(
                                    asyncio.to_thread(perplexity_client.search_recipe, f"{title} 作り方", max_results=max_results),
                                    timeout=30.0
                                )
                                
                                for recipe in web_recipes:
                                    recipe_data = {
                                        "title": recipe.title,
                                        "url": recipe.url,
                                        "source": recipe.source,
                                        "ingredients": recipe.ingredients,
                                        "instructions": recipe.instructions,
                                        "cooking_time": recipe.cooking_time,
                                        "servings": recipe.servings,
                                        "snippet": recipe.snippet
                                    }
                                    rag_recipes.append(recipe_data)
                                
                                logger.info(f"✅ [並列提示] RAGタイトル '{title}' のWeb検索完了: {len(web_recipes)}件")
                                
                            except asyncio.TimeoutError:
                                logger.warning(f"⚠️ [並列提示] RAGタイトル '{title}' のWeb検索タイムアウト")
                            except Exception as e:
                                logger.error(f"❌ [並列提示] RAGタイトル '{title}' のWeb検索エラー: {e}")
                
                results["rag_recipes"] = rag_recipes
                logger.info(f"✅ [並列提示] RAG検索完了: {len(rag_recipes)}件")
                
            except Exception as e:
                logger.error(f"❌ [並列提示] RAG検索エラー: {e}")
                results["rag_recipes"] = []

@mcp.tool()
async def search_recipe_integrated(
    query: str,
    max_results: int = 5,
    rag_weight: float = 0.6,
    web_weight: float = 0.4
) -> Dict[str, Any]:
    """統合レシピ検索（RAG検索 + Web検索）
    
    🎯 使用場面: RAG検索とWeb検索を組み合わせて最適なレシピを提案する場合
    
    📋 パラメータ:
    - query: 検索クエリ（例: "肉じゃが 作り方", "フレンチトースト レシピ"）
    - max_results: 取得する最大件数（デフォルト: 5）
    - rag_weight: RAG検索結果の重み（デフォルト: 0.6）
    - web_weight: Web検索結果の重み（デフォルト: 0.4）
    
    📋 JSON形式:
    {
        "success": true,
        "data": {
            "query": "肉じゃが 作り方",
            "total_found": 5,
            "rag_results": 3,
            "web_results": 2,
            "recipes": [
                {
                    "rank": 1,
                    "title": "基本の肉じゃが",
                    "source": "rag",
                    "similarity_score": 0.85,
                    "url": null,
                    "ingredients": ["じゃがいも", "玉ねぎ", "牛肉", "だし汁"],
                    "cooking_time": "30分",
                    "servings": "4人分"
                }
            ]
        }
    }
    """
    try:
        logger.info(f"統合検索開始: '{query}' (最大{max_results}件, RAG重み:{rag_weight}, Web重み:{web_weight})")
        
        # 1. RAG検索実行
        rag_results = await search_recipe_from_rag(
            query=query,
            max_results=max_results * 2,  # 多めに取得してフィルタリング用
            similarity_threshold=0.2
        )
        
        # 2. Web検索実行
        web_results = await search_recipe_from_web(
            query=query,
            max_results=max_results * 2  # 多めに取得してフィルタリング用
        )
        
        # 3. 結果の統合
        integrated_recipes = []
        
        # RAG結果の処理
        if rag_results.get("success") and rag_results.get("data", {}).get("recipes"):
            for recipe in rag_results["data"]["recipes"]:
                integrated_recipe = {
                    "title": recipe.get("title", ""),
                    "source": "rag",
                    "similarity_score": recipe.get("similarity_score", 0.0),
                    "url": None,
                    "ingredients": recipe.get("main_ingredients", "").split(", ") if recipe.get("main_ingredients") else [],
                    "cooking_time": "記載なし",
                    "servings": "記載なし",
                    "category": recipe.get("category", ""),
                    "text_preview": recipe.get("text_preview", "")
                }
                integrated_recipes.append(integrated_recipe)
        
        # Web結果の処理
        if web_results.get("success") and web_results.get("data", {}).get("recipes"):
            for recipe in web_results["data"]["recipes"]:
                integrated_recipe = {
                    "title": recipe.get("title", ""),
                    "source": "web",
                    "similarity_score": 0.0,  # Web検索には類似度スコアがない
                    "url": recipe.get("url", ""),
                    "ingredients": recipe.get("ingredients", []),
                    "cooking_time": recipe.get("cooking_time", "記載なし"),
                    "servings": recipe.get("servings", "記載なし"),
                    "category": "",
                    "text_preview": recipe.get("snippet", "")
                }
                integrated_recipes.append(integrated_recipe)
        
        # 4. 重複除去（タイトルの類似度で判定）
        unique_recipes = []
        for recipe in integrated_recipes:
            is_duplicate = False
            for existing in unique_recipes:
                # タイトルの類似度を簡易計算
                title_similarity = calculate_title_similarity(recipe["title"], existing["title"])
                if title_similarity > 0.8:  # 80%以上類似している場合は重複とみなす
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_recipes.append(recipe)
        
        # 5. 簡単なランキング（RAGスコア + Web順位）
        for i, recipe in enumerate(unique_recipes):
            if recipe["source"] == "rag":
                # RAG結果: 類似度スコアを重み付け
                recipe["rank_score"] = recipe["similarity_score"] * rag_weight
            else:
                # Web結果: 順位を重み付け（上位ほど高スコア）
                web_rank = i + 1
                recipe["rank_score"] = (1.0 / web_rank) * web_weight
        
        # ランキングスコアでソート
        unique_recipes.sort(key=lambda x: x["rank_score"], reverse=True)
        
        # 最大件数に制限
        final_recipes = unique_recipes[:max_results]
        
        # ランクを再設定
        for i, recipe in enumerate(final_recipes, 1):
            recipe["rank"] = i
            # ランキングスコアは内部用なので削除
            if "rank_score" in recipe:
                del recipe["rank_score"]
        
        # レスポンス構築
        response_data = {
            "query": query,
            "total_found": len(final_recipes),
            "rag_results": len([r for r in final_recipes if r["source"] == "rag"]),
            "web_results": len([r for r in final_recipes if r["source"] == "web"]),
            "recipes": final_recipes
        }
        
        logger.info(f"統合検索完了: {len(final_recipes)}件のレシピを発見 (RAG:{response_data['rag_results']}件, Web:{response_data['web_results']}件)")
        
        return {
            "success": True,
            "data": response_data
        }
        
    except Exception as e:
        logger.error(f"統合検索エラー: {e}")
        return {
            "success": False,
            "error": f"統合検索エラー: {str(e)}"
        }


def calculate_title_similarity(title1: str, title2: str) -> float:
    """タイトルの類似度を計算（簡易版）"""
    if not title1 or not title2:
        return 0.0
    
    # 文字列を小文字に変換
    t1 = title1.lower()
    t2 = title2.lower()
    
    # 完全一致
    if t1 == t2:
        return 1.0
    
    # 部分一致
    if t1 in t2 or t2 in t1:
        return 0.8
    
    # 単語レベルでの一致
    words1 = set(t1.split())
    words2 = set(t2.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

if __name__ == "__main__":
    print("🚀 Recipe MCP Server (stdio transport) starting...")
    print("📡 Available tools: generate_menu_plan_with_history, search_menu_from_rag_with_history, search_recipe_from_rag, search_recipe_from_web, search_recipe_integrated")
    print("🔗 Transport: stdio")
    print("Press Ctrl+C to stop the server")
    
    # stdioトランスポートで起動
    mcp.run(transport="stdio")
