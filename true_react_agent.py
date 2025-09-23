"""
真のReActエージェント
行動計画立案→タスク管理→ReActループ→完了報告の完全なAIエージェント
"""

import json
import logging
from typing import List, Dict, Any, Optional
from action_planner import ActionPlanner, Task
from task_manager import TaskManager
from openai import OpenAI

logger = logging.getLogger("morizo_ai.true_react")

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
            tasks = self.planner.create_plan(user_request, available_tools)
            
            if not self.planner.validate_plan(tasks):
                logger.error("❌ [真のReAct] タスクプランが無効です")
                return "申し訳ありません。要求を理解できませんでした。"
            
            # タスクを最適化
            tasks = self.planner.optimize_plan(tasks)
            
            # Phase 2: タスク管理に追加
            self.task_manager.add_tasks(tasks)
            
            logger.info(f"🤖 [真のReAct] {len(tasks)}個のタスクを生成")
            
            # Phase 3: ReActループ
            react_cycles = 0
            while self.task_manager.has_remaining_tasks() and react_cycles < self.max_react_cycles:
                react_cycles += 1
                logger.info(f"🔄 [真のReAct] サイクル {react_cycles} 開始")
                
                # 次のタスクを取得
                current_task = self.task_manager.get_next_task()
                if not current_task:
                    break
                
                # タスクを実行中にマーク
                self.task_manager.mark_task_in_progress(current_task)
                
                # ReActステップを実行
                result = await self._react_step(current_task, user_session)
                
                if result.get("success"):
                    self.task_manager.mark_task_completed(current_task, result)
                else:
                    self.task_manager.mark_task_failed(current_task, result.get("error"))
            
            # Phase 4: 完了報告
            return self._generate_completion_report(user_request)
            
        except Exception as e:
            logger.error(f"❌ [真のReAct] 処理エラー: {str(e)}")
            return f"申し訳ありません。処理中にエラーが発生しました: {str(e)}"
    
    async def _react_step(self, task: Task, user_session) -> Dict[str, Any]:
        """
        単一のReActステップを実行する
        
        Args:
            task: 実行するタスク
            user_session: ユーザーセッション
            
        Returns:
            実行結果
        """
        logger.info(f"🔄 [ReAct] タスク実行: {task.description}")
        
        try:
            # 観察: 現在の状況を把握
            observation = await self._observe(task, user_session)
            
            # 思考: 最適な行動を決定
            thought = await self._think(task, observation)
            
            # 決定: 実行するツールを選択
            decision = await self._decide(task, thought)
            
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
            "current_inventory": user_session.current_inventory,
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
- 在庫状況: {json.dumps(observation['current_inventory'], ensure_ascii=False, indent=2)}
- 最近の操作: {json.dumps(observation['operation_history'], ensure_ascii=False, indent=2)}

このタスクを実行するために必要な行動を簡潔に説明してください。
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": thinking_prompt}],
                max_tokens=200,
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
            # MCPツールを実行（main.pyのMCPClientを使用）
            from main import mcp_client
            
            # トークンを追加
            params = decision["parameters"].copy()
            params["token"] = user_session.token
            
            logger.info(f"🎬 [行動] {decision['tool']} 実行開始")
            logger.info(f"🎬 [行動] パラメータ: {params}")
            
            result = await mcp_client.call_tool(
                decision["tool"],
                params
            )
            
            logger.info(f"🎬 [行動] {decision['tool']} 実行完了")
            return {"success": True, "result": result}
            
        except Exception as e:
            logger.error(f"❌ [行動] エラー: {str(e)}")
            logger.error(f"❌ [行動] エラー詳細: {type(e).__name__}")
            return {"success": False, "error": str(e)}
    
    def _generate_completion_report(self, user_request: str) -> str:
        """
        完了報告を生成する
        
        Args:
            user_request: 元のユーザー要求
            
        Returns:
            完了報告
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
        
        logger.info(f"✅ [完了報告] ユーザー要求: {user_request}")
        return report
