# Morizo AI - Python AIエージェント

Smart Pantry MVPのAIエージェント（LLM処理 + 音声認識 ✅ **実装済み**）


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

### 🚀 新機能: ストリーミング機能 + 並列化 ✅ **実装完了**

#### リアルタイム進捗表示
- **Server-Sent Events (SSE)**: リアルタイム進捗表示
- **進捗バー**: 0% → 25% → 50% → 75% → 100%の完全な進捗更新
- **タスク状況**: 現在実行中のタスクをリアルタイムで表示
- **エラー通知**: エラー発生時の適切な通知
- **タイムアウト対応**: 120秒（Web検索処理時間を考慮）

#### 並列化による高速化
- **レシピ検索の並列化**: search_recipe_from_webの完全並列化
- **処理時間短縮**: 54秒 → 9秒（**83%改善**）
- **API効率**: 6倍向上（並列実行）
- **ユーザー体験**: 大幅改善
- **エラー耐性**: 完全保持（return_exceptions=True）

#### 技術仕様
- **エンドポイント**: `GET /chat/stream/{sse_session_id}`
- **認証**: Bearer Token認証
- **接続管理**: SSESenderクラス
- **進捗管理**: TaskChainManager
- **並列処理**: asyncio.gatherによる並列実行

#### 実装ファイル
- `sse_sender.py`: SSE接続管理とメッセージ配信
- `task_chain_manager.py`: 進捗管理とSSE送信
- `true_react_agent.py`: SSEセッションID連携
- `main.py`: SSEエンドポイント（SSESender方式）
- **`recipe_mcp_server_stdio.py`: 並列化実装（_search_single_recipe関数）**

### AIエージェント
- OpenAI GPT-4による自然言語処理
- 音声コマンドの意図解析 ✅ **OpenAI Whisper統合済み**
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

### 🚀 レシピ検索統合システム（2025/9/29完成）
- **Phase A: 依存関係解決**: タスクの実行順序を自動決定
- **Phase B: データフロー**: 前のタスクの結果を次のタスクに動的に渡す
- **Phase C: 並列実行**: 依存関係を満たしたタスクを同時実行（asyncio.gather使用）
- **MCPツール統合**: 実際のツールが正常に動作
- **LLM統合**: 最終結果の整形も動作
- **並列実行テスト**: 複雑なシナリオでの動作確認
- **レシピ検索統合**: 献立生成→レシピ検索の完全フロー動作確認完了
- **配列対応レシピ検索**: 主菜・副菜・汁物の個別レシピ検索機能実装完了
- **複数レシピURL表示**: 各料理の具体的なレシピURL提供機能実装完了

### 🤔 確認プロセスシステム（2025/9/28 Phase 4.4.1-4.4.3完成）
- **曖昧性検出**: 複数アイテム操作時の自動検出
- **音声認識対応**: チャットコンソールでの自然な会話 ✅ **Web版・モバイル版実装済み**
- **タスクチェーン保持**: 確認プロセス中も全体の文脈を維持
- **例外ベース処理**: `UserConfirmationRequired`による適切な中断
- **確認メッセージ生成**: 詳細な選択肢と進捗表示
- **統合テスト完了**: 確認プロセスの動作確認済み
- **Phase 4.4.3完了**: 確認後のプロンプト処理実装済み

### 在庫管理システム
- **個別在庫法**: 各アイテムを個別に管理
- **ユーザー指定**: 「古い方」「最新」指定時は適切なアイテムを選択
- **ID取得**: セッションから適切なIDを自動取得
- **削除・更新機能**: 2025/9/25完了

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

## 技術スタック

- **フレームワーク**: FastAPI 0.117.1
- **言語**: Python 3.11+
- **AI/ML**: OpenAI API 1.108.1 (GPT-4, Whisper)
- **データベース**: Supabase PostgreSQL 2.19.0
- **認証**: Supabase Auth
- **FastMCP**: Micro-Agent Communication Protocol 2.12.3
- **HTTP**: httpx 0.28.1
- **Web検索**: Perplexity API 1.0.5
- **ベクトルDB**: ChromaDB 1.1.0
- **自然言語処理**: spaCy 3.8.7, NLTK 3.9.1
- **データ処理**: pandas 2.3.2, numpy 2.3.3


### 🚀 次のステップ
- **フロントエンド対応**: レシピ選択UIの実装（プルダウン選択、レシピビューアー）
- **ユーザー分析**: どの提案が選ばれやすいかの統計収集
- **機能拡張**: 追加の提案オプション検討
- **パフォーマンス最適化**: レスポンス時間の改善

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
- ✅ **Phase 4.4**: 確認プロセス（完了）
- ✅ **Phase 4.5**: 並列提示システム（完了・2025年9月29日）
- ✅ **ストリーミング機能**: リアルタイム進捗表示（完了・2025年10月1日）

詳細は[開発ロードマップ](docs/ROADMAP.md)と[自前ReActループ実装フロー](docs/MAKINGREACT.md)をご確認ください。

## ライセンス

このプロジェクトは**プロプライエタリライセンス**の下で提供されています。

- **商用利用**: 別途ライセンス契約が必要
- **改変・再配布**: 禁止
- **個人利用**: 許可（非商用のみ）
- **教育・研究目的**: 許可（適切な帰属表示が必要）

詳細は[LICENSE](LICENSE)ファイルをご確認ください。

## ログ設定

現状：INFO以上を表示
DEBUGレベルを出力したい場合は、`config/logging_config.py`を修正してください。

## AIエージェント協働

このプロジェクトでは、AIエージェントとの協働ルールを定めています。
詳細は[AGENTS.md](AGENTS.md)をご確認ください。