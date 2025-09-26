# Morizo AI - レシピ提案機能 MCP設計

## 📋 概要

レシピ提案機能のMCP（Micro-Agent Communication Protocol）設計ドキュメント。在庫食材から独創的なレシピタイトルを生成し、Web検索とRAG検索を組み合わせてレシピを提案する機能の設計。

## 🧠 設計思想の核心

### **根本的な問題認識**
- **目的**: 少ない食材から飽きの来ない献立を提案
- **制約**: LLMには魂のこもったレシピ作成ができない
- **解決策**: 人間が蓄積してきたレシピを参照する必要がある

### **検索の固定化問題**
- **問題**: 単純なレシピ検索では同じものばかり検索してしまう
- **原因**: ユーザーの検索思考が固定化
- **解決策**: LLMに独創的なレシピタイトルを推論してもらう

### **独創性と抑制のバランス**
- **LLMの役割**: 独創的なレシピタイトルの推論（飽きの防止）
- **RAGの役割**: 蓄積した厳選レシピからタイトルを抽出（独創性の抑制）
- **未解決**: どちらを採用するかのロジック

### **人間の叡智への橋渡し**
- **最終段階**: WEB検索で人間が作った魂のこもったレシピを探す
- **MorizoAIの役割**: LLMの独創性と人間の叡智の橋渡し

### **処理フローの再定義**
```
1. LLM推論: 独創的なレシピタイトルの生成（飽きの防止）
   ↓
2. RAG検索: 蓄積レシピからタイトルを抽出（独創性の抑制）
   ↓
3. 採用ロジック: LLM提案とRAG提案の選択（未実装）
   ↓
4. WEB検索: 選択されたタイトルで人間のレシピを検索
   ↓
5. 統合: 魂のこもったレシピの提供
```

## 🎯 核心思想

### **「飽きない献立提案」の本質**
- **問題**: 単純なレシピ検索 → 同じものの繰り返し
- **解決**: 献立構成（主菜・副菜・汁物）+ 過去履歴管理 → 多様な献立提案
- **価値**: ミニマリスト対応 + 食材効率 + 履歴管理 + 文化的適切性

### **設計の核心（修正版）**
```
在庫食材 → 献立構成（主菜・副菜・汁物） → 過去履歴チェック → レシピ検索 → 献立提案
```

### **制約条件**
```python
MENU_CONSTRAINTS = {
    "dishes": ["主菜", "副菜", "汁物"],
    "ingredient_exclusivity": "各料理で同じ食材を使用しない",
    "history_exclusion": "過去1-2週間のレシピを除外",
    "simplicity": "栄養バランスは後回し（シンプル優先）",
    "cultural_appropriateness": "献立タイプに応じて汁物を選択（和食→味噌汁、洋食→スープ、中華→スープ）"
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

## 🔄 **設計の進化（壁打ち結果）**

### **Phase 1完了後の設計見直し**

#### **問題点の発見**
1. **ループバックの複雑さ**: タスクの途中でプランニングに戻る機能がない
2. **固定順序の繰り返し**: ベクトル検索は同じ順序で結果を返す
3. **ReActループの制限**: 現在のReActループは動的なプラン修正に対応していない

#### **RAGの役割の明確化（壁打ちで整理）**
- **✅ 正解**: RAGでLLMのレシピ提案を**補佐**する
- **本来の目的**: 美味しいレシピの厳選済みデータ（6,233件）を活用
- **データの内容**: タイトル、材料、調理手順を含む完全なレシピ情報
- **実際の役割**: LLMが生成したレシピタイトルの詳細情報を提供
- **補佐の方法**: 類似レシピの検索、材料の確認、調理手順の提供
- **Web検索との使い分け**: RAGで見つからない場合の詳細取得
- **独創性の抑制**: 蓄積レシピからタイトルを抽出して独創性を適度に抑制

#### **修正された処理フロー**
```
サイクル1: inventory_list 実行
サイクル2: generate_menu_plan_with_history 実行
  ├─ 在庫食材から献立生成 ← LLMがタイトルを生成
  ├─ 過去履歴をチェック ← データベースで履歴確認
  ├─ 重複があれば代替案生成 ← LLMが代替タイトルを生成
  └─ 最終的な献立を決定 ← タイトルのみ決定
