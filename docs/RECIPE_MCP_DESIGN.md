# Morizo AI - レシピ提案機能 MCP設計

## 📋 概要

レシピ提案機能のMCP（Micro-Agent Communication Protocol）設計ドキュメント。在庫食材から独創的なレシピタイトルを生成し、Web検索とRAG検索を組み合わせてレシピを提案する機能の設計。

## 🎯 核心思想

### **「飽きない献立提案」の本質**
- **問題**: 単純なレシピ検索 → 同じものの繰り返し
- **解決**: 献立構成（主菜・副菜・味噌汁）+ 過去履歴管理 → 多様な献立提案
- **価値**: ミニマリスト対応 + 食材効率 + 履歴管理

### **設計の核心（修正版）**
```
在庫食材 → 献立構成（主菜・副菜・味噌汁） → 過去履歴チェック → レシピ検索 → 献立提案
```

### **制約条件**
```python
MENU_CONSTRAINTS = {
    "dishes": ["主菜", "副菜", "味噌汁"],
    "ingredient_exclusivity": "各料理で同じ食材を使用しない",
    "history_exclusion": "過去1-2週間のレシピを除外",
    "simplicity": "栄養バランスは後回し（シンプル優先）"
}
```

## 🏗️ アーキテクチャ設計

### **責任分担**
- **メインReAct**: タスク分解・制御の責任
- **Recipe MCP**: 純粋なツール提供のみ
- **DB MCP**: 在庫管理（既存）

### **ツール構成（献立提案用）**
```
1. generate_menu_plan: 献立構成生成
2. check_cooking_history: 過去履歴チェック
3. search_recipe_for_menu: 献立用レシピ検索
4. （統合提案機能は削除）
```

## 🛠️ MCPツール設計

### **1. generate_menu_plan（献立構成生成）**

#### **仕様**
```python
@mcp.tool()
async def generate_menu_plan(
    inventory_items: List[str],
    user_id: str,
    menu_type: str = "和食"
) -> Dict[str, Any]:
    """
    在庫食材から献立構成を生成（シンプル版）
    
    Args:
        inventory_items: 在庫食材リスト
        user_id: ユーザーID（履歴チェック用）
        menu_type: 献立のタイプ
    
    Returns:
        {
            "main_dish": {
                "title": "鶏もも肉の照り焼き",
                "ingredients": ["鶏もも肉", "醤油", "みりん", "酒"]
            },
            "side_dish": {
                "title": "ほうれん草の胡麻和え",
                "ingredients": ["ほうれん草", "胡麻", "醤油"]
            },
            "soup": {
                "title": "豆腐とわかめの味噌汁",
                "ingredients": ["豆腐", "わかめ", "味噌", "だし"]
            },
            "ingredient_usage": {
                "used": ["鶏もも肉", "醤油", "みりん", "酒", "ほうれん草", "胡麻", "豆腐", "わかめ", "味噌", "だし"],
                "remaining": ["牛乳", "卵", "パン"]
            }
        }
    """
```

### **2. check_cooking_history（過去履歴チェック）**

#### **仕様**
```python
@mcp.tool()
async def check_cooking_history(
    user_id: str,
    recipe_titles: List[str],
    exclusion_days: int = 14
) -> Dict[str, Any]:
    """
    過去の調理履歴をチェックして重複を回避
    
    Args:
        user_id: ユーザーID
        recipe_titles: チェックするレシピタイトルリスト
        exclusion_days: 除外する日数（デフォルト14日）
    
    Returns:
        {
            "excluded_recipes": [
                {
                    "title": "鶏もも肉の照り焼き",
                    "cooked_at": "2025-01-15",
                    "days_ago": 5,
                    "reason": "過去14日以内に調理済み"
                }
            ],
            "available_recipes": [
                {
                    "title": "豚肉の生姜焼き",
                    "status": "available"
                }
            ],
            "exclusion_summary": {
                "total_checked": 3,
                "excluded_count": 1,
                "available_count": 2
            }
        }
    """
```

