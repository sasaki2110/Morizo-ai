# Morizo AI - Python AIエージェント

Smart Pantry MVPのAIエージェント（LLM処理 + 音声認識）

## プロジェクト構成

- **Morizo-ai** - Python AIエージェント（このリポジトリ）
- **Morizo-web** - Next.js Webアプリ（別リポジトリ）
- **Morizo-mobile** - Expo モバイルアプリ（別リポジトリ）

## 機能

### AIエージェント
- OpenAI GPT-4による自然言語処理
- 音声コマンドの意図解析
- 食材在庫管理の自動化
- レシピ提案の生成

### 音声処理
- OpenAI Whisper APIによる音声認識
- 自然言語コマンドの理解
- 音声データのテキスト変換

### データベース連携
- Supabase PostgreSQLとの連携
- 在庫データの読み書き
- ユーザー認証情報の取得

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
uvicorn main:app --reload --port 8000
```

### 4. 動作確認
```bash
curl http://localhost:8000/health
```

## ドキュメント

- **[詳細セットアップ](docs/SETUP.md)** - セットアップ手順（MCP依存関係問題の解決手順含む）
- **[API仕様](docs/API.md)** - エンドポイント詳細
- **[認証機能](docs/AUTHENTICATION.md)** - 認証システム
- **[アーキテクチャ](docs/ARCHITECTURE.md)** - システム設計
- **[開発ロードマップ](docs/ROADMAP.md)** - 開発計画・ToDo
- **[MCP作成フロー](docs/MAKINGMCP.md)** - MCPサーバー実装手順
- **[自前ReActループ実装フロー](docs/MAKINGREACT.md)** - 動的MCPエージェント実装手順

## 技術スタック

- **フレームワーク**: FastAPI 0.117.1
- **言語**: Python 3.11+
- **AI/ML**: OpenAI API 1.108.1 (GPT-4, Whisper)
- **データベース**: Supabase PostgreSQL 2.19.0
- **認証**: Supabase Auth
- **FastMCP**: Micro-Agent Communication Protocol 2.12.3
- **HTTP**: httpx 0.28.1

## 🎉 最新の成果

**2025年9月22日** - 完全動的MCPエージェントが完成！

### ✅ 実装完了
- **FastMCP 2.12.3**でMCPサーバー構築
- **5つのCRUDツール**が正常動作
- **Supabase認証**と**データベース操作**が統合
- **stdio接続**で軽量動作
- **完全動的MCPエージェント**実現
- **自然言語での在庫管理**が実現
- **ハードコーディングの完全排除**

### 🚀 次のステップ
- **高度なAIエージェント化**の設計
- **レシピ提案機能**の追加
- **文脈理解**の強化

## 関連リポジトリ

- **[Morizo-web](../Morizo-web)**: Next.js Webアプリケーション
- **[Morizo-mobile](../Morizo-mobile)**: Expo モバイルアプリ

## 開発状況

- ✅ **Phase 1**: 基本機能（完了）
- ✅ **Phase 2**: MCP化（完了）
- ✅ **Phase 3**: 動的AIエージェント化（完了）
- 🚀 **Phase 4**: 高度なAIエージェント化（計画中）

詳細は[開発ロードマップ](docs/ROADMAP.md)と[自前ReActループ実装フロー](docs/MAKINGREACT.md)をご確認ください。