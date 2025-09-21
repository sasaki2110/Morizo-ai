# Morizo AI - API仕様

## ベースURL
```
http://localhost:8000
```

## エンドポイント一覧

### ヘルスチェック
- **GET** `/health`
- **説明**: サーバーの状態確認
- **認証**: 不要
- **レスポンス**:
```json
{
  "status": "healthy",
  "service": "Morizo AI"
}
```

### ルートエンドポイント
- **GET** `/`
- **説明**: 基本的な接続確認
- **認証**: 不要
- **レスポンス**:
```json
{
  "message": "Morizo AI is running!"
}
```

### チャット機能
- **POST** `/chat`
- **説明**: AIエージェントとの対話
- **認証**: 必須（Bearer Token）
- **リクエスト**:
```json
{
  "message": "こんにちは、Morizo！"
}
```
- **レスポンス**:
```json
{
  "response": "こんにちは！Morizoです。今日はどんな食材を管理したり、レシピを提案したりしましょうか？何かお手伝いできることがあれば教えてくださいね！",
  "success": true,
  "model_used": "gpt-4o-mini-2024-07-18",
  "user_id": "d0e0d523-1831-4541-bd67-f312386db951"
}
```

## 認証

### Bearer Token認証
```
Authorization: Bearer <supabase-token>
```

### 認証エラー
```json
{
  "detail": "Not authenticated"
}
```

## エラーレスポンス

### 400 Bad Request
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "message"],
      "msg": "Field required",
      "input": {},
      "url": "https://errors.pydantic.dev/2.5/v/missing"
    }
  ]
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 500 Internal Server Error
```json
{
  "detail": "AI processing error: <error-message>"
}
```

## 使用例

### 認証なし（エラー）
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "こんにちは"}'
```

### 認証あり（正常）
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <supabase-token>" \
  -d '{"message": "こんにちは"}'
```

### ヘルスチェック
```bash
curl http://localhost:8000/health
```

## レスポンスフィールド

### ChatResponse
- `response` (string): AIからの応答メッセージ
- `success` (boolean): 処理成功フラグ
- `model_used` (string): 実際に使用されたOpenAIモデル名
- `user_id` (string): 認証済みユーザーのID

## 注意事項

- 認証が必要なエンドポイントは`Authorization`ヘッダーが必須
- トークンはSupabase認証システムから取得
- トークンに角括弧`[` `]`が含まれている場合は除去が必要
- サーバー起動時に使用モデルと設定状況が表示される
