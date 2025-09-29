# 並列提示システム設計書

## 📋 概要

**実装目標**: 配列対応レシピ検索機能を基盤として、斬新な提案（LLM生成）と伝統的な提案（RAG検索）の両方を提示する並列提示システムの実装。

## 🎯 レスポンス構造設計

### 1. **基本レスポンス形式**

```python
class ParallelProposalResponse:
    """並列提示レスポンスの基本構造"""
    
    def __init__(self):
        self.type = "parallel_proposal"
        self.novel_proposal = NovelProposal()
        self.traditional_proposal = TraditionalProposal()
        self.user_selection_hint = "どちらの提案がお好みですか？"
```

### 2. **斬新な提案（Novel Proposal）**

```python
class NovelProposal:
    """LLM生成による独創的な献立提案"""
    
    def __init__(self):
        self.title = "斬新な提案"
        self.description = "AI生成による独創的な献立提案"
        self.dishes = {
            "main_dish": {
                "title": "...",
                "recipe_urls": [...],
                "sources": [...],
                "confidence": 0.85
            },
            "side_dish": {
                "title": "...", 
                "recipe_urls": [...],
                "sources": [...],
                "confidence": 0.82
            },
            "soup": {
                "title": "...",
                "recipe_urls": [...],
                "sources": [...],
                "confidence": 0.88
            }
        }
        self.total_recipes = 9  # 各料理3つずつ
```

### 3. **伝統的な提案（Traditional Proposal）**

```python
class TraditionalProposal:
    """RAG検索による実証済み献立提案"""
    
    def __init__(self):
        self.title = "伝統的な提案"
        self.description = "蓄積レシピからの実証済み提案"
        self.dishes = {
            "main_dish": {
                "title": "...",
                "recipe_urls": [...],
                "sources": [...],
                "similarity_score": 0.92
            },
            "side_dish": {
                "title": "...",
                "recipe_urls": [...], 
                "sources": [...],
                "similarity_score": 0.89
            },
            "soup": {
                "title": "...",
                "recipe_urls": [...],
                "sources": [...],
                "similarity_score": 0.87
            }
        }
        self.total_recipes = 9  # 各料理3つずつ
```

### 4. **統合検索レスポンス**

```python
class IntegratedSearchResponse:
    """Web検索 + RAG検索の統合結果"""
    
    def __init__(self):
        self.web_recipes = []  # Perplexity検索結果
        self.rag_recipes = []  # RAG検索結果
        self.novel_proposal = None
        self.traditional_proposal = None
        self.metadata = {
            "search_timestamp": "...",
            "total_queries": 0,
            "web_results_count": 0,
            "rag_results_count": 0
        }
```

## 🔄 データフロー設計

### 1. **タスク実行フロー**

```
1. ユーザーリクエスト: "在庫で作れる献立とレシピを教えて"

2. ActionPlanner: タスク生成
   - task1: generate_menu_plan_with_history
   - task2: search_recipe_from_web_with_rag (新機能)

3. TrueReactAgent: 並列実行
   - 実行: generate_menu_plan_with_history
   - 結果: menu_data
   - 実行: search_recipe_from_web_with_rag
     ├─ Web検索: inventory_items → queries → Perplexity
     ├─ RAG検索: inventory_items → ChromaDB
     └─ 結果統合: Web + RAG → parallel_proposal

4. _generate_final_response: 並列提示判定
   - menu_data + web_data + rag_data → Parallel Response
   - フォールバック: 従来レスポンス
```

### 2. **ヘルパー関数設計**

```python
async def _generate_novel_proposal(menu_data: dict, web_recipes: list) -> NovelProposal:
    """斬新な提案の生成"""
    
async def _generate_traditional_proposal(inventory_items: list, rag_recipes: list) -> TraditionalProposal:
    """伝統的な提案の生成"""

def _format_novel_proposal(novel_proposal: NovelProposal) -> str:
    """斬新な提案のフォーマット"""

def _format_traditional_proposal(traditional_proposal: TraditionalProposal) -> str:
    """伝統的な提案のフォーマット"""

def _create_user_selection_hint() -> str:
    """ユーザー選択ヒントの生成"""
```

## 🚀 実装優先順位

### Phase 1: レスポンス構造実装
1. ParallelProposalResponse クラス実装
2. NovelProposal クラス実装  
3. TraditionalProposal クラス実装
4. 基本テストケース作成

### Phase 2: 検索機能拡張
1. search_recipe_from_web_with_rag 実装
2. RAG検索との統合
3. 提案生成ロジック実装
4. 統合テスト

### Phase 3: UI統合準備
1. レスポンスフォーマット標準化
2. フロントエンド連携API
3. ユーザー選択機能設計

## 📊 成功指標

- ✅ 斬新な提案と伝統的な提案の両方が正常表示
- ✅ 各提案にレシピURL（3つずつ）が含まれる
- ✅ レスポンス時間 < 10秒
- ✅ フォールバック処理が正常動作
- ✅ 統合テスト全ケース成功
