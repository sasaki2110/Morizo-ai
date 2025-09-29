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
import asyncio
from typing import List, Dict, Any, Optional
from action_planner import ActionPlanner, Task
from task_manager import TaskManager
from openai import OpenAI
from ambiguity_detector import AmbiguityDetector
from confirmation_processor import ConfirmationProcessor
from confirmation_exceptions import UserConfirmationRequired
from task_chain_manager import TaskChainManager

logger = logging.getLogger("morizo_ai.true_react")

# 定数定義
MAX_TOKENS = 4000

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
        
        # Phase 4.4: 確認プロセス用のコンポーネント
        self.ambiguity_detector = AmbiguityDetector()
        self.confirmation_processor = ConfirmationProcessor()
        self.task_chain_manager = TaskChainManager()
    
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
            
            # Phase 4.4: タスクチェーン管理を初期化
            self.task_chain_manager.set_task_chain(tasks)
            
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
            
        except UserConfirmationRequired as e:
            # Phase 4.4: ユーザー確認が必要な場合は例外を再発生
            logger.info(f"🤔 [確認プロセス] ユーザー確認が必要: {user_request}")
            raise e
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
        
        logger.debug(f"🔍 [並列依存関係解決] {len(tasks)}個のタスクの依存関係を解析")
        
        # 依存関係の詳細をログ出力
        for task in tasks:
            deps_str = ", ".join(task.dependencies) if task.dependencies else "なし"
            logger.debug(f"🔍 [並列依存関係解決] {task.id}: {task.description} (依存: [{deps_str}])")
        
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
                # 依存関係エラーが発生しても残りのタスクを実行可能にする
                remaining_tasks = [task for task in tasks if task.id not in completed]
                if remaining_tasks:
                    logger.warning(f"⚠️ [並列依存関係解決] 残りのタスクを強制実行: {[t.id for t in remaining_tasks]}")
                    # 残りのタスクを依存関係なしで実行
                    for task in remaining_tasks:
                        task.dependencies = []
                    executable_tasks = remaining_tasks
                else:
                    break
            
            # 実行可能なタスクのIDをグループ化
            executable_ids = [task.id for task in executable_tasks]
            execution_groups.append(executable_ids)
            
            # 完了したタスクに追加
            for task_id in executable_ids:
                completed.add(task_id)
            
            logger.debug(f"✅ [並列依存関係解決] 並列実行グループ: {executable_ids}")
        
        logger.debug(f"📝 [並列依存関係解決] 最終実行グループ: {execution_groups}")
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
                elif self._should_inject_menu_data(task, dep_result):
                    self._inject_menu_data(enhanced_task, dep_result)
        
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
    
    def _should_inject_menu_data(self, task: Task, dep_result: Dict[str, Any]) -> bool:
        """
        献立データの注入が必要かどうかを判定
        
        Args:
            task: 現在のタスク
            dep_result: 依存タスクの結果
            
        Returns:
            注入が必要かどうか
        """
        # generate_menu_plan_with_history → search_recipe_from_web の組み合わせ
        return (task.tool == "search_recipe_from_web" and
                dep_result.get("success") is True and
                "result" in dep_result)
    
    def _inject_menu_data(self, task: Task, dep_result: Dict[str, Any]) -> None:
        """
        献立データをレシピ検索タスクのパラメータに注入
        
        Args:
            task: 注入先のタスク
            dep_result: 献立生成の結果
        """
        try:
            # 献立データを取得
            result_data = dep_result.get("result", {})
            menu_data = result_data.get("data", {})
            
            logger.info(f"🔄 [データフロー] 献立データ構造確認: {type(menu_data)}")
            
            # 献立から料理名を抽出
            dish_names = []
            if isinstance(menu_data, dict):
                # 献立の構造に応じて料理名を抽出
                if "menu" in menu_data:
                    menu_items = menu_data["menu"]
                    if isinstance(menu_items, list):
                        for item in menu_items:
                            if isinstance(item, dict) and "name" in item:
                                dish_names.append(item["name"])
                            elif isinstance(item, str):
                                dish_names.append(item)
                
                # その他の構造も考慮
                for key in ["dishes", "recipes", "items"]:
                    if key in menu_data:
                        items = menu_data[key]
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict) and "name" in item:
                                    dish_names.append(item["name"])
                                elif isinstance(item, str):
                                    dish_names.append(item)
            
            # 料理名からレシピ検索クエリを構築
            if dish_names:
                # 料理名を「作り方」で検索するクエリに変換
                query_parts = []
                for dish in dish_names[:3]:  # 最大3つの料理名を使用
                    query_parts.append(f"{dish} 作り方")
                
                search_query = " ".join(query_parts)
                
                # パラメータに注入
                if "query" in task.parameters:
                    task.parameters["query"] = search_query
                    logger.info(f"✅ [データフロー] レシピ検索クエリを注入: {search_query}")
                else:
                    logger.warning(f"⚠️ [データフロー] query パラメータが見つかりません")
            else:
                logger.warning(f"⚠️ [データフロー] 料理名を抽出できませんでした")
                
        except Exception as e:
            logger.error(f"❌ [データフロー] 献立データ注入エラー: {str(e)}")
    
    async def _react_step(self, task: Task, user_session, completed_tasks: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        単一のReActステップを実行する（Phase B: データフロー対応 + Phase 4.4: 確認プロセス）
        
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
            
            # Phase 4.4: 曖昧性検出（在庫操作タスクの場合）
            if self._is_inventory_operation_task(enhanced_task):
                try:
                    await self._check_ambiguity_and_confirm(enhanced_task, user_session, completed_tasks)
                except UserConfirmationRequired as e:
                    # 確認が必要な場合は例外を再発生
                    raise e
                except Exception as e:
                    # その他のエラーはログに記録して続行
                    logger.warning(f"⚠️ [曖昧性チェック] エラーを無視して続行: {str(e)}")
            
            # 観察: 現在の状況を把握
            observation = await self._observe(enhanced_task, user_session)
            
            # 思考: 最適な行動を決定
            thought = await self._think(enhanced_task, observation)
            
            # 決定: 実行するツールを選択
            decision = await self._decide(enhanced_task, thought)
            
            # 行動: ツールを実行
            action_result = await self._act(decision, user_session)
            
            return action_result
            
        except UserConfirmationRequired as e:
            # Phase 4.4: 確認が必要な場合は例外を再発生
            logger.info(f"🤔 [確認プロセス] ユーザー確認が必要: {enhanced_task.description}")
            raise e
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
            # プロンプト表示を5行に制限
            prompt_lines = thinking_prompt.split('\n')
            if len(prompt_lines) > 5:
                logger.info(f"🧠 [思考] {chr(10).join(prompt_lines[:5])}")
                logger.info(f"🧠 [思考] ... (残り{len(prompt_lines)-5}行を省略)")
            else:
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
            # トークンを省略してログ出力
            log_params = params.copy()
            if "token" in log_params:
                log_params["token"] = f"{log_params['token'][:20]}..."
            logger.info(f"🎬 [行動] パラメータ: {log_params}")
            
            result = await call_mcp_tool(
                decision["tool"],
                params
            )
            
            # 在庫0個での削除操作の場合の特別処理
            if (decision["tool"] in ["inventory_delete_by_name_oldest", "inventory_delete_by_name_latest"] 
                and isinstance(result, dict) 
                and result.get("success") == False 
                and "not found" in str(result.get("error", "")).lower()):
                
                item_name = params.get("item_name", "アイテム")
                logger.info(f"🔍 [在庫0個処理] {item_name}の在庫が0個のため削除をスキップ")
                return {
                    "success": True, 
                    "result": f"{item_name}の在庫が0個のため、削除操作をスキップしました。",
                    "skipped": True
                }
            
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
    
    def _is_inventory_operation_task(self, task: Task) -> bool:
        """
        在庫操作タスクかどうかを判定する
        
        Args:
            task: 判定するタスク
            
        Returns:
            在庫操作タスクかどうか
        """
        inventory_tools = [
            "inventory_delete_by_name", "inventory_update_by_name",
            "inventory_delete_by_name_oldest", "inventory_delete_by_name_latest",
            "inventory_update_by_name_oldest", "inventory_update_by_name_latest"
        ]
        return task.tool in inventory_tools
    
    async def _check_ambiguity_and_confirm(self, task: Task, user_session, completed_tasks: Dict[str, Any] = None) -> None:
        """
        曖昧性をチェックし、必要に応じて確認を求める
        
        Args:
            task: チェックするタスク
            user_session: ユーザーセッション
            completed_tasks: 完了したタスクの結果（前提タスクの結果を含む）
            
        Raises:
            UserConfirmationRequired: 確認が必要な場合
        """
        try:
            # Phase 2: 前提タスクの結果を活用した曖昧性検出
            inventory_data = []
            
            # 前提タスクの結果を確認
            logger.info(f"🔍 [曖昧性チェック] completed_tasks: {list(completed_tasks.keys()) if completed_tasks else 'None'}")
            if completed_tasks:
                item_name = task.parameters.get("item_name")
                logger.info(f"🔍 [曖昧性チェック] 検索対象item_name: {item_name}")
                if item_name:
                    # 前提タスクのIDを検索
                    prerequisite_task_id = None
                    for task_id, result in completed_tasks.items():
                        logger.info(f"🔍 [曖昧性チェック] チェック中task_id: {task_id}")
                        if task_id.startswith(f"prerequisite_{item_name}_"):
                            prerequisite_task_id = task_id
                            logger.info(f"🔍 [曖昧性チェック] 前提タスク発見: {prerequisite_task_id}")
                            break
                    
                    if prerequisite_task_id and prerequisite_task_id in completed_tasks:
                        prerequisite_result = completed_tasks[prerequisite_task_id]
                        logger.debug(f"🔍 [曖昧性チェック] 前提タスク結果: {prerequisite_result}")
                        if isinstance(prerequisite_result, dict) and prerequisite_result.get("success"):
                            # MCPツールの結果構造に合わせて修正（二重構造対応）
                            inner_result = prerequisite_result.get("result", {})
                            if isinstance(inner_result, dict) and inner_result.get("success"):
                                inventory_data = inner_result.get("data", [])
                            else:
                                inventory_data = prerequisite_result.get("data", [])
                            logger.info(f"🔍 [曖昧性チェック] 前提タスクの結果を活用: {len(inventory_data)}件の在庫")
            
            # 前提タスクの結果がない場合は全在庫を取得
            if inventory_data is None:
                logger.info(f"🔍 [曖昧性チェック] 前提タスクの結果がないため全在庫を取得")
                from agents.mcp_client import call_mcp_tool
                
                inventory_result = await call_mcp_tool("inventory_list", {"token": user_session.token})
                
                if not inventory_result.get("success"):
                    logger.warning(f"⚠️ [曖昧性チェック] 在庫リスト取得失敗: {inventory_result.get('error')}")
                    return
                
                inventory_data = inventory_result.get("data", [])
            
            # 曖昧性検出
            ambiguity_info = self.ambiguity_detector.detect_ambiguity(task, inventory_data)
            
            if ambiguity_info and ambiguity_info.needs_confirmation:
                logger.info(f"🤔 [曖昧性検出] 確認が必要: {task.description}")
                
                # 残りのタスクチェーンを取得
                remaining_tasks = self.task_chain_manager.get_remaining_tasks()
                
                # 確認レスポンスを生成
                confirmation_response = self.confirmation_processor.generate_confirmation_response(
                    ambiguity_info, remaining_tasks
                )
                
                # 実行済みタスクを取得
                executed_tasks = self.task_chain_manager.get_executed_tasks()
                
                # UserConfirmationRequired例外を発生
                raise UserConfirmationRequired(
                    confirmation_context=confirmation_response,
                    executed_tasks=executed_tasks,
                    remaining_tasks=remaining_tasks
                )
            else:
                logger.info(f"✅ [曖昧性チェック] 確認不要: {task.description}")
                
        except UserConfirmationRequired:
            # 既に発生した例外は再発生
            raise
        except Exception as e:
            logger.error(f"❌ [曖昧性チェック] エラー: {str(e)}")
            # エラーの場合は確認をスキップして続行
                
    # Phase 4.4.3: タスクチェーン再開処理
    async def resume_task_chain(self, tasks: List[Task], user_session, confirmation_context: dict) -> str:
        """
        Phase 4.4.3: タスクチェーン再開処理
        
        Args:
            tasks: 再開するタスクリスト
            user_session: ユーザーセッション
            confirmation_context: 確認コンテキスト
            
        Returns:
            処理結果の応答
        """
        logger.info(f"🔄 [真のReAct] タスクチェーン再開: {len(tasks)}個のタスク")
        
        try:
            # 確認応答で生成されたタスクのみを実行（元の曖昧なタスクは除外済み）
            logger.info(f"🔄 [真のReAct] 確認応答で生成されたタスク: {[t.id for t in tasks]}")
            
            # タスクチェーン管理を更新
            self.task_chain_manager.set_task_chain(tasks)
            
            # 依存関係を考慮した実行順序の決定
            execution_groups = self._resolve_dependencies_with_parallel(tasks)
            logger.info(f"🔄 [真のReAct] 再開実行グループ: {execution_groups}")
            
            # タスクチェーン実行
            completed_tasks = {}
            final_response = ""
            
            for group_index, task_group_ids in enumerate(execution_groups):
                logger.info(f"🔄 [真のReAct] 再開サイクル {group_index + 1}: {task_group_ids}")
                
                # タスクIDからタスクオブジェクトを取得
                task_group = [task for task in tasks if task.id in task_group_ids]
                
                # グループ内のタスクを並列実行
                if len(task_group) == 1:
                    try:
                        result = await self._react_step(task_group[0], user_session, completed_tasks)
                        # 成功したタスクのみをcompleted_tasksに追加
                        if result.get("success", False):
                            completed_tasks[task_group[0].id] = result
                    except UserConfirmationRequired as e:
                        # 再開中に確認が必要になった場合は、エラーメッセージを返す
                        logger.warning(f"⚠️ [真のReAct] 再開中に確認が必要: {e}")
                        return f"タスクチェーンの再開中に確認が必要になりました。最初からやり直してください。\n\nエラー: {str(e)}"
                else:
                    # 複数タスクの並列実行
                    async def execute_single_task(task: Task) -> tuple[str, Dict[str, Any]]:
                        logger.info(f"🔄 [再開並列実行] タスク開始: {task.id}")
                        result = await self._react_step(task, user_session, completed_tasks)
                        logger.info(f"✅ [再開並列実行] タスク完了: {task.id}")
                        return task.id, result
                    
                    # asyncio.gatherで並列実行
                    try:
                        results = await asyncio.gather(*[execute_single_task(task) for task in task_group])
                        
                        # 結果を辞書に変換（成功したタスクのみ）
                        for task_id, result in results:
                            if result.get("success", False):
                                completed_tasks[task_id] = result
                    except UserConfirmationRequired as e:
                        # 再開中に確認が必要になった場合は、エラーメッセージを返す
                        logger.warning(f"⚠️ [真のReAct] 再開中に確認が必要: {e}")
                        return f"タスクチェーンの再開中に確認が必要になりました。最初からやり直してください。\n\nエラー: {str(e)}"
                
                # 進捗表示は最終段階で生成（中間表示を削除）
            
            # 最終結果の生成
            final_response += await self._generate_final_response(completed_tasks, confirmation_context)
            
            # ログ出力を削除（レスポンスのみで完了状況を報告）
            
            return final_response
            
        except Exception as e:
            logger.error(f"❌ [真のReAct] タスクチェーン再開エラー: {str(e)}")
            import traceback
            logger.error(f"❌ [真のReAct] トレースバック: {traceback.format_exc()}")
            return f"タスクチェーンの再開中にエラーが発生しました: {str(e)}"
    
    async def _generate_final_response(self, completed_tasks: dict, confirmation_context: dict) -> str:
        """
        最終結果の応答を生成
        
        Args:
            completed_tasks: 実行済みタスクの結果
            confirmation_context: 確認コンテキスト
            
        Returns:
            最終応答
        """
        try:
            # 実行結果をまとめる
            results_summary = []
            detailed_results = []
            
            for task_id, result in completed_tasks.items():
                logger.debug(f"🔍 [デバッグ] タスク結果構造: {task_id}")
                logger.debug(f"🔍 [デバッグ] result構造: {type(result)} - {result}")
                
                if isinstance(result, dict) and result.get("success"):
                    message = result.get('message', '処理完了')
                    # 具体的な結果がある場合は詳細を表示
                    if 'data' in result and result['data']:
                        logger.debug(f"🔍 [デバッグ] dataフィールド発見: {result['data']}")
                        detailed_results.append(result['data'])
                    elif 'response' in result and result['response']:
                        logger.debug(f"🔍 [デバッグ] responseフィールド発見: {result['response']}")
                        detailed_results.append(result['response'])
                    elif 'result' in result and result['result']:
                        # MCPツールの結果をチェック
                        mcp_result = result['result']
                        logger.debug(f"🔍 [デバッグ] MCP結果構造: {type(mcp_result)} - {mcp_result}")
                        if isinstance(mcp_result, dict):
                            # MCPツールの結果からdataフィールドを抽出
                            if 'data' in mcp_result:
                                logger.debug(f"🔍 [デバッグ] MCP dataフィールド発見: {mcp_result['data']}")
                                detailed_results.append(mcp_result['data'])
                            elif 'recipes' in mcp_result:
                                logger.debug(f"🔍 [デバッグ] MCP recipesフィールド発見: {mcp_result['recipes']}")
                                detailed_results.append(mcp_result)
                            elif 'menu' in mcp_result:
                                logger.debug(f"🔍 [デバッグ] MCP menuフィールド発見: {mcp_result['menu']}")
                                detailed_results.append(mcp_result)
                            else:
                                # その他の構造の場合は文字列化
                                logger.debug(f"🔍 [デバッグ] MCP結果を文字列化: {str(mcp_result)}")
                                detailed_results.append(str(mcp_result))
                        elif isinstance(mcp_result, str):
                            logger.debug(f"🔍 [デバッグ] MCP結果文字列: {mcp_result}")
                            detailed_results.append(mcp_result)
                    else:
                        logger.debug(f"🔍 [デバッグ] 汎用メッセージを使用: {message}")
                        results_summary.append(f"✅ {message}")
                else:
                    logger.debug(f"🔍 [デバッグ] タスク失敗: {task_id}")
                    results_summary.append(f"⚠️ {task_id}: 処理に問題がありました")
            
            # 最終応答を生成
            final_response = ""
            
            # 詳細な結果がある場合はそれを優先表示
            if detailed_results:
                for detail in detailed_results:
                    if isinstance(detail, str) and len(detail.strip()) > 0:
                        final_response += detail + "\n\n"
            
            # 処理完了のサマリーを追加
            if results_summary:
                final_response += "処理が完了しました。\n\n"
                final_response += "\n".join(results_summary)
            else:
                final_response += "処理が完了しました。"
            
            return final_response.strip()
            
        except Exception as e:
            logger.error(f"❌ [真のReAct] 最終応答生成エラー: {str(e)}")
            return "処理が完了しました。"