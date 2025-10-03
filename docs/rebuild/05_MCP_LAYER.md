# Morizo AI v2 - MCP層設計

## 📋 概要

**作成日**: 2025年1月29日  
**バージョン**: 1.0  
**目的**: MCP層のアーキテクチャ設計と実装方針

## 🧠 設計思想

### **MCP層の役割**
- **疎結合な通信**: 複数のマイクロエージェント間の疎結合な通信を実現
- **単独動作保証**: 各MCPは単独での動作を保証
- **相互独立性**: 各MCPサーバー間の直接通信を禁止
- **動的ツール提供**: ツールの動的発見と実行

### **疎結合設計の実装**
- **動的ツール取得**: MCPサーバーからツール詳細を動的に取得
- **プロンプト動的埋め込み**: 取得したツール説明を本体プロンプトに動的に埋め込み
- **直接呼び出し禁止**: MCPツールの機能を直接呼び出さず、MCP経由で実行
- **相互独立性**: 各MCPサーバー間の直接通信を禁止

## 🏗️ MCP層アーキテクチャ

### **全体構成**
```
┌─────────────────────────────────────────────────────────────┐
│                      MCP Layer                             │
├─────────────────┬─────────────────┬─────────────────────────┤
│   RecipeMCP     │     DBMCP       │      AuthMCP            │
│                 │                 │                         │
│ • レシピ生成    │ • 在庫CRUD      │ • 認証・認可            │
│ • レシピ検索    │ • ユーザー管理  │ • トークン検証          │
│ • Web検索       │ • 履歴管理      │ • セッション管理        │
│ • RAG検索       │ • 設定管理      │ • 権限チェック          │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### **データフロー**
```
Service Layer (各サービス)
    ↓
MCP Client (ツール選択・通信)
    ↓
MCP Servers (各MCPツール)
    ↓
External Systems (DB, API, etc.)
```

## 🔧 MCPコンポーネント

### **1. MCP Client（ツール通信）**

#### **役割**
- 複数のMCPサーバーの管理
- ツール名による適切なサーバー選択
- stdio接続による軽量通信

#### **主要機能**
```python
class MCPClient:
    async def get_available_tools(self) -> List[Tool]:
        """利用可能なツール一覧を取得"""
        
    async def call_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any]
    ) -> Any:
        """ツールを呼び出し"""
        
    async def select_server(self, tool_name: str) -> MCPServer:
        """ツール名に基づいて適切なサーバーを選択"""
```

#### **実装方針**
```python
class MCPClient:
    def __init__(self):
        self.servers = {
            "recipe": RecipeMCPServer(),
            "db": DBMCP Server(),
            "auth": AuthMCPServer()
        }
        self.tool_server_mapping = {
            "inventory_*": "db",
            "recipes_*": "db",
            "generate_menu_*": "recipe",
            "search_recipe_*": "recipe",
            "auth_*": "auth"
        }
    
    async def get_available_tools(self) -> List[Tool]:
        """利用可能なツール一覧を取得"""
        all_tools = []
        
        for server_name, server in self.servers.items():
            tools = await server.list_tools()
            all_tools.extend(tools)
        
        return all_tools
    
    async def call_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any]
    ) -> Any:
        """ツールを呼び出し"""
        # 1. 適切なサーバーの選択
        server = await self.select_server(tool_name)
        
        # 2. ツールの実行
        result = await server.call_tool(tool_name, parameters)
        
        return result
    
    async def select_server(self, tool_name: str) -> MCPServer:
        """ツール名に基づいて適切なサーバーを選択"""
        for pattern, server_name in self.tool_server_mapping.items():
            if fnmatch.fnmatch(tool_name, pattern):
                return self.servers[server_name]
        
        raise ValueError(f"No server found for tool: {tool_name}")
