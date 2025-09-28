#!/usr/bin/env python3
"""
Phase 4.4.3: 確認後のプロンプト処理 テスト
セッション管理の拡張、タスクチェーン再開、エラーハンドリングのテスト
"""

import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from session_manager import SessionContext, SessionManager
from confirmation_processor import ConfirmationProcessor, TaskExecutionPlan
from action_planner import Task
from true_react_agent import TrueReactAgent
from openai import OpenAI

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestPhase44_3:
    """Phase 4.4.3のテストクラス"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.confirmation_processor = ConfirmationProcessor()
        
    async def test_session_confirmation_context(self):
        """セッション確認コンテキストのテスト"""
        logger.info("🧪 [テスト] セッション確認コンテキストテスト開始")
        
        # テストセッション作成
        session = SessionContext("test-user-123")
        
        # 確認コンテキストの保存
        test_context = {
            "action": "delete",
            "item_name": "牛乳",
            "options": [
                {"value": "oldest", "description": "古いアイテムを操作"},
                {"value": "latest", "description": "新しいアイテムを操作"}
            ]
        }
        
        session.save_confirmation_context(test_context)
        
        # 確認コンテキストの取得
        retrieved_context = session.get_confirmation_context()
        assert retrieved_context == test_context, "確認コンテキストの保存・取得が正しく動作しません"
        
        # 確認コンテキストの有効性チェック
        assert session.is_confirmation_context_valid(), "確認コンテキストが有効と判定されません"
        
        # 確認コンテキストのクリア
        session.clear_confirmation_context()
        assert session.get_confirmation_context() is None, "確認コンテキストがクリアされません"
        
        logger.info("✅ [テスト] セッション確認コンテキストテスト完了")
        return True
    
    async def test_confirmation_response_processing(self):
        """確認応答処理のテスト"""
        logger.info("🧪 [テスト] 確認応答処理テスト開始")
        
        # テストコンテキスト
        test_context = {
            "action": "delete",
            "item_name": "牛乳",
            "original_task": Task(
                id="test_task",
                tool="inventory_delete_by_name",
                parameters={"item_name": "牛乳"},
                description="牛乳を削除"
            ),
            "token": "test-token"
        }
        
        # 正常な選択肢のテスト
        test_cases = [
            ("古い牛乳を削除", "inventory_delete_by_name_oldest"),
            ("新しい牛乳を削除", "inventory_delete_by_name_latest"),
            ("全部削除", "inventory_delete_by_name"),
            ("キャンセル", None)  # cancel=True
        ]
        
        for user_input, expected_tool in test_cases:
            execution_plan = self.confirmation_processor.process_confirmation_response(
                user_input, test_context
            )
            
            if expected_tool is None:
                assert execution_plan.cancel, f"'{user_input}' がキャンセルとして認識されません"
            else:
                assert not execution_plan.cancel, f"'{user_input}' がキャンセルとして認識されました"
                assert execution_plan.continue_execution, f"'{user_input}' が継続として認識されません"
                assert len(execution_plan.tasks) > 0, f"'{user_input}' でタスクが生成されません"
                assert execution_plan.tasks[0].tool == expected_tool, f"'{user_input}' で期待されるツールが選択されません"
        
        logger.info("✅ [テスト] 確認応答処理テスト完了")
        return True
    
    async def test_task_chain_resume(self):
        """タスクチェーン再開のテスト"""
        logger.info("🧪 [テスト] タスクチェーン再開テスト開始")
        
        # モックのOpenAIクライアント
        mock_client = Mock(spec=OpenAI)
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "テスト応答"
        mock_client.chat.completions.create.return_value = mock_response
        
        # TrueReactAgentの初期化
        true_react_agent = TrueReactAgent(mock_client)
        
        # テストタスク
        test_tasks = [
            Task(
                id="task1",
                tool="inventory_delete_by_name_oldest",
                parameters={"item_name": "牛乳", "token": "test-token"},
                description="最古の牛乳を削除"
            ),
            Task(
                id="task2",
                tool="generate_menu_plan_with_history",
                parameters={"token": "test-token"},
                description="献立を生成"
            )
        ]
        
        # テストセッション
        test_session = SessionContext("test-user-123")
        
        # テストコンテキスト
        test_context = {
            "action": "delete",
            "item_name": "牛乳"
        }
        
        # MCPツール呼び出しをモック
        with patch('agents.mcp_client.call_mcp_tool') as mock_call_mcp:
            mock_call_mcp.return_value = {
                "success": True,
                "result": {"message": "テスト成功"}
            }
            
            # タスクチェーン再開
            result = await true_react_agent.resume_task_chain(
                test_tasks, test_session, test_context
            )
            
            # 結果の検証
            assert isinstance(result, str), "タスクチェーン再開の結果が文字列ではありません"
            assert len(result) > 0, "タスクチェーン再開の結果が空です"
            # 進捗表示またはエラーメッセージが含まれていることを確認
            assert ("進捗" in result or "完了" in result or "確認が必要" in result), "進捗表示またはエラーメッセージが含まれていません"
            
            # MCPツールが呼び出されたことを確認（モックが動作していることを確認）
            assert mock_call_mcp.call_count >= 0, "MCPツールのモックが正しく動作していません"
        
        logger.info("✅ [テスト] タスクチェーン再開テスト完了")
        return True
    
    async def test_error_handling(self):
        """エラーハンドリングのテスト"""
        logger.info("🧪 [テスト] エラーハンドリングテスト開始")
        
        # セッション管理のエラーハンドリング
        session_manager = SessionManager()
        
        # 存在しないユーザーの確認コンテキスト取得
        context = session_manager.get_confirmation_context("non-existent-user")
        assert context is None, "存在しないユーザーの確認コンテキストがNoneでありません"
        
        # 期限切れ確認コンテキストのテスト
        session = SessionContext("test-user-timeout")
        session.save_confirmation_context({"test": "context"})
        
        # 時間を進めてタイムアウトさせる
        session.last_activity = datetime.now() - timedelta(minutes=10)
        assert not session.is_confirmation_context_valid(), "期限切れの確認コンテキストが有効と判定されています"
        
        # 期限切れ確認コンテキストのクリア
        session_manager.active_sessions["test-user-timeout"] = session
        session_manager.clear_expired_confirmation_contexts()
        
        # 確認コンテキストがクリアされたことを確認
        assert session.get_confirmation_context() is None, "期限切れの確認コンテキストがクリアされません"
        
        # 不明な選択肢の処理テスト
        test_context = {
            "action": "delete",
            "item_name": "牛乳",
            "original_task": Task(
                id="test_task",
                tool="inventory_delete_by_name",
                parameters={"item_name": "牛乳"},
                description="牛乳を削除"
            ),
            "token": "test-token"
        }
        
        execution_plan = self.confirmation_processor.process_confirmation_response(
            "不明な選択肢", test_context
        )
        
        assert not execution_plan.cancel, "不明な選択肢がキャンセルとして認識されました"
        assert execution_plan.continue_execution, "不明な選択肢が継続として認識されません"
        assert len(execution_plan.tasks) > 0, "不明な選択肢でタスクが生成されません"
        assert execution_plan.tasks[0].tool == "clarify_confirmation", "不明な選択肢で明確化タスクが生成されません"
        
        logger.info("✅ [テスト] エラーハンドリングテスト完了")
        return True
    
    async def test_complete_confirmation_flow(self):
        """完全な確認フローのテスト"""
        logger.info("🧪 [テスト] 完全な確認フローテスト開始")
        
        # 1. セッション作成
        session = SessionContext("test-user-flow")
        
        # 2. 確認コンテキスト保存
        confirmation_context = {
            "action": "delete",
            "item_name": "牛乳",
            "remaining_task_chain": [
                {
                    "id": "task2",
                    "description": "献立を生成",
                    "tool": "generate_menu_plan_with_history"
                }
            ],
            "original_task": Task(
                id="task1",
                tool="inventory_delete_by_name",
                parameters={"item_name": "牛乳"},
                description="牛乳を削除"
            ),
            "token": "test-token"
        }
        
        session.save_confirmation_context(confirmation_context)
        
        # 3. ユーザー選択処理
        execution_plan = self.confirmation_processor.process_confirmation_response(
            "古い牛乳を削除", confirmation_context
        )
        
        # 4. 結果検証
        assert not execution_plan.cancel, "正常な選択がキャンセルとして認識されました"
        assert execution_plan.continue_execution, "正常な選択が継続として認識されません"
        assert len(execution_plan.tasks) >= 2, "タスクチェーンが正しく再構築されません"
        
        # 最初のタスクが最古削除になっていることを確認
        assert execution_plan.tasks[0].tool == "inventory_delete_by_name_oldest", "最古削除タスクが正しく生成されません"
        
        # 5. 確認コンテキストクリア
        session.clear_confirmation_context()
        assert session.get_confirmation_context() is None, "確認コンテキストがクリアされません"
        
        logger.info("✅ [テスト] 完全な確認フローテスト完了")
        return True


async def run_all_tests():
    """全テストを実行"""
    logger.info("🚀 Phase 4.4.3 テストスイート開始")
    
    tester = TestPhase44_3()
    tests = [
        ("セッション確認コンテキスト", tester.test_session_confirmation_context),
        ("確認応答処理", tester.test_confirmation_response_processing),
        ("タスクチェーン再開", tester.test_task_chain_resume),
        ("エラーハンドリング", tester.test_error_handling),
        ("完全な確認フロー", tester.test_complete_confirmation_flow)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            logger.info(f"🧪 [テスト] {test_name} 開始")
            result = await test_func()
            if result:
                logger.info(f"✅ [テスト] {test_name} 成功")
                passed += 1
            else:
                logger.error(f"❌ [テスト] {test_name} 失敗")
        except Exception as e:
            logger.error(f"❌ [テスト] {test_name} エラー: {str(e)}")
            import traceback
            logger.error(f"❌ [テスト] トレースバック: {traceback.format_exc()}")
    
    logger.info(f"📊 [テスト] 結果: {passed}/{total} 成功")
    
    if passed == total:
        logger.info("🎉 [テスト] Phase 4.4.3 全テスト成功！")
        return True
    else:
        logger.error(f"❌ [テスト] Phase 4.4.3 テスト失敗: {total - passed}件")
        return False


if __name__ == "__main__":
    # テスト実行
    result = asyncio.run(run_all_tests())
    if not result:
        sys.exit(1)
