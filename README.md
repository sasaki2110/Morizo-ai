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

- **[詳細セットアップ](docs/SETUP.md)** - セットアップ手順
- **[API仕様](docs/API.md)** - エンドポイント詳細
- **[認証機能](docs/AUTHENTICATION.md)** - 認証システム
- **[アーキテクチャ](docs/ARCHITECTURE.md)** - システム設計
- **[開発ロードマップ](docs/ROADMAP.md)** - 開発計画・ToDo

## 技術スタック

- **フレームワーク**: FastAPI
- **言語**: Python 3.11+
- **AI/ML**: OpenAI API (GPT-4, Whisper)
- **データベース**: Supabase PostgreSQL
- **認証**: Supabase Auth

## 関連リポジトリ

- **[Morizo-web](../Morizo-web)**: Next.js Webアプリケーション
- **[Morizo-mobile](../Morizo-mobile)**: Expo モバイルアプリ

## 開発状況

- ✅ **Phase 1**: 基本機能（完了）
- 🔄 **Phase 2**: MCP化（進行中）
- 🚀 **Phase 3**: AI Agent Loop（計画中）

詳細は[開発ロードマップ](docs/ROADMAP.md)をご確認ください。