#### **独創性制御**
```python
CREATIVITY_LEVELS = {
    1: {
        "name": "保守的",
        "description": "定番の組み合わせ",
        "examples": ["牛乳と卵のスクランブルエッグ", "パンとバターのトースト"]
    },
    2: {
        "name": "標準",
        "description": "少し工夫した組み合わせ",
        "examples": ["牛乳と卵のフレンチトースト", "パンとバターのガーリックトースト"]
    },
    3: {
        "name": "独創的",
        "description": "創造的な組み合わせ",
        "examples": ["牛乳と卵の和風フレンチトースト", "パンとバターのハーブトースト"]
    },
    4: {
        "name": "革新的",
        "description": "非常に独創的な組み合わせ",
        "examples": ["牛乳と卵の分子ガストロノミー風デザート", "パンとバターのアート風トースト"]
    }
}
```

#### **プロンプト設計**
```python
RECIPE_GENERATION_PROMPT = """
あなたは創造的なレシピタイトル生成AIです。

在庫食材: {inventory_items}
独創性レベル: {creativity_level} ({creativity_description})
調理時間: {cooking_time}
難易度: {difficulty}
料理スタイル: {cuisine_style}

制約:
- 在庫食材のみを使用
- 家庭で作れるレベルの独創性
- 実用的で美味しいレシピ
- 日本語で回答

生成するレシピタイトル（1つ）:
"""
```

### **3. search_recipe_for_menu（献立用レシピ検索）**

#### **仕様**
```python
@mcp.tool()
async def search_recipe_for_menu(
    dish_type: str,  # "主菜", "副菜", "味噌汁"
    title: str,
    available_ingredients: List[str],
    excluded_ingredients: List[str] = None
) -> Dict[str, Any]:
    """
    献立用のレシピ検索（食材の重複回避）
    
    Args:
        dish_type: 料理の種類
        title: 検索するレシピタイトル
        available_ingredients: 使用可能な食材
        excluded_ingredients: 使用禁止食材（他の料理で使用済み）
    
    Returns:
        {
            "recipe": {
                "title": "豚肉の生姜焼き",
                "ingredients": ["豚肉", "生姜", "醤油", "酒"],
                "source": "cookpad",
                "url": "https://cookpad.com/recipe/789012"
            },
            "ingredient_compatibility": {
                "available": ["豚肉", "生姜", "醤油", "酒"],
                "missing": [],
                "excluded": ["牛乳", "卵"]  # 他の料理で使用済み
            }
        }
    """
```

#### **内部実装戦略**
```python
SEARCH_STRATEGY = {
    "step1": "web_search_primary",
    "step2": "rag_search_secondary", 
    "step3": "result_integration",
    "step4": "similarity_ranking"
}
```

## 🔍 Web検索の実装

### **法的リスクの軽減**
- **スクレイピング回避**: 有料コンテンツの規約外利用を避ける
- **API利用**: Google Search API等の公式API使用
- **要約のみ**: 完全なレシピ内容は取得しない
- **リンク提供**: 元サイトへの誘導のみ

### **検索エンジンAPIの利用**
```python
WEB_SEARCH_STRATEGY = {
    "primary": "google_search_api",
    "fallback": "bing_search_api",
    "method": "api_based_search",
    "content_type": "title_and_url_only"
}
```

### **検索結果の処理**
```python
SEARCH_RESULT_PROCESSING = {
    "extract": ["title", "url", "snippet"],
    "avoid": ["full_content", "images", "detailed_instructions"],
    "legal_safe": True
}
```

### **Google Search API設定**
```python
GOOGLE_SEARCH_CONFIG = {
    "api_key": "GOOGLE_SEARCH_API_KEY",
    "search_engine_id": "CUSTOM_SEARCH_ENGINE_ID",
    "search_type": "web",
    "safe_search": "active",
    "num_results": 10
}
```

### **検索クエリの最適化**
```python
SEARCH_QUERY_OPTIMIZATION = {
    "base_query": "レシピ {title}",
    "site_specific": [
        "site:cookpad.com レシピ {title}",
        "site:delishkitchen.tv レシピ {title}",
        "site:kurashiru.com レシピ {title}"
    ],
    "fallback_query": "レシピ {title} 作り方"
}
```

