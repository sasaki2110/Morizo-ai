# Phase 4: エラーハンドリング
# 目標: 依存関係エラー時の処理と堅牢性の向上

import asyncio
import time
import random
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import traceback


class TaskStatus(Enum):
    """タスクの状態を定義"""
    PENDING = "pending"      # 待機中
    RUNNING = "running"      # 実行中
    COMPLETED = "completed"  # 完了
    FAILED = "failed"        # 失敗
    RETRYING = "retrying"    # 再試行中
    SKIPPED = "skipped"      # スキップ


class TaskError(Exception):
    """タスク実行エラーのカスタム例外"""
    def __init__(self, task_id: str, message: str, original_error: Exception = None):
        self.task_id = task_id
        self.message = message
        self.original_error = original_error
        super().__init__(f"Task {task_id}: {message}")


class RobustMockTool:
    """エラーハンドリング対応のMCPツールを模擬するクラス"""
    
    def __init__(self, name: str, execution_time: float = 1.0, failure_rate: float = 0.0):
        self.name = name
        self.execution_time = execution_time
        self.failure_rate = failure_rate  # 失敗率（0.0-1.0）
        self.execution_count = 0
    
    async def execute_async(self, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """非同期でツールを実行（エラーハンドリング付き）"""
        self.execution_count += 1
        
        print(f"🔧 {self.name} 非同期実行開始... (試行回数: {self.execution_count})")
        
        # 失敗率に基づいてエラーを発生
        if random.random() < self.failure_rate:
            error_msg = f"{self.name} でエラーが発生しました"
            print(f"❌ {error_msg}")
            raise TaskError(self.name, error_msg)
        
        await asyncio.sleep(self.execution_time)
        
        result = self._generate_mock_result(input_data)
        print(f"✅ {self.name} 非同期実行完了: {result.get('summary', '完了')}")
        return result
    
    def execute_sync(self, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """同期でツールを実行（エラーハンドリング付き）"""
        self.execution_count += 1
        
        print(f"🔧 {self.name} 同期実行開始... (試行回数: {self.execution_count})")
        
        # 失敗率に基づいてエラーを発生
        if random.random() < self.failure_rate:
            error_msg = f"{self.name} でエラーが発生しました"
            print(f"❌ {error_msg}")
            raise TaskError(self.name, error_msg)
        
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
        elif self.name == "fallback_tool":
            return {
                "summary": "フォールバック処理を実行",
                "data": {"fallback": True, "message": "代替処理が実行されました"}
            }
        else:
            return {
                "summary": f"{self.name}の実行完了",
                "data": input_data or {}
            }


class RobustTask:
    """エラーハンドリング対応のタスククラス"""
    
    def __init__(self, task_id: str, description: str, tool: RobustMockTool, 
                 dependencies: List[str] = None, parameters: Dict[str, Any] = None,
                 max_retries: int = 3, fallback_tool: RobustMockTool = None):
        self.task_id = task_id
        self.description = description
        self.tool = tool
        self.dependencies = dependencies or []
        self.parameters = parameters or {}
        self.max_retries = max_retries
        self.fallback_tool = fallback_tool
        
        self.result = None
        self.status = TaskStatus.PENDING
        self.retry_count = 0
        self.error_history = []
        self.execution_start_time = None
        self.execution_end_time = None
    
    def can_run(self, completed_tasks: Dict[str, 'RobustTask']) -> bool:
        """このタスクが実行可能かどうかを判定"""
        return all(dep in completed_tasks for dep in self.dependencies)
    
    async def execute_async(self, completed_tasks: Dict[str, 'RobustTask']) -> Dict[str, Any]:
        """非同期でタスクを実行（エラーハンドリング付き）"""
        self.status = TaskStatus.RUNNING
        self.execution_start_time = time.time()
        
        print(f"\n🚀 非同期タスク実行: {self.task_id}")
        print(f"   説明: {self.description}")
        print(f"   依存関係: {self.dependencies}")
        print(f"   再試行回数: {self.retry_count}/{self.max_retries}")
        
        # 依存タスクの結果を取得してパラメータに追加
        input_data = self.parameters.copy()
        for dep_id in self.dependencies:
            if dep_id in completed_tasks:
                dep_result = completed_tasks[dep_id].result
                if dep_result:
                    input_data[dep_id] = dep_result
        
        # 再試行ループ
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    self.status = TaskStatus.RETRYING
                    print(f"   🔄 再試行 {attempt}/{self.max_retries}")
                    await asyncio.sleep(1)  # 再試行前の待機
                
                # ツールを実行
                self.result = await self.tool.execute_async(input_data)
                self.status = TaskStatus.COMPLETED
                self.execution_end_time = time.time()
                
                execution_time = self.execution_end_time - self.execution_start_time
                print(f"   ✅ 成功: {self.result.get('summary', '完了')} (実行時間: {execution_time:.2f}秒)")
                return self.result
                
            except TaskError as e:
                self.error_history.append({
                    "attempt": attempt + 1,
                    "error": str(e),
                    "timestamp": time.time()
                })
                
                print(f"   ❌ エラー (試行 {attempt + 1}/{self.max_retries + 1}): {e.message}")
                
                if attempt == self.max_retries:
                    # 最大再試行回数に達した場合
                    if self.fallback_tool:
                        print(f"   🔄 フォールバック処理を実行")
                        try:
                            self.result = await self.fallback_tool.execute_async(input_data)
                            self.status = TaskStatus.COMPLETED
                            self.execution_end_time = time.time()
                            
                            execution_time = self.execution_end_time - self.execution_start_time
                            print(f"   ✅ フォールバック成功: {self.result.get('summary', '完了')} (実行時間: {execution_time:.2f}秒)")
                            return self.result
                        except Exception as fallback_error:
                            print(f"   ❌ フォールバックも失敗: {fallback_error}")
                            self.status = TaskStatus.FAILED
                            raise TaskError(self.task_id, f"フォールバック処理も失敗: {fallback_error}", fallback_error)
                    else:
                        self.status = TaskStatus.FAILED
                        raise TaskError(self.task_id, f"最大再試行回数に達しました: {e.message}", e)
        
        return self.result
    
    def execute_sync(self, completed_tasks: Dict[str, 'RobustTask']) -> Dict[str, Any]:
        """同期でタスクを実行（エラーハンドリング付き）"""
        self.status = TaskStatus.RUNNING
        self.execution_start_time = time.time()
        
        print(f"\n🚀 同期タスク実行: {self.task_id}")
        print(f"   説明: {self.description}")
        print(f"   依存関係: {self.dependencies}")
        print(f"   再試行回数: {self.retry_count}/{self.max_retries}")
        
        # 依存タスクの結果を取得してパラメータに追加
        input_data = self.parameters.copy()
        for dep_id in self.dependencies:
            if dep_id in completed_tasks:
                dep_result = completed_tasks[dep_id].result
                if dep_result:
                    input_data[dep_id] = dep_result
        
        # 再試行ループ
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    self.status = TaskStatus.RETRYING
                    print(f"   🔄 再試行 {attempt}/{self.max_retries}")
                    time.sleep(1)  # 再試行前の待機
                
                # ツールを実行
                self.result = self.tool.execute_sync(input_data)
                self.status = TaskStatus.COMPLETED
                self.execution_end_time = time.time()
                
                execution_time = self.execution_end_time - self.execution_start_time
                print(f"   ✅ 成功: {self.result.get('summary', '完了')} (実行時間: {execution_time:.2f}秒)")
                return self.result
                
            except TaskError as e:
                self.error_history.append({
                    "attempt": attempt + 1,
                    "error": str(e),
                    "timestamp": time.time()
                })
                
                print(f"   ❌ エラー (試行 {attempt + 1}/{self.max_retries + 1}): {e.message}")
                
                if attempt == self.max_retries:
                    # 最大再試行回数に達した場合
                    if self.fallback_tool:
                        print(f"   🔄 フォールバック処理を実行")
                        try:
                            self.result = self.fallback_tool.execute_sync(input_data)
                            self.status = TaskStatus.COMPLETED
                            self.execution_end_time = time.time()
                            
                            execution_time = self.execution_end_time - self.execution_start_time
                            print(f"   ✅ フォールバック成功: {self.result.get('summary', '完了')} (実行時間: {execution_time:.2f}秒)")
                            return self.result
                        except Exception as fallback_error:
                            print(f"   ❌ フォールバックも失敗: {fallback_error}")
                            self.status = TaskStatus.FAILED
                            raise TaskError(self.task_id, f"フォールバック処理も失敗: {fallback_error}", fallback_error)
                    else:
                        self.status = TaskStatus.FAILED
                        raise TaskError(self.task_id, f"最大再試行回数に達しました: {e.message}", e)
        
        return self.result


class RobustTaskExecutor:
    """エラーハンドリング対応のタスク実行器"""
    
    def __init__(self):
        self.tools = {
            "inventory_list": RobustMockTool("inventory_list", 0.5, failure_rate=0.0),
            "generate_menu_plan_with_history": RobustMockTool("generate_menu_plan_with_history", 1.0, failure_rate=0.3),
            "generate_shopping_list": RobustMockTool("generate_shopping_list", 0.8, failure_rate=0.2),
            "create_final_plan": RobustMockTool("create_final_plan", 0.3, failure_rate=0.1),
            "fallback_tool": RobustMockTool("fallback_tool", 0.2, failure_rate=0.0)
        }
    
    def create_task(self, task_id: str, description: str, tool_name: str, 
                   dependencies: List[str] = None, parameters: Dict[str, Any] = None,
                   max_retries: int = 3, fallback_tool_name: str = None) -> RobustTask:
        """タスクを作成"""
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"ツール '{tool_name}' が見つかりません")
        
        fallback_tool = None
        if fallback_tool_name:
            fallback_tool = self.tools.get(fallback_tool_name)
            if not fallback_tool:
                raise ValueError(f"フォールバックツール '{fallback_tool_name}' が見つかりません")
        
        return RobustTask(task_id, description, tool, dependencies, parameters, max_retries, fallback_tool)
    
    def find_executable_tasks(self, tasks: List[RobustTask], 
                             completed_tasks: Dict[str, RobustTask]) -> List[RobustTask]:
        """実行可能なタスクを特定"""
        executable_tasks = []
        for task in tasks:
            if task.status == TaskStatus.PENDING and task.can_run(completed_tasks):
                executable_tasks.append(task)
        return executable_tasks
    
    async def execute_with_error_handling(self, tasks: List[RobustTask]) -> Dict[str, Any]:
        """エラーハンドリング付きでタスクを実行"""
        print("=" * 60)
        print("🎯 Phase 4: エラーハンドリング")
        print("=" * 60)
        
        completed_tasks = {}
        results = {}
        failed_tasks = []
        total_start_time = time.time()
        
        while len(completed_tasks) < len(tasks):
            # 実行可能なタスクを特定
            executable_tasks = self.find_executable_tasks(tasks, completed_tasks)
            
            if not executable_tasks:
                # 実行可能なタスクがない場合
                remaining_tasks = [t for t in tasks if t.status == TaskStatus.PENDING]
                if remaining_tasks:
                    print(f"❌ 循環依存または依存関係エラーが発生しました")
                    print(f"   残りのタスク: {[t.task_id for t in remaining_tasks]}")
                    break
                else:
                    break
            
            print(f"\n🔄 実行可能なタスク: {[t.task_id for t in executable_tasks]}")
            
            # 並列実行
            if len(executable_tasks) == 1:
                # 単一タスクの場合は同期実行
                task = executable_tasks[0]
                try:
                    result = task.execute_sync(completed_tasks)
                    completed_tasks[task.task_id] = task
                    results[task.task_id] = result
                except TaskError as e:
                    print(f"❌ タスク {task.task_id} が最終的に失敗しました: {e.message}")
                    failed_tasks.append(task)
            else:
                # 複数タスクの場合は非同期並列実行
                print(f"⚡ {len(executable_tasks)}個のタスクを並列実行開始")
                
                async_tasks = []
                for task in executable_tasks:
                    async_tasks.append(task.execute_async(completed_tasks))
                
                try:
                    # 並列実行（エラーハンドリング付き）
                    parallel_results = await asyncio.gather(*async_tasks, return_exceptions=True)
                    
                    # 結果を処理
                    for task, result in zip(executable_tasks, parallel_results):
                        if isinstance(result, Exception):
                            print(f"❌ タスク {task.task_id} が失敗しました: {result}")
                            failed_tasks.append(task)
                        else:
                            completed_tasks[task.task_id] = task
                            results[task.task_id] = result
                    
                    print(f"⚡ 並列実行完了: {[t.task_id for t in executable_tasks]}")
                    
                except Exception as e:
                    print(f"❌ 並列実行中にエラーが発生しました: {e}")
                    break
        
        total_end_time = time.time()
        total_execution_time = total_end_time - total_start_time
        
        # 結果サマリーを表示
        self._display_execution_summary(tasks, completed_tasks, failed_tasks, total_execution_time)
        
        return results
    
    def _display_execution_summary(self, tasks: List[RobustTask], completed_tasks: Dict[str, RobustTask], 
                                  failed_tasks: List[RobustTask], total_execution_time: float):
        """実行結果のサマリーを表示"""
        print(f"\n📊 実行結果サマリー:")
        print(f"   総実行時間: {total_execution_time:.2f}秒")
        print(f"   完了タスク数: {len(completed_tasks)}")
        print(f"   失敗タスク数: {len(failed_tasks)}")
        print(f"   成功率: {len(completed_tasks)}/{len(tasks)} ({len(completed_tasks)/len(tasks)*100:.1f}%)")
        
        print(f"\n✅ 完了したタスク:")
        for task_id, task in completed_tasks.items():
            print(f"   {task_id}: {task.status.value}")
        
        if failed_tasks:
            print(f"\n❌ 失敗したタスク:")
            for task in failed_tasks:
                print(f"   {task.task_id}: {task.status.value}")
                if task.error_history:
                    print(f"      エラー履歴: {len(task.error_history)}回")
        
        print(f"\n🔄 再試行統計:")
        total_retries = sum(len(task.error_history) for task in tasks)
        print(f"   総再試行回数: {total_retries}")


# テストケース
async def test_error_handling():
    """エラーハンドリングのテスト"""
    print("\n🧪 テスト1: エラーハンドリング")
    
    executor = RobustTaskExecutor()
    
    # エラーが発生しやすいタスクを作成
    tasks = [
        executor.create_task(
            "inventory_fetch",
            "現在の在庫を取得",
            "inventory_list",
            dependencies=[],
            parameters={},
            max_retries=2
        ),
        executor.create_task(
            "menu_generation",
            "在庫から献立を生成",
            "generate_menu_plan_with_history",
            dependencies=["inventory_fetch"],
            parameters={},
            max_retries=3,
            fallback_tool_name="fallback_tool"
        ),
        executor.create_task(
            "shopping_list",
            "不足食材の買い物リストを生成",
            "generate_shopping_list",
            dependencies=["inventory_fetch"],
            parameters={},
            max_retries=2
        ),
        executor.create_task(
            "final_plan",
            "献立と買い物リストの最終計画を作成",
            "create_final_plan",
            dependencies=["menu_generation", "shopping_list"],
            parameters={},
            max_retries=1
        )
    ]
    
    # エラーハンドリング付き実行
    results = await executor.execute_with_error_handling(tasks)
    
    print(f"\n📊 エラーハンドリング結果:")
    for task_id, result in results.items():
        print(f"  {task_id}: {result.get('summary', '完了')}")
    
    return results


async def test_circular_dependency():
    """循環依存のテスト"""
    print("\n🧪 テスト2: 循環依存の検出")
    
    executor = RobustTaskExecutor()
    
    # 循環依存を作成
    tasks = [
        executor.create_task("task1", "タスク1", "inventory_list", ["task3"], {}),
        executor.create_task("task2", "タスク2", "generate_menu_plan_with_history", ["task1"], {}),
        executor.create_task("task3", "タスク3", "generate_shopping_list", ["task2"], {})
    ]
    
    # 循環依存の検出
    results = await executor.execute_with_error_handling(tasks)
    
    print(f"\n📊 循環依存検出結果:")
    print(f"   完了タスク数: {len(results)}")
    
    return results


if __name__ == "__main__":
    print("🚀 Phase 4: エラーハンドリング")
    print("=" * 60)
    
    # テスト実行
    asyncio.run(test_error_handling())
    asyncio.run(test_circular_dependency())
    
    print("\n✅ Phase 4 完了!")
    print("学習内容:")
    print("- 依存関係エラー時の処理")
    print("- 再試行機能の実装")
    print("- フォールバック処理の実装")
    print("- 循環依存の検出")
    print("- 堅牢性の向上")
