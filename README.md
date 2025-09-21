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

### Web検索
- レシピタイトルに基づくWeb検索
- 人間が作成したレシピの発見
- レシピ情報の取得・整理

## セットアップ

### 1. Python環境の準備

```bash
# Python 3.9+ の確認
python --version

# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate     # Windows
```

### 2. 依存関係のインストール

```bash
# 依存関係をインストール
pip install -r requirements.txt
```

### 3. 環境変数の設定

```bash
# 環境変数ファイルの作成
cp .env.example .env

# 必要な環境変数を設定
# OPENAI_API_KEY=your-openai-api-key
# SUPABASE_URL=your-supabase-url
# SUPABASE_KEY=your-supabase-key
```

### 4. 開発サーバーの起動

```bash
# FastAPIサーバーの起動
uvicorn main:app --reload --port 8000

# または直接実行
python ai_agent.py
```

## 開発コマンド

```bash
# FastAPIサーバーの起動
uvicorn main:app --reload --port 8000

# テストの実行
pytest

# リンター
flake8 .

# 型チェック
mypy .

# 依存関係の更新
pip freeze > requirements.txt
```

## API エンドポイント

### 音声処理
- `POST /voice/process` - 音声データの処理
- `POST /voice/transcribe` - 音声のテキスト変換

### AIエージェント
- `POST /agent/chat` - チャットメッセージの処理
- `POST /agent/inventory` - 在庫管理コマンド
- `POST /agent/recipes` - レシピ提案

### データベース
- `GET /db/inventory` - 在庫データの取得
- `POST /db/inventory` - 在庫データの更新
- `GET /db/recipes` - レシピ履歴の取得

## 技術スタック

- **フレームワーク**: FastAPI
- **言語**: Python 3.9+
- **AI/ML**: OpenAI API (GPT-4, Whisper)
- **データベース**: Supabase PostgreSQL
- **Web検索**: requests, BeautifulSoup
- **認証**: Supabase Auth

## アーキテクチャ

```
Python AI (このリポジトリ)
├── FastAPI サーバー
├── AIエージェント
├── 音声処理
├── データベース連携
└── Web検索
    ↑ HTTP API (localhost:8000)
Next.js (Morizo-web リポジトリ)
    ↓
Supabase (認証 + データベース)
    ↓
OpenAI API (GPT-4 + Whisper)
```

## プロジェクト全体の起動

```bash
# ターミナル1: Python AIエージェント（このリポジトリ）
uvicorn main:app --reload --port 8000

# ターミナル2: Next.js Webアプリ（別リポジトリ）
cd ../Morizo-web
npm run dev
```

## 関連リポジトリ

- **[Morizo-web](../Morizo-web)**: Next.js Webアプリケーション
- **[Morizo-mobile](../Morizo-mobile)**: Expo モバイルアプリ

## 開発メモ

### AIエージェントの動作フロー
1. **音声入力** → Whisper API → テキスト変換
2. **テキスト解析** → GPT-4 → 意図理解
3. **データベース操作** → Supabase → 在庫更新
4. **レシピ提案** → Web検索 → 人間のレシピ発見
5. **レスポンス生成** → GPT-4 → 自然な応答

### 音声コマンド例
- "Hey Morizo、鶏胸肉2個"
- "Hey Morizo、牛乳は約1/3残ってる"
- "Hey Morizo、生姜あったっけ？"
- "今日のレシピを教えて"
