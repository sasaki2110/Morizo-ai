# Phase 2: 実際のMCPツールを模擬した依存関係管理
# 目標: 実際のMCPツールを模擬した依存関係管理とデータフロー

import time
import json
from typing import Dict, List, Any, Optional


class MockTool:
    """実際のMCPツールを模擬するクラス"""
    
    def __init__(self, name: str, execution_time: float = 1.0):
        self.name = name
        self.execution_time = execution_time
    
    def execute(self, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """ツールを実行（模擬）"""
        print(f"🔧 {self.name} 実行中... (所要時間: {self.execution_time}秒)")
        time.sleep(self.execution_time)
        
        # ツールごとの模擬結果を生成
        result = self._generate_mock_result(input_data)
        
        print(f"✅ {self.name} 完了: {result.get('summary', '完了')}")
        return result
    
    def _generate_mock_result(self, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """ツールごとの模擬結果を生成"""
        if self.name == "inventory_list":
            return {
                "summary": "在庫一覧を取得",
                "data": [
                    {"id": 1, "name": "米", "quantity": 2, "unit": "kg"},
                    {"id": 2, "name": "卵", "quantity": 10, "unit": "個"},
                    {"id": 3, "name": "牛乳", "quantity": 1, "unit": "L"}
                ]
            }
        elif self.name == "generate_menu_plan_with_history":
            inventory = input_data.get("inventory", []) if input_data else []
            return {
                "summary": f"在庫{len(inventory)}品目から献立を生成",
                "data": {
                    "breakfast": "卵かけご飯",
                    "lunch": "牛乳を使ったスープ",
                    "dinner": "米を使ったリゾット"
                }
            }
        elif self.name == "generate_shopping_list":
            inventory = input_data.get("inventory", []) if input_data else []
            return {
                "summary": f"在庫{len(inventory)}品目から買い物リストを生成",
                "data": [
                    {"name": "野菜", "quantity": 3, "unit": "種類"},
                    {"name": "肉", "quantity": 2, "unit": "種類"},
                    {"name": "調味料", "quantity": 1, "unit": "セット"}
                ]
            }
        elif self.name == "create_final_plan":
            menu = input_data.get("menu", {}) if input_data else {}
            shopping = input_data.get("shopping", []) if input_data else []
            return {
                "summary": f"献立{len(menu)}品目と買い物{len(shopping)}品目の最終計画を作成",
                "data": {
                    "plan_type": "週間計画",
                    "total_items": len(menu) + len(shopping),
                    "estimated_time": "2時間"
                }
            }
        else:
            return {
                "summary": f"{self.name}の実行完了",
                "data": input_data or {}
            }


class TaskWithData:
    """データフローを考慮したタスククラス"""
    
    def __init__(self, task_id: str, description: str, tool: MockTool, 
                 dependencies: List[str] = None, parameters: Dict[str, Any] = None):
        self.task_id = task_id
        self.description = description
        self.tool = tool
        self.dependencies = dependencies or []
        self.parameters = parameters or {}
        self.result = None
        self.completed = False
    
    def can_run(self, completed_tasks: Dict[str, 'TaskWithData']) -> bool:
        """このタスクが実行可能かどうかを判定"""
        return all(dep in completed_tasks for dep in self.dependencies)
    
    def execute(self, completed_tasks: Dict[str, 'TaskWithData']) -> Dict[str, Any]:
        """タスクを実行し、データフローを処理"""
        print(f"\n🚀 タスク実行: {self.task_id}")
        print(f"   説明: {self.description}")
        print(f"   依存関係: {self.dependencies}")
        
        # 依存タスクの結果を取得してパラメータに追加
        input_data = self.parameters.copy()
        for dep_id in self.dependencies:
            if dep_id in completed_tasks:
                dep_result = completed_tasks[dep_id].result
                if dep_result:
                    # 依存タスクの結果をパラメータに追加
                    input_data[dep_id] = dep_result
        
        # ツールを実行
        self.result = self.tool.execute(input_data)
        self.completed = True
        
        print(f"   結果: {self.result.get('summary', '完了')}")
        return self.result


class TaskExecutor:
    """依存関係を考慮したタスク実行器"""
    
    def __init__(self):
        self.tools = {
            "inventory_list": MockTool("inventory_list", 0.5),
            "generate_menu_plan_with_history": MockTool("generate_menu_plan_with_history", 1.0),
            "generate_shopping_list": MockTool("generate_shopping_list", 0.8),
            "create_final_plan": MockTool("create_final_plan", 0.3)
        }
    
    def create_task(self, task_id: str, description: str, tool_name: str, 
                   dependencies: List[str] = None, parameters: Dict[str, Any] = None) -> TaskWithData:
        """タスクを作成"""
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"ツール '{tool_name}' が見つかりません")
        
        return TaskWithData(task_id, description, tool, dependencies, parameters)
    
    def execute_with_dependencies(self, tasks: List[TaskWithData]) -> Dict[str, Any]:
        """依存関係を考慮してタスクを実行"""
        print("=" * 60)
        print("🎯 Phase 2: 実際のMCPツールを模擬した依存関係管理")
        print("=" * 60)
        
        # 依存関係を解決して実行順序を決定
        execution_order = self._resolve_dependencies(tasks)
        
        # 順番に実行
        completed_tasks = {}
        results = {}
        
        for step, task_id in enumerate(execution_order, 1):
            task = next(t for t in tasks if t.task_id == task_id)
            
            print(f"\n{'='*20} ステップ {step}: {task_id} {'='*20}")
            
            # 実行前の状態を表示
            self._display_task_states(tasks, completed_tasks, step, "実行前")
            
            if task.can_run(completed_tasks):
                result = task.execute(completed_tasks)
                completed_tasks[task_id] = task
                results[task_id] = result
                
                # 実行後の状態を表示
                self._display_task_states(tasks, completed_tasks, step, "実行後")
            else:
                print(f"❌ 依存関係エラー: {task_id}")
                break
        
        return results
    
    def _resolve_dependencies(self, tasks: List[TaskWithData]) -> List[str]:
        """依存関係を解決して実行順序を決定"""
        completed = set()
        order = []
        
        print("\n📋 依存関係の解析:")
        for task in tasks:
            deps_str = ", ".join(task.dependencies) if task.dependencies else "なし"
            print(f"  {task.task_id}: {task.description}")
            print(f"    依存関係: [{deps_str}]")
            print(f"    ツール: {task.tool.name}")
        
        print("\n🔄 実行順序の決定:")
        while len(completed) < len(tasks):
            executable_tasks = [
                task for task in tasks 
                if task.task_id not in completed and task.can_run(completed)
            ]
            
            if not executable_tasks:
                print("❌ 循環依存または依存関係エラーが発生しました")
                break
            
            task = executable_tasks[0]
            order.append(task.task_id)
            completed.add(task.task_id)
            print(f"  ✅ 実行可能: {task.task_id}")
        
        print(f"\n📝 最終実行順序: {order}")
        return order
    
    def _display_task_states(self, tasks: List[TaskWithData], completed_tasks: Dict[str, TaskWithData], 
                           step: int, phase: str):
        """全タスクの状態を表示"""
        print(f"\n📊 {phase} - 全タスクの状態:")
        print("-" * 80)
        
        for task in tasks:
            # 基本情報
            status = "✅ 完了" if task.completed else "⏳ 待機中"
            can_run = "🟢 実行可能" if task.can_run(completed_tasks) else "🔴 実行不可"
            
            print(f"📋 {task.task_id}: {task.description}")
            print(f"   状態: {status} | {can_run}")
            print(f"   依存関係: {task.dependencies}")
            print(f"   初期パラメータ: {task.parameters}")
            
            # 実行時のパラメータを計算（実行可能な場合）
            if task.can_run(completed_tasks):
                runtime_params = task.parameters.copy()
                for dep_id in task.dependencies:
                    if dep_id in completed_tasks:
                        dep_result = completed_tasks[dep_id].result
                        if dep_result:
                            runtime_params[dep_id] = dep_result
                
                print(f"   実行時パラメータ: {runtime_params}")
            
            # 結果（完了している場合）
            if task.completed and task.result:
                print(f"   結果: {task.result.get('summary', '完了')}")
            
            print()


# テストケース
def test_menu_planning_workflow():
    """献立計画ワークフローのテスト"""
    print("\n🧪 テスト1: 献立計画ワークフロー")
    
    executor = TaskExecutor()
    
    # タスクを作成
    tasks = [
        executor.create_task(
            "inventory_fetch",
            "現在の在庫を取得",
            "inventory_list",
            dependencies=[],
            parameters={}
        ),
        executor.create_task(
            "menu_generation",
            "在庫から献立を生成",
            "generate_menu_plan_with_history",
            dependencies=["inventory_fetch"],
            parameters={}
        ),
        executor.create_task(
            "shopping_list",
            "不足食材の買い物リストを生成",
            "generate_shopping_list",
            dependencies=["inventory_fetch"],
            parameters={}
        ),
        executor.create_task(
            "final_plan",
            "献立と買い物リストの最終計画を作成",
            "create_final_plan",
            dependencies=["menu_generation", "shopping_list"],
            parameters={}
        )
    ]
    
    # 初期状態を表示
    print("\n🔍 初期状態:")
    executor._display_task_states(tasks, {}, 0, "初期状態")
    
    # 実行
    results = executor.execute_with_dependencies(tasks)
    
    print(f"\n📊 実行結果:")
    for task_id, result in results.items():
        print(f"  {task_id}: {result.get('summary', '完了')}")
    
    return results


def test_data_flow():
    """データフローのテスト"""
    print("\n🧪 テスト2: データフローの確認")
    
    executor = TaskExecutor()
    
    # より複雑なデータフローをテスト
    tasks = [
        executor.create_task(
            "step1",
            "ステップ1: 基本データ取得",
            "inventory_list",
            dependencies=[],
            parameters={"step": 1}
        ),
        executor.create_task(
            "step2",
            "ステップ2: データ処理",
            "generate_menu_plan_with_history",
            dependencies=["step1"],
            parameters={"step": 2}
        ),
        executor.create_task(
            "step3",
            "ステップ3: 最終処理",
            "create_final_plan",
            dependencies=["step2"],
            parameters={"step": 3}
        )
    ]
    
    # 初期状態を表示
    print("\n🔍 初期状態:")
    executor._display_task_states(tasks, {}, 0, "初期状態")
    
    results = executor.execute_with_dependencies(tasks)
    
    print(f"\n📊 データフロー結果:")
    for task_id, result in results.items():
        print(f"  {task_id}: {result.get('summary', '完了')}")
        if 'data' in result:
            print(f"    データ: {result['data']}")
    
    return results


if __name__ == "__main__":
    print("🚀 Phase 2: 実際のMCPツールを模擬した依存関係管理")
    print("=" * 60)
    
    # テスト実行
    test_menu_planning_workflow()
    test_data_flow()
    
    print("\n✅ Phase 2 完了!")
    print("学習内容:")
    print("- 実際のMCPツールの模擬")
    print("- データフローの管理")
    print("- 実行結果の受け渡し")
    print("- より実用的な依存関係管理")
