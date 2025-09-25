# Morizo AI - アーキテクチャ設計

## 📋 概要

Morizo AIは、音声認識と自然言語処理を活用したスマートパントリー管理システムです。統一されたReActエージェントアーキテクチャを採用し、シンプルな挨拶から複雑な在庫管理まで、一貫したフローで処理します。

## 🏗️ システムアーキテクチャ

### 全体構成
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js Web   │    │   Expo Mobile   │    │   Voice Input   │
│   Application   │    │   Application   │    │   (Whisper)     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     FastAPI Server        │
                    │   (Python Backend)       │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │    TrueReactAgent         │
                    │  (Unified ReAct Loop)     │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     ActionPlanner          │
                    │   (Task Decomposition)    │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     TaskManager           │
                    │   (Task Execution)        │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │      MCP Client           │
                    │  (Tool Communication)     │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     DB MCP Server         │
                    │   (Database Operations)   │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │      Supabase DB          │
                    │   (PostgreSQL + Auth)    │
                    └───────────────────────────┘
```

## 🧠 コアコンポーネント

### 1. TrueReactAgent（統一ReActループ）
**役割**: 全てのユーザーリクエストを統一的に処理

**処理フロー**:
```
ユーザーリクエスト
    ↓
ActionPlanner（タスク分解）
    ↓
TaskManager（タスク実行）
    ↓
MCP Client（ツール呼び出し）
    ↓
DB MCP Server（データベース操作）
    ↓
レスポンス生成
```

**特徴**:
- シンプルな挨拶から複雑な在庫管理まで同じフロー
- LLM判断による責任分離
- 動的なレスポンス生成

### 2. ActionPlanner（タスク分解）
**役割**: ユーザーリクエストを実行可能なタスクに分解

**機能**:
- 自然言語の理解とタスク分解
- 利用可能ツールの動的取得
- JSON形式でのタスク出力
- シンプルメッセージの判定

**出力例**:
```json
{
  "tasks": [
    {
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
    }
  ]
}
```

### 3. TaskManager（タスク実行）
**役割**: タスクの順序管理と実行制御

**機能**:
- タスクの依存関係管理
- 優先度に基づく実行順序
- エラーハンドリングとリトライ
- 実行結果の収集

### 4. MCP Client（ツール通信）
**役割**: マイクロエージェント間の通信

**機能**:
- stdio接続による軽量通信
- ツールの動的発見と実行
- エラーハンドリング
- レスポンスの正規化

### 5. DB MCP Server（データベース操作）
**役割**: データベースCRUD操作の提供

**利用可能ツール**:
- `inventory_add` - 在庫追加
- `inventory_update_by_id` - ID指定更新
- `inventory_delete_by_id` - ID指定削除
- `inventory_update_by_name` - 名前指定一括更新
- `inventory_delete_by_name` - 名前指定一括削除
- `inventory_update_by_name_oldest` - FIFO原則による最古アイテム更新
- `inventory_update_by_name_latest` - ユーザー指定による最新アイテム更新
- `inventory_delete_by_name_oldest` - FIFO原則による最古アイテム削除
- `inventory_delete_by_name_latest` - ユーザー指定による最新アイテム削除
- `inventory_list` - 在庫一覧取得

## 🔐 認証システム

### 認証方式
- **方式**: Bearer Token認証
- **プロバイダー**: Supabase Auth
- **フロー**: Next.js → FastAPI → Supabase

### 認証フロー
1. **トークン取得**: Next.js側でSupabase認証
2. **API呼び出し**: `Authorization: Bearer <token>`ヘッダー
3. **トークン検証**: Supabaseの`getUser(token)`で検証
4. **ユーザー情報取得**: 認証成功時にユーザー情報を取得
5. **レスポンス**: ユーザーID付きでレスポンスを返却

### セキュリティ考慮事項
- HTTPS通信でのトークン送信
- クライアント側での安全なトークン保存
- サーバー側でのトークン検証のみ
- 必要最小限のユーザー情報取得

## 🗄️ データベース設計

### Supabase PostgreSQL
**テーブル構成**:
- `inventory` - 在庫データ
- `users` - ユーザー情報（Supabase Auth連携）

**在庫テーブル構造**:
```sql
CREATE TABLE inventory (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  item_name VARCHAR(255) NOT NULL,
  quantity DECIMAL(10,2) NOT NULL,
  unit VARCHAR(50) NOT NULL,
  storage_location VARCHAR(100),
  expiry_date DATE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 🔄 データフロー

### 在庫追加フロー
```
ユーザー: "牛乳1本買ってきたから、冷蔵庫に入れておいて"
    ↓
ActionPlanner: inventory_addタスク生成
    ↓
TaskManager: タスク実行
    ↓
MCP Client: inventory_addツール呼び出し
    ↓
DB MCP Server: INSERT文実行
    ↓
Supabase: データベース更新
    ↓
レスポンス: "牛乳1本を冷蔵庫に追加しました"
```

### 在庫一覧取得フロー
```
ユーザー: "今の在庫を教えて"
    ↓
ActionPlanner: inventory_listタスク生成
    ↓
TaskManager: タスク実行
    ↓
MCP Client: inventory_listツール呼び出し
    ↓
DB MCP Server: SELECT文実行
    ↓
Supabase: データベースクエリ
    ↓
レスポンス: "現在の在庫: 牛乳3本、パン2袋..."
```

## 🧪 テストアーキテクチャ

### テスト構成
**統合テスト**:
- `test_true_react_agent_short.py` - メインの統合テスト

**個別テスト**:
- `test_db_mcp_stdio.py` - DB MCPの基本テスト
- `test_delete_by_name.py` - 一括削除テスト
- `test_insert_once.py` - 単一登録テスト
- `test_insert_twice.py` - 複数登録テスト

### テスト方針
- MCPアーキテクチャに統一
- 直接DB操作のテストを排除
- 統合テストで全体をカバー
- シンプルな構成で保守性向上

## 🚀 デプロイメント

### 開発環境
- **ローカル**: `python main.py` または `uvicorn main:app --reload`
- **ポート**: 8000
- **CORS**: 開発用に`*`を許可

### 本番環境考慮事項
- HTTPS通信の強制
- CORS設定の適切な制限
- 環境変数の安全な管理
- ログレベルの調整

## 📊 パフォーマンス考慮事項

### レスポンス時間
- **シンプルメッセージ**: < 1秒
- **在庫操作**: < 2秒
- **複雑なタスク**: < 5秒

### スケーラビリティ
- **セッション管理**: インメモリ（将来はRedis化）
- **データベース**: Supabaseの自動スケーリング
- **MCP通信**: stdio接続による軽量通信

## 🔮 将来の拡張性

### 予定機能
- **確認プロセス**: 操作前検証、確認ダイアログ
- **ロールバック機能**: 操作履歴、Undo/Redo機能
- **レシピ提案機能**: 在庫に基づくレシピ提案
- **音声認識**: Whisper統合による音声入力

### アーキテクチャの進化
- **マイクロサービス化**: 各コンポーネントの独立デプロイ
- **イベント駆動**: 非同期処理による応答性向上
- **AI機能拡張**: より高度な自然言語理解

---

**最終更新**: 2025年9月24日  
**バージョン**: 3.0  
**作成者**: Morizo AI開発チーム
