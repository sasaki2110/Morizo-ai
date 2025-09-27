# Phase 1: 超シンプルな依存関係
# 目標: 依存関係の基本概念理解

class SimpleTask:
    """シンプルなタスククラス - 依存関係の基本概念を学習"""
    
    def __init__(self, name: str, dependencies: list = None):
        self.name = name
        self.dependencies = dependencies or []
        self.result = None
        self.completed = False
    
    def can_run(self, completed_tasks: set) -> bool:
        """このタスクが実行可能かどうかを判定"""
        return all(dep in completed_tasks for dep in self.dependencies)
    
    def execute(self):
        """タスクを実行（模擬）"""
        print(f"実行中: {self.name}")
        self.result = f"{self.name}の結果"
        self.completed = True
        return self.result


def find_execution_order(tasks):
    """依存関係を考慮した実行順序を決定"""
    completed = set()
    order = []
    
    print("=== 依存関係の解析 ===")
    for task in tasks:
        deps_str = ", ".join(task.dependencies) if task.dependencies else "なし"
        print(f"タスク {task.name}: 依存関係 = [{deps_str}]")
    
    print("\n=== 実行順序の決定 ===")
    while len(completed) < len(tasks):
        # 実行可能なタスクを探す
        executable_tasks = [
            task for task in tasks 
            if task.name not in completed and task.can_run(completed)
        ]
        
        if not executable_tasks:
            print("❌ 循環依存または依存関係エラーが発生しました")
            break
        
        # 最初に見つかった実行可能なタスクを実行
        task = executable_tasks[0]
        order.append(task.name)
        completed.add(task.name)
        print(f"実行可能: {task.name}")
    
    return order


def execute_tasks_in_order(tasks):
    """決定された順序でタスクを実行"""
    order = find_execution_order(tasks)
    
    print(f"\n=== 実行順序: {order} ===")
    
    completed = set()
    results = {}
    
    for task_name in order:
        # タスクオブジェクトを取得
        task = next(t for t in tasks if t.name == task_name)
        
        # タスクを実行
        result = task.execute()
        results[task_name] = result
        completed.add(task_name)
        
        print(f"完了: {task_name} -> {result}")
    
    return results


# テストケース
def test_simple_dependencies():
    """基本的な依存関係のテスト"""
    print("🧪 テスト1: 基本的な依存関係")
    
    tasks = [
        SimpleTask("A"),  # 依存関係なし
        SimpleTask("B", ["A"]),  # Aに依存
        SimpleTask("C", ["A"]),  # Aに依存（並列実行可能）
        SimpleTask("D", ["B", "C"])  # BとCに依存
    ]
    
    results = execute_tasks_in_order(tasks)
    
    # 期待される実行順序: A -> B,C（並列） -> D
    expected_order = ["A", "B", "C", "D"]  # 実際はBとCは並列実行可能
    print(f"期待される順序: {expected_order}")
    print(f"実際の順序: {list(results.keys())}")
    
    return results


def test_parallel_execution():
    """並列実行可能なタスクのテスト"""
    print("\n🧪 テスト2: 並列実行可能なタスク")
    
    tasks = [
        SimpleTask("inventory_fetch"),  # 在庫取得
        SimpleTask("menu_generation", ["inventory_fetch"]),  # 献立生成
        SimpleTask("shopping_list", ["inventory_fetch"]),  # 買い物リスト
        SimpleTask("final_plan", ["menu_generation", "shopping_list"])  # 最終計画
    ]
    
    results = execute_tasks_in_order(tasks)
    
    print(f"実行結果: {list(results.keys())}")
    return results


def test_complex_dependencies():
    """複雑な依存関係のテスト"""
    print("\n🧪 テスト3: 複雑な依存関係")
    
    tasks = [
        SimpleTask("1"),  # 独立
        SimpleTask("2", ["1"]),  # 1に依存
        SimpleTask("3", ["1"]),  # 1に依存
        SimpleTask("4", ["2"]),  # 2に依存
        SimpleTask("5", ["3"]),  # 3に依存
        SimpleTask("6", ["4", "5"]),  # 4と5に依存
        SimpleTask("7", ["6"])  # 6に依存
    ]
    
    results = execute_tasks_in_order(tasks)
    
    print(f"実行結果: {list(results.keys())}")
    return results


if __name__ == "__main__":
    print("🚀 Phase 1: 超シンプルな依存関係の学習開始")
    print("=" * 50)
    
    # テスト実行
    test_simple_dependencies()
    test_parallel_execution()
    test_complex_dependencies()
    
    print("\n✅ Phase 1 完了!")
    print("学習内容:")
    print("- 依存関係の基本概念")
    print("- 実行順序の決定方法")
    print("- シンプルなアルゴリズムの実装")
    print("- 並列実行可能なタスクの特定")
