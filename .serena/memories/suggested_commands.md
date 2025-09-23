# Morizo AI 開発コマンド

## サーバー起動
```bash
# メインアプリケーション起動
python main.py

# または uvicorn で起動
uvicorn main:app --reload --port 8000
```

## テスト実行
```bash
# 真のReActエージェントテスト
python tests/test_true_react_agent_short.py

# その他のテスト
python tests/test_session_manager.py
python tests/test_db_mcp_stdio.py
```

## 環境設定
```bash
# 仮想環境のアクティベート
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .envファイルに必要な設定を記入
```

## 動作確認
```bash
# ヘルスチェック
curl http://localhost:8000/health

# 認証なしテスト
curl -X POST http://localhost:8000/chat-test -H "Content-Type: application/json" -d '{"message": "test"}'

# 認証ありテスト
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -H "Authorization: Bearer <token>" -d '{"message": "test"}'
```

## ログ確認
```bash
# ログファイルの確認
tail -f morizo_ai.log

# ログファイルのバックアップ確認
ls -la backups/
```

## Git操作
```bash
# ステータス確認
git status

# 変更のコミット
git add .
git commit -m "message"

# プッシュ
git push
```

## システムユーティリティ
```bash
# ファイル検索
find . -name "*.py" -type f

# パターン検索
grep -r "pattern" .

# ディレクトリ一覧
ls -la

# プロセス確認
ps aux | grep python
```