## 🗄️ RAG検索の実装

### **既存データの活用**
- **データソース**: `me2you/recipe_data.jsonl` (6,234件のレシピ)
- **データ構造**: タイトル、食材リスト、分類情報
- **法的安全性**: 過去に取得済みの学習データ

### **データ構造**
```json
{
  "text": "以下のレシピの分類を行ってください。\n\n[レシピ本文]\n(title)レシピタイトル (ingredientText)食材リスト\n[回答]\n{\"レシピ分類\":\"主菜\",\"主材料\":[\"食材1\",\"食材2\"],\"カテゴリ\":\"おかず肉じゃが\"}"
}
```

### **ベクトルDB構築戦略**

#### **事前ベクトル化アプローチ**
- **毎回API呼び出し回避**: 検索のたびにOpenAI APIを呼び出さない
- **コスト削減**: 99.98%のコスト削減（月額$1,870 → $0.30）
- **レスポンス時間向上**: API呼び出しによる遅延を排除
- **可用性向上**: OpenAI APIの制限や障害の影響を回避

#### **技術スタック（開発段階）**
```python
# LangChain + Chroma（ローカル）
- 簡単な実装
- 無料
- 開発・テストに最適
- 永続化機能
- メタデータ検索
```

#### **ベクトル化対象**
```python
VECTORIZATION_TARGETS = {
    "title": {
        "weight": 0.4,
        "description": "レシピタイトルのベクトル化"
    },
    "ingredientText": {
        "weight": 0.3,
        "description": "食材リストのベクトル化"
    },
    "recipe_category": {
        "weight": 0.2,
        "description": "レシピ分類のベクトル化"
    },
    "main_ingredients": {
        "weight": 0.1,
        "description": "主材料のベクトル化"
    }
}
```

#### **データ構造の最適化**
```python
RECIPE_VECTOR_STRUCTURE = {
    "id": "recipe_001",
    "title": "牛乳と卵のフレンチトースト",
    "ingredients": ["牛乳", "卵", "パン", "バター"],
    "combined_text": "牛乳と卵のフレンチトースト 牛乳 卵 パン バター 主菜",
    "metadata": {
        "recipe_category": "主菜",
        "main_ingredients": ["牛乳", "卵"],
        "category": "おかずフレンチトースト"
    }
}
```

#### **ベクトル化の戦略**
```python
VECTORIZATION_STRATEGY = {
    "text_combination": "title + ingredients + category",
    "weighting": {
        "title": 0.4,
        "ingredients": 0.3,
        "category": 0.3
    },
    "preprocessing": [
        "normalize_text",
        "remove_special_chars",
        "standardize_ingredients"
    ]
}
```

### **在庫食材とのマッチング**
```python
INVENTORY_MATCHING_LOGIC = {
    "exact_match": {
        "priority": 1,
        "description": "在庫食材と完全一致"
    },
    "partial_match": {
        "priority": 2,
        "description": "在庫食材の一部一致"
    },
    "category_match": {
        "priority": 3,
        "description": "食材カテゴリの一致"
    },
    "fallback": {
        "priority": 4,
        "description": "類似食材での検索"
    }
}
```

### **食材正規化**
```python
INGREDIENT_NORMALIZATION = {
    "牛乳": ["牛乳", "ミルク", "乳"],
    "卵": ["卵", "たまご", "玉子"],
    "パン": ["パン", "食パン", "ブレッド"],
    "バター": ["バター", "マーガリン", "油脂"]
}
```

### **マッチングスコア計算**
```python
MATCHING_SCORE_CALCULATION = {
    "exact_match": 1.0,
    "partial_match": 0.8,
    "category_match": 0.6,
    "similarity_match": 0.4
}
```

## 🚀 実装の段階