サイクル3: search_recipe_for_menu 実行 (主菜) ← Web検索のみ
サイクル4: search_recipe_for_menu 実行 (副菜) ← Web検索のみ
サイクル5: search_recipe_for_menu 実行 (汁物) ← Web検索のみ
```

#### **責任分離の明確化**
- **LLM**: 創造的な献立タイトル生成
- **RAG**: LLMの推論補佐（類似レシピの検索・食材組み合わせ提案・文化的適切性向上）
- **Web**: 具体的なレシピ情報の取得（調理手順）

#### **技術実装への影響**
- **LLM推論の調整**: 独創性を重視したプロンプト設計、飽きの防止を意識した多様性の確保
- **RAG検索の調整**: 独創性の抑制を意識した検索戦略、蓄積レシピからのタイトル抽出機能
- **採用ロジックの実装**: LLM提案とRAG提案の評価基準、ユーザー好みの学習機能
- **WEB検索の調整**: 人間のレシピの品質評価、魂のこもったレシピの識別

#### **この設計思想の重要性**
- **ユーザー体験の向上**: 飽きの来ない献立提案、独創性と実用性のバランス
- **技術的優位性**: LLMの独創性と人間の叡智の組み合わせ
- **差別化要因**: 単純なレシピ検索との違い、AIと人間の協働による新しい価値創造

## 🛠️ MCPツール設計（修正版）

### **1. generate_menu_plan_with_history（献立構成生成）**

#### **仕様（修正版）**
```python
@mcp.tool()
async def generate_menu_plan_with_history(
    inventory_items: List[str],
    user_id: str,
    menu_type: str = "和食"
) -> Dict[str, Any]:
    """
    在庫食材から献立構成を生成（過去履歴を考慮）
    
    Args:
        inventory_items: 在庫食材リスト
        user_id: ユーザーID（履歴チェック用）
        menu_type: 献立のタイプ
    
    Returns:
        {
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
            "ingredient_usage": {
                "used": ["牛乳", "卵", "パン", "バター", "ほうれん草", "胡麻", "白菜", "ハム", "小麦粉"],
                "remaining": []
            },
            "excluded_recipes": ["フレンチトースト", "オムレツ"],
            "fallback_used": true
        }
    """
```

#### **処理フロー**
```python
async def generate_menu_plan_with_history(inventory_items, user_id, menu_type):
    # 1. LLMが献立候補を生成
    menu_candidates = await llm_generate_menu_candidates(inventory_items)
    
    # 2. RAGで類似レシピを検索（LLM補佐）
    rag_suggestions = await rag_search_similar_recipes(menu_candidates)
    
    # 3. LLMがRAGの結果を参考に最終的な献立を決定
    final_menu = await llm_decide_final_menu(menu_candidates, rag_suggestions)
    
    # 4. 過去履歴をチェック
    recent_recipes = await get_recent_recipes(user_id, 14)
    
    # 5. 重複があれば代替案生成
    if has_overlap(final_menu, recent_recipes):
        alternative_menu = await llm_generate_alternative_menu(
            inventory_items, 
            exclude_recipes=recent_recipes
        )
        return alternative_menu
    
    return final_menu
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

#### **仕様（修正版）**
```python
@mcp.tool()
async def search_recipe_for_menu(
    dish_type: str,  # "主菜", "副菜", "汁物"
    title: str,
    available_ingredients: List[str],
    excluded_ingredients: List[str] = None
) -> Dict[str, Any]:
    """
    献立用のレシピ検索（Web検索のみ）
    
    Args:
        dish_type: 料理の種類
        title: 検索するレシピタイトル
        available_ingredients: 使用可能な食材
        excluded_ingredients: 使用禁止食材（他の料理で使用済み）
    
    Returns:
        {
            "recipe": {
                "title": "牛乳と卵のフレンチトースト",
                "ingredients": ["牛乳", "卵", "パン", "バター"],
                "instructions": "1. 牛乳と卵を混ぜる...",
                "source": "cookpad",
                "url": "https://cookpad.com/recipe/789012"
            },
            "ingredient_compatibility": {
                "available": ["牛乳", "卵", "パン", "バター"],
                "missing": [],
                "excluded": ["ほうれん草", "豆腐"]  # 他の料理で使用済み
            }
        }
    """
```

#### **処理フロー（修正版）**
```python
async def search_recipe_for_menu(dish_type, title, available_ingredients, excluded_ingredients):
    # 1. Web検索でレシピを検索
    web_results = await web_search_recipe(title)
    
    # 2. 食材の互換性をチェック
    compatible_recipes = filter_by_ingredients(web_results, available_ingredients, excluded_ingredients)
    
    # 3. 最適なレシピを選択
    best_recipe = select_best_recipe(compatible_recipes, dish_type)
    
    return best_recipe
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

## 🗄️ RAG検索の実装（LLM補佐機能）

### **RAGの補佐機能**
- **レシピタイトルの精度向上**: 既存の美味しいレシピを参考
- **食材の組み合わせ提案**: 実際に使われている組み合わせを学習
- **文化的適切性**: 日本の食文化に合った提案

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

## 🎯 本体ReActループでの使用例（修正版）

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
      "description": "在庫食材から献立構成を生成（過去履歴を考慮）",
      "tool": "generate_menu_plan_with_history",
      "parameters": {
        "inventory_items": "{{task1_result}}",
        "user_id": "{{user_id}}",
        "menu_type": "和食"
      },
      "priority": 2,
      "dependencies": ["task1"]
    },
    {
      "description": "主菜のレシピを検索",
      "tool": "search_recipe_for_menu",
      "parameters": {
        "dish_type": "主菜",
        "title": "{{task2_result.main_dish.title}}",
        "available_ingredients": "{{task2_result.main_dish.ingredients}}",
        "excluded_ingredients": "{{task2_result.side_dish.ingredients + task2_result.soup.ingredients}}"
      },
      "priority": 3,
      "dependencies": ["task2"]
    },
    {
      "description": "副菜のレシピを検索",
      "tool": "search_recipe_for_menu",
      "parameters": {
        "dish_type": "副菜",
        "title": "{{task2_result.side_dish.title}}",
        "available_ingredients": "{{task2_result.side_dish.ingredients}}",
        "excluded_ingredients": "{{task2_result.main_dish.ingredients + task2_result.soup.ingredients}}"
      },
      "priority": 4,
      "dependencies": ["task2"]
    },
    {
      "description": "汁物のレシピを検索",
      "tool": "search_recipe_for_menu",
      "parameters": {
        "dish_type": "汁物",
        "title": "{{task2_result.soup.title}}",
        "available_ingredients": "{{task2_result.soup.ingredients}}",
        "excluded_ingredients": "{{task2_result.main_dish.ingredients + task2_result.side_dish.ingredients}}"
      },
      "priority": 5,
      "dependencies": ["task2"]
    }
  ]
}
```

