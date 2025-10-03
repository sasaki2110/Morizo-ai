# Morizo AI v2 - サービス層設計

## 📋 概要

**作成日**: 2025年1月29日  
**バージョン**: 1.0  
**目的**: サービス層のアーキテクチャ設計と実装方針

## 🧠 設計思想

### **サービス層の役割**
- **ビジネスロジックの実装**: 各ドメインのビジネスロジックを実装
- **データ変換**: コア層とMCP層の間でのデータ変換
- **バリデーション**: 入力データの検証
- **エラーハンドリング**: サービス固有のエラー処理

### **責任分離の徹底**
- **RecipeService**: レシピ関連のビジネスロジック
- **InventoryService**: 在庫管理のビジネスロジック
- **SessionService**: セッション管理のビジネスロジック

## 🏗️ サービス層アーキテクチャ

### **全体構成**
```
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                           │
├─────────────────┬─────────────────┬─────────────────────────┤
│  RecipeService  │ InventoryService│    SessionService       │
│                 │                 │                         │
│ • レシピ生成    │ • 在庫管理      │ • セッション管理        │
│ • レシピ検索    │ • 在庫検索      │ • ユーザー管理          │
│ • 履歴管理      │ • 在庫更新      │ • 認証管理              │
│ • 重複回避      │ • 在庫削除      │ • 権限管理              │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### **データフロー**
```
Core Layer (TrueReactAgent)
    ↓
Service Layer (各サービス)
    ↓
MCP Layer (各MCPツール)
    ↓
External Systems (DB, API, etc.)
```

## 🔧 サービスコンポーネント

### **1. RecipeService（レシピ関連サービス）**

#### **役割**
- レシピ生成・検索・履歴管理のビジネスロジック
- 食材重複回避の制御
- 過去履歴の管理

#### **主要機能**
```python
class RecipeService:
    async def generate_menu_plan(
        self, 
        inventory_items: List[str], 
        user_id: str,
        menu_type: str = "和食"
    ) -> MenuPlan:
        """在庫食材から献立構成を生成"""
        
    async def search_recipes(
        self, 
        dish_type: str, 
        title: str,
        available_ingredients: List[str]
    ) -> List[Recipe]:
        """レシピを検索"""
        
    async def check_cooking_history(
        self, 
        user_id: str, 
        recipe_titles: List[str],
        exclusion_days: int = 14
    ) -> CookingHistory:
        """過去の調理履歴をチェック"""
        
    async def save_recipe(
        self, 
        user_id: str, 
        recipe: Recipe
    ) -> str:
        """レシピを保存"""
```

#### **実装方針**
```python
class RecipeService:
    def __init__(self, recipe_mcp: RecipeMCP, db_mcp: DBMCP):
        self.recipe_mcp = recipe_mcp
        self.db_mcp = db_mcp
    
    async def generate_menu_plan(
        self, 
        inventory_items: List[str], 
        user_id: str,
        menu_type: str = "和食"
    ) -> MenuPlan:
        # 1. 過去履歴の取得
        recent_recipes = await self.get_recent_recipes(user_id, 14)
        
        # 2. 献立候補の生成
        menu_candidates = await self.recipe_mcp.generate_menu_candidates(
            inventory_items, menu_type
        )
        
        # 3. 重複チェック
        available_menus = self.filter_excluded_recipes(
            menu_candidates, recent_recipes
        )
        
        # 4. 最適な献立の選択
        selected_menu = self.select_best_menu(available_menus)
        
        return selected_menu
```

#### **食材重複回避ロジック**
```python
def filter_excluded_recipes(
    self, 
    menu_candidates: List[MenuPlan], 
    recent_recipes: List[str]
) -> List[MenuPlan]:
    """重複レシピを除外"""
    filtered_menus = []
    
    for menu in menu_candidates:
        # 過去履歴との重複チェック
        if not self.has_recipe_overlap(menu, recent_recipes):
            # 食材重複チェック
            if not self.has_ingredient_overlap(menu):
                filtered_menus.append(menu)
    
    return filtered_menus

def has_ingredient_overlap(self, menu: MenuPlan) -> bool:
    """献立内の食材重複チェック"""
    all_ingredients = []
    
    # 主菜の食材
    all_ingredients.extend(menu.main_dish.ingredients)
    
    # 副菜の食材
    all_ingredients.extend(menu.side_dish.ingredients)
    
    # 汁物の食材
    all_ingredients.extend(menu.soup.ingredients)
    
    # 重複チェック
    return len(all_ingredients) != len(set(all_ingredients))