```

### **2. RecipeMCP（レシピMCP）**

#### **役割**
- 献立提案とレシピ検索機能の専門化されたツール提供
- 単独動作保証
- 説明の手厚さ

#### **利用可能ツール**
```python
@mcp.tool()
async def generate_menu_plan_with_history(
    inventory_items: List[str],
    user_id: str,
    menu_type: str = "和食"
) -> Dict[str, Any]:
    """
    在庫食材から献立構成を生成（過去履歴を考慮）
    
    Args:
        inventory_items: 在庫食材リスト
        user_id: ユーザーID（履歴チェック用）
        menu_type: 献立のタイプ
    
    Returns:
        {
            "main_dish": {
                "title": "牛乳と卵のフレンチトースト",
                "ingredients": ["牛乳", "卵", "パン", "バター"]
            },
            "side_dish": {
                "title": "ほうれん草の胡麻和え",
                "ingredients": ["ほうれん草", "胡麻", "醤油"]
            },
            "soup": {
                "title": "白菜とハムのクリームスープ",
                "ingredients": ["白菜", "ハム", "牛乳", "バター", "小麦粉"]
            },
            "ingredient_usage": {
                "used": ["牛乳", "卵", "パン", "バター", "ほうれん草", "胡麻", "白菜", "ハム", "小麦粉"],
                "remaining": []
            },
            "excluded_recipes": ["フレンチトースト", "オムレツ"],
            "fallback_used": true
        }
    """
```

#### **実装方針**
```python
class RecipeMCPServer:
    def __init__(self):
        self.llm_client = OpenAI()
        self.rag_client = RAGClient()
        self.web_search_client = WebSearchClient()
    
    async def generate_menu_plan_with_history(
        self, 
        inventory_items: List[str], 
        user_id: str,
        menu_type: str = "和食"
    ) -> Dict[str, Any]:
        # 1. LLMによる献立候補生成
        menu_candidates = await self._generate_menu_candidates(
            inventory_items, menu_type
        )
        
        # 2. 過去履歴のチェック（外部から受け取る）
        # 注意: 疎結合設計により、履歴チェックは外部で実行
        
        # 3. 最適な献立の選択
        selected_menu = self._select_best_menu(menu_candidates)
        
        # 4. 食材重複チェック
        if self._has_ingredient_overlap(selected_menu):
            # 代替案の生成
            selected_menu = await self._generate_alternative_menu(
                inventory_items, menu_type
            )
        
        return selected_menu
    
    async def _generate_menu_candidates(
        self, 
        inventory_items: List[str], 
        menu_type: str
    ) -> List[MenuPlan]:
        """LLMによる献立候補生成"""
        prompt = f"""
        在庫食材: {inventory_items}
        献立タイプ: {menu_type}
        
        以下の条件で献立を生成してください:
        1. 主菜・副菜・汁物の3品構成
        2. 在庫食材のみを使用
        3. 食材の重複を避ける
        4. 実用的で美味しいレシピ
        
        生成する献立:
        """
        
        response = await self.llm_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        # レスポンスの解析
        menu_candidates = self._parse_menu_response(response.choices[0].message.content)
        
        return menu_candidates
```

### **3. DBMCP（データベースMCP）**

#### **役割**
- データベースCRUD操作の専門化されたツール提供
- 単独動作保証
- 説明の手厚さ

#### **利用可能ツール**
```python
@mcp.tool()
async def inventory_add(
    user_id: str,
    item_name: str,
    quantity: float,
    unit: str,
    storage_location: str = None,
    expiry_date: str = None
) -> str:
    """
    在庫を追加する
    
    Args:
        user_id: ユーザーID
        item_name: アイテム名
        quantity: 数量
        unit: 単位
        storage_location: 保管場所
        expiry_date: 消費期限
    
    Returns:
        追加されたアイテムのID
    """

@mcp.tool()
async def inventory_list(user_id: str) -> List[Dict[str, Any]]:
    """
    在庫一覧を取得する
    
    Args:
        user_id: ユーザーID
    
    Returns:
        在庫アイテムのリスト
    """

@mcp.tool()
async def recipes_add(
    user_id: str,
    title: str,
    source: str,
    url: str = None
) -> str:
    """
    レシピを保存する
    
    Args:
        user_id: ユーザーID
        title: レシピタイトル
        source: レシピの出典
        url: レシピのURL
    
    Returns:
        保存されたレシピのID
    """
```

#### **実装方針**
```python
class DBMCP Server:
    def __init__(self):
        self.supabase_client = create_client(
            SUPABASE_URL, 
            SUPABASE_KEY
        )
    
    async def inventory_add(
        self, 
        user_id: str,
        item_name: str,
        quantity: float,
        unit: str,
        storage_location: str = None,
        expiry_date: str = None
    ) -> str:
        """在庫を追加"""
        try:
            result = await self.supabase_client.table("inventory").insert({
                "user_id": user_id,
                "item_name": item_name,
                "quantity": quantity,
                "unit": unit,
                "storage_location": storage_location,
                "expiry_date": expiry_date
            }).execute()
            
            return result.data[0]["id"]
            
        except Exception as e:
            logger.error(f"Failed to add inventory: {e}")
            raise DatabaseError(f"Failed to add inventory: {e}")
    
    async def inventory_list(self, user_id: str) -> List[Dict[str, Any]]:
        """在庫一覧を取得"""
        try:
            result = await self.supabase_client.table("inventory").select(
                "*"
            ).eq("user_id", user_id).order("created_at", desc=False).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Failed to list inventory: {e}")
            raise DatabaseError(f"Failed to list inventory: {e}")
