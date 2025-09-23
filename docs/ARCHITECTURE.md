# Morizo AI - アーキテクチャ設計

## 全体アーキテクチャ

### **現在のアーキテクチャ（リファクタリング完了）**
```
Morizo AI Agent (main.py - 145行)
├── FastAPI Server
├── 統一されたReActエージェントシステム
│   ├── ActionPlanner (行動計画立案)
│   │   ├── 複雑な要求の分析
│   │   ├── タスク分解（単純・複雑問わず）
│   │   ├── 依存関係の特定
│   │   └── 優先度の設定
│   ├── TaskManager (タスク管理)
│   │   ├── タスクの状態管理
│   │   ├── 依存関係の検証
│   │   ├── 実行順序の最適化
│   │   └── 進捗追跡
│   └── TrueReactAgent (統一ReActループ)
│       ├── 観察: 現在の状況把握
│       ├── 思考: 最適な行動の決定
│       ├── 決定: ツール選択とパラメータ設定
│       └── 行動: MCPツールの実行
├── モジュラー設計（15モジュール）
│   ├── config/ (設定管理)
│   │   ├── logging_config.py
│   │   └── cors_config.py
│   ├── auth/ (認証・セキュリティ)
│   │   └── authentication.py
│   ├── agents/ (エージェント・MCP)
│   │   └── mcp_client.py
│   ├── models/ (データモデル)
│   │   └── requests.py
│   ├── utils/ (ユーティリティ)
│   │   ├── session_utils.py
│   │   └── llm_utils.py
│   └── handlers/ (ハンドラー)
│       ├── chat_handler.py
│       └── session_handler.py
├── セッション管理システム
│   ├── SessionContext (メモリ内)
│   ├── 操作履歴管理 (最大10件)
│   ├── 在庫状態管理 (ID情報含む)
│   └── 自動タイムアウト
├── FIFO原則による在庫管理
│   ├── 個別在庫法
│   ├── 最古→最新の操作順序
│   └── ユーザー指定対応
├── MCP Client (stdio接続)
├── Supabase CRUD MCP Server
│   ├── inventory_add
│   ├── inventory_list
│   ├── inventory_get
│   ├── inventory_update
│   └── inventory_delete
└── Supabase PostgreSQL
```

### **目標アーキテクチャ（LangChain統合）**
```
Morizo AI Agent (main.py)
├── FastAPI Server
├── LangChain ReAct Agent
│   ├── Tool Selection
│   ├── MCP Tools (LangChain化)
│   └── Recipe Tools
├── MCP Server (stdio接続)
└── Supabase PostgreSQL
```

## AI Agent基本ループ

### **統一されたReActエージェントループ（実装完了）**
```
すべての要求の処理（単純・複雑問わず）:
1. 要求分析 → ActionPlanner
2. タスク分解 → 個別タスクの生成（1個または複数）
3. 依存関係特定 → 実行順序の決定
4. ReActループ実行:
   - 観察: 現在の状況把握
   - 思考: 最適な行動の決定
   - 決定: ツール選択とパラメータ設定
   - 行動: MCPツールの実行
5. 完了報告 → ユーザーへの結果通知
```

### **リファクタリング前の混在ループ（削除済み）**
```
❌ 削除された混在システム:
- なんちゃってReAct（単一サイクル）
- 真のReAct（複数サイクル）
- 判定ロジックによる分岐
→ 統一されたReActエージェントに統合
```

### Action（行動）
- Supabase CRUD操作
- レシピ生成・提案
- Web検索実行
- レスポンス生成

## MCP設計思想

### stdio通信による軽量実装
- HTTPサーバー不要
- ローカル通信のみ
- 設定が簡単

### モジュラー設計
- 各機能を独立したMCPサーバーとして分離
- 必要な分だけMCPサーバーを追加
- 個別にテスト可能

### スケーラブルな拡張性
- 新しいツールの追加が容易
- プラグインシステム
- カスタムツール対応

## 技術スタック

### バックエンド
- **FastAPI**: メインAPIサーバー
- **OpenAI API**: LLM・音声認識
- **Supabase**: 認証・データベース
- **FastMCP**: MCPサーバー実装

### フロントエンド
- **Next.js**: Webアプリケーション
- **Supabase Auth**: 認証管理
- **Web Speech API**: 音声入力

## データフロー

1. **音声入力** → Web Speech API → テキスト変換
2. **テキスト解析** → Perception MCP → 意図理解
3. **思考・判断** → Cognition MCP → ツール選択
4. **行動実行** → Action MCP → Supabase CRUD
5. **レスポンス生成** → LLM → 自然な応答

## セキュリティ設計

### 認証・認可
- Supabase認証システム
- Bearer Token認証
- Row Level Security (RLS)

### データ保護
- ユーザー別データ分離
- API権限管理
- データ暗号化

## 拡張性

### Phase 1: 基本機能
- 単純なチャット機能
- 基本的なCRUD操作

### Phase 2: MCP化 ✅ **完了**
- モジュラー設計
- ツール分離
- stdio接続
- main.py統合

### Phase 3: 動的AIエージェント化 ✅ **完了**
- ReAct Agent
- 動的ツール選択
- 自然言語理解
- 完全動的MCPエージェント

### Phase 4.1: 基本コンテキスト管理 ✅ **完了**
- セッション管理
- 操作履歴
- 在庫状態管理

### Phase 4.2: インテリジェント判断 ✅ **完了**
- FIFO原則
- 個別在庫法
- ユーザー指定対応

### Phase 4.3: 真のAIエージェント化 ✅ **完了**
- ActionPlanner
- TaskManager
- TrueReactAgent

### Phase 4.4: 確認プロセス 🚀 **計画中**
- 操作前検証
- 確認ダイアログ
- エラーハンドリング強化

### Phase 4.5: ロールバック機能 🚀 **計画中**
- 操作履歴
- ロールバック
- Undo/Redo機能

### Phase 5: リファクタリング ✅ **完了**
- 71%のコード削減
- 完全な責任分離
- 統一されたReActエージェント
- 15モジュールに分割
