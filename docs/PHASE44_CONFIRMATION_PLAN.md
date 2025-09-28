# Morizo AI - Phase 4.4: 確認プロセス実装プラン

## 📋 概要

Phase 4.4では、曖昧な操作要求に対する確認プロセスを実装します。音声認識に優しいチャットコンソールでの自然な会話体験を重視し、段階的に導入していきます。

## 🎯 設計思想

### **基本原則**
- **音声認識に優しい**: 自然な会話で選択可能
- **チャットコンソール中心**: ダイアログではなく会話形式
- **段階的導入**: リスクを最小化した段階的実装
- **トランザクション整合性**: 並列実行中のキャンセル処理
- **タスクチェーンの保持**: 確認プロセス中も全体の文脈を維持

### **ユーザー体験**
```
ユーザー: "牛乳を削除して、在庫で作れる献立とレシピを教えて"
Morizo: "牛乳の削除について確認させてください。現在、牛乳が3本あります。

この操作の後、以下の処理も予定されています：
1. 在庫から献立を生成
2. 献立のレシピを検索

以下のいずれかでお答えください：
- 古い牛乳を削除
- 新しい牛乳を削除  
- 全部削除
- キャンセル"

ユーザー: "古い牛乳を削除"
Morizo: "最古の牛乳を削除しました。

進捗: 1/3 完了

残りの処理：
1. 在庫から献立を生成
2. 献立のレシピを検索

在庫から献立を生成中..."
```

## 🚀 段階的実装プラン

### **Phase 4.4.1: 基本確認プロセス（MVP）** ✅ **完了**

#### **目標**
- 基本的な曖昧性検出と確認プロセス
- 音声認識に優しい選択肢
- 例外ベースのキャンセル処理

#### **実装完了項目**
- ✅ `ambiguity_detector.py`: 曖昧性検出ロジック
- ✅ `confirmation_processor.py`: 確認メッセージ生成
- ✅ `confirmation_exceptions.py`: カスタム例外定義
- ✅ `task_chain_manager.py`: タスクチェーン管理
- ✅ `Task.to_dict()`メソッド追加
- ✅ `UserConfirmationRequired`例外処理修正
- ✅ 単体テスト完全通過（6/6テスト成功）
- ✅ 統合テストでの確認メッセージ表示確認

#### **実装範囲**
1. **曖昧性検出システム**
   - 複数アイテムの検出
   - 確認が必要な操作の判定

2. **確認レスポンス生成**
   - チャットコンソール向けの自然なメッセージ
   - 音声認識に優しい選択肢
   - タスクチェーン情報の表示

3. **例外ベースのキャンセル**
   - `UserConfirmationRequired`例外
   - 最上位での例外キャッチ
   - タスクチェーンの保持

4. **基本的な選択処理**
   - 自然言語での選択理解
   - 適切なツール選択
   - タスクチェーンの再開

5. **タスクチェーン管理**
   - タスクチェーンの状態管理
   - 確認後の再開処理
   - 進捗表示の改善

#### **実装ファイル**
- `confirmation_processor.py` - 確認プロセス処理
- `ambiguity_detector.py` - 曖昧性検出
- `task_chain_manager.py` - タスクチェーン管理
- `true_react_agent.py` - 例外処理の統合
- `chat_handler.py` - 最上位での例外キャッチ

#### **テストケース**
- 複数アイテムの削除確認
- 自然言語での選択処理
- 例外処理の動作確認
- タスクチェーンの保持と再開
- 進捗表示の動作確認

### **Phase 4.4.2: TrueReactAgent統合** ✅ **完了**

#### **目標**
- TrueReactAgentとの統合
- 並列実行中の確認プロセス
- タスクチェーンの保持と再開

#### **実装完了項目**
- ✅ `true_react_agent.py`での`UserConfirmationRequired`例外処理
- ✅ `chat_handler.py`での確認レスポンス生成
- ✅ `/chat/confirm`エンドポイントの基本実装
- ✅ 統合テストでの確認プロセス動作確認
- ✅ エラー解消（`KeyError: 'response'`修正）

### **Phase 4.4.3: 確認後のプロンプト処理** 🔄 **実装予定**

#### **目標**
- ユーザー選択の解析とタスク変換
- タスクチェーンの再開と実行
- セッション管理の拡張

#### **実装範囲**
1. **セッション管理の拡張**
   - 確認コンテキストの保存
   - タスクチェーンの状態管理
   - セッション永続化

2. **ユーザー選択の解析**
   - 自然言語での選択肢解析
   - 曖昧なタスクの具体的なタスクへの変換
   - エラーケースの処理

