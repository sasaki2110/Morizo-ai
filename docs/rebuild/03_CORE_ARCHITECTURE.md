# Morizo AI v2 - コアアーキテクチャ設計

## 📋 概要

**作成日**: 2025年1月29日  
**バージョン**: 1.0  
**目的**: コア機能のアーキテクチャ設計と実装方針

## 🧠 設計思想

### **統一されたReActエージェント**
- **シンプルかつ汎用的**: エージェント機能に特化した設計
- **MCP独立性**: 特定のMCPに依存しない汎用的な設計
- **動的ツール選択**: MCPから動的に取得したツールリストから適切なツールを選択
- **疎結合**: 各MCPの内部実装に依存しない

### **責任分離の徹底**
- **TrueReactAgent**: タスク分解・制御・実行の責任のみ
- **ActionPlanner**: ユーザーリクエストを実行可能なタスクに分解
- **TaskExecutor**: タスクの順序管理と実行制御

## 🏗️ コアアーキテクチャ

### **全体構成**
```
┌─────────────────────────────────────────────────────────────┐
│                    TrueReactAgent                          │
│                 (統一ReActループ)                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   ActionPlanner                            │
│                (タスク分解・依存関係生成)                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   TaskExecutor                             │
│                (タスク実行・並列処理)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   MCP Client                               │
│                (ツール通信・サーバー選択)                    │
└─────────────────────────────────────────────────────────────┘
```

### **データフロー**
```
ユーザーリクエスト
    ↓
ActionPlanner（タスク分解 + 依存関係生成）
    ↓
TrueReactAgent（依存関係解決 + 並列実行グループ化）
    ↓
並列実行グループ1（asyncio.gather）
    ↓
並列実行グループ2（asyncio.gather）
    ↓
データフロー注入（前のタスク結果を次のタスクに注入）
    ↓
MCP Client（ツール呼び出し）
    ↓
レスポンス生成
```

## 🔧 コアコンポーネント

### **1. TrueReactAgent（統一ReActループ）**

#### **役割**
- 全てのユーザーリクエストを統一的に処理する**シンプルかつ汎用的なエージェント**
- タスク分解・制御・実行の責任のみ

#### **設計原則**
- **エージェント機能特化**: タスク分解・制御・実行の責任のみ
- **MCP独立性**: 特定のMCPに依存しない汎用的な設計
- **動的ツール選択**: MCPから動的に取得したツールリストから適切なツールを選択
- **疎結合**: 各MCPの内部実装に依存しない

#### **新機能**
- **依存関係解決**: タスクの実行順序を自動決定
- **データフロー**: 前のタスクの結果を次のタスクに動的に注入
- **並列実行**: 依存関係を満たしたタスクを同時実行（asyncio.gather使用）
- **エラーハンドリング**: 並列実行失敗時の個別実行フォールバック

#### **処理フロー**
```python
async def process_request(user_request: str, user_id: str) -> str:
    # 1. タスク分解
    tasks = await action_planner.decompose(user_request, user_id)
    
    # 2. 依存関係解決
    execution_groups = resolve_dependencies(tasks)
    
    # 3. 並列実行
    results = await execute_parallel_groups(execution_groups)
    
    # 4. レスポンス生成
    response = await generate_response(results)
    
    return response
```

#### **特徴**
- シンプルな挨拶から複雑な在庫管理まで同じフロー
- LLM判断による責任分離
- 動的なレスポンス生成
- MCPの内部実装に依存しない設計
- **真のAIエージェント**: 複雑なタスクを効率的に処理

### **2. ActionPlanner（タスク分解）**

#### **役割**
- ユーザーリクエストを実行可能なタスクに分解
- 利用可能ツールの動的取得
- タスクIDと依存関係の生成

#### **機能**
- 自然言語の理解とタスク分解
- 利用可能ツールの動的取得
- JSON形式でのタスク出力
- Perplexity API統合によるWeb検索機能
- シンプルメッセージの判定
- **タスクIDと依存関係の生成**

#### **出力例**
```json
{
  "tasks": [
    {
      "id": "task1",
      "description": "牛乳を在庫に追加する",
      "tool": "inventory_add",
      "parameters": {
        "item_name": "牛乳",
        "quantity": 1,
        "unit": "本",
        "storage_location": "冷蔵庫"
      },
      "priority": 1,
      "dependencies": []
    },
    {
      "id": "task2",
      "description": "在庫から献立を生成する",
      "tool": "generate_menu_plan_with_history",
      "parameters": {
        "inventory_items": [],
        "excluded_recipes": [],
        "menu_type": "和食"
      },
      "priority": 2,
      "dependencies": ["task1"]
    }
  ]
}
```