### **TaskManager（タスク実行）**
```
サイクル1: inventory_list 実行
サイクル2: generate_menu_plan_with_history 実行
  ├─ 在庫食材から献立生成 ← LLMがタイトルを生成
  ├─ 過去履歴をチェック ← データベースで履歴確認
  ├─ 重複があれば代替案生成 ← LLMが代替タイトルを生成
  └─ 最終的な献立を決定 ← タイトルのみ決定
サイクル3: search_recipe_for_menu 実行 (主菜) ← Web検索のみ
サイクル4: search_recipe_for_menu 実行 (副菜) ← Web検索のみ
サイクル5: search_recipe_for_menu 実行 (汁物) ← Web検索のみ
```

### **最終応答生成**
```
"今日の献立をご提案します！（過去14日間の重複を回避）

【主菜】牛乳と卵のフレンチトースト
【副菜】ほうれん草の胡麻和え  
【汁物】白菜とハムのクリームスープ

使用食材: 牛乳、卵、パン、バター、ほうれん草、胡麻、白菜、ハム、小麦粉
残り食材: なし

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

## 🔧 疎結合設計の実現

### **モジュール独立性の実現**
- **recipe_mcp**: 献立生成のみに専念
- **db_mcp**: データベース操作のみに専念
- **呼び出し元**: 過去レシピ取得の責任を負う

### **責任分離の具体例**
```python
# 疎結合設計前（密結合）
async def generate_menu_plan_with_history(token, inventory_items):
    user_id = db_client.authenticate(token)  # ← DB操作
    excluded_recipes = await get_recent_recipes(user_id)  # ← DB操作
    menu = await generate_menu_with_llm(inventory_items, excluded_recipes)

# 疎結合設計後（疎結合）
async def generate_menu_plan_with_history(inventory_items, excluded_recipes):
    menu = await generate_menu_with_llm(inventory_items, excluded_recipes)
    # 過去レシピは外部から受け取る
```

### **疎結合の利点**
- **再利用性**: 他のMCPからも利用可能
- **テスト容易性**: モックデータでテスト可能
- **保守性**: 各モジュールが独立して変更可能
- **拡張性**: 新しい機能を独立して追加可能

## 📊 プロンプト最適化とトークン管理

### **一般的な最大トークン数のベンチマーク**

#### **業界標準**
- **GPT-4o**: 128,000トークン
- **GPT-4o-mini**: 128,000トークン
- **Claude-3.5-Sonnet**: 200,000トークン
- **Gemini-1.5-Pro**: 1,000,000トークン

#### **実用的な上限**
- **推奨**: 4,000-8,000トークン（レスポンス品質維持）
- **許容**: 10,000-15,000トークン（性能劣化あり）
- **危険**: 20,000トークン以上（品質大幅低下）

#### **Morizo AIでの実績**
- **修正前**: 1972/1500トークン（131.5%超過）→ **危険**
- **修正後**: 747/1500トークン（49.8%超過）→ **許容範囲内**
- **改善効果**: **62%の削減**（1972 → 747トークン）

### **ツール数増加の影響予測**
- **安全**: 20個以下（約800トークン）
- **許容**: 30個以下（約1,200トークン）
- **危険**: 40個以上（約1,600トークン）

### **プロンプト最適化戦略**
1. **階層的フィルタリング**: 関連ツールのみを選択
2. **シンプル応答パターン検出**: 挨拶・雑談の早期判定
3. **ツール説明文の短縮**: 30文字以内に制限
4. **デフォルト空返却**: 安全性を優先した設計

---

**作成日**: 2025年1月27日  
**最終更新**: 2025年9月26日  
**作成者**: AIエージェント協働チーム  
**ステータス**: Phase 2完了（疎結合設計実装済み）  
**バージョン**: 2.2（RAG補佐機能・疎結合設計・プロンプト最適化対応）
