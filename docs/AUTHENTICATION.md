# Morizo AI - 認証機能詳細

## 認証方式

### Bearer Token認証
- **方式**: `Authorization: Bearer <supabase-token>`
- **トークン取得**: Supabase認証システム
- **検証**: Supabaseの`getUser(token)`でトークン有効性確認

## 認証フロー

1. **トークン取得**: Next.js側でSupabase認証からトークンを取得
2. **API呼び出し**: `Authorization: Bearer <token>`ヘッダーでAPIを呼び出し
3. **トークン検証**: Python側でSupabaseの`getUser(token)`でトークンを検証
4. **ユーザー情報取得**: 認証成功時にユーザー情報を取得
5. **レスポンス**: ユーザーID付きでレスポンスを返却

## 認証が必要なエンドポイント

- `POST /chat` - チャット機能（認証必須）

## 認証テスト

### 認証なし（401エラー）
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "こんにちは、Morizo！"}'
```

期待される応答（エラー）：
```json
{"detail":"Not authenticated"}
```

### 認証あり（正常動作）
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <supabase-token>" \
  -d '{"message": "こんにちは、Morizo！"}'
```

期待される応答：
```json
{
  "response": "こんにちは！Morizoです。今日はどんな食材を管理したり、レシピを提案したりしましょうか？何かお手伝いできることがあれば教えてくださいね！",
  "success": true,
  "model_used": "gpt-4o-mini-2024-07-18",
  "user_id": "user-uuid-here"
}
```

## トークン取得方法

### Next.js側でのトークン表示
```typescript
// ブラウザのコンソールで実行
const { data: { session } } = await supabase.auth.getSession();
console.log('Access Token:', session?.access_token);
```

### デバッグ用コンポーネント
```typescript
// components/DebugToken.tsx
'use client';
import { useEffect, useState } from 'react';
import { createClient } from '@/lib/supabase-client';

export default function DebugToken() {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const supabase = createClient();
    
    // 現在のセッションを取得
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        setToken(session.access_token);
        setUser(session.user);
      }
    });

    // 認証状態の変更を監視
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        if (session) {
          setToken(session.access_token);
          setUser(session.user);
        } else {
          setToken(null);
          setUser(null);
        }
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  if (!token) {
    return <div>ログインしてください</div>;
  }

  return (
    <div className="p-4 border rounded-lg bg-gray-50">
      <h3 className="font-bold mb-2">🔑 デバッグ用トークン</h3>
      <p className="text-sm mb-2">ユーザー: {user?.email}</p>
      <div className="bg-white p-2 rounded border">
        <code className="text-xs break-all">{token}</code>
      </div>
      <button 
        onClick={() => navigator.clipboard.writeText(token)}
        className="mt-2 px-3 py-1 bg-blue-500 text-white rounded text-sm"
      >
        コピー
      </button>
    </div>
  );
}
```

## エラーハンドリング

### 認証エラー
```json
{
  "detail": "Not authenticated"
}
```

### 無効なトークン
```json
{
  "detail": "Authentication failed: invalid JWT: unable to parse or verify signature, token is malformed: could not base64 decode header: illegal base64 data at input byte 0"
}
```

### Supabase設定エラー
```json
{
  "detail": "Supabase not configured"
}
```

## 注意事項

- トークンに角括弧`[` `]`が含まれている場合は除去が必要
- トークンは有効期限があるため、定期的に更新が必要
- 開発環境では`CORS`設定で`*`を許可しているが、本番環境では適切なドメインに制限する
- 認証失敗時は401ステータスコードを返す

## セキュリティ考慮事項

- トークンはHTTPS通信で送信
- トークンはクライアント側で安全に保存
- サーバー側ではトークンの検証のみ実行
- ユーザー情報は必要最小限のみ取得
