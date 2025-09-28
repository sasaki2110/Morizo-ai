# Morizo AI - Python AIエージェント

Smart Pantry MVPのAIエージェント（LLM処理 + 音声認識）


## プロジェクト構成

- **Morizo-ai** - Python AIエージェント（このリポジトリ）
- **Morizo-web** - Next.js Webアプリ（別リポジトリ）
- **Morizo-mobile** - Expo モバイルアプリ（別リポジトリ）

## 📁 フォルダ構成（最適化後）

```
/app/Morizo-ai/
├── morizo_ai.log            # 📊 現在の作業ログ
├── PRIORITY_TASK.md         # 🎯 最優先課題
├── LOG_SUMMARY.md          # 📋 ログ要約
├── AGENTS.md               # 🤝 協働ルール
├── README.md               # 📖 プロジェクト概要
├── main.py                 # メインアプリケーション
├── true_react_agent.py     # 真のReActエージェント
├── action_planner.py       # 行動計画立案
├── task_manager.py         # タスク管理
├── config/                 # 設定管理
├── auth/                   # 認証・セキュリティ
├── agents/                 # エージェント・MCP
├── models/                 # データモデル
├── utils/                  # ユーティリティ
├── handlers/               # ハンドラー
├── tests/                  # テスト
└── docs/
    ├── PHASE44_CONFIRMATION_PLAN.md  # 現在の作業
    ├── reference/           # 参考情報（必要時のみ）
    │   ├── ARCHITECTURE.md
    │   ├── ROADMAP.md
    │   └── DEPENDENCY_LEARNING_PLAN.md
    └── archive/            # アーカイブ
        └── morizo_ai.log.1  # 過去ログ
```