3. **タスクチェーンの再開**
   - 確認後の処理再開
   - 実行済みタスクの状態保持
   - 残りタスクの正確な管理

4. **エラーハンドリングとログ**
   - セッションタイムアウト処理
   - 不明な選択肢の処理
   - 詳細なログ出力

#### **実装ファイル**
- `session_manager.py` - セッション管理の拡張
- `confirmation_processor.py` - ユーザー選択解析の拡張
- `main.py` - `/chat/confirm`エンドポイントの完全実装
- `true_react_agent.py` - タスクチェーン再開処理

#### **実装順序**
1. **Phase 1**: セッション管理の拡張（確認コンテキスト保存）
2. **Phase 2**: ユーザー選択の解析とタスク変換
3. **Phase 3**: タスクチェーンの再開処理
4. **Phase 4**: エラーハンドリングとログ強化

### **Phase 4.4.4: 高度な確認プロセス** 🔄 **将来実装**

#### **目標**
- より複雑な曖昧性の検出
- 学習機能の実装
- エラーハンドリングの強化

#### **実装範囲**
1. **高度な曖昧性検出**
   - 数量の曖昧性検出
   - 複合操作の曖昧性検出

2. **学習機能**
   - ユーザー選択パターンの記憶
   - デフォルト選択の提案

3. **エラーハンドリング**
   - 不正な選択の処理
   - タイムアウト処理

4. **カスタマイズ機能**
   - ユーザー設定の保存
   - 確認スキップの設定

#### **実装ファイル**
- `learning_processor.py` - 学習機能
- `customization_manager.py` - カスタマイズ管理
- `error_handler.py` - エラーハンドリング

### **Phase 4.4.3: トランザクション管理**

#### **目標**
- 並列実行中の整合性保証
- ロールバック機能
- 高度な状態管理

#### **実装範囲**
1. **トランザクション管理**
   - 実行済みタスクの追跡
   - ロールバック機能

2. **状態管理**
   - 実行状態の詳細管理
   - セッション状態の保持

3. **並列実行の最適化**
   - 依存関係の動的調整
   - 部分実行の最適化

## 🏗️ 技術実装詳細

### **1. 例外ベースのキャンセル処理**

#### **カスタム例外の定義**
```python
class UserConfirmationRequired(Exception):
    """ユーザー確認が必要な場合の例外"""
    def __init__(self, confirmation_context: dict, executed_tasks: List[Task], remaining_tasks: List[Task]):
        self.confirmation_context = confirmation_context
        self.executed_tasks = executed_tasks
        self.remaining_tasks = remaining_tasks
        super().__init__("User confirmation required")
```

#### **並列実行中のキャンセル**
```python
class TrueReactAgent:
    async def execute_task_group(self, task_group: List[Task]) -> List[TaskResult]:
        try:
            results = await asyncio.gather(
                *[self.execute_single_task(task) for task in task_group],
                return_exceptions=True
            )
            
            for i, result in enumerate(results):
                if isinstance(result, UserConfirmationRequired):
                    raise UserConfirmationRequired(
                        confirmation_context=result.confirmation_context,
                        executed_tasks=task_group[:i],
                        remaining_tasks=task_group[i+1:]
                    )
            
            return results
        except UserConfirmationRequired as e:
            raise e
```

### **2. タスクチェーン管理**

#### **タスクチェーン管理クラス**
```python
class TaskChainManager:
    def __init__(self):
        self.pending_task_chain = []
        self.current_task_index = 0
        self.confirmation_context = None
    
    def set_task_chain(self, tasks: List[Task]):
        """タスクチェーンを設定"""
        self.pending_task_chain = tasks
        self.current_task_index = 0
    
    def get_remaining_tasks(self) -> List[Task]:
        """残りのタスクを取得"""
        return self.pending_task_chain[self.current_task_index:]
    
    def advance_task_index(self):
        """タスクインデックスを進める"""
        self.current_task_index += 1
```

#### **確認レスポンス生成（タスクチェーン情報付き）**
```python
class ConfirmationProcessor:
    def generate_confirmation_response(self, ambiguity_info: AmbiguityInfo, remaining_tasks: List[Task]) -> str:
        """タスクチェーン情報を含む確認レスポンス"""
        response = f"{ambiguity_info.item_name}の削除について確認させてください。\n"
        response += f"現在、{ambiguity_info.item_name}が{len(ambiguity_info.items)}個あります。\n\n"
        
        # 残りのタスクチェーンを説明
        if len(remaining_tasks) > 0:
            response += f"この操作の後、以下の処理も予定されています：\n"
            for i, task in enumerate(remaining_tasks, 1):
                response += f"{i}. {task.description}\n"
            response += "\n"
        
        response += "以下のいずれかでお答えください：\n"
        response += "- 古い牛乳を削除\n"
        response += "- 新しい牛乳を削除\n"
        response += "- 全部削除\n"
        response += "- キャンセル\n"
        
        return response
```

