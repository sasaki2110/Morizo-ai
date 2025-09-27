"""
Morizo AI - Smart Pantry AI Agent
Copyright (c) 2024 Morizo AI Project. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, modification,
distribution, or use is strictly prohibited without explicit written permission.

For licensing inquiries, contact: [contact@morizo-ai.com]
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional
from action_planner import ActionPlanner, Task
from task_manager import TaskManager
from openai import OpenAI

logger = logging.getLogger("morizo_ai.true_react")

# 定数定義
MAX_TOKENS = 200

def estimate_tokens(text: str) -> int:
    """テキストのトークン数を概算する（日本語は1文字=1トークン、英語は4文字=1トークン）"""
    japanese_chars = sum(1 for c in text if '\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF' or '\u4E00' <= c <= '\u9FAF')
    other_chars = len(text) - japanese_chars
    return japanese_chars + (other_chars // 4)

class TrueReactAgent:
    """真のReActエージェントクラス"""
    
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        self.planner = ActionPlanner(openai_client)
        self.task_manager = TaskManager()
        self.max_react_cycles = 10  # 最大ReActサイクル数
    
    async def process_request(self, user_request: str, user_session, available_tools: List[str]) -> str:
        """
        ユーザー要求を処理する（真のAIエージェントとして）
        
        Args:
            user_request: ユーザーの要求
            user_session: ユーザーセッション
            available_tools: 利用可能なツール一覧
            
        Returns:
            処理結果の応答
        """
        logger.info(f"🤖 [真のReAct] ユーザー要求を処理開始: {user_request}")
        
        try:
            # Phase 1: 行動計画立案
            tasks = await self.planner.create_plan(user_request, available_tools)
            
            # タスクが空の場合（挨拶など）は直接LLM応答を返す
            if not tasks or len(tasks) == 0:
                logger.info("🤖 [真のReAct] ツール不要の要求を検出")
                return await self._generate_simple_response(user_request)
            
            if not self.planner.validate_plan(tasks):
                logger.error("❌ [真のReAct] タスクプランが無効です")
                return "申し訳ありません。要求を理解できませんでした。"
            
            # タスクを最適化
            tasks = self.planner.optimize_plan(tasks)
            
            # Phase 2: タスク管理に追加
            self.task_manager.add_tasks(tasks)
            
            logger.info(f"🤖 [真のReAct] {len(tasks)}個のタスクを生成")
            
            # Phase 3: 依存関係を考慮した実行順序の決定（Phase C: 並列実行対応）
            execution_groups = self._resolve_dependencies_with_parallel(tasks)
            logger.info(f"🤖 [真のReAct] 実行グループ: {execution_groups}")
            
            # Phase 4: ReActループ（並列実行対応）
            react_cycles = 0
            completed_tasks = {}
            
            for group_index, task_group in enumerate(execution_groups):
                react_cycles += 1
                logger.info(f"🔄 [真のReAct] サイクル {react_cycles} 開始: グループ {group_index + 1} - {task_group}")
                
                # グループ内のタスクを並列実行
                if len(task_group) == 1:
                    # 単一タスクの場合は従来通り実行
                    task_id = task_group[0]
                    current_task = next((t for t in tasks if t.id == task_id), None)
                    if not current_task:
                        logger.warning(f"⚠️ [真のReAct] タスク {task_id} が見つかりません")
                        continue
                    
                    # 依存関係をチェック
                    if not self._can_execute_task(current_task, completed_tasks):
                        logger.warning(f"⚠️ [真のReAct] タスク {task_id} の依存関係が満たされていません")
                        continue
                    
                    # タスクを実行中にマーク
                    self.task_manager.mark_task_in_progress(current_task)
                    
                    # ReActステップを実行（Phase B: データフロー対応）
                    result = await self._react_step(current_task, user_session, completed_tasks)
                    
                    if result.get("success"):
                        self.task_manager.mark_task_completed(current_task, result)
                        completed_tasks[task_id] = result
                        logger.info(f"✅ [真のReAct] タスク {task_id} 完了")
                    else:
                        self.task_manager.mark_task_failed(current_task, result.get("error"))
                        logger.error(f"❌ [真のReAct] タスク {task_id} 失敗: {result.get('error')}")
                else:
                    # 複数タスクの場合は並列実行
                    group_results = await self._execute_parallel_tasks(task_group, tasks, user_session, completed_tasks)
                    completed_tasks.update(group_results)
            
            # Phase 4: 完了報告
            return await self._generate_completion_report(user_request, completed_tasks)
            
        except Exception as e:
            logger.error(f"❌ [真のReAct] 処理エラー: {str(e)}")
            return f"申し訳ありません。処理中にエラーが発生しました: {str(e)}"
    
    def _resolve_dependencies(self, tasks: List[Task]) -> List[str]:
        """
        依存関係を考慮した実行順序を決定する（Phase 1で学習したアルゴリズム）
        
        Args:
            tasks: 実行するタスクのリスト
            
        Returns:
            実行順序（タスクIDのリスト）
        """
        completed = set()
        order = []
        
        logger.info(f"🔍 [依存関係解決] {len(tasks)}個のタスクの依存関係を解析")
        
        # 依存関係の詳細をログ出力
        for task in tasks:
            deps_str = ", ".join(task.dependencies) if task.dependencies else "なし"
            logger.info(f"🔍 [依存関係解決] {task.id}: {task.description} (依存: [{deps_str}])")
        
        # 依存関係を解決して実行順序を決定
        while len(completed) < len(tasks):
            # 実行可能なタスクを探す
            executable_tasks = [
                task for task in tasks 
                if task.id not in completed and 
                all(dep in completed for dep in task.dependencies)
            ]
            
            if not executable_tasks:
                logger.error("❌ [依存関係解決] 循環依存または依存関係エラーが発生しました")
                break
            
            # 最初に見つかった実行可能なタスクを実行
            task = executable_tasks[0]
            order.append(task.id)
            completed.add(task.id)
            logger.info(f"✅ [依存関係解決] 実行可能: {task.id}")
        
        logger.info(f"📝 [依存関係解決] 最終実行順序: {order}")
        return order
    
    def _resolve_dependencies_with_parallel(self, tasks: List[Task]) -> List[List[str]]:
        """
        Phase C: 依存関係を考慮した実行順序を決定（並列実行対応）
        
        Args:
            tasks: 実行するタスクのリスト
            
        Returns:
            実行順序（並列実行可能なタスクのグループのリスト）
        """
        completed = set()
        execution_groups = []
        
        logger.info(f"🔍 [並列依存関係解決] {len(tasks)}個のタスクの依存関係を解析")
        
        # 依存関係の詳細をログ出力
        for task in tasks:
            deps_str = ", ".join(task.dependencies) if task.dependencies else "なし"
            logger.info(f"🔍 [並列依存関係解決] {task.id}: {task.description} (依存: [{deps_str}])")
        
        # 依存関係を解決して実行順序を決定（並列実行対応）
        while len(completed) < len(tasks):
            # 実行可能なタスクを探す
            executable_tasks = [
                task for task in tasks 
                if task.id not in completed and 
                all(dep in completed for dep in task.dependencies)
            ]
            
            if not executable_tasks:
                logger.error("❌ [並列依存関係解決] 循環依存または依存関係エラーが発生しました")
                break
            
            # 実行可能なタスクのIDをグループ化
            executable_ids = [task.id for task in executable_tasks]
            execution_groups.append(executable_ids)
            
            # 完了したタスクに追加
            for task_id in executable_ids:
                completed.add(task_id)
            
            logger.info(f"✅ [並列依存関係解決] 並列実行グループ: {executable_ids}")
        
        logger.info(f"📝 [並列依存関係解決] 最終実行グループ: {execution_groups}")
        return execution_groups
    
    def _can_execute_task(self, task: Task, completed_tasks: Dict[str, Any]) -> bool:
        """
        タスクが実行可能かどうかを判定する
        
        Args:
            task: 判定するタスク
            completed_tasks: 完了したタスクの辞書
            
        Returns:
            実行可能かどうか
        """
        return all(dep in completed_tasks for dep in task.dependencies)
    
    async def _execute_parallel_tasks(self, task_ids: List[str], tasks: List[Task], user_session, completed_tasks: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase C: 複数のタスクを並列実行する
        
        Args:
            task_ids: 並列実行するタスクのIDリスト
            tasks: 全タスクのリスト
            user_session: ユーザーセッション
            completed_tasks: 完了したタスクの結果
            
        Returns:
            実行結果の辞書
        """
        import asyncio
        
        logger.info(f"🚀 [並列実行] {len(task_ids)}個のタスクを並列実行: {task_ids}")
        
        # 並列実行するタスクを取得
        parallel_tasks = [task for task in tasks if task.id in task_ids]
        
        # 各タスクのReActステップを並列実行
        async def execute_single_task(task: Task) -> tuple[str, Dict[str, Any]]:
            logger.info(f"🔄 [並列実行] タスク開始: {task.id}")
            result = await self._react_step(task, user_session, completed_tasks)
            logger.info(f"✅ [並列実行] タスク完了: {task.id}")
            return task.id, result
        
        # asyncio.gatherで並列実行
        try:
            results = await asyncio.gather(*[execute_single_task(task) for task in parallel_tasks])
            
            # 結果を辞書に変換
            result_dict = {}
            for task_id, result in results:
                result_dict[task_id] = result
                
                # TaskManagerに結果を記録
                task = next(t for t in tasks if t.id == task_id)
                if result.get("success"):
                    self.task_manager.mark_task_completed(task, result)
                    logger.info(f"✅ [並列実行] タスク {task_id} 完了")
                else:
                    self.task_manager.mark_task_failed(task, result.get("error"))
                    logger.error(f"❌ [並列実行] タスク {task_id} 失敗: {result.get('error')}")
            
            logger.info(f"🎉 [並列実行] {len(task_ids)}個のタスクが並列実行完了")
            return result_dict
            
        except Exception as e:
            logger.error(f"❌ [並列実行] エラー: {str(e)}")
            # エラーが発生した場合、各タスクを個別に実行
            logger.info("🔄 [並列実行] フォールバック: 個別実行に切り替え")
            result_dict = {}
            for task in parallel_tasks:
                try:
                    result = await self._react_step(task, user_session, completed_tasks)
                    result_dict[task.id] = result
                    
                    if result.get("success"):
                        self.task_manager.mark_task_completed(task, result)
                    else:
                        self.task_manager.mark_task_failed(task, result.get("error"))
                except Exception as task_error:
                    logger.error(f"❌ [並列実行] 個別実行エラー {task.id}: {str(task_error)}")
                    result_dict[task.id] = {"success": False, "error": str(task_error)}
                    self.task_manager.mark_task_failed(task, str(task_error))
            
            return result_dict
    
    def _inject_dependency_results(self, task: Task, completed_tasks: Dict[str, Any]) -> Task:
        """
        Phase B: 依存タスクの結果を現在のタスクのパラメータに注入する
        
        Args:
            task: 現在のタスク
            completed_tasks: 完了したタスクの結果
            
        Returns:
            パラメータが注入されたタスク
        """
        if not task.dependencies or not completed_tasks:
            return task
        
        logger.info(f"🔄 [データフロー] {task.id} の依存関係結果を注入開始")
        
        # タスクのコピーを作成（元のタスクを変更しない）
        enhanced_task = Task(
            id=task.id,
            description=task.description,
            tool=task.tool,
            parameters=task.parameters.copy(),  # パラメータをコピー
            priority=task.priority,
            dependencies=task.dependencies
        )
        
        # 各依存タスクの結果を注入
        for dep_id in task.dependencies:
            if dep_id in completed_tasks:
                dep_result = completed_tasks[dep_id]
                logger.info(f"🔄 [データフロー] {dep_id} の結果を {task.id} に注入")
                
                # 特定のツール組み合わせに対するデータフロー処理
                if self._should_inject_inventory_data(task, dep_result):
                    self._inject_inventory_data(enhanced_task, dep_result)
        
        return enhanced_task
    
    def _should_inject_inventory_data(self, task: Task, dep_result: Dict[str, Any]) -> bool:
        """
        在庫データの注入が必要かどうかを判定
        
        Args:
            task: 現在のタスク
            dep_result: 依存タスクの結果
            
        Returns:
            注入が必要かどうか
        """
        # inventory_list → generate_menu_plan_with_history の組み合わせ
        # dep_resultの構造: {"success": True, "result": {...}}
        return (task.tool == "generate_menu_plan_with_history" and
                dep_result.get("success") is True and
                "result" in dep_result)
    
    def _inject_inventory_data(self, task: Task, dep_result: Dict[str, Any]) -> None:
        """
        在庫データを献立生成タスクのパラメータに注入
        
        Args:
            task: 注入先のタスク
            dep_result: 在庫リストの結果
        """
        try:
            # 在庫データを取得（dep_resultの構造: {"success": True, "result": {"data": [...]}}）
            result_data = dep_result.get("result", {})
            inventory_data = result_data.get("data", [])
            
            logger.info(f"🔄 [データフロー] 在庫データ構造確認: {type(inventory_data)}, 件数: {len(inventory_data) if isinstance(inventory_data, list) else 'N/A'}")
            
            # item_nameのリストを作成
            inventory_items = []
            for item in inventory_data:
                if isinstance(item, dict) and "item_name" in item:
                    inventory_items.append(item["item_name"])
            
            # パラメータに注入
            if "inventory_items" in task.parameters:
                task.parameters["inventory_items"] = inventory_items
                logger.info(f"✅ [データフロー] inventory_items に {len(inventory_items)} 個のアイテムを注入: {inventory_items}")
            else:
                logger.warning(f"⚠️ [データフロー] inventory_items パラメータが見つかりません")
                
        except Exception as e:
            logger.error(f"❌ [データフロー] 在庫データ注入エラー: {str(e)}")
    
    async def _react_step(self, task: Task, user_session, completed_tasks: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        単一のReActステップを実行する（Phase B: データフロー対応）
        
        Args:
            task: 実行するタスク
            user_session: ユーザーセッション
            completed_tasks: 完了したタスクの結果（データフロー用）
            
        Returns:
            実行結果
        """
        logger.info(f"🔄 [ReAct] タスク実行: {task.description}")
        
        try:
            # Phase B: データフロー - 依存タスクの結果をパラメータに注入
            enhanced_task = self._inject_dependency_results(task, completed_tasks or {})
            
            # 観察: 現在の状況を把握
            observation = await self._observe(enhanced_task, user_session)
            
            # 思考: 最適な行動を決定
            thought = await self._think(enhanced_task, observation)
            
            # 決定: 実行するツールを選択
            decision = await self._decide(enhanced_task, thought)
            
            # 行動: ツールを実行
            action_result = await self._act(decision, user_session)
            
            return action_result
            
        except Exception as e:
            logger.error(f"❌ [ReAct] ステップエラー: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _observe(self, task: Task, user_session) -> Dict[str, Any]:
        """
        観察: 現在の状況を把握
        
        Args:
            task: 実行するタスク
            user_session: ユーザーセッション
            
        Returns:
            観察結果
        """
        observation = {
            "task": task.description,
            "tool": task.tool,
            "parameters": task.parameters,
            "operation_history": user_session.get_recent_operations(3)
        }
        
        logger.info(f"👁️ [観察] タスク: {task.description}")
        return observation
    
    async def _think(self, task: Task, observation: Dict[str, Any]) -> str:
        """
        思考: 最適な行動を決定
        
        Args:
            task: 実行するタスク
            observation: 観察結果
            
        Returns:
            思考結果
        """
        thinking_prompt = f"""
以下のタスクを実行するための最適な行動を考えてください。

タスク: {task.description}
使用ツール: {task.tool}
パラメータ: {json.dumps(task.parameters, ensure_ascii=False, indent=2)}

現在の状況:
- 最近の操作: {json.dumps(observation['operation_history'], ensure_ascii=False, indent=2)}

このタスクを実行するために必要な行動を簡潔に説明してください。
"""
        
        try:
            # トークン数予測
            estimated_tokens = estimate_tokens(thinking_prompt)
            overage_rate = (estimated_tokens / MAX_TOKENS) * 100
            
            logger.info(f"🧠 [思考] プロンプト全文 (総トークン数: {estimated_tokens}/{MAX_TOKENS}, 超過率: {overage_rate:.1f}%):")
            logger.info(f"🧠 [思考] {thinking_prompt}")
            
            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": thinking_prompt}],
                max_tokens=MAX_TOKENS,
                temperature=0.3
            )
            
            thought = response.choices[0].message.content
            logger.info(f"🧠 [思考] {thought}")
            return thought
            
        except Exception as e:
            logger.error(f"❌ [思考] エラー: {str(e)}")
            return f"タスク {task.description} を実行します"
    
    async def _decide(self, task: Task, thought: str) -> Dict[str, Any]:
        """
        決定: 実行するツールを選択
        
        Args:
            task: 実行するタスク
            thought: 思考結果
            
        Returns:
            決定結果
        """
        decision = {
            "tool": task.tool,
            "parameters": task.parameters,
            "reasoning": thought
        }
        
        logger.info(f"🎯 [決定] ツール: {task.tool}")
        return decision
    
    async def _act(self, decision: Dict[str, Any], user_session) -> Dict[str, Any]:
        """
        行動: ツールを実行
        
        Args:
            decision: 決定結果
            user_session: ユーザーセッション
            
        Returns:
            実行結果
        """
        try:
            # MCPツールを実行（新しいcall_mcp_tool関数を使用）
            from agents.mcp_client import call_mcp_tool
            
            # トークンを追加（tokenが必要なツールのみ）
            params = decision["parameters"].copy()
            if self._needs_token(decision["tool"]):
                params["token"] = user_session.token
            
            logger.info(f"🎬 [行動] {decision['tool']} 実行開始")
            logger.info(f"🎬 [行動] パラメータ: {params}")
            
            result = await call_mcp_tool(
                decision["tool"],
                params
            )
            
            logger.info(f"🎬 [行動] {decision['tool']} 実行完了")
            return {"success": True, "result": result}
            
        except Exception as e:
            logger.error(f"❌ [行動] エラー: {str(e)}")
            logger.error(f"❌ [行動] エラー詳細: {type(e).__name__}")
            return {"success": False, "error": str(e)}
    
    def _needs_token(self, tool_name: str) -> bool:
        """
        ツールがtokenパラメータを必要とするかどうかを判定
        
        Args:
            tool_name: ツール名
            
        Returns:
            tokenが必要かどうか
        """
        # DB MCPツール（認証が必要）
        db_tools = [
            "inventory_add", "inventory_list", "inventory_get", 
            "inventory_update_by_id", "inventory_delete_by_id",
            "inventory_delete_by_name", "inventory_update_by_name",
            "inventory_update_by_name_oldest", "inventory_update_by_name_latest",
            "inventory_delete_by_name_oldest", "inventory_delete_by_name_latest",
            "recipes_add", "recipes_list", "recipes_update_latest", "recipes_delete_latest"
        ]
        
        # Recipe MCPツール（認証不要）
        recipe_tools = [
            "generate_menu_plan_with_history", "search_recipe_from_rag", "search_recipe_from_web"
        ]
        
        if tool_name in db_tools:
            return True
        elif tool_name in recipe_tools:
            return False
        else:
            # 不明なツールは安全のためtokenを追加
            logger.warning(f"⚠️ [認証判定] 不明なツール: {tool_name} - tokenを追加")
            return True
    
    async def _generate_completion_report(self, user_request: str, completed_tasks: Dict[str, Any]) -> str:
        """
        完了報告を生成する（LLMによる最終結果整形）（Phase B: データフロー対応）
        
        Args:
            user_request: 元のユーザー要求
            completed_tasks: 完了したタスクの結果
            
        Returns:
            完了報告
        """
        try:
            # 1. 完了したタスクの実行結果を収集（Phase B: completed_tasksから直接取得）
            task_results = self._collect_task_results_from_completed(completed_tasks)
            
            # 2. LLMに最終結果の整形を依頼
            final_response = await self._generate_final_response_with_llm(
                user_request, task_results
            )
            
            logger.info(f"✅ [完了報告] ユーザー要求: {user_request}")
            return final_response
            
        except Exception as e:
            logger.error(f"❌ [完了報告] エラー: {str(e)}")
            # フォールバック: 従来の報告方式
            return self._generate_fallback_report(user_request)
    
    def _collect_task_results_from_completed(self, completed_tasks: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Phase B: 完了したタスクの実行結果を収集する（completed_tasksから直接取得）
        
        Args:
            completed_tasks: 完了したタスクの結果
            
        Returns:
            タスク結果のリスト
        """
        results = []
        
        logger.info(f"📊 [結果収集] {len(completed_tasks)}個のタスク結果を収集")
        
        for task_id, result in completed_tasks.items():
            # タスク情報を取得
            task_info = self.task_manager.get_task_by_id(task_id)
            
            if task_info:
                # resultの構造: {"success": True, "result": {...}}
                task_result = {
                    "tool": task_info.tool,
                    "description": task_info.description,
                    "result": result.get("result", {}),
                    "status": "completed" if result.get("success") else "failed"
                }
                results.append(task_result)
                logger.info(f"📊 [結果収集] {task_id}: {task_info.tool} - {result.get('success', False)}")
            else:
                logger.warning(f"⚠️ [結果収集] タスク情報が見つかりません: {task_id}")
        
        return results
    
    def _collect_task_results(self) -> List[Dict[str, Any]]:
        """
        完了したタスクの実行結果を収集する
        
        Returns:
            タスク結果のリスト
        """
        results = []
        
        for task in self.task_manager.completed_tasks:
            if task.result and task.result.get("success"):
                results.append({
                    "tool": task.tool,
                    "description": task.description,
                    "result": task.result.get("result", {}),
                    "status": "completed"
                })
            else:
                results.append({
                    "tool": task.tool,
                    "description": task.description,
                    "error": task.result.get("error", "不明なエラー") if task.result else "結果なし",
                    "status": "failed"
                })
        
        logger.info(f"📊 [結果収集] {len(results)}個のタスク結果を収集")
        return results
    
    async def _generate_final_response_with_llm(self, user_request: str, task_results: List[Dict[str, Any]]) -> str:
        """
        LLMに最終結果の整形を依頼
        
        Args:
            user_request: 元のユーザー要求
            task_results: タスク実行結果
            
        Returns:
            LLMが生成した最終回答
        """
        try:
            # タスク結果を整理
            results_summary = []
            for result in task_results:
                if result["status"] == "completed":
                    results_summary.append({
                        "tool": result["tool"],
                        "description": result["description"],
                        "result": result["result"]
                    })
                else:
                    results_summary.append({
                        "tool": result["tool"],
                        "description": result["description"],
                        "error": result["error"]
                    })
            
            # LLMに整形を依頼
            prompt = f"""
ユーザーの要求: {user_request}

実行されたタスクとその結果:
{json.dumps(results_summary, ensure_ascii=False, indent=2)}

上記の結果を基に、ユーザーに適切な回答を生成してください。

**重要**: 在庫リストの場合は、以下のルールに従って正確に集計してください：
1. 同じitem_nameのアイテムのquantityを全て合計する
2. 例: 牛乳が1本、2本、1本、2本、1本、2本 → 合計9本
3. 推測や概算は禁止、必ず正確な計算を行う
4. 各アイテムのquantityを一つずつ確認して合計する

指示:
- 在庫リストの場合は、実際の在庫データを正確に集計して回答してください
- その他の場合は、実行結果を分かりやすく説明してください
- 自然で親しみやすい日本語で回答してください
- エラーが発生した場合は、その内容も含めて説明してください
- タスク状況の統計情報は含めず、ユーザーが求める情報に集中してください
"""
            logger.info(f"🔍 [LLM整形] プロンプト内容:")
            logger.info(f"   {prompt}")
            
            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7
            )
            
            final_response = response.choices[0].message.content
            logger.info(f"🤖 [LLM整形] 最終回答を生成: {len(final_response)}文字")
            return final_response
            
        except Exception as e:
            logger.error(f"❌ [LLM整形] エラー: {str(e)}")
            raise e
    
    def _generate_fallback_report(self, user_request: str) -> str:
        """
        フォールバック用の完了報告（従来方式）
        
        Args:
            user_request: 元のユーザー要求
            
        Returns:
            フォールバック報告
        """
        status = self.task_manager.get_task_status()
        summary = self.task_manager.get_task_summary()
        
        if status["failed_tasks"] > 0:
            report = f"""
一連の作業が完了しました。

{summary}

⚠️ 一部のタスクでエラーが発生しました。詳細はログをご確認ください。
"""
        else:
            report = f"""
一連の作業が完了しました！

{summary}

✅ すべてのタスクが正常に完了しました。
"""
        
        logger.info(f"✅ [フォールバック報告] ユーザー要求: {user_request}")
        return report
    
    async def _generate_simple_response(self, user_request: str) -> str:
        """
        ツール不要の要求（挨拶など）に対するシンプルな応答を生成
        
        Args:
            user_request: ユーザーの要求
            
        Returns:
            シンプルな応答
        """
        try:
            prompt = f"""
ユーザーからの要求: {user_request}

これは挨拶や一般的な会話の要求です。在庫管理ツールは使用せず、自然で親しみやすい日本語で応答してください。

指示:
- 挨拶には適切に応答してください
- 在庫管理についての質問があれば、お手伝いできることを説明してください
- 自然で親しみやすい日本語で回答してください
- 短めで簡潔な回答を心がけてください
"""
            
            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )
            
            simple_response = response.choices[0].message.content
            logger.info(f"🤖 [シンプル応答] 応答を生成: {len(simple_response)}文字")
            return simple_response
            
        except Exception as e:
            logger.error(f"❌ [シンプル応答] エラー: {str(e)}")
            return "こんにちは！何かお手伝いできることがあれば教えてください。"
