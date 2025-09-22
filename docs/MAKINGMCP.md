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

- **FastMCP**: Micro-Agent Communication Protocol（FastMCP 2.12.3）
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
- **fastmcp**: 2.12.3
- **anyio**: 4.10.0
- **gotrue**: 2.12.4
- **supafunc**: 0.10.2

## 🎉 実装完了！

### ✅ 成功した実装

**2025年9月21日** - Supabase MCPサーバーの完全動作を確認

#### **実装されたツール**
- `inventory_add`: 在庫アイテムの追加
- `inventory_list`: 在庫一覧の取得
- `inventory_get`: 特定アイテムの取得
- `inventory_update`: 在庫アイテムの更新
- `inventory_delete`: 在庫アイテムの削除

#### **成功した技術要素**
- ✅ **FastMCP 2.12.3**: 最新版で正常動作
- ✅ **HTTPトランスポート**: `mcp.run(transport="http", host="0.0.0.0", port=8001, path="/mcp")`
- ✅ **実績のある方法**: アノテーション削除、明示的登録
- ✅ **Supabase認証**: JWT トークン認証が正常動作
- ✅ **CRUD操作**: 全操作が正常に実行
- ✅ **CallToolResult処理**: `result.data` で正しくアクセス

#### **テスト結果**
```
🧪 FastMCPサーバー包括テスト開始
✅ FastMCPサーバー接続成功
✅ 利用可能ツール数: 5
✅ 在庫追加成功
✅ 在庫一覧取得成功: 1件
✅ 在庫更新成功 (quantity: 2.0→5.0, storage_location: 冷蔵庫→冷凍庫)
✅ 在庫削除成功
🎉 全テスト完了！
```

#### **重要な学び**
- **実績のあるソース**の重要性
- **アノテーション vs 明示的登録**の違い
- **CallToolResult**の正しい処理方法
- **HTTPトランスポート**の安定性

### 🚀 次のステップ
- [ ] stdio接続への移行
- [ ] main.pyへの統合
- [ ] 本格的な運用開始

## 🎉 アノテーション方式のMCPサーバー実装完了！

**2025年9月22日** - 公式チュートリアルに従ったアノテーション方式のMCPサーバーが完全動作！

### ✅ 実装されたアノテーション方式サーバー

#### **ファイル構成**
- **`supabase_mcp_server2.py`** - アノテーション方式のMCPサーバー
- **`test_supabase_mcp_server2.py`** - テストファイル

#### **実装されたツール（アノテーション方式）**
```python
@mcp.tool()
async def inventory_add(...):
    """在庫にアイテムを追加
    
    Args:
        token: Supabase認証トークン
        item_name: アイテム名
        quantity: 数量
        unit: 単位（デフォルト: 個）
        storage_location: 保管場所（デフォルト: 冷蔵庫）
        expiry_date: 消費期限（オプション）
    
    Returns:
        追加されたアイテムの情報
    """
    # ...

@mcp.tool()
async def inventory_list(...):
    """在庫一覧を取得"""
    # ...

@mcp.tool()
async def inventory_get(...):
    """特定の在庫アイテムを取得"""
    # ...

@mcp.tool()
async def inventory_update(...):
    """在庫アイテムを更新"""
    # ...

@mcp.tool()
async def inventory_delete(...):
    """在庫アイテムを削除"""
    # ...
```

### 🆚 両方式の比較

| 項目 | 従来方式 | アノテーション方式 |
|------|----------|-------------------|
| ツール登録 | `mcp.tool(func)` | `@mcp.tool()` |
| ドキュメント | 関数内コメント | 関数のdocstring |
| 型定義 | 関数パラメータ | Pydanticモデル |
| ポート | 8001 | 8002 |
| 動作確認 | ✅ 実績あり | ✅ **完全動作** |
| 公式準拠 | ❌ 独自実装 | ✅ **チュートリアル準拠** |

### 🧪 テスト結果

#### **完全なCRUD操作テスト**
```
📦 在庫追加テスト... ✅ 在庫追加成功
📋 在庫一覧取得テスト... ✅ 在庫一覧取得成功: 1件
🔍 在庫取得テスト... ✅ 在庫取得成功
✏️ 在庫更新テスト... ✅ 在庫更新成功
🗑️ 在庫削除テスト... ✅ 在庫削除成功
🎉 全テスト完了！
```

#### **成功した技術要素**
- ✅ **FastMCP 2.12.3**: 最新版で正常動作
- ✅ **HTTPトランスポート**: `http://0.0.0.0:8002/mcp`
- ✅ **アノテーション方式**: `@mcp.tool()` デコレータ
- ✅ **Supabase認証**: JWT トークン認証が正常動作
- ✅ **CRUD操作**: 全操作が正常に実行
- ✅ **CallToolResult処理**: `result.data` で正しくアクセス
- ✅ **セキュリティ**: トークンの安全な取り扱い

### 🔧 技術的改善点

#### **1. CallToolResultの正しい処理**
```python
# 修正前（エラーの原因）
if add_result and len(add_result) > 0:
    result_data = json.loads(add_result[0].text)

# 修正後（正しい方法）
if add_result and hasattr(add_result, 'data') and add_result.data:
    result_data = add_result.data
```

#### **2. セキュアなトークン取得**
```python
# 修正前（セキュリティリスク）
test_token = "your-test-token-here"

# 修正後（セキュア）
print("\n🔑 Supabase認証トークンの入力が必要です")
test_token = input("Supabase Access Token を入力してください: ").strip()
```

#### **3. FastMCPクライアントの正しい使用方法**
```python
# 正しい引数の渡し方
add_result = await mcp_client.call_tool(
    "inventory_add",
    arguments={
        "token": test_token,
        "item_name": "テスト牛乳",
        "quantity": 2.0,
        "unit": "本",
        "storage_location": "冷蔵庫"
    }
)
```

### 🎯 推奨事項

**アノテーション方式（`supabase_mcp_server2.py`）を推奨**

理由：
- ✅ **公式チュートリアル準拠**
- ✅ **詳細なドキュメント**
- ✅ **型安全性**
- ✅ **保守性**
- ✅ **拡張性**

### 📋 使用方法

#### **1. サーバー起動**
```bash
python supabase_mcp_server2.py
```

#### **2. テスト実行**
```bash
python test_supabase_mcp_server2.py
```

#### **3. トークン取得（Next.js側）**
```javascript
const { data: { session } } = await supabase.auth.getSession();
console.log('Access Token:', session?.access_token);
```

### 🚀 次のステップ

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