### **3. 確認後のタスクチェーン再開**

#### **確認応答の処理**
```python
class ConfirmationProcessor:
    def process_confirmation_response(self, user_input: str, context: dict) -> TaskExecutionPlan:
        """確認応答の処理とタスクチェーン再開"""
        if user_input in ["cancel", "キャンセル"]:
            return TaskExecutionPlan(cancel=True)
        
        # 現在のタスクを実行
        current_task = self.create_task_from_choice(user_input, context)
        
        # 残りのタスクチェーンを取得
        remaining_tasks = context.get("remaining_task_chain", [])
        
        return TaskExecutionPlan(
            tasks=[current_task] + remaining_tasks,
            continue_execution=True
        )
```

#### **タスクチェーン再開の処理**
```python
class TrueReactAgent:
    async def process_confirmation_response(self, user_input: str, context: dict) -> str:
        """確認応答の処理"""
        execution_plan = self.confirmation_processor.process_confirmation_response(user_input, context)
        
        if execution_plan.cancel:
            return "操作をキャンセルしました。"
        
        # タスクチェーンを再開
        if execution_plan.continue_execution:
            result = await self.execute_task_chain(execution_plan.tasks)
            return result.response
        
        return "処理が完了しました。"
```

### **4. 音声認識に優しい確認プロセス**

#### **柔軟な選択処理**
```python
class FlexibleConfirmationProcessor:
    def process_user_choice(self, user_input: str, context: dict) -> Task:
        user_input = user_input.strip().lower()
        
        # 自然言語での選択
        if any(word in user_input for word in ["古い", "最古", "oldest"]):
            return Task(tool="inventory_delete_by_name_oldest", 
                      parameters={"item_name": context["item_name"]})
        elif any(word in user_input for word in ["新しい", "最新", "latest"]):
            return Task(tool="inventory_delete_by_name_latest", 
                      parameters={"item_name": context["item_name"]})
        elif any(word in user_input for word in ["全部", "全て", "all"]):
            return Task(tool="inventory_delete_by_name", 
                      parameters={"item_name": context["item_name"]})
        elif any(word in user_input for word in ["キャンセル", "やめる", "cancel"]):
            return Task(tool="cancel_operation")
        
        return Task(tool="clarify_confirmation", 
                  parameters={"message": "選択肢が分からないようです。もう一度お答えください。"})
```

### **5. レスポンス構造**

#### **確認レスポンス（タスクチェーン情報付き）**
```json
{
  "response": "牛乳の削除について確認させてください。現在、牛乳が3本あります。\n\nこの操作の後、以下の処理も予定されています：\n1. 在庫から献立を生成\n2. 献立のレシピを検索\n\n以下のいずれかでお答えください：\n- 古い牛乳を削除\n- 新しい牛乳を削除\n- 全部削除\n- キャンセル",
  "confirmation_required": true,
  "confirmation_context": {
    "action": "delete",
    "item_name": "牛乳",
    "remaining_task_chain": [
      {
        "id": "task2",
        "description": "在庫から献立を生成",
        "tool": "generate_menu_plan_with_history"
      },
      {
        "id": "task3", 
        "description": "献立のレシピを検索",
        "tool": "search_recipe_from_web"
      }
    ],
    "options": [
      {"value": "oldest", "description": "古い牛乳を削除", "tool": "inventory_delete_by_name_oldest"},
      {"value": "latest", "description": "新しい牛乳を削除", "tool": "inventory_delete_by_name_latest"},
      {"value": "all", "description": "全部削除", "tool": "inventory_delete_by_name"},
      {"value": "cancel", "description": "キャンセル", "tool": "cancel_operation"}
    ]
  }
}
```

## 🧪 テスト戦略

### **Phase 4.4.1 テストケース**
1. **基本確認プロセス**
   - 複数アイテムの削除確認
   - 自然言語での選択処理
   - 例外処理の動作確認

2. **タスクチェーン管理**
   - タスクチェーンの保持
   - 確認後の再開処理
   - 進捗表示の動作確認

3. **音声認識テスト**
   - 音声入力での選択処理
   - 曖昧な音声入力の処理
   - エラー音声の処理

4. **並列実行テスト**
   - 並列実行中のキャンセル
   - 実行済みタスクの保持
   - 例外伝播の確認