### **Phase 1: ベクトルDB構築（事前処理）**
1. **レシピデータ前処理**: `me2you/recipe_data.jsonl`の解析・正規化
2. **ベクトル化**: LangChain + ChromaによるベクトルDB構築
3. **永続化**: ローカルディスクへの保存

### **Phase 2: 基本献立機能**
1. **`generate_menu_plan`**: シンプルな献立構成生成
2. **`check_cooking_history`**: 過去履歴チェック
3. **食材配分アルゴリズム**: 重複回避のロジック

### **Phase 3: レシピ検索機能**
1. **`search_recipe_for_menu`**: 献立用レシピ検索
2. **食材制約**: 使用禁止食材の考慮
3. **統合検索**: Web + RAG の統合

### **Phase 4: 統合提案機能**
1. **完全な献立提案**: 履歴除外済みの献立
2. **代替案生成**: 複数の献立パターン
3. **買い物提案**: 不足食材の提案

## 🎯 本体ReActループでの使用例

### **ユーザーリクエスト**
```
"冷蔵庫の食材で今日の献立を提案して！"
```

### **ActionPlanner（タスク分解）**
```json
{
  "tasks": [
    {
      "description": "現在の在庫を確認",
      "tool": "inventory_list",
      "parameters": {},
      "priority": 1
    },
    {
      "description": "過去の調理履歴をチェック",
      "tool": "check_cooking_history",
      "parameters": {
        "user_id": "{{user_id}}",
        "recipe_titles": "{{all_possible_recipes}}",
        "exclusion_days": 14
      },
      "priority": 2
    },
    {
      "description": "在庫食材から献立構成を生成",
      "tool": "generate_menu_plan",
      "parameters": {
        "inventory_items": "{{task1_result}}",
        "user_id": "{{user_id}}",
        "menu_type": "和食"
      },
      "priority": 3,
      "dependencies": ["task1", "task2"]
    },
    {
      "description": "各料理のレシピを検索",
      "tool": "search_recipe_for_menu",
      "parameters": {
        "dish_type": "主菜",
        "title": "{{task3_result.main_dish.title}}",
        "available_ingredients": "{{task3_result.main_dish.ingredients}}"
      },
      "priority": 4,
      "dependencies": ["task3"]
    }
  ]
}
```

### **TaskManager（タスク実行）**
```
サイクル1: inventory_list 実行
サイクル2: check_cooking_history 実行
サイクル3: generate_menu_plan 実行
サイクル4: search_recipe_for_menu 実行
```

### **最終応答生成**
```
"今日の献立をご提案します！（過去14日間の重複を回避）

【主菜】豚肉の生姜焼き
【副菜】ほうれん草の胡麻和え  
【味噌汁】豆腐とわかめの味噌汁

使用食材: 豚肉、生姜、醤油、酒、ほうれん草、胡麻、豆腐、わかめ、味噌、だし
残り食材: 牛乳、卵、パン

※過去14日間で調理したレシピは除外しています"
```

## ⚖️ 法的リスクの軽減策

### **1. 利用規約の遵守**
- **API利用**: 公式APIの利用規約遵守
- **レート制限**: 適切なリクエスト頻度
- **利用目的**: 個人利用・研究目的の明記

### **2. コンテンツの取り扱い**
- **要約のみ**: 完全なレシピ内容は取得しない
- **リンク提供**: 元サイトへの誘導のみ
- **出典明記**: 情報源の明確な表示

### **3. データの管理**
- **最小限の保存**: 必要最小限の情報のみ
- **定期削除**: 古い検索結果の削除
- **プライバシー**: 個人情報の保護

## 🎯 この設計の利点

### **シンプル性**
- **MCP**: 純粋なツール提供のみ
- **本体**: タスク分解・制御の責任
- **責任分離**: 明確な役割分担

### **ミニマリスト対応**
- **食材効率**: 限られた食材の最大活用
- **重複回避**: 同じ食材の使い回し防止
- **履歴管理**: 同じレシピの繰り返しを防止

### **実用性**
- **現実的**: 実際の家庭の献立構成
- **時間効率**: 調理時間の最適化
- **買い物提案**: 不足食材の明確化

