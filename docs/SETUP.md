# Morizo AI - 詳細セットアップ手順

## システム環境の準備（初回のみ）

```bash
# システムパッケージの更新
apt update
apt upgrade

# pipのインストール
apt install python3-pip

# 仮想環境作成に必要なパッケージのインストール
apt install python3.11-venv
```

## Python環境の準備

```bash
# Python 3.11+ の確認
python3 --version

# 仮想環境の作成
cd /app/Morizo-ai
python3 -m venv venv

# 仮想環境の有効化
source venv/bin/activate
```

## 依存関係のインストール

```bash
# 依存関係をインストール
pip install -r requirements.txt
```

## 環境変数の設定

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

## 開発サーバーの起動

```bash
# FastAPIサーバーの起動
uvicorn main:app --reload --port 8000
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
   - 解決: `requirements.txt`で`httpx>=0.24.0,<0.25.0`を指定し、`pip install -r requirements.txt --force-reinstall`を実行

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

## プロジェクト全体の起動

```bash
# ターミナル1: Python AIエージェント（このリポジトリ）
uvicorn main:app --reload --port 8000

# ターミナル2: Next.js Webアプリ（別リポジトリ）
cd ../Morizo-web
npm run dev
```