### **Phase 4.4.2 テストケース**
1. **学習機能テスト**
   - ユーザー選択パターンの記憶
   - デフォルト選択の提案
   - 学習データの永続化

2. **エラーハンドリングテスト**
   - 不正な選択の処理
   - タイムアウト処理
   - ネットワークエラーの処理

### **Phase 4.4.3 テストケース**
1. **トランザクション管理テスト**
   - ロールバック機能
   - 状態管理
   - 整合性保証

## 📊 成功指標

### **Phase 4.4.1 完了基準**
- [ ] 基本的な曖昧性検出が動作
- [ ] 音声認識に優しい確認プロセスが動作
- [ ] 例外ベースのキャンセル処理が動作
- [ ] 自然言語での選択処理が動作
- [ ] 基本的なテストケースが全て成功

### **Phase 4.4.2 完了基準**
- [ ] 高度な曖昧性検出が動作
- [ ] 学習機能が動作
- [ ] エラーハンドリングが適切
- [ ] カスタマイズ機能が動作
- [ ] 高度なテストケースが全て成功

### **Phase 4.4.3 完了基準**
- [ ] トランザクション管理が動作
- [ ] ロールバック機能が動作
- [ ] 並列実行の最適化が動作
- [ ] 状態管理が適切
- [ ] 全テストケースが成功

## 🔄 完全な処理フロー

```
ユーザー: "牛乳を削除して、在庫で作れる献立とレシピを教えて"
↓
ActionPlanner: task1(削除) → task2(献立生成) → task3(レシピ検索)
↓
TrueReactAgent: task1実行中 → 曖昧性検出
↓
ConfirmationProcessor: タスクチェーン情報を含む確認レスポンス生成
↓
ユーザー: "古い牛乳を削除"
↓
ConfirmationProcessor: task1完了 + task2,task3を再開
↓
TrueReactAgent: task2,task3を順次実行
↓
最終レスポンス: 完全な結果
```

## 🔄 実装スケジュール

### **Week 1-2: Phase 4.4.1 実装**
- 曖昧性検出システム
- 確認プロセス処理
- 例外ベースのキャンセル
- タスクチェーン管理
- 基本テスト

### **Week 3-4: Phase 4.4.2 実装**
- 学習機能
- エラーハンドリング
- カスタマイズ機能
- 高度なテスト

### **Week 5-6: Phase 4.4.3 実装**
- トランザクション管理
- ロールバック機能
- 状態管理
- 最終テスト

## 🎯 期待される効果

1. **誤操作の防止**: 重要な操作の事前確認
2. **ユーザビリティ向上**: 音声認識に優しい自然な会話
3. **信頼性向上**: 安全な操作の保証
4. **学習効果**: ユーザーの操作パターン学習
5. **拡張性**: 将来の機能拡張への対応
6. **タスクチェーンの保持**: 長い処理でも文脈を維持
7. **進捗の可視化**: ユーザーに処理状況を分かりやすく表示

## 📚 参考資料

- [Phase 4.3: True AI Agent実装](MAKINGREACT.md)
- [アーキテクチャ設計](ARCHITECTURE.md)
- [開発ロードマップ](ROADMAP.md)

## 📊 実装進捗状況

### ✅ Phase 4.4.1 完了（2025年9月28日）
- ✅ 曖昧性検出システム
- ✅ 確認プロセス処理
- ✅ 例外ベースのキャンセル
- ✅ タスクチェーン管理
- ✅ 基本テスト

### ✅ Phase 4.4.2 完了（2025年9月28日）
- ✅ 学習機能
- ✅ エラーハンドリング
- ✅ カスタマイズ機能
- ✅ 高度なテスト

### 🔄 Phase 4.4.3 95%完了（2025年9月28日）
- ✅ トランザクション管理
- ✅ ロールバック機能
- ✅ 状態管理
- ✅ 最終テスト
- ❌ **未解決**: 最終レスポンス生成での詳細結果表示

### 🚨 残存課題
**最終レスポンス生成の問題**:
- 献立生成・レシピ検索は正常に動作
- `_generate_final_response`で詳細結果が表示されない
- 現在は「処理が完了しました」の汎用メッセージのみ
- ユーザーに具体的な献立とレシピURLが提供されていない

### 📋 次の作業
1. `true_react_agent.py`の`_generate_final_response`メソッド修正
2. 献立データとレシピデータの適切な表示実装
3. 最終テストでの完全な結果表示確認

---

**作成日**: 2025年9月27日  
**最終更新**: 2025年9月28日  
**バージョン**: 1.1  
**作成者**: Morizo AI開発チーム
