# MCP (Micro-Agent Communication Protocol) 作成フロー

## 📋 概要

Supabase CRUD操作をMCPツール化して、AI Agentがデータベース操作を実行できるようにする。

## 🚀 実装プラン

### 1. MCPサーバー設計

```
supabase_mcp_server.py
├── SupabaseClient クラス
├── CRUD操作メソッド
├── MCPツール定義
└── エラーハンドリング
```

### 2. 実装するMCPツール

#### A. 在庫管理ツール
- `inventory_add` - 在庫追加
- `inventory_get` - 在庫取得
- `inventory_update` - 在庫更新
- `inventory_delete` - 在庫削除
- `inventory_list` - 在庫一覧

#### B. レシピ履歴ツール
- `recipe_add` - レシピ履歴追加
- `recipe_get` - レシピ履歴取得
- `recipe_list` - レシピ履歴一覧

#### C. ユーザー設定ツール
- `user_settings_get` - 設定取得
- `user_settings_update` - 設定更新

### 3. 認証フロー

```python
# 1. クライアント作成
supabase = create_client(url, key)

# 2. トークン検証
user = supabase.auth.get_user(token)

# 3. DB認証
supabase.postgrest.auth(token)

# 4. CRUD操作実行
```

### 4. エラーハンドリング

- 認証エラー
- RLSポリシー違反
- データベース接続エラー
- バリデーションエラー

## 📝 実装順序

1. **基本MCPサーバー構造**
2. **SupabaseClient クラス**
3. **在庫管理ツール（5つ）**
4. **レシピ履歴ツール（3つ）**
5. **ユーザー設定ツール（2つ）**
6. **エラーハンドリング**
7. **テスト**

## 🛠️ 技術スタック

- **MCP**: Micro-Agent Communication Protocol（標準ライブラリ）
- **supabase-py**: Supabaseクライアント
- **pydantic**: データバリデーション
- **stdio**: プロセス間通信

## ⚠️ 依存関係の競合問題と解決

### 問題の背景
MCPライブラリは最新のhttpx/anyioを要求するが、従来のライブラリ（fastapi, openai, supabase）は古いバージョンを要求するため、依存関係の競合が発生。

### 解決戦略
**全パッケージを最新版に更新** - 最新動向に追従するため、リスクを取って最新版を使用。

### 解決手順
```bash
# 1. 仮想環境をクリーンアップ
pip uninstall -y fastapi uvicorn openai httpx supabase mcp anyio

# 2. 最新版で再インストール
pip install -r requirements.txt

# 3. 残りの競合パッケージを更新
pip install --upgrade gotrue supafunc --break-system-packages
```

### 最終的なパッケージ構成
- **fastapi**: 0.117.1
- **uvicorn**: 0.36.0
- **openai**: 1.108.1
- **httpx**: 0.28.1
- **supabase**: 2.19.0
- **mcp**: 1.14.1
- **anyio**: 4.10.0
- **gotrue**: 2.12.4
- **supafunc**: 0.10.2

## 📚 参考資料

- [FastMCP Documentation](https://github.com/pydantic/fastmcp)
- [Supabase Python Client](https://supabase.com/docs/reference/python)
- [MCP Specification](https://modelcontextprotocol.io/)

## 🔄 開発フロー

1. **設計**: ツール仕様の定義
2. **実装**: MCPサーバーの作成
3. **テスト**: 単体テストと統合テスト
4. **統合**: main.pyへの組み込み
5. **デプロイ**: 本番環境への展開

## 📋 チェックリスト

- [ ] 基本MCPサーバー構造
- [ ] SupabaseClient クラス
- [ ] 在庫管理ツール
- [ ] レシピ履歴ツール
- [ ] ユーザー設定ツール
- [ ] エラーハンドリング
- [ ] テスト
- [ ] ドキュメント

## 🎯 目標

AI Agentが自然言語でデータベース操作を実行できるようにする。

例：
- "牛乳を冷蔵庫に追加して"
- "冷蔵庫の在庫を教えて"
- "昨日作ったレシピを記録して"
