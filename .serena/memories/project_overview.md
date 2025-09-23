# Morizo AI プロジェクト概要

## プロジェクトの目的
- **Smart Pantry MVPのAIエージェント**: LLM処理 + 音声認識による在庫管理システム
- **統一されたReActエージェント**: 単純・複雑問わず同じフローで処理する真のAIエージェント
- **動的MCPエージェント**: リアルタイムツール選択と実行

## 技術スタック
- **フレームワーク**: FastAPI 0.115.0+
- **言語**: Python 3.11+
- **AI/ML**: OpenAI API 1.50.0+ (GPT-4, Whisper)
- **データベース**: Supabase PostgreSQL 2.19.0
- **認証**: Supabase Auth
- **MCP**: FastMCP 0.1.0+ (Micro-Agent Communication Protocol)
- **HTTP**: httpx 0.27.1+

## プロジェクト構造（リファクタリング後）
```
Morizo AI/
├── main.py (145行)                    # メインアプリケーション
├── config/                            # 設定管理
├── auth/                              # 認証・セキュリティ
├── agents/                            # エージェント・MCP
├── models/                            # データモデル
├── utils/                             # ユーティリティ
├── handlers/                          # ハンドラー
├── tests/                             # テスト
├── docs/                              # ドキュメント
└── backups/                           # バックアップファイル
```

## 主要機能
- **統一されたReActエージェント**: ActionPlanner + TaskManager + TrueReactAgent
- **セッション管理システム**: メモリ内セッション、操作履歴、在庫状態管理
- **FIFO原則による在庫管理**: 個別在庫法、最古→最新の操作順序
- **MCP統合**: 5つのCRUDツール（inventory_add, list, get, update, delete）