### **拡張性**
- **新しい検索方法**: MCP内で追加可能
- **新しい制約**: パラメータで制御可能
- **新しいサイト**: Web検索対象の追加可能

### **デバッグの容易さ**
- **問題の特定**: どのツールで失敗したか明確
- **個別テスト**: 各ツールを独立してテスト可能
- **ログ管理**: ツール単位でのログ出力

### **豊富なデータ**
- **6,234件のレシピ**: 十分な検索対象
- **詳細な食材情報**: 正確なマッチング
- **分類情報**: カテゴリベースの検索

## 🤔 検討すべき点

### **1. 独創性の定量化**
- どの程度が「独創的だが実用的」か？
- ユーザーフィードバックによる学習が必要？

### **2. 検索精度の向上**
- 生成されたタイトルで実際にレシピが見つかるか？
- フォールバック戦略の充実が必要？

### **3. パフォーマンス**
- LLM呼び出し + Web検索のレスポンス時間
- キャッシュ戦略の検討

### **4. 品質管理**
- 生成されたタイトルの品質評価
- 不適切なレシピのフィルタリング

### **5. データの鮮度**
- **古いデータ**: 新しいレシピが含まれない
- **更新頻度**: 定期的なデータ更新の必要性
- **品質管理**: データの品質維持

### **6. ベクトルDB構築**
- **初期コスト**: 6,234件のベクトル化（一度だけ）
- **メモリ使用量**: ベクトルデータのサイズ
- **更新頻度**: 新しいレシピの追加方法

## 🚀 商用化の可能性

### **MCPとしての価値**
- **汎用性**: どのレシピサイトでも利用可能
- **差別化**: 独創性 + 実用性のバランス
- **スケーラビリティ**: ユーザー数に応じた拡張

### **売り込み先候補**
- **クックパッド**: レシピ提案機能の強化
- **DELISH KITCHEN**: 動画レシピとの連携
- **クラシル**: 初心者向けレシピ提案
- **レシピブログ**: 個人ブロガー向けツール

## 🔧 ベクトルDB構築の実装例

### **ベクトルDB構築スクリプト**
```python
# build_vector_db.py
import json
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

def build_recipe_vector_db():
    # 1. レシピデータの読み込み
    recipes = load_recipe_data()
    
    # 2. テキストの前処理
    processed_recipes = preprocess_recipes(recipes)
    
    # 3. ベクトル化
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_texts(
        texts=[recipe['combined_text'] for recipe in processed_recipes],
        metadatas=[recipe['metadata'] for recipe in processed_recipes],
        embeddings=embeddings,
        persist_directory="./recipe_vector_db"
    )
    
    print(f"ベクトルDB構築完了: {len(processed_recipes)}件")
    return vectorstore
```

### **検索機能の実装**
```python
# recipe_search.py
class RecipeVectorSearch:
    def __init__(self):
        self.vectorstore = Chroma(
            persist_directory="./recipe_vector_db",
            embedding_function=OpenAIEmbeddings()
        )
    
    def search_by_title(self, title: str, k: int = 5):
        results = self.vectorstore.similarity_search_with_score(
            query=title,
            k=k
        )
        return results
    
    def search_by_ingredients(self, ingredients: List[str], k: int = 5):
        query = " ".join(ingredients)
        results = self.vectorstore.similarity_search_with_score(
            query=query,
            k=k
        )
        return results
```

### **コスト比較**
```
毎回API呼び出し:
- 検索回数: 100回/日
- レシピ数: 6,234件
- API料金: 100回 × 6,234件 × $0.0001 = $62.34/日
- 月額: $1,870

事前ベクトル化:
- 初期構築: 6,234件 × $0.0001 = $0.62（一度だけ）
- 検索時: 100回/日 × $0.0001 = $0.01/日
- 月額: $0.30

コスト削減: 99.98%の削減！
```

---

**作成日**: 2025年1月27日  
**作成者**: AIエージェント協働チーム  
**ステータス**: 設計完了（実装未着手）  
**バージョン**: 2.0（献立提案機能対応）
