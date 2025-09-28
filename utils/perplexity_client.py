#!/usr/bin/env python3
"""
Perplexity API クライアント
レシピ検索用のWeb検索機能を提供
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import requests
from dataclasses import dataclass
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RecipeSearchResult:
    """レシピ検索結果のデータクラス"""
    title: str
    url: str
    snippet: str
    source: str
    ingredients: List[str]
    instructions: str
    cooking_time: Optional[str] = None
    servings: Optional[str] = None

class PerplexityAPIClient:
    """Perplexity API クライアント"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初期化
        
        Args:
            api_key: Perplexity API キー（環境変数から取得可能）
        """
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("Perplexity API キーが設定されていません")
        
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def search_recipe(self, query: str, max_results: int = 3) -> List[RecipeSearchResult]:
        """
        レシピ検索
        
        Args:
            query: 検索クエリ（例: "肉じゃが 作り方"）
            max_results: 取得する最大件数
            
        Returns:
            レシピ検索結果のリスト
        """
        try:
            logger.info(f"Perplexity API レシピ検索開始: '{query}' (最大{max_results}件)")
            
            # レシピ専用の検索クエリを構築
            recipe_query = self._build_recipe_query(query)
            
            # API リクエストの構築
            payload = {
                "model": "sonar",
                "messages": [
                    {
                        "role": "system",
                        "content": "あなたは料理の専門家です。レシピ検索の結果を構造化されたJSON形式で返してください。"
                    },
                    {
                        "role": "user",
                        "content": recipe_query
                    }
                ],
                "max_tokens": 4000,
                "temperature": 0.1,
                "top_p": 0.9,
                "return_citations": True,
                "search_domain_filter": ["cookpad.com", "recipe.rakuten.co.jp", "delishkitchen.tv", "kurashiru.com"]
            }
            
            # API リクエストの実行（タイムアウト延長 + リトライ機能）
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        self.base_url,
                        headers=self.headers,
                        json=payload,
                        timeout=60  # 30秒 → 60秒に延長
                    )
                    break  # 成功したらループを抜ける
                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        logger.warning(f"タイムアウト発生 (試行 {attempt + 1}/{max_retries})。リトライします...")
                        continue
                    else:
                        logger.error(f"タイムアウト: {max_retries}回の試行後も失敗")
                        return []
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"リクエストエラー (試行 {attempt + 1}/{max_retries}): {e}。リトライします...")
                        continue
                    else:
                        logger.error(f"リクエストエラー: {max_retries}回の試行後も失敗")
                        return []
            
            if response.status_code != 200:
                logger.error(f"Perplexity API エラー: {response.status_code} - {response.text}")
                return []
            
            # レスポンスの解析
            result = response.json()
            recipes = self._parse_recipe_response(result, max_results)
            
            logger.info(f"Perplexity API レシピ検索完了: {len(recipes)}件のレシピを発見")
            return recipes
            
        except Exception as e:
            logger.error(f"Perplexity API レシピ検索エラー: {e}")
            return []
    
    def _build_recipe_query(self, query: str) -> str:
        """
        レシピ専用の検索クエリを構築
        
        Args:
            query: 元のクエリ
            
        Returns:
            レシピ検索用のクエリ
        """
        return f"""
以下のレシピについて、詳細な情報をJSON形式で提供してください：

レシピ名: {query}

以下の情報を含めてください：
1. レシピのタイトル
2. 材料（ingredients）のリスト
3. 作り方（instructions）の詳細
4. 調理時間（cooking_time）
5. 人数分（servings）
6. 参考URL（url）
7. レシピサイト名（source）

JSON形式で返してください：
{{
    "recipes": [
        {{
            "title": "レシピ名",
            "ingredients": ["材料1", "材料2", "材料3"],
            "instructions": "作り方の詳細",
            "cooking_time": "調理時間",
            "servings": "人数分",
            "url": "参考URL",
            "source": "レシピサイト名"
        }}
    ]
}}
"""
    
    def _parse_recipe_response(self, response: Dict[str, Any], max_results: int) -> List[RecipeSearchResult]:
        """
        API レスポンスを解析してレシピ情報を抽出
        
        Args:
            response: API レスポンス
            max_results: 最大取得件数
            
        Returns:
            レシピ検索結果のリスト
        """
        recipes = []
        
        try:
            # レスポンスからコンテンツを取得
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # JSON形式の部分を抽出
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            
            if json_start != -1 and json_end != -1:
                json_str = content[json_start:json_end]
                data = json.loads(json_str)
                
                # レシピ情報を抽出
                recipe_list = data.get("recipes", [])
                for i, recipe_data in enumerate(recipe_list[:max_results]):
                    try:
                        recipe = RecipeSearchResult(
                            title=recipe_data.get("title", ""),
                            url=recipe_data.get("url", ""),
                            snippet=recipe_data.get("instructions", "")[:200] + "...",
                            source=recipe_data.get("source", ""),
                            ingredients=recipe_data.get("ingredients", []),
                            instructions=recipe_data.get("instructions", ""),
                            cooking_time=recipe_data.get("cooking_time"),
                            servings=recipe_data.get("servings")
                        )
                        recipes.append(recipe)
                    except Exception as e:
                        logger.warning(f"レシピ {i+1} の解析エラー: {e}")
                        continue
            
            # 引用情報も取得
            citations = response.get("citations", [])
            for i, citation in enumerate(citations[:max_results]):
                if i < len(recipes):
                    recipes[i].url = citation.get("url", recipes[i].url)
                    recipes[i].source = citation.get("title", recipes[i].source)
            
        except Exception as e:
            logger.error(f"レスポンス解析エラー: {e}")
        
        return recipes
    
    def get_usage_info(self) -> Dict[str, Any]:
        """
        使用量情報を取得
        
        Returns:
            使用量情報の辞書
        """
        try:
            # 使用量APIのエンドポイント（推定）
            usage_url = "https://api.perplexity.ai/usage"
            
            response = requests.get(
                usage_url,
                headers=self.headers,
                timeout=30  # 10秒 → 30秒に延長
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"使用量情報取得エラー: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"使用量情報取得エラー: {e}")
            return {}

# テスト用のメイン関数
if __name__ == "__main__":
    # 環境変数からAPIキーを取得
    api_key = os.getenv("PERPLEXITY_API_KEY")
    
    if not api_key:
        print("❌ PERPLEXITY_API_KEY が設定されていません")
        print("環境変数を設定してください: export PERPLEXITY_API_KEY=your_api_key")
        exit(1)
    
    # クライアントの初期化
    client = PerplexityAPIClient(api_key)
    
    # テスト検索
    print("🧪 Perplexity API テスト開始")
    print("=" * 50)
    
    test_queries = [
        "肉じゃが 作り方",
        "フレンチトースト レシピ",
        "味噌汁 基本"
    ]
    
    for query in test_queries:
        print(f"\n🔍 検索クエリ: {query}")
        recipes = client.search_recipe(query, max_results=2)
        
        for i, recipe in enumerate(recipes, 1):
            print(f"\n📋 レシピ {i}:")
            print(f"  タイトル: {recipe.title}")
            print(f"  材料: {', '.join(recipe.ingredients[:3])}...")
            print(f"  調理時間: {recipe.cooking_time}")
            print(f"  人数分: {recipe.servings}")
            print(f"  参考URL: {recipe.url}")
            print(f"  サイト: {recipe.source}")
    
    print("\n✅ テスト完了")