```

### **2. InventoryService（在庫管理サービス）**

#### **役割**
- 在庫管理のビジネスロジック
- FIFO原則による在庫操作
- 在庫検索・更新・削除の制御

#### **主要機能**
```python
class InventoryService:
    async def add_inventory(
        self, 
        user_id: str, 
        item: InventoryItem
    ) -> str:
        """在庫を追加"""
        
    async def get_inventory(
        self, 
        user_id: str
    ) -> List[InventoryItem]:
        """在庫一覧を取得"""
        
    async def update_inventory(
        self, 
        user_id: str, 
        item_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """在庫を更新"""
        
    async def delete_inventory(
        self, 
        user_id: str, 
        item_id: str
    ) -> bool:
        """在庫を削除"""
```

#### **FIFO原則の実装**
```python
class InventoryService:
    async def add_inventory(
        self, 
        user_id: str, 
        item: InventoryItem
    ) -> str:
        # 1. 既存アイテムの確認
        existing_items = await self.db_mcp.get_inventory_by_name(
            user_id, item.item_name
        )
        
        # 2. 新規アイテムの追加
        new_item_id = await self.db_mcp.add_inventory(user_id, item)
        
        # 3. 在庫の再ソート（FIFO原則）
        await self.reorder_inventory_by_fifo(user_id, item.item_name)
        
        return new_item_id
    
    async def reorder_inventory_by_fifo(
        self, 
        user_id: str, 
        item_name: str
    ) -> None:
        """FIFO原則による在庫の再ソート"""
        items = await self.db_mcp.get_inventory_by_name(user_id, item_name)
        
        # 作成日時でソート（最古→最新）
        sorted_items = sorted(items, key=lambda x: x.created_at)
        
        # 順序の更新
        for i, item in enumerate(sorted_items):
            await self.db_mcp.update_inventory_order(
                user_id, item.id, i
            )
```

### **3. SessionService（セッション管理サービス）**

#### **役割**
- セッション管理のビジネスロジック
- ユーザー認証・認可の制御
- セッション状態の管理

#### **主要機能**
```python
class SessionService:
    async def create_session(
        self, 
        user_id: str, 
        token: str
    ) -> Session:
        """セッションを作成"""
        
    async def get_session(
        self, 
        session_id: str
    ) -> Optional[Session]:
        """セッションを取得"""
        
    async def update_session(
        self, 
        session_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """セッションを更新"""
        
    async def delete_session(
        self, 
        session_id: str
    ) -> bool:
        """セッションを削除"""
```

#### **実装方針**
```python
class SessionService:
    def __init__(self, auth_mcp: AuthMCP):
        self.auth_mcp = auth_mcp
        self.sessions: Dict[str, Session] = {}
    
    async def create_session(
        self, 
        user_id: str, 
        token: str
    ) -> Session:
        # 1. トークンの検証
        user_info = await self.auth_mcp.verify_token(token)
        
        if not user_info:
            raise AuthenticationError("Invalid token")
        
        # 2. セッションの作成
        session = Session(
            id=generate_session_id(),
            user_id=user_id,
            created_at=datetime.now(),
            last_accessed=datetime.now()
        )
        
        # 3. セッションの保存
        self.sessions[session.id] = session
        
        return session
    
    async def get_session(
        self, 
        session_id: str
    ) -> Optional[Session]:
        session = self.sessions.get(session_id)
        
        if session:
            # 最終アクセス時刻の更新
            session.last_accessed = datetime.now()
        
        return session
```

## 🔄 サービス間の連携

### **サービス間通信**
```python
class ServiceCoordinator:
    def __init__(
        self, 
        recipe_service: RecipeService,
        inventory_service: InventoryService,
        session_service: SessionService
    ):
        self.recipe_service = recipe_service
        self.inventory_service = inventory_service
        self.session_service = session_service
    
    async def process_menu_request(
        self, 
        user_id: str, 
        menu_type: str = "和食"
    ) -> MenuPlan:
        # 1. セッションの確認
        session = await self.session_service.get_session(user_id)
        if not session:
            raise AuthenticationError("Session not found")
        
        # 2. 在庫の取得
        inventory_items = await self.inventory_service.get_inventory(user_id)
        
        # 3. 献立の生成
        menu_plan = await self.recipe_service.generate_menu_plan(
            inventory_items, user_id, menu_type
        )
        
        return menu_plan
```

## 🚀 実装戦略

### **Phase 1: 基本サービス**
1. **RecipeService**: 基本的なレシピ生成・検索
2. **InventoryService**: 基本的な在庫管理
3. **SessionService**: 基本的なセッション管理

### **Phase 2: 高度な機能**
1. **食材重複回避**: 重複チェックロジックの実装
2. **FIFO原則**: 在庫のFIFO管理
3. **履歴管理**: 過去履歴の管理

### **Phase 3: 最適化**
1. **パフォーマンス最適化**: 処理時間の短縮
2. **メモリ最適化**: メモリ使用量の削減
3. **エラーハンドリング**: エラー処理の強化

## 📊 成功基準

### **機能面**
- [ ] RecipeServiceの動作確認
- [ ] InventoryServiceの動作確認
- [ ] SessionServiceの動作確認
- [ ] サービス間連携の動作確認
- [ ] 食材重複回避の動作確認

### **技術面**
- [ ] 全ファイルが100行以下
- [ ] 責任分離の徹底
- [ ] 疎結合設計の実現
- [ ] エラーハンドリングの実装
- [ ] バリデーションの実装

### **品質面**
- [ ] 各サービスの独立動作確認
- [ ] デバッグの容易性確認
- [ ] 拡張性の確認
- [ ] 保守性の確認

---

**このドキュメントは、Morizo AI v2のサービス層設計を定義します。**
**すべてのサービスは、この設計に基づいて実装されます。**
