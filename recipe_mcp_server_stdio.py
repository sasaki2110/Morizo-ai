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
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI

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
3. 在庫食材を最大限活用する
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
            max_tokens=1000
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
            return menu_data
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析エラー: {e}")
            logger.error(f"解析対象テキスト: {content}")
            raise
        
    except Exception as e:
        logger.error(f"LLM献立生成エラー: {e}")
        raise

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

if __name__ == "__main__":
    print("🚀 Recipe MCP Server (stdio transport) starting...")
    print("📡 Available tools: generate_menu_plan_with_history")
    print("🔗 Transport: stdio")
    print("Press Ctrl+C to stop the server")
    
    # stdioトランスポートで起動
    mcp.run(transport="stdio")
