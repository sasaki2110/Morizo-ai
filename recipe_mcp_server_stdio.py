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
import sys
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

# プロジェクトの統一されたログ設定を使用（競合回避版）
try:
    # プロジェクトルートをパスに追加
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.append(project_root)
    
    from config.logging_config import setup_logging
    
    # 既存のログハンドラーをクリア（競合回避）
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()
    
    # プロジェクトのログ設定を適用
    logger = setup_logging()
    logger.info("🔧 [recipe_mcp] プロジェクトの統一されたログ設定を使用")
    
    # ログハンドラーのフラッシュを強制
    for handler in root_logger.handlers:
        if hasattr(handler, 'flush'):
            handler.flush()
    
    logger.info("🔧 [recipe_mcp] ログ設定を再適用完了（競合回避版）")
    
except ImportError as e:
    # フォールバック: 基本的なログ設定
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ [recipe_mcp] プロジェクトのログ設定が見つからないため、基本的なログ設定を使用: {e}")
except Exception as e:
    # その他のエラー
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.error(f"❌ [recipe_mcp] ログ設定エラー: {e}")

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

def detect_ingredient_duplication_internal(menu_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    献立データから食材重複を検出する内部関数
    
    Args:
        menu_data: 献立データ
        
    Returns:
        重複検出結果
    """
    try:
        logger.info(f"🔍 [食材重複検出] 検出開始")
        
        # 各料理の食材を取得
        main_ingredients = set(menu_data.get("main_dish", {}).get("ingredients", []))
        side_ingredients = set(menu_data.get("side_dish", {}).get("ingredients", []))
        soup_ingredients = set(menu_data.get("soup", {}).get("ingredients", []))
        
        logger.info(f"🔍 [食材重複検出] 主菜食材: {main_ingredients}")
        logger.info(f"🔍 [食材重複検出] 副菜食材: {side_ingredients}")
        logger.info(f"🔍 [食材重複検出] 汁物食材: {soup_ingredients}")
        
        # 重複検出
        duplicated_ingredients = []
        
        # 主菜と副菜の重複
        main_side_duplication = main_ingredients & side_ingredients
        if main_side_duplication:
            duplicated_ingredients.extend([(ingredient, "主菜-副菜") for ingredient in main_side_duplication])
            logger.warning(f"⚠️ [食材重複検出] 主菜-副菜重複: {main_side_duplication}")
        
        # 主菜と汁物の重複
        main_soup_duplication = main_ingredients & soup_ingredients
        if main_soup_duplication:
            duplicated_ingredients.extend([(ingredient, "主菜-汁物") for ingredient in main_soup_duplication])
            logger.warning(f"⚠️ [食材重複検出] 主菜-汁物重複: {main_soup_duplication}")
        
        # 副菜と汁物の重複
        side_soup_duplication = side_ingredients & soup_ingredients
        if side_soup_duplication:
            duplicated_ingredients.extend([(ingredient, "副菜-汁物") for ingredient in side_soup_duplication])
            logger.warning(f"⚠️ [食材重複検出] 副菜-汁物重複: {side_soup_duplication}")
        
        has_duplication = len(duplicated_ingredients) > 0
        
        result = {
            "has_duplication": has_duplication,
            "duplicated_ingredients": duplicated_ingredients,
            "main_ingredients": list(main_ingredients),
            "side_ingredients": list(side_ingredients),
            "soup_ingredients": list(soup_ingredients)
        }
        
        if has_duplication:
            logger.warning(f"❌ [食材重複検出] 重複検出: {len(duplicated_ingredients)}件")
        else:
            logger.info(f"✅ [食材重複検出] 重複なし")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ [食材重複検出] エラー: {e}")
        return {
            "has_duplication": True,
            "duplicated_ingredients": [("エラー", "検出失敗")],
            "main_ingredients": [],
            "side_ingredients": [],
            "soup_ingredients": []
        }

async def generate_menu_with_llm(
    inventory_items: List[str],
    menu_type: str,
    excluded_recipes: List[str],
    use_constraint_solver: bool = True
) -> Dict[str, Any]:
    """
    LLMを使って献立を生成（AI制約解決対応）
    
    Args:
        inventory_items: 在庫食材リスト
        menu_type: 献立タイプ
        excluded_recipes: 除外レシピリスト
        use_constraint_solver: AI制約解決エンジンを使用するか
        
    Returns:
        献立データ（食材重複回避済み）
    """
    try:
        if use_constraint_solver:
            logger.info(f"🔍 [LLM制約解決] AI制約解決エンジンを使用して献立生成")
            try:
                result = await generate_menu_with_llm_constraints(inventory_items, menu_type, excluded_recipes)
                logger.info(f"✅ [LLM制約解決] 制約解決完了: 重複回避={result.get('constraint_satisfied', False)}")
                return result
            except Exception as e:
                logger.error(f"❌ [LLM制約解決] エラー: {e}")
                logger.info(f"🔄 [LLM制約解決] フォールバック: 従来方式に切り替え")
                return await generate_menu_with_llm_legacy(inventory_items, menu_type, excluded_recipes)
        else:
            logger.info(f"🔍 [LLM従来] 従来の方式で献立生成")
            return await generate_menu_with_llm_legacy(inventory_items, menu_type, excluded_recipes)
            
    except Exception as e:
        logger.error(f"❌ [LLM献立生成] エラー: {e}")
        raise


async def generate_menu_with_llm_constraints(
    inventory_items: List[str],
    menu_type: str,
    excluded_recipes: List[str]
) -> Dict[str, Any]:
    """
    LLM生成 + AI制約解決による献立生成（レシピURL付き）
    
    Args:
        inventory_items: 在庫食材リスト
        menu_type: 献立タイプ
        excluded_recipes: 除外レシピリスト
        
    Returns:
        制約解決済み献立データ（レシピURL付き）
    """
    try:
        # Step 1: 複数候補を生成（食材情報付き）
        candidates_data = await generate_menu_candidates_with_ingredients(
            inventory_items, menu_type, excluded_recipes
        )
        
        # Step 2: 制約解決で最適な組み合わせを選択
        optimal_menu = await select_optimal_menu_from_candidates(
            candidates_data["candidates"], inventory_items
        )
        
        # Step 3: 結果を整形（レシピURLなし - 責任分離の設計思想に従う）
        selected = optimal_menu["selected_candidate"]
        
        result = {
            "main_dish": selected["main_dish"],
            "side_dish": selected["side_dish"],
            "soup": selected["soup"],
            "constraint_satisfied": optimal_menu["constraint_check"]["ingredient_duplication"] == False,
            "reasoning": optimal_menu["constraint_check"]["reasoning"],
            "source": "LLM + AI制約解決"
        }
        
        logger.info(f"✅ [LLM制約解決] 献立生成完了: 重複回避={result['constraint_satisfied']}")
        return result
        
    except Exception as e:
        logger.error(f"❌ [LLM制約解決] エラー: {e}")
        raise


async def generate_menu_with_llm_legacy(
    inventory_items: List[str],
    menu_type: str,
    excluded_recipes: List[str]
) -> Dict[str, Any]:
    """
    LLMを使って献立を生成（従来方式）
    
    Args:
        inventory_items: 在庫食材リスト
        menu_type: 献立タイプ
        excluded_recipes: 除外レシピリスト
        
    Returns:
        献立データ
    """
    try:
        client = openai_client.get_client()
        
        # シンプルなプロンプト（食材を丸投げ）
        prompt = f"""
あなたは料理の専門家です。在庫食材から3品構成の献立（主菜・副菜・汁物）を提案してください。

【在庫食材】
{', '.join(inventory_items)}

【献立タイプ】
{menu_type}

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
        logger.info(f"🔍 [LLM従来] LLM応答: {content}")
        
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
            logger.info(f"✅ [LLM従来] JSON解析後の献立データ: {menu_data}")
            return menu_data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ [LLM従来] JSON解析エラー: {e}")
            logger.error(f"❌ [LLM従来] 解析対象テキスト: {content}")
            raise
        
    except Exception as e:
        logger.error(f"❌ [LLM従来] エラー: {e}")
        raise

async def generate_menu_candidates_with_ingredients(
    inventory_items: List[str], 
    menu_type: str,
    excluded_recipes: List[str],
    num_candidates: int = 3
) -> Dict[str, Any]:
    """
    LLMで複数候補を生成（食材情報付き）
    
    Args:
        inventory_items: 在庫食材リスト
        menu_type: 献立タイプ
        excluded_recipes: 除外レシピリスト
        num_candidates: 生成する候補数
        
    Returns:
        複数の献立候補（食材情報付き）
    """
    try:
        client = openai_client.get_client()
        
        logger.info(f"🔍 [LLM候補生成] {num_candidates}個の候補を生成開始")
        
        prompt = f"""
あなたは料理の専門家です。以下の在庫食材から{num_candidates}つの献立候補を提案してください。

【在庫食材】
{', '.join(inventory_items)}

【献立タイプ】
{menu_type}

【除外レシピ】
{', '.join(excluded_recipes)}

【出力形式】
JSON形式で以下の構造で{num_candidates}つの候補を出力してください：

{{
    "candidates": [
        {{
            "candidate_id": 1,
            "main_dish": {{
                "title": "料理名",
                "ingredients": ["食材1", "食材2", "食材3"]
            }},
            "side_dish": {{
                "title": "料理名",
                "ingredients": ["食材1", "食材2", "食材3"]
            }},
            "soup": {{
                "title": "料理名",
                "ingredients": ["食材1", "食材2", "食材3"]
            }}
        }},
        {{
            "candidate_id": 2,
            "main_dish": {{...}},
            "side_dish": {{...}},
            "soup": {{...}}
        }},
        {{
            "candidate_id": 3,
            "main_dish": {{...}},
            "side_dish": {{...}},
            "soup": {{...}}
        }}
    ]
}}

【重要】
- 各料理のingredientsには、在庫食材から選択した主要食材を明記
- 調味料（塩、胡椒、醤油など）は除く
- 在庫食材のみを使用
- 各候補で異なる献立を提案
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
        logger.info(f"🔍 [LLM候補生成] LLM応答: {content[:200]}...")
        
        # JSON解析（マークダウンのコードブロックを除去）
        try:
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
            
            candidates_data = json.loads(content)
            logger.info(f"✅ [LLM候補生成] {len(candidates_data.get('candidates', []))}個の候補を生成完了")
            return candidates_data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ [LLM候補生成] JSON解析エラー: {e}")
            logger.error(f"❌ [LLM候補生成] 解析対象テキスト: {content}")
            raise
            
    except Exception as e:
        logger.error(f"❌ [LLM候補生成] エラー: {e}")
        raise


async def select_optimal_menu_from_candidates(
    candidates: List[Dict[str, Any]],
    inventory_items: List[str]
) -> Dict[str, Any]:
    """
    候補から最適な献立を選択（食材重複チェック付き）
    
    Args:
        candidates: 献立候補リスト
        inventory_items: 在庫食材リスト
        
    Returns:
        最適な献立と制約チェック結果
    """
    try:
        client = openai_client.get_client()
        
        logger.info(f"🔍 [AI制約解決] {len(candidates)}個の候補から最適解を選択")
        
        # 候補の詳細をログ出力
        logger.info(f"🔍 [AI制約解決] 候補詳細:")
        for i, candidate in enumerate(candidates):
            logger.info(f"  候補{i+1}:")
            logger.info(f"    主菜: {candidate['main_dish']['title']} - 食材: {candidate['main_dish']['ingredients']}")
            logger.info(f"    副菜: {candidate['side_dish']['title']} - 食材: {candidate['side_dish']['ingredients']}")
            logger.info(f"    汁物: {candidate['soup']['title']} - 食材: {candidate['soup']['ingredients']}")
        
        prompt = f"""
あなたは献立の制約解決専門家です。以下の候補から、制約を満たす最適な献立を選択してください。

【在庫食材】
{', '.join(inventory_items)}

【献立候補】
{json.dumps(candidates, ensure_ascii=False, indent=2)}

【制約条件】
1. 各料理で同じ食材を使用しない（調味料除く）
2. 在庫食材のみを使用
3. 主菜・副菜・汁物の3品構成

【制約チェック手順】
1. 各候補について、主菜・副菜・汁物の食材を確認
2. 重複する食材がないかチェック
3. 在庫食材にない食材がないかチェック
4. 制約を満たす候補を選択

【出力形式】
{{
    "selected_candidate": {{
        "candidate_id": 1,
        "main_dish": {{
            "title": "選択した主菜",
            "ingredients": ["食材1", "食材2", "食材3"]
        }},
        "side_dish": {{
            "title": "選択した副菜",
            "ingredients": ["食材1", "食材2", "食材3"]
        }},
        "soup": {{
            "title": "選択した汁物",
            "ingredients": ["食材1", "食材2", "食材3"]
        }}
    }},
    "constraint_check": {{
        "ingredient_duplication": false,
        "inventory_compliance": true,
        "reasoning": "選択理由と制約チェック結果"
    }}
}}
"""
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        logger.info(f"🔍 [AI制約解決] LLM応答: {content[:200]}...")
        
        # JSON解析
        try:
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
            
            optimal_result = json.loads(content)
            logger.info(f"✅ [AI制約解決] 最適解選択完了: 重複回避={optimal_result['constraint_check']['ingredient_duplication'] == False}")
            return optimal_result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ [AI制約解決] JSON解析エラー: {e}")
            logger.error(f"❌ [AI制約解決] 解析対象テキスト: {content}")
            raise
            
    except Exception as e:
        logger.error(f"❌ [AI制約解決] エラー: {e}")
        raise

async def generate_menu_with_rag(
    inventory_items: List[str],
    menu_type: str,
    excluded_recipes: List[str],
    max_results: int = 3,
    use_constraint_solver: bool = True
) -> Dict[str, Any]:
    """
    RAG検索を使って献立を生成（AI制約解決対応）
    
    Args:
        inventory_items: 在庫食材リスト
        menu_type: 献立タイプ
        excluded_recipes: 除外レシピリスト
        max_results: 最大検索結果数
        use_constraint_solver: AI制約解決エンジンを使用するか
        
    Returns:
        献立データ（食材重複回避済み）
    """
    try:
        if use_constraint_solver:
            logger.info(f"🔍 [RAG制約解決] AI制約解決エンジンを使用して献立生成")
            try:
                result = await generate_menu_with_rag_constraints(inventory_items, menu_type, excluded_recipes, max_results)
                logger.info(f"✅ [RAG制約解決] 制約解決完了: 重複回避={result.get('constraint_satisfied', False)}")
                return result
            except Exception as e:
                logger.error(f"❌ [RAG制約解決] エラー: {e}")
                logger.info(f"🔄 [RAG制約解決] フォールバック: 従来方式に切り替え")
                return await generate_menu_with_rag_legacy(inventory_items, menu_type, excluded_recipes, max_results)
        else:
            logger.info(f"🔍 [RAG従来] 従来の方式で献立生成")
            return await generate_menu_with_rag_legacy(inventory_items, menu_type, excluded_recipes, max_results)
            
    except Exception as e:
        logger.error(f"❌ [RAG献立生成] エラー: {e}")
        raise


async def generate_menu_with_rag_constraints(
    inventory_items: List[str],
    menu_type: str,
    excluded_recipes: List[str],
    max_results: int = 3
) -> Dict[str, Any]:
    """
    RAG検索 + AI制約解決による献立生成
    
    Args:
        inventory_items: 在庫食材リスト
        menu_type: 献立タイプ
        excluded_recipes: 除外レシピリスト
        max_results: 最大検索結果数
        
    Returns:
        制約解決済み献立データ
    """
    try:
        # Step 1: RAG検索で候補レシピを取得
        rag_candidates = await search_rag_candidates_with_ingredients(
            inventory_items, menu_type, excluded_recipes, max_results
        )
        
        # Step 2: AI制約解決で最適な組み合わせを選択
        optimal_menu = await select_optimal_menu_from_rag_candidates(
            rag_candidates, inventory_items
        )
        
        # Step 3: 結果を整形
        result = {
            "main_dish": optimal_menu["selected_menu"]["main_dish"],
            "side_dish": optimal_menu["selected_menu"]["side_dish"],
            "soup": optimal_menu["selected_menu"]["soup"],
            "constraint_satisfied": optimal_menu["constraint_check"]["ingredient_duplication"] == False,
            "reasoning": optimal_menu["constraint_check"]["reasoning"],
            "source": "RAG + AI制約解決"
        }
        
        logger.info(f"✅ [RAG制約解決] 献立生成完了: 重複回避={result['constraint_satisfied']}")
        return result
        
    except Exception as e:
        logger.error(f"❌ [RAG制約解決] エラー: {e}")
        raise


async def search_rag_candidates_with_ingredients(
    inventory_items: List[str],
    menu_type: str,
    excluded_recipes: List[str],
    max_results: int = 3
) -> Dict[str, List[Dict]]:
    """
    RAG検索で各料理タイプの候補を取得（食材情報付き）
    
    Args:
        inventory_items: 在庫食材リスト
        menu_type: 献立タイプ
        excluded_recipes: 除外レシピリスト
        max_results: 最大検索結果数
        
    Returns:
        料理タイプ別の候補リスト（食材情報付き）
    """
    try:
        # ベクトル検索インスタンスを取得
        vector_search = get_vector_search()
        vector_search._load_vector_db()  # ベクトルDBを読み込み
        
        # 検索クエリ生成
        rag_query = f"{menu_type} {' '.join(inventory_items[:5])} 献立 主菜 副菜 汁物"
        logger.info(f"🔍 [RAG候補検索] 検索クエリ生成: '{rag_query}'")
        
        # ベクトル検索実行
        search_results = vector_search.search_similar_recipes(rag_query, k=max_results * 5)
        logger.info(f"🔍 [RAG候補検索] ベクトル検索結果: {len(search_results)}件")
        
        # 料理タイプ別に分類
        candidates = {
            "main_dish": [],
            "side_dish": [],
            "soup": []
        }
        
        logger.info(f"🔍 [RAG候補検索] ベクトル検索結果を料理タイプ別に分類開始")
        
        for result in search_results:
            title = result.get("title", "")
            ingredients = result.get("ingredients", [])
            
            logger.info(f"🔍 [RAG候補検索] 処理中: '{title}' - 食材: {ingredients}")
            
            # 除外レシピチェック
            if any(excluded in title for excluded in excluded_recipes):
                logger.info(f"⏭️ [RAG候補検索] 除外レシピのためスキップ: '{title}'")
                continue
            
            # 料理タイプ判定
            if any(keyword in title for keyword in ["肉", "魚", "鶏", "豚", "牛", "カレー", "ハンバーグ", "唐揚げ"]):
                candidates["main_dish"].append({
                    "title": title,
                    "ingredients": ingredients,
                    "source": "RAG"
                })
                logger.info(f"🍖 [RAG候補検索] 主菜候補追加: '{title}'")
            elif any(keyword in title for keyword in ["サラダ", "和え物", "おひたし", "炒め物", "煮物"]):
                candidates["side_dish"].append({
                    "title": title,
                    "ingredients": ingredients,
                    "source": "RAG"
                })
                logger.info(f"🥗 [RAG候補検索] 副菜候補追加: '{title}'")
            elif any(keyword in title for keyword in ["汁", "スープ", "味噌汁", "豚汁"]):
                candidates["soup"].append({
                    "title": title,
                    "ingredients": ingredients,
                    "source": "RAG"
                })
                logger.info(f"🍲 [RAG候補検索] 汁物候補追加: '{title}'")
        
        logger.info(f"🔍 [RAG候補検索] 分類完了: 主菜={len(candidates['main_dish'])}, 副菜={len(candidates['side_dish'])}, 汁物={len(candidates['soup'])}")
        
        # デフォルト値の設定（食材重複回避）
        logger.info(f"🔧 [RAG候補検索] デフォルト値設定開始（食材重複回避）")
        
        if not candidates["main_dish"]:
            candidates["main_dish"] = [{"title": "肉じゃが", "ingredients": ["豚肉", "じゃがいも", "玉ねぎ"], "source": "RAG"}]
            logger.info(f"🍖 [RAG候補検索] 主菜デフォルト設定: 肉じゃが")
            
        if not candidates["side_dish"]:
            # 主菜の食材を避けて副菜を設定
            main_ingredients = []
            if candidates["main_dish"]:
                main_ingredients = candidates["main_dish"][0].get("ingredients", [])
            
            logger.info(f"🥗 [RAG候補検索] 副菜デフォルト設定開始: 主菜食材={main_ingredients}")
            
            if "ほうれん草" not in main_ingredients:
                candidates["side_dish"] = [{"title": "ほうれん草のおひたし", "ingredients": ["ほうれん草"], "source": "RAG"}]
                logger.info(f"🥗 [RAG候補検索] 副菜デフォルト設定: ほうれん草のおひたし（重複回避成功）")
            else:
                candidates["side_dish"] = [{"title": "キャベツのサラダ", "ingredients": ["キャベツ"], "source": "RAG"}]
                logger.info(f"🥗 [RAG候補検索] 副菜デフォルト設定: キャベツのサラダ（ほうれん草重複回避）")
                
        if not candidates["soup"]:
            # 主菜・副菜の食材を避けて汁物を設定
            used_ingredients = []
            if candidates["main_dish"]:
                used_ingredients.extend(candidates["main_dish"][0].get("ingredients", []))
            if candidates["side_dish"]:
                used_ingredients.extend(candidates["side_dish"][0].get("ingredients", []))
            
            logger.info(f"🍲 [RAG候補検索] 汁物デフォルト設定開始: 使用済み食材={used_ingredients}")
            
            if "豆腐" not in used_ingredients:
                candidates["soup"] = [{"title": "味噌汁", "ingredients": ["豆腐", "わかめ"], "source": "RAG"}]
                logger.info(f"🍲 [RAG候補検索] 汁物デフォルト設定: 味噌汁（重複回避成功）")
            elif "わかめ" not in used_ingredients:
                candidates["soup"] = [{"title": "わかめスープ", "ingredients": ["わかめ"], "source": "RAG"}]
                logger.info(f"🍲 [RAG候補検索] 汁物デフォルト設定: わかめスープ（豆腐重複回避）")
            else:
                candidates["soup"] = [{"title": "コンソメスープ", "ingredients": ["人参"], "source": "RAG"}]
                logger.info(f"🍲 [RAG候補検索] 汁物デフォルト設定: コンソメスープ（豆腐・わかめ重複回避）")
        
        logger.info(f"✅ [RAG候補検索] 候補取得完了: 主菜={len(candidates['main_dish'])}, 副菜={len(candidates['side_dish'])}, 汁物={len(candidates['soup'])}")
        return candidates
        
    except Exception as e:
        logger.error(f"❌ [RAG候補検索] エラー: {e}")
        raise


async def select_optimal_menu_from_rag_candidates(
    rag_candidates: Dict[str, List[Dict]],
    inventory_items: List[str]
) -> Dict[str, Any]:
    """
    RAG候補から最適な献立を選択（食材重複チェック付き）
    
    Args:
        rag_candidates: RAG検索結果の候補
        inventory_items: 在庫食材リスト
        
    Returns:
        最適な献立と制約チェック結果
    """
    try:
        client = openai_client.get_client()
        
        logger.info(f"🔍 [RAG制約解決] RAG候補から最適解を選択")
        logger.info(f"🔍 [RAG制約解決] 候補数: 主菜={len(rag_candidates['main_dish'])}, 副菜={len(rag_candidates['side_dish'])}, 汁物={len(rag_candidates['soup'])}")
        
        # 候補の詳細をログ出力
        for dish_type, candidates in rag_candidates.items():
            logger.info(f"🔍 [RAG制約解決] {dish_type}候補:")
            for i, candidate in enumerate(candidates):
                logger.info(f"  {i+1}. {candidate['title']} - 食材: {candidate.get('ingredients', [])}")
        
        prompt = f"""
あなたは献立の制約解決専門家です。以下のRAG検索結果から、制約を満たす最適な献立を選択してください。

【在庫食材】
{', '.join(inventory_items)}

【RAG検索結果】
{json.dumps(rag_candidates, ensure_ascii=False, indent=2)}

【制約条件】
1. 在庫食材のみを使用
2. 各料理で同じ食材を使用しない（調味料除く）
3. 主菜・副菜・汁物の3品構成
4. RAG検索結果から選択

【解決方針】
- まず主菜を選択
- 主菜の食材を避けて副菜を選択
- 主菜・副菜の食材を避けて汁物を選択
- 各段階で最適解を選択

【出力形式】
{{
    "selected_menu": {{
        "main_dish": {{
            "title": "選択した主菜",
            "ingredients": ["食材1", "食材2", "食材3"],
            "source": "RAG"
        }},
        "side_dish": {{
            "title": "選択した副菜",
            "ingredients": ["食材1", "食材2", "食材3"],
            "source": "RAG"
        }},
        "soup": {{
            "title": "選択した汁物",
            "ingredients": ["食材1", "食材2", "食材3"],
            "source": "RAG"
        }}
    }},
    "constraint_check": {{
        "ingredient_duplication": false,
        "inventory_compliance": true,
        "reasoning": "制約解決の過程と選択理由"
    }}
}}
"""
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        logger.info(f"🔍 [RAG制約解決] LLM応答: {content[:200]}...")
        
        # JSON解析
        try:
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
            
            optimal_result = json.loads(content)
            logger.info(f"✅ [RAG制約解決] 最適解選択完了: 重複回避={optimal_result['constraint_check']['ingredient_duplication'] == False}")
            return optimal_result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ [RAG制約解決] JSON解析エラー: {e}")
            logger.error(f"❌ [RAG制約解決] 解析対象テキスト: {content}")
            raise
            
    except Exception as e:
        logger.error(f"❌ [RAG制約解決] エラー: {e}")
        raise


async def generate_menu_with_rag_legacy(
    inventory_items: List[str],
    menu_type: str,
    excluded_recipes: List[str],
    max_results: int = 3
) -> Dict[str, Any]:
    """
    RAG検索を使って献立を生成（従来方式）
    
    Args:
        inventory_items: 在庫食材リスト
        menu_type: 献立タイプ
        excluded_recipes: 除外レシピリスト
        max_results: 最大検索結果数
        
    Returns:
        献立データ
    """
    try:
        # ベクトル検索インスタンスを取得
        vector_search = get_vector_search()
        vector_search._load_vector_db()  # ベクトルDBを読み込み
        
        # 在庫食材から検索クエリを生成
        rag_query = f"{menu_type} {' '.join(inventory_items[:5])} 献立 主菜 副菜 汁物"
        logger.info(f"🔍 [RAG従来] 検索クエリ生成: '{rag_query}'")
        
        # ベクトル検索実行
        search_results = vector_search.search_similar_recipes(rag_query, k=max_results * 3)
        logger.info(f"🔍 [RAG従来] ベクトル検索結果: {len(search_results)}件")
        
        # 検索結果から献立タイトルを抽出
        rag_titles = []
        for result in search_results:
            title = result.get("title", "レシピ")
            rag_titles.append(title)
            logger.info(f"🔍 [RAG従来] 発見: {title}")
        
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
        
        logger.info(f"✅ [RAG従来] 生成完了: 主菜={menu_data['main_dish']['title']}")
        return menu_data
        
    except Exception as e:
        logger.error(f"❌ [RAG従来] 生成エラー: {e}")
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
    menu_type: str = "和食",
    use_constraint_solver: bool = True
) -> Dict[str, Any]:
    """
    在庫食材から献立構成を生成（AI制約解決対応）
    
    🎯 使用場面: 在庫食材から過去履歴を考慮した献立を提案する場合
    
    📋 パラメータ:
    - inventory_items: 在庫食材リスト
    - excluded_recipes: 除外する過去レシピのリスト
    - menu_type: 献立のタイプ（和食・洋食・中華）
    - use_constraint_solver: AI制約解決エンジンを使用するか（デフォルト: True）
    
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
            "excluded_recipes": ["フレンチトースト", "オムレツ"],
            "constraint_satisfied": true,
            "reasoning": "食材重複を回避した最適な組み合わせを選択"
        }
    }
    """
    logger.info("🚀 [MCP] generate_menu_plan_with_history 開始")
    logger.info("🚀 [MCP] generate_menu_plan_with_history 開始 - 制約解決フラグ確認")
    logger.info(f"🚀 [MCP] use_constraint_solver = {use_constraint_solver}")
    try:
        logger.info(f"🔍 [献立生成] 開始: 食材{len(inventory_items)}件, 除外レシピ{len(excluded_recipes)}件, 制約解決={use_constraint_solver}")
        
        # LLMによる献立生成（AI制約解決対応）
        menu_data = await generate_menu_with_llm(
            inventory_items, 
            menu_type, 
            excluded_recipes,
            use_constraint_solver=use_constraint_solver
        )
        
        # レスポンス構築
        response_data = {
            "main_dish": menu_data.get("main_dish", {}),
            "side_dish": menu_data.get("side_dish", {}),
            "soup": menu_data.get("soup", {}),
            "excluded_recipes": excluded_recipes
        }
        
        # 制約解決結果の追加
        if use_constraint_solver:
            response_data["constraint_satisfied"] = menu_data.get("constraint_satisfied", False)
            response_data["reasoning"] = menu_data.get("reasoning", "")
            response_data["source"] = menu_data.get("source", "LLM")
        
        logger.info(f"✅ [献立生成] 完了: 主菜={response_data['main_dish'].get('title', 'N/A')}, 制約満足={response_data.get('constraint_satisfied', 'N/A')}")
        
        return {
            "success": True,
            "data": response_data
        }
        
    except Exception as e:
        logger.error(f"❌ [献立生成] エラー: {e}")
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
    use_constraint_solver: bool = True,
    token: str = None
) -> Dict[str, Any]:
    """
    在庫食材からRAG検索で献立タイトルを生成（AI制約解決対応）
    
    🎯 使用場面: 在庫食材からRAG検索で伝統的な献立タイトルを提案する場合
    
    📋 パラメータ:
    - inventory_items: 在庫食材リスト
    - excluded_recipes: 除外する過去レシピのリスト
    - menu_type: 献立のタイプ（和食・洋食・中華）
    - max_results: 取得する最大件数（デフォルト: 3）
    - use_constraint_solver: AI制約解決エンジンを使用するか（デフォルト: True）
    - token: 認証トークン（未使用）
    
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
            "excluded_recipes": [],
            "constraint_satisfied": true,
            "reasoning": "RAG検索結果から食材重複を回避した最適な組み合わせを選択"
        }
    }
    """
    logger.info("🚀 [MCP] search_menu_from_rag_with_history 開始")
    logger.info("🚀 [MCP] search_menu_from_rag_with_history 開始 - 制約解決フラグ確認")
    logger.info(f"🚀 [MCP] use_constraint_solver = {use_constraint_solver}")
    try:
        logger.info(f"🔍 [RAG献立] 検索開始: 食材{len(inventory_items)}件, 制約解決={use_constraint_solver}")
        
        # RAG検索で献立タイトルを生成（AI制約解決対応）
        menu_data = await generate_menu_with_rag(
            inventory_items, 
            menu_type, 
            excluded_recipes or [],
            max_results,
            use_constraint_solver=use_constraint_solver
        )
        
        # レスポンス構築
        response_data = {
            "main_dish": menu_data.get("main_dish", {}),
            "side_dish": menu_data.get("side_dish", {}),
            "soup": menu_data.get("soup", {}),
            "excluded_recipes": excluded_recipes or []
        }
        
        # 制約解決結果の追加
        if use_constraint_solver:
            response_data["constraint_satisfied"] = menu_data.get("constraint_satisfied", False)
            response_data["reasoning"] = menu_data.get("reasoning", "")
            response_data["source"] = menu_data.get("source", "RAG")
        
        logger.info(f"✅ [RAG献立] 検索完了: 主菜={response_data['main_dish'].get('title', 'N/A')}, 制約満足={response_data.get('constraint_satisfied', 'N/A')}")
        
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

if __name__ == "__main__":
    print("🚀 Recipe MCP Server (stdio transport) starting...")
    print("📡 Available tools: generate_menu_plan_with_history, search_menu_from_rag_with_history, search_recipe_from_web")
    print("🔗 Transport: stdio")
    print("Press Ctrl+C to stop the server")
    
    # stdioトランスポートで起動
    mcp.run(transport="stdio")
