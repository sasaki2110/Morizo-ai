# Morizo AI - LangChain統合フロー

## ⚠️ 重要: LangChainアプローチは挫折

**2025年9月22日**: LangChainアプローチは複雑すぎて挫折しました。

### 挫折の理由
1. **ReActフォーマットの強制**: LangChainのReAct Agentが期待するフォーマットに従わない
2. **プロンプトエンジニアリングの困難**: 例が強すぎて模倣してしまう問題
3. **デバッグの困難**: LLMとのやり取りがラップされて解りづらい
4. **拡張性の限界**: 複雑な設定が必要で、シンプルな修正が困難

### 代替アプローチ
**自前ReActループ**に切り替え、よりシンプルで制御可能な実装を採用。

---

## 📋 概要（参考: 挫折したアプローチ）

現在のMCP統合ベースのMorizo AIを、LangChain ReAct Agentアプローチに移行して、より柔軟で実用的なAI Agentを構築する。

## 🎯 目標

### **Phase 3: LangChain統合**
- 動的ツール選択による自然言語理解
- 複雑な在庫管理操作の自動化
- レシピ提案機能の統合
- より自然な対話体験

## 🚀 実装プラン

### 1. 依存関係の整備

#### **追加が必要なライブラリ**
```txt
# LangChain関連
langchain>=0.1.0
langchain-openai>=0.1.0
langchain-core>=0.1.0
langchain-community>=0.0.20
```

#### **更新されたrequirements.txt**
```txt
# FastAPI関連
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
python-multipart>=0.0.6

# AI/ML関連
openai>=1.50.0
langchain>=0.1.0
langchain-openai>=0.1.0
langchain-core>=0.1.0
langchain-community>=0.0.20

# データベース・認証
supabase>=2.19.0

# MCP関連
fastmcp>=0.1.0
anyio>=4.5.0
websockets>=15.0.0

# その他
httpx>=0.27.1
python-dotenv>=1.0.0
pydantic>=2.5.0
```

### 2. アーキテクチャ設計

#### **現在のアーキテクチャ（MCP統合）**
```
FastAPI Server
├── /chat (パターンマッチング)
├── /inventory/* (MCP呼び出し)
└── MCP Client → db_mcp_server_stdio.py
```

#### **目標アーキテクチャ（LangChain統合）**
```
FastAPI Server
├── /chat (LangChain Agent)
├── LangChain Agent
│   ├── ReAct Loop
│   ├── Tool Selection
│   └── MCP Tools (LangChain化)
└── MCP Server (stdio)
```

### 3. 実装ステップ

#### **Step 1: 依存関係のインストール**
- [ ] LangChainライブラリのインストール
- [ ] 依存関係の競合解決
- [ ] インポートテスト

#### **Step 2: MCPツールのLangChain化**
- [ ] `inventory_add` → LangChain Tool
- [ ] `inventory_list` → LangChain Tool
- [ ] `inventory_get` → LangChain Tool
- [ ] `inventory_update` → LangChain Tool
- [ ] `inventory_delete` → LangChain Tool

#### **Step 3: LangChain Agentの統合**
- [ ] ReAct Agentの作成
- [ ] プロンプトテンプレートの設計
- [ ] ツール統合
- [ ] エラーハンドリング

#### **Step 4: 既存機能の移行**
- [ ] `/chat`エンドポイントの置き換え
- [ ] 認証システムの統合
- [ ] デバッグログの統合

#### **Step 5: レシピ提案機能の追加**
- [ ] レシピ検索ツール
- [ ] 食材マッチング機能
- [ ] レシピ提案ロジック

## 🛠️ 技術的詳細

### **LangChain Agent設計**

#### **ツール定義**
```python
from langchain.tools import Tool

def inventory_add_tool(query: str) -> str:
    """在庫にアイテムを追加"""
    # MCP呼び出しロジック
    pass

tools = [
    Tool(
        name="inventory_add",
        description="在庫にアイテムを追加する。例: '牛乳を2本追加'",
        func=inventory_add_tool
    ),
    # 他のツール...
]
```

#### **ReAct Agent設定**
```python
from langchain.agents import create_react_agent, AgentExecutor

agent = create_react_agent(
    llm=ChatOpenAI(model="gpt-4o-mini"),
    tools=tools,
    prompt=prompt_template
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=10,
    handle_parsing_errors=True
)
```

### **プロンプトテンプレート**

#### **Morizo用プロンプト**
```
あなたはMorizoという名前のスマートパントリーアシスタントです。
食材管理とレシピ提案を手伝います。

利用可能なツール:
{tools}

ツール名: {tool_names}

手順:
1. ユーザーの要求を理解してください
2. 適切なツールを選択してください
3. ツールを実行してください
4. 結果を自然な日本語で説明してください

以下の形式で回答してください:

Thought: 何をすべきか考えてください
Action: 使用するツール名
Action Input: ツールへの入力
Observation: ツールの実行結果

最終的に回答が完了したら、Final Answer: で回答してください。

{agent_scratchpad}
```

## ⚠️ 注意事項

### **依存関係の競合**
- **httpx**: LangChainとFastAPIで異なるバージョン要求
- **pydantic**: LangChainとFastAPIで異なるバージョン要求
- **openai**: LangChainと直接使用で重複

### **パフォーマンス考慮**
- **LLM呼び出し**: レスポンス時間の増加
- **MCP起動**: stdio接続のオーバーヘッド
- **メモリ使用量**: LangChainの追加メモリ

### **エラーハンドリング**
- **ツール実行失敗**: フォールバック機能
- **LLM解析エラー**: パースエラーの処理
- **MCP接続エラー**: 接続失敗時の対応

## 📋 チェックリスト

### **Phase 3.1: 基盤整備**
- [ ] LangChain依存関係のインストール
- [ ] 依存関係の競合解決
- [ ] 基本的なLangChain Agentの動作確認

### **Phase 3.2: MCP統合**
- [ ] MCPツールのLangChain化
- [ ] 認証システムの統合
- [ ] 基本的な在庫操作の動作確認

### **Phase 3.3: 機能拡張**
- [ ] レシピ提案機能の追加
- [ ] 複雑な自然言語理解の実装
- [ ] エラーハンドリングの改善

### **Phase 3.4: 最適化**
- [ ] パフォーマンスの最適化
- [ ] デバッグ機能の統合
- [ ] 本番環境への準備

## 🎯 成功基準

### **Phase 3完了基準**
- [ ] LangChain Agentが正常動作
- [ ] 在庫管理操作が自然言語で実行可能
- [ ] レシピ提案機能が動作
- [ ] エラーハンドリングが適切
- [ ] パフォーマンスが許容範囲内

## 📚 参考資料

- [LangChain Documentation](https://python.langchain.com/)
- [ReAct Agent](https://python.langchain.com/docs/modules/agents/agent_types/react)
- [LangChain Tools](https://python.langchain.com/docs/modules/tools/)
- [FastAPI Integration](https://fastapi.tiangolo.com/)

## 🔄 開発フロー

1. **設計**: アーキテクチャとツール設計
2. **実装**: LangChain Agentの作成
3. **統合**: 既存システムとの統合
4. **テスト**: 機能テストとパフォーマンステスト
5. **最適化**: パフォーマンスとエラーハンドリングの改善

---

**最終目標**: 自然言語で在庫管理とレシピ提案ができる、実用的なAI Agentの完成
