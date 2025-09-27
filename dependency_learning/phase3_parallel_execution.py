# Phase 3: 並列実行の学習
# 目標: 並列実行可能なタスクの特定と実行

import asyncio
import time
from typing import Dict, List, Any, Set
from concurrent.futures import ThreadPoolExecutor
import threading


class AsyncMockTool:
    """非同期実行可能なMCPツールを模擬するクラス"""
    
    def __init__(self, name: str, execution_time: float = 1.0):
        self.name = name
        self.execution_time = execution_time
    
    async def execute_async(self, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """非同期でツールを実行（模擬）"""
        print(f"🔧 {self.name} 非同期実行開始... (所要時間: {self.execution_time}秒)")
        await asyncio.sleep(self.execution_time)
        
        # ツールごとの模擬結果を生成
        result = self._generate_mock_result(input_data)
        
        print(f"✅ {self.name} 非同期実行完了: {result.get('summary', '完了')}")
        return result
    
    def execute_sync(self, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """同期でツールを実行（模擬）"""
        print(f"🔧 {self.name} 同期実行開始... (所要時間: {self.execution_time}秒)")
        time.sleep(self.execution_time)
        
        result = self._generate_mock_result(input_data)
        
        print(f"✅ {self.name} 同期実行完了: {result.get('summary', '完了')}")
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


class ParallelTask:
    """並列実行を考慮したタスククラス"""
    
    def __init__(self, task_id: str, description: str, tool: AsyncMockTool, 
                 dependencies: List[str] = None, parameters: Dict[str, Any] = None):
        self.task_id = task_id
        self.description = description
        self.tool = tool
        self.dependencies = dependencies or []
        self.parameters = parameters or {}
        self.result = None
        self.completed = False
        self.execution_start_time = None
        self.execution_end_time = None
    
    def can_run(self, completed_tasks: Dict[str, 'ParallelTask']) -> bool:
        """このタスクが実行可能かどうかを判定"""
        return all(dep in completed_tasks for dep in self.dependencies)
    
    async def execute_async(self, completed_tasks: Dict[str, 'ParallelTask']) -> Dict[str, Any]:
        """非同期でタスクを実行"""
        self.execution_start_time = time.time()
        print(f"\n🚀 非同期タスク実行: {self.task_id}")
        print(f"   説明: {self.description}")
        print(f"   依存関係: {self.dependencies}")
        
        # 依存タスクの結果を取得してパラメータに追加
        input_data = self.parameters.copy()
        for dep_id in self.dependencies:
            if dep_id in completed_tasks:
                dep_result = completed_tasks[dep_id].result
                if dep_result:
                    input_data[dep_id] = dep_result
        
        # 非同期でツールを実行
        self.result = await self.tool.execute_async(input_data)
        self.completed = True
        self.execution_end_time = time.time()
        
        execution_time = self.execution_end_time - self.execution_start_time
        print(f"   結果: {self.result.get('summary', '完了')} (実行時間: {execution_time:.2f}秒)")
        return self.result
    
    def execute_sync(self, completed_tasks: Dict[str, 'ParallelTask']) -> Dict[str, Any]:
        """同期でタスクを実行"""
        self.execution_start_time = time.time()
        print(f"\n🚀 同期タスク実行: {self.task_id}")
        print(f"   説明: {self.description}")
        print(f"   依存関係: {self.dependencies}")
        
        # 依存タスクの結果を取得してパラメータに追加
        input_data = self.parameters.copy()
        for dep_id in self.dependencies:
            if dep_id in completed_tasks:
                dep_result = completed_tasks[dep_id].result
                if dep_result:
                    input_data[dep_id] = dep_result
        
        # 同期でツールを実行
        self.result = self.tool.execute_sync(input_data)
        self.completed = True
        self.execution_end_time = time.time()
        
        execution_time = self.execution_end_time - self.execution_start_time
        print(f"   結果: {self.result.get('summary', '完了')} (実行時間: {execution_time:.2f}秒)")
        return self.result


class ParallelTaskExecutor:
    """並列実行を考慮したタスク実行器"""
    
    def __init__(self):
        self.tools = {
            "inventory_list": AsyncMockTool("inventory_list", 0.5),
            "generate_menu_plan_with_history": AsyncMockTool("generate_menu_plan_with_history", 1.0),
            "generate_shopping_list": AsyncMockTool("generate_shopping_list", 0.8),
            "create_final_plan": AsyncMockTool("create_final_plan", 0.3)
        }
    
    def create_task(self, task_id: str, description: str, tool_name: str, 
                   dependencies: List[str] = None, parameters: Dict[str, Any] = None) -> ParallelTask:
        """タスクを作成"""
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"ツール '{tool_name}' が見つかりません")
        
        return ParallelTask(task_id, description, tool, dependencies, parameters)
    
    def find_parallel_executable_tasks(self, tasks: List[ParallelTask], 
                                     completed_tasks: Dict[str, ParallelTask]) -> List[ParallelTask]:
        """並列実行可能なタスクを特定"""
        executable_tasks = []
        for task in tasks:
            if not task.completed and task.can_run(completed_tasks):
                executable_tasks.append(task)
        return executable_tasks
    
    async def execute_with_parallel_dependencies(self, tasks: List[ParallelTask]) -> Dict[str, Any]:
        """依存関係を考慮して並列実行"""
        print("=" * 60)
        print("🎯 Phase 3: 並列実行の学習")
        print("=" * 60)
        
        completed_tasks = {}
        results = {}
        total_start_time = time.time()
        
        while len(completed_tasks) < len(tasks):
            # 並列実行可能なタスクを特定
            executable_tasks = self.find_parallel_executable_tasks(tasks, completed_tasks)
            
            if not executable_tasks:
                print("❌ 循環依存または依存関係エラーが発生しました")
                break
            
            print(f"\n🔄 並列実行可能なタスク: {[t.task_id for t in executable_tasks]}")
            
            # 並列実行
            if len(executable_tasks) == 1:
                # 単一タスクの場合は同期実行
                task = executable_tasks[0]
                result = task.execute_sync(completed_tasks)
                completed_tasks[task.task_id] = task
                results[task.task_id] = result
            else:
                # 複数タスクの場合は非同期並列実行
                print(f"⚡ {len(executable_tasks)}個のタスクを並列実行開始")
                
                # 非同期タスクを作成
                async_tasks = []
                for task in executable_tasks:
                    async_tasks.append(task.execute_async(completed_tasks))
                
                # 並列実行
                parallel_results = await asyncio.gather(*async_tasks)
                
                # 結果を保存
                for task, result in zip(executable_tasks, parallel_results):
                    completed_tasks[task.task_id] = task
                    results[task.task_id] = result
                
                print(f"⚡ 並列実行完了: {[t.task_id for t in executable_tasks]}")
        
        total_end_time = time.time()
        total_execution_time = total_end_time - total_start_time
        
        print(f"\n📊 総実行時間: {total_execution_time:.2f}秒")
        print(f"📊 完了タスク数: {len(completed_tasks)}")
        
        return results
    
    def execute_with_thread_parallel(self, tasks: List[ParallelTask]) -> Dict[str, Any]:
        """スレッド並列実行"""
        print("=" * 60)
        print("🎯 Phase 3: スレッド並列実行の学習")
        print("=" * 60)
        
        completed_tasks = {}
        results = {}
        total_start_time = time.time()
        
        while len(completed_tasks) < len(tasks):
            # 並列実行可能なタスクを特定
            executable_tasks = self.find_parallel_executable_tasks(tasks, completed_tasks)
            
            if not executable_tasks:
                print("❌ 循環依存または依存関係エラーが発生しました")
                break
            
            print(f"\n🔄 スレッド並列実行可能なタスク: {[t.task_id for t in executable_tasks]}")
            
            if len(executable_tasks) == 1:
                # 単一タスクの場合は同期実行
                task = executable_tasks[0]
                result = task.execute_sync(completed_tasks)
                completed_tasks[task.task_id] = task
                results[task.task_id] = result
            else:
                # 複数タスクの場合はスレッド並列実行
                print(f"🧵 {len(executable_tasks)}個のタスクをスレッド並列実行開始")
                
                with ThreadPoolExecutor(max_workers=len(executable_tasks)) as executor:
                    # スレッド並列実行
                    future_to_task = {
                        executor.submit(task.execute_sync, completed_tasks): task 
                        for task in executable_tasks
                    }
                    
                    # 結果を取得
                    for future in future_to_task:
                        task = future_to_task[future]
                        try:
                            result = future.result()
                            completed_tasks[task.task_id] = task
                            results[task.task_id] = result
                        except Exception as exc:
                            print(f"❌ タスク {task.task_id} でエラー: {exc}")
                
                print(f"🧵 スレッド並列実行完了: {[t.task_id for t in executable_tasks]}")
        
        total_end_time = time.time()
        total_execution_time = total_end_time - total_start_time
        
        print(f"\n📊 総実行時間: {total_execution_time:.2f}秒")
        print(f"📊 完了タスク数: {len(completed_tasks)}")
        
        return results


# テストケース
async def test_async_parallel_execution():
    """非同期並列実行のテスト"""
    print("\n🧪 テスト1: 非同期並列実行")
    
    executor = ParallelTaskExecutor()
    
    # 並列実行可能なタスクを作成
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
    
    # 非同期並列実行
    results = await executor.execute_with_parallel_dependencies(tasks)
    
    print(f"\n📊 非同期並列実行結果:")
    for task_id, result in results.items():
        print(f"  {task_id}: {result.get('summary', '完了')}")
    
    return results


def test_thread_parallel_execution():
    """スレッド並列実行のテスト"""
    print("\n🧪 テスト2: スレッド並列実行")
    
    executor = ParallelTaskExecutor()
    
    # 並列実行可能なタスクを作成
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
    
    # スレッド並列実行
    results = executor.execute_with_thread_parallel(tasks)
    
    print(f"\n📊 スレッド並列実行結果:")
    for task_id, result in results.items():
        print(f"  {task_id}: {result.get('summary', '完了')}")
    
    return results


async def test_performance_comparison():
    """パフォーマンス比較テスト"""
    print("\n🧪 テスト3: パフォーマンス比較")
    
    executor = ParallelTaskExecutor()
    
    # テスト用タスクを作成
    tasks = [
        executor.create_task("task1", "タスク1", "inventory_list", [], {}),
        executor.create_task("task2", "タスク2", "generate_menu_plan_with_history", ["task1"], {}),
        executor.create_task("task3", "タスク3", "generate_shopping_list", ["task1"], {}),
        executor.create_task("task4", "タスク4", "create_final_plan", ["task2", "task3"], {})
    ]
    
    print("📊 パフォーマンス比較:")
    print("1. 非同期並列実行")
    start_time = time.time()
    await executor.execute_with_parallel_dependencies(tasks.copy())
    async_time = time.time() - start_time
    
    print("2. スレッド並列実行")
    start_time = time.time()
    executor.execute_with_thread_parallel(tasks.copy())
    thread_time = time.time() - start_time
    
    print(f"\n📈 結果:")
    print(f"  非同期並列実行: {async_time:.2f}秒")
    print(f"  スレッド並列実行: {thread_time:.2f}秒")
    print(f"  効率: {thread_time/async_time:.2f}倍")


if __name__ == "__main__":
    print("🚀 Phase 3: 並列実行の学習")
    print("=" * 60)
    
    # テスト実行
    asyncio.run(test_async_parallel_execution())
    test_thread_parallel_execution()
    asyncio.run(test_performance_comparison())
    
    print("\n✅ Phase 3 完了!")
    print("学習内容:")
    print("- 並列実行可能なタスクの特定")
    print("- 非同期プログラミング（asyncio）")
    print("- スレッド並列実行（ThreadPoolExecutor）")
    print("- 依存関係を考慮した並列処理")
    print("- パフォーマンス比較")