#### **実装方針**
```python
class ActionPlanner:
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
    
    async def decompose(self, user_request: str, user_id: str) -> List[Task]:
        # 1. 利用可能ツールの取得
        available_tools = await self.mcp_client.get_available_tools()
        
        # 2. LLMによるタスク分解
        tasks = await self._llm_decompose(user_request, available_tools, user_id)
        
        # 3. 依存関係の生成
        tasks_with_deps = self._generate_dependencies(tasks)
        
        return tasks_with_deps
```

### **3. TaskExecutor（タスク実行）**

#### **役割**
- タスクの順序管理と実行制御
- 依存関係管理
- 並列実行の制御

#### **機能**
- タスクの依存関係管理
- 優先度に基づく実行順序
- エラーハンドリングとリトライ
- 実行結果の収集
- **タスクIDによる検索と状態管理**

#### **並列実行戦略**
```python
class TaskExecutor:
    async def execute_tasks(self, tasks: List[Task]) -> Dict[str, Any]:
        # 1. 依存関係の解決
        execution_groups = self._resolve_dependencies(tasks)
        
        # 2. 並列実行グループの実行
        results = {}
        for group in execution_groups:
            group_results = await asyncio.gather(
                *[self._execute_task(task) for task in group],
                return_exceptions=True
            )
            
            # 3. 結果の処理
            for task, result in zip(group, group_results):
                results[task.id] = result
        
        return results
```

#### **エラーハンドリング**
```python
async def _execute_task(self, task: Task) -> Any:
    try:
        # タスク実行
        result = await self.mcp_client.call_tool(task.tool, task.parameters)
        return result
    except Exception as e:
        # エラーログ出力
        logger.error(f"Task {task.id} failed: {e}")
        
        # フォールバック処理
        if task.fallback_tool:
            return await self.mcp_client.call_tool(task.fallback_tool, task.parameters)
        
        raise e
```

## 🔄 依存関係解決アルゴリズム

### **依存関係グラフ構築**
```python
def build_dependency_graph(tasks: List[Task]) -> Dict[str, List[str]]:
    """タスクの依存関係グラフを構築"""
    graph = {}
    for task in tasks:
        graph[task.id] = task.dependencies
    return graph
```

### **トポロジカルソート**
```python
def topological_sort(graph: Dict[str, List[str]]) -> List[List[str]]:
    """依存関係を満たす実行順序を決定"""
    execution_groups = []
    remaining_tasks = set(graph.keys())
    
    while remaining_tasks:
        # 依存関係を満たしたタスクを特定
        ready_tasks = [
            task for task in remaining_tasks
            if all(dep not in remaining_tasks for dep in graph[task])
        ]
        
        if not ready_tasks:
            raise ValueError("Circular dependency detected")
        
        execution_groups.append(ready_tasks)
        remaining_tasks -= set(ready_tasks)
    
    return execution_groups
```

## 🚀 実装戦略

### **Phase 1: 基本構造**
1. **TrueReactAgent**: 基本的なReActループ
2. **ActionPlanner**: シンプルなタスク分解
3. **TaskExecutor**: 基本的なタスク実行

### **Phase 2: 高度な機能**
1. **依存関係解決**: トポロジカルソートの実装
2. **並列実行**: asyncio.gatherによる並列処理
3. **エラーハンドリング**: フォールバック処理の実装

### **Phase 3: 最適化**
1. **パフォーマンス最適化**: 実行時間の短縮
2. **メモリ最適化**: メモリ使用量の削減
3. **ログ最適化**: ログ出力の最適化

## 📊 成功基準

### **機能面**
- [ ] 統一されたReActエージェントの動作確認
- [ ] タスク分解機能の動作確認
- [ ] 依存関係解決機能の動作確認
- [ ] 並列実行機能の動作確認
- [ ] エラーハンドリング機能の動作確認

### **技術面**
- [ ] 全ファイルが150行以下
- [ ] 循環依存の排除
- [ ] 責任分離の徹底
- [ ] 疎結合設計の実現
- [ ] 並列実行の正常動作

### **品質面**
- [ ] 各コンポーネントの独立動作確認
- [ ] デバッグの容易性確認
- [ ] 拡張性の確認
- [ ] 保守性の確認

---

**このドキュメントは、Morizo AI v2のコアアーキテクチャ設計を定義します。**
**すべてのコア機能は、この設計に基づいて実装されます。**
