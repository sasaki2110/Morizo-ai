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

### 1. システム環境の準備（初回のみ）

```bash
# システムパッケージの更新
apt update
apt upgrade

# pipのインストール
apt install python3-pip

# 仮想環境作成に必要なパッケージのインストール
apt install python3.11-venv
```

### 2. Python環境の準備

```bash
# Python 3.11+ の確認
python3 --version

# 仮想環境の作成
cd /app/Morizo-ai
python3 -m venv venv

# 仮想環境の有効化
source venv/bin/activate
```

### 3. 依存関係のインストール

```bash
# 依存関係をインストール
pip install -r requirements.txt
```

### 4. 環境変数の設定

```bash
# 環境変数ファイルの作成
nano .env
```

`.env`ファイルの内容：
```
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
SUPABASE_URL=your-supabase-url-here
SUPABASE_KEY=your-supabase-key-here
HOST=0.0.0.0
PORT=8000
```

**利用可能なモデル：**
- `gpt-4o-mini` - コスト効率が良く、開発・テストに推奨
- `gpt-4o` - より高性能だが、コストが高い
- `gpt-4-turbo` - バランス型
- `gpt-3.5-turbo` - 最もコスト効率が良い（軽量タスク向け）

### 5. 開発サーバーの起動

```bash
# FastAPIサーバーの起動
uvicorn main:app --reload --port 8000
```

## API動作確認

サーバーが正常に起動したら、以下のコマンドでAPIの動作を確認できます：

### 1. ヘルスチェック
```bash
curl http://localhost:8000/health
```
期待される応答：
```json
{"status":"healthy","service":"Morizo AI"}
```

### 2. ルートエンドポイント
```bash
curl http://localhost:8000/
```
期待される応答：
```json
{"message":"Morizo AI is running!"}
```

### 3. チャットAPI（メイン機能）
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "こんにちは、Morizo！"}'
```
期待される応答：
```json
{
  "response": "こんにちは！Morizoです。今日はどんな食材を管理したり、レシピを提案したりしましょうか？何かお手伝いできることがあれば教えてくださいね！",
  "success": true,
  "model_used": "gpt-4o-mini"
}
```

### 4. 食材管理のテスト
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hey Morizo、鶏胸肉2個を在庫に追加して"}'
```

### 5. エラーハンドリングのテスト
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{}'
```
期待される応答（エラー）：
```json
{"detail":[{"type":"missing","loc":["body","message"],"msg":"Field required","input":{},"url":"https://errors.pydantic.dev/2.5/v/missing"}]}
```

## トラブルシューティング

### よくあるエラーと解決方法

1. **`externally-managed-environment`エラー**
   - 原因: システム全体のPython環境への直接インストールが制限されている
   - 解決: 仮想環境を使用する（上記手順2を実行）

2. **`ensurepip is not available`エラー**
   - 原因: `python3-venv`パッケージが不足
   - 解決: `apt install python3.11-venv`を実行

3. **`pip: command not found`エラー**
   - 原因: pipがインストールされていない
   - 解決: `apt install python3-pip`を実行

4. **`TypeError: Client.__init__() got an unexpected keyword argument 'proxies'`エラー**
   - 原因: `httpx`と`openai`ライブラリのバージョン互換性の問題
   - 解決: `requirements.txt`で`httpx==0.25.0`を明示的に指定し、`pip install -r requirements.txt --force-reinstall`を実行

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
