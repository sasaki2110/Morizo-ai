# Morizo AI - 開発ロードマップ

## Phase 1: 基本機能 ✅

### 完了済み
- [x] FastAPIサーバー構築
- [x] OpenAI API連携（GPT-4o-mini対応）
- [x] Supabase認証システム
- [x] 基本チャット機能
- [x] 依存関係管理（httpx互換性解決）
- [x] CORS設定
- [x] エラーハンドリング
- [x] API動作確認

## Phase 2: MCP化 🔄

### Supabase CRUD MCP
- [x] Supabase CRUD MCPサーバー作成 ✅ **2025/9/21完了**
- [x] 在庫管理の基本CRUD操作 ✅ **5つのツール実装完了**
- [x] ユーザー別データアクセス制御 ✅ **JWT認証実装完了**
- [ ] リアルタイム更新機能
- [ ] mcp.json設定

### Recipe RAG MCP
- [ ] レシピデータのRAG化
- [ ] ベクトル検索機能
- [ ] レシピ提案システム
- [ ] 履歴管理

### Web Search MCP
- [ ] Web検索機能
- [ ] レシピ情報の取得
- [ ] データクリーニング

### Voice Processing MCP
- [ ] 音声認識機能
- [ ] 音声コマンド解析
- [ ] 音声応答生成

## Phase 3: AI Agent Loop 🚀

### Perception（認識）
- [ ] 音声入力の認識
- [ ] テキスト意図の解析
- [ ] コンテキスト理解

### Cognition（思考）
- [ ] 意図の判断
- [ ] 適切なツールの選択
- [ ] 行動計画の立案

### Action（行動）
- [ ] Supabase CRUD操作
- [ ] レシピ生成・提案
- [ ] Web検索実行
- [ ] レスポンス生成

## Phase 4: 高度な機能 🌟

### 状態管理
- [ ] セッション管理
- [ ] 会話履歴の保持
- [ ] ユーザー設定の管理

### 自動化
- [ ] ツール選択の自動化
- [ ] エラー回復機能
- [ ] 学習機能

### 拡張性
- [ ] プラグインシステム
- [ ] カスタムツール追加
- [ ] 外部API連携

## 技術的ToDo

### MCP実装
- [x] FastMCPでHTTP通信実装 ✅ **2025/9/21完了**
- [ ] FastMCPでstdio通信実装
- [ ] mcp.jsonでの設定管理
- [x] エラーハンドリング ✅ **CallToolResult処理完了**
- [ ] ログ管理

### データベース設計
- [x] 在庫管理テーブル設計 ✅ **DDL.mdで完了**
- [ ] レシピマスターデータ設計
- [ ] ユーザー設定テーブル設計
- [ ] インデックス最適化

### セキュリティ
- [x] Row Level Security (RLS) 設定 ✅ **DDL.mdで完了**
- [x] API権限管理 ✅ **JWT認証実装完了**
- [ ] データ暗号化

## 現在の優先度

1. **Supabase CRUD MCP** - ✅ **基本機能完了！**
2. **stdio接続への移行** - HTTPからstdioへ
3. **main.pyへの統合** - MCPクライアントとして組み込み
4. **mcp.json設定** - 設定管理の確立
5. **基本ループ実装** - Perception → Cognition → Action
6. **Recipe RAG MCP** - レシピ機能の拡張

## 完了基準

### Phase 2完了基準
- Supabase CRUD MCPが正常動作
- mcp.jsonでMCPサーバー管理
- 基本チャット機能がMCP経由で動作

### Phase 3完了基準
- AI Agent基本ループが実装
- 複数MCPの連携動作
- 自動ツール選択機能

---

**最終目標**: 音声駆動型のスマートパントリーAIエージェント