```

### **4. AuthMCP（認証MCP）**

#### **役割**
- 認証・認可の専門化されたツール提供
- トークン検証
- セッション管理

#### **利用可能ツール**
```python
@mcp.tool()
async def verify_token(token: str) -> Dict[str, Any]:
    """
    トークンを検証する
    
    Args:
        token: 検証するトークン
    
    Returns:
        ユーザー情報（検証成功時）
        None（検証失敗時）
    """

@mcp.tool()
async def get_user_info(user_id: str) -> Dict[str, Any]:
    """
    ユーザー情報を取得する
    
    Args:
        user_id: ユーザーID
    
    Returns:
        ユーザー情報
    """
```

#### **実装方針**
```python
class AuthMCPServer:
    def __init__(self):
        self.supabase_client = create_client(
            SUPABASE_URL, 
            SUPABASE_KEY
        )
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """トークンを検証"""
        try:
            # トークンの検証
            response = await self.supabase_client.auth.get_user(token)
            
            if response.user:
                return {
                    "user_id": response.user.id,
                    "email": response.user.email,
                    "verified": True
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None
```

## 🔄 MCP間の通信

### **疎結合通信の実現**
```python
class MCPCommunicationManager:
    def __init__(self):
        self.mcp_client = MCPClient()
    
    async def execute_task_chain(self, tasks: List[Task]) -> Dict[str, Any]:
        """タスクチェーンの実行"""
        results = {}
        
        for task in tasks:
            # 1. ツールの実行
            result = await self.mcp_client.call_tool(
                task.tool, 
                task.parameters
            )
            
            # 2. 結果の保存
            results[task.id] = result
            
            # 3. 次のタスクへのデータ注入
            if task.next_tasks:
                for next_task in task.next_tasks:
                    # 前のタスクの結果を次のタスクに注入
                    next_task.parameters = self._inject_data(
                        next_task.parameters, 
                        result
                    )
        
        return results
    
    def _inject_data(
        self, 
        parameters: Dict[str, Any], 
        previous_result: Any
    ) -> Dict[str, Any]:
        """前のタスクの結果を次のタスクに注入"""
        # パラメータ内のプレースホルダーを置換
        for key, value in parameters.items():
            if isinstance(value, str) and "{{" in value:
                # プレースホルダーの置換ロジック
                parameters[key] = self._replace_placeholder(
                    value, 
                    previous_result
                )
        
        return parameters
```

## 🚀 実装戦略

### **Phase 1: 基本MCP**
1. **MCPClient**: 基本的なツール通信
2. **RecipeMCP**: 基本的なレシピ生成・検索
3. **DBMCP**: 基本的なデータベース操作

### **Phase 2: 高度な機能**
1. **疎結合通信**: サーバー間の疎結合通信
2. **動的ツール選択**: ツール名によるサーバー選択
3. **エラーハンドリング**: MCP固有のエラー処理

### **Phase 3: 最適化**
1. **パフォーマンス最適化**: 通信速度の向上
2. **メモリ最適化**: メモリ使用量の削減
3. **ログ最適化**: ログ出力の最適化

## 📊 成功基準

### **機能面**
- [ ] MCPClientの動作確認
- [ ] RecipeMCPの動作確認
- [ ] DBMCPの動作確認
- [ ] AuthMCPの動作確認
- [ ] 疎結合通信の動作確認

### **技術面**
- [ ] 全ファイルが100行以下
- [ ] 疎結合設計の実現
- [ ] 単独動作保証
- [ ] 動的ツール選択
- [ ] エラーハンドリング

### **品質面**
- [ ] 各MCPの独立動作確認
- [ ] デバッグの容易性確認
- [ ] 拡張性の確認
- [ ] 保守性の確認

---

**このドキュメントは、Morizo AI v2のMCP層設計を定義します。**
**すべてのMCPは、この設計に基づいて実装されます。**