### 📋 ドキュメント優先順位
1. **PRIORITY_TASK.md** - 最優先課題（常に参照）
2. **LOG_SUMMARY.md** - ログ要約（10行程度）
3. **AGENTS.md** - 協働ルール（最重要）
4. **docs/reference/** - 参考情報（必要時のみ）

## 機能

### AIエージェント
- OpenAI GPT-4による自然言語処理
- 音声コマンドの意図解析
- 食材在庫管理の自動化
- レシピ提案の生成
- **真のAIエージェント**: 複雑な要求のタスク分解とReActループ実行
- **動的MCPエージェント**: リアルタイムツール選択と実行
- **挨拶パターンの適切な処理**: 2025/9/24完了
- **不適切なタスク生成の検出とフォールバック**: 2025/9/24完了
- **プロンプト最適化とエラーハンドリング改善**: 2025/9/24完了

### ✅ 解決済み課題
- **在庫数量不一致問題の解決**: ✅ **2025年9月24日解決**
- **LLM応答の完全性確保**: ✅ **max_tokens増加とプロンプト最適化で解決**
- **在庫集計ロジックの見直し**: ✅ **LLM集計指示の強化で解決**

### セッション管理システム
- **メモリ内セッション**: ユーザー別のセッション管理
- **操作履歴**: 最大10件の操作履歴保持
- **在庫状態管理**: ID情報を含む在庫一覧の保持
- **自動タイムアウト**: 期限切れセッションの自動クリア

### 真のAIエージェントシステム
- **ActionPlanner**: 複雑な要求のタスク分解と依存関係管理
- **TaskManager**: タスクの状態管理と実行順序の最適化
- **TrueReactAgent**: 観察→思考→決定→行動の完全なループ
- **統合テスト**: 複雑な要求のテストとエラー処理の検証

### 🚀 レシピ検索統合システム（2025/9/27完成）
- **Phase A: 依存関係解決**: タスクの実行順序を自動決定
- **Phase B: データフロー**: 前のタスクの結果を次のタスクに動的に渡す
- **Phase C: 並列実行**: 依存関係を満たしたタスクを同時実行（asyncio.gather使用）
- **MCPツール統合**: 実際のツールが正常に動作
- **LLM統合**: 最終結果の整形も動作
- **並列実行テスト**: 複雑なシナリオでの動作確認
- **レシピ検索統合**: 献立生成→レシピ検索の完全フロー動作確認完了

### 🤔 確認プロセスシステム（2025/9/28 Phase 4.4.1-4.4.2完成）
- **曖昧性検出**: 複数アイテム操作時の自動検出
- **音声認識対応**: チャットコンソールでの自然な会話
- **タスクチェーン保持**: 確認プロセス中も全体の文脈を維持
- **例外ベース処理**: `UserConfirmationRequired`による適切な中断
- **確認メッセージ生成**: 詳細な選択肢と進捗表示
- **統合テスト完了**: 確認プロセスの動作確認済み
- **Phase 4.4.3実装予定**: 確認後のプロンプト処理

### 在庫管理システム
- **個別在庫法**: 各アイテムを個別に管理
- **ユーザー指定**: 「古い方」「最新」指定時は適切なアイテムを選択
- **ID取得**: セッションから適切なIDを自動取得
- **削除・更新機能**: 2025/9/25完了
  - `inventory_delete_by_name_oldest`: ユーザー指定による最古アイテム削除
  - `inventory_delete_by_name_latest`: ユーザー指定による最新アイテム削除
  - `inventory_update_by_name_oldest`: ユーザー指定による最古アイテム更新
  - `inventory_update_by_name_latest`: ユーザー指定による最新アイテム更新

### データベース連携
- Supabase PostgreSQLとの連携
- 在庫データの読み書き
- ユーザー認証情報の取得
- **MCP統合**: マイクロエージェント通信プロトコル

## クイックスタート

### 1. 環境準備
```bash
cd /app/Morizo-ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 環境変数設定
```bash
cp .env.example .env
# .envファイルに必要な設定を記入
```

### 3. サーバー起動
```bash
python main.py
# または
uvicorn main:app --reload --port 8000
```

### 4. 動作確認
```bash
curl http://localhost:8000/health
```

## 🔐 認証

### 認証方式
- **方式**: `Authorization: Bearer <supabase-token>`
- **トークン取得**: Supabase認証システム
- **検証**: Supabaseの`getUser(token)`でトークン有効性確認

### 認証フロー
1. **トークン取得**: Next.js側でSupabase認証からトークンを取得
2. **API呼び出し**: `Authorization: Bearer <token>`ヘッダーでAPIを呼び出し
3. **トークン検証**: Python側でSupabaseの`getUser(token)`でトークンを検証
4. **ユーザー情報取得**: 認証成功時にユーザー情報を取得
5. **レスポンス**: ユーザーID付きでレスポンスを返却

### 認証が必要なエンドポイント
- `POST /chat` - チャット機能（認証必須）

### 認証テスト例
```bash
# 認証なし（401エラー）
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "こんにちは、Morizo！"}'

# 認証あり（正常動作）
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <supabase-token>" \
  -d '{"message": "こんにちは、Morizo！"}'
```

## ドキュメント

- **[詳細セットアップ](docs/SETUP.md)** - セットアップ手順（MCP依存関係問題の解決手順含む）
- **[API仕様](docs/API.md)** - エンドポイント詳細
- **[アーキテクチャ](docs/ARCHITECTURE.md)** - システム設計
- **[開発ロードマップ](docs/ROADMAP.md)** - 開発計画・ToDo
- **[自前ReActループ実装フロー](docs/MAKINGREACT.md)** - 動的MCPエージェント実装手順

## 技術スタック

- **フレームワーク**: FastAPI 0.117.1
- **言語**: Python 3.11+
- **AI/ML**: OpenAI API 1.108.1 (GPT-4, Whisper)
- **データベース**: Supabase PostgreSQL 2.19.0
- **認証**: Supabase Auth
- **FastMCP**: Micro-Agent Communication Protocol 2.12.3
- **HTTP**: httpx 0.28.1

## 🧪 テスト

### テストファイル構成（整理済み）
**統合テスト**:
- `tests/test_true_react_agent_short.py` - メインの統合テスト（シンプル版）

**個別テスト**:
- `tests/test_db_mcp_stdio.py` - DB MCPの基本テスト
- `tests/test_delete_by_name.py` - 一括削除テスト
- `tests/test_insert_once.py` - 単一登録テスト
- `tests/test_insert_twice.py` - 複数登録テスト

### テスト実行方法
```bash
# 統合テスト（シンプル版）- 推奨
python tests/test_true_react_agent_short.py

# 個別テスト
python tests/test_db_mcp_stdio.py
python tests/test_delete_by_name.py
python tests/test_insert_once.py
python tests/test_insert_twice.py
```


## 🎉 最新の成果

**2025年9月24日** - プロジェクト整理完了！スッキリした構成に！

### ✅ プロジェクト整理成果
- **バックアップファイル削除**: `main_old.py`と`backups/`ディレクトリを削除
- **テストファイル整理**: 不要なテストファイルを削除し、シンプルな構成に
- **MCPアーキテクチャ統一**: 直接DB操作のテストを削除し、MCP経由のテストに統一
- **プロジェクト構成の最適化**: 必要最小限のファイルで管理しやすい構成

### ✅ リファクタリング成果
- **71%のコード削減**: main.py 504行 → 145行
- **完全な責任分離**: 15のモジュールに分割
- **統一されたReActエージェント**: 単純・複雑問わず同じフロー
- **真のAIエージェント化**: ActionPlanner + TaskManager + TrueReactAgent
- **保守性の大幅向上**: 各モジュールが独立して動作

### ✅ 実装完了
- **FastMCP 2.12.3**でMCPサーバー構築
- **5つのCRUDツール**が正常動作
- **Supabase認証**と**データベース操作**が統合
- **stdio接続**で軽量動作
- **完全動的MCPエージェント**実現
- **自然言語での在庫管理**が実現
- **ハードコーディングの完全排除**

### ✅ 最新成果（2025年9月26日）
- **レシピMCP統合**: 献立提案機能を主処理に組み込み完了
- **プロンプト最適化**: 1972トークン → 747トークン（62%削減）
- **階層的フィルタリング**: 関連ツールのみ選択（16個 → 4個）
- **シンプル応答パターン検出**: 挨拶・雑談の早期判定
- **ツール説明文短縮**: 30文字以内に制限
- **利用可能ツール**: 18個（DB MCP: 15個 + Recipe MCP: 3個）
- **RAG検索機能**: ベクトルDB検索による類似レシピ検索（完了）
- **Perplexity API統合**: Web検索機能による人間のレシピ取得（完了）
- **テストスイート完成**: MCPサーバー個別テスト + 統合テスト（完了）

### 🚀 次のステップ
- **Phase 4.4**: 確認プロセス（操作前検証、確認ダイアログ）
- **Phase 4.5**: ロールバック機能（操作履歴、Undo/Redo機能）
- **依存関係エラー修正**: タスク検証ロジックの改善
- **レシピMCP機能拡張**: RAG補佐システムの実装

## 関連リポジトリ

- **[Morizo-web](../Morizo-web)**: Next.js Webアプリケーション
- **[Morizo-mobile](../Morizo-mobile)**: Expo モバイルアプリ

## 開発状況

- ✅ **Phase 1**: 基本機能（完了）
- ✅ **Phase 2**: MCP化（完了）
- ✅ **Phase 3**: 動的AIエージェント化（完了）
- ✅ **Phase 4.1**: 基本コンテキスト管理（完了）
- ✅ **Phase 4.2**: インテリジェント判断（完了）
- ✅ **Phase 4.3**: 真のAIエージェント化（完了）
- ✅ **リファクタリング**: 統一されたReActエージェント（完了）
- ✅ **Perplexity API統合**: Web検索機能（完了）
- 🚀 **Phase 4.4**: 確認プロセス（計画中）
- 🚀 **Phase 4.5**: ロールバック機能（計画中）

詳細は[開発ロードマップ](docs/ROADMAP.md)と[自前ReActループ実装フロー](docs/MAKINGREACT.md)をご確認ください。

## ライセンス

このプロジェクトは**プロプライエタリライセンス**の下で提供されています。

- **商用利用**: 別途ライセンス契約が必要
- **改変・再配布**: 禁止
- **個人利用**: 許可（非商用のみ）
- **教育・研究目的**: 許可（適切な帰属表示が必要）

詳細は[LICENSE](LICENSE)ファイルをご確認ください。

## AIエージェント協働

このプロジェクトでは、AIエージェントとの協働ルールを定めています。
詳細は[AGENTS.md](AGENTS.md)をご確認ください。