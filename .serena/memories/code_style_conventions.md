# Morizo AI コードスタイルと規約

## 命名規則
- **ファイル名**: スネークケース (例: `chat_handler.py`, `session_manager.py`)
- **クラス名**: パスカルケース (例: `TrueReactAgent`, `MCPClient`)
- **関数名**: スネークケース (例: `handle_chat_request`, `process_with_unified_react`)
- **変数名**: スネークケース (例: `user_session`, `raw_token`)

## 型ヒント
- **必須**: すべての関数に型ヒントを記述
- **例**: `async def handle_chat_request(request: ChatRequest, auth_data) -> ChatResponse:`
- **Optional**: `Optional[str] = None` でデフォルト値付き

## ドキュメント文字列
- **関数**: 簡潔な説明とパラメータ、戻り値の説明
- **例**:
```python
async def process_with_unified_react(request: ChatRequest, user_session, raw_token: str) -> ChatResponse:
    """
    統一されたReActエージェントで処理する
    単純な要求も複雑な要求も同じフローで処理
    """
```

## ログ出力
- **フォーマット**: `logger.info(f"🔍 [MODULE] メッセージ")`
- **絵文字使用**: 🔍(開始), ✅(成功), ❌(エラー), 🚀(起動), 🤖(AI), 📋(タスク)
- **モジュール名**: `[MAIN]`, `[CHAT_HANDLER]`, `[AUTH]` など

## エラーハンドリング
- **try-except**: 適切な例外処理
- **ログ出力**: エラー詳細とトレースバック
- **HTTPException**: FastAPIでの適切なエラーレスポンス

## インポート順序
1. 標準ライブラリ
2. サードパーティライブラリ
3. ローカルモジュール
4. 相対インポート

## モジュール設計原則
- **単一責任**: 各モジュールは1つの責任を持つ
- **依存関係**: 循環参照を避ける
- **インターフェース**: 明確なAPI設計