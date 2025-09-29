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

5. **MCP依存関係の競合エラー**
   - 原因: MCPライブラリが最新版のhttpx/anyioを要求するが、他のライブラリが古いバージョンを要求
   - 解決: 全パッケージを最新版に更新（下記「MCP対応の依存関係更新」を参照）

## MCP対応の依存関係更新

### 問題の背景
MCP（Micro-Agent Communication Protocol）ライブラリは最新のhttpx/anyioを要求するが、従来のライブラリ（fastapi, openai, supabase）は古いバージョンを要求するため、依存関係の競合が発生。

### 解決手順

```bash
# 1. 仮想環境をクリーンアップ
pip uninstall -y fastapi uvicorn openai httpx supabase mcp anyio

# 2. 最新版で再インストール
pip install -r requirements.txt

# 3. 残りの競合パッケージを更新
pip install --upgrade gotrue supafunc --break-system-packages

# 4. 段階的依存関係解決（必要に応じて）
pip install --upgrade realtime --break-system-packages
pip install --upgrade websockets --break-system-packages

# 5. FastMCPのインストール（MCPサーバー用）
pip install fastmcp>=0.1.0
```

### 更新されたパッケージバージョン
- **fastapi**: 0.104.1 → 0.117.1
- **uvicorn**: 0.24.0 → 0.36.0
- **openai**: 1.3.0 → 1.108.1
- **httpx**: 0.24.1 → 0.28.1
- **supabase**: 2.0.0 → 2.19.0
- **mcp**: 新規インストール 1.14.1
- **anyio**: 新規インストール 4.10.0
- **gotrue**: 1.3.1 → 2.12.4
- **supafunc**: 0.3.3 → 0.10.2
- **realtime**: 1.0.6 → 2.19.0
- **websockets**: 12.0 → 15.0.1
- **fastmcp**: 新規インストール 2.12.3

### 段階的解決の成功例
1. **realtime**: `AuthorizationError` インポートエラー → 2.19.0に更新で解決
2. **websockets**: `websockets.asyncio` インポートエラー → 15.0.1に更新で解決
3. **fastmcp**: 依存関係解決後、FastMCP 2.12.3で正常動作
4. **負のスパイラル回避**: 個別パッケージ更新で全体の安定性を維持

## 🎉 MCPサーバーの動作確認

**2025年9月21日** - Supabase MCPサーバーが完全動作！

### MCPサーバーの起動
```bash
# Supabase MCPサーバーを起動
python supabase_mcp_server.py
```

### MCPサーバーのテスト
```bash
# 包括テストの実行
python test_supabase_with_mcp.py
```

### 成功した機能
- ✅ **5つのCRUDツール**: inventory_add, inventory_list, inventory_get, inventory_update, inventory_delete
- ✅ **Supabase認証**: JWT トークン認証
- ✅ **HTTPトランスポート**: 安定した接続
- ✅ **実績のある方法**: アノテーション削除、明示的登録

## 開発コマンド

```bash
# FastAPIサーバーの起動
uvicorn main:app --reload --port 8000

# MCPサーバーの起動
python supabase_mcp_server.py

# Supabase接続テスト
python test_supabase_connection.py

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
