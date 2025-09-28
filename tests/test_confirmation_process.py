#!/usr/bin/env python3
"""
Phase 4.4.1: 基本確認プロセスのテスト
曖昧性検出、確認プロセス、タスクチェーン管理の動作確認
"""

import asyncio
import sys
import os
from typing import List, Dict, Any

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ambiguity_detector import AmbiguityDetector, AmbiguityInfo
from confirmation_processor import ConfirmationProcessor, TaskExecutionPlan
from task_chain_manager import TaskChainManager
from confirmation_exceptions import UserConfirmationRequired
from action_planner import Task


class ConfirmationProcessTester:
    """確認プロセステストクラス"""
    
    def __init__(self):
        self.ambiguity_detector = AmbiguityDetector()
        self.confirmation_processor = ConfirmationProcessor()
        self.task_chain_manager = TaskChainManager()
    
    def create_test_inventory(self) -> List[Dict[str, Any]]:
        """テスト用の在庫データを作成"""
        return [
            {
                "id": "abc123",
                "item_name": "牛乳",
                "quantity": 1.0,
                "unit": "本",
                "created_at": "2025-09-25T10:00:00Z"
            },
            {
                "id": "def456", 
                "item_name": "牛乳",
                "quantity": 1.0,
                "unit": "本",
                "created_at": "2025-09-26T10:00:00Z"
            },
            {
                "id": "ghi789",
                "item_name": "牛乳", 
                "quantity": 1.0,
                "unit": "本",
                "created_at": "2025-09-27T10:00:00Z"
            },
            {
                "id": "jkl012",
                "item_name": "パン",
                "quantity": 1.0,
                "unit": "個",
                "created_at": "2025-09-27T10:00:00Z"
            }
        ]
    
    def create_test_task(self) -> Task:
        """テスト用のタスクを作成"""
        return Task(
            id="test_task_1",
            tool="inventory_delete_by_name",
            parameters={"item_name": "牛乳"},
            description="牛乳を削除"
        )
    
    def test_ambiguity_detection(self) -> bool:
        """曖昧性検出のテスト"""
        print("\n=== 曖昧性検出テスト ===")
        
        inventory = self.create_test_inventory()
        task = self.create_test_task()
        
        # 曖昧性検出
        ambiguity_info = self.ambiguity_detector.detect_ambiguity(task, inventory)
        
        if ambiguity_info is None:
            print("❌ 曖昧性が検出されませんでした")
            return False
        
        print(f"✅ 曖昧性検出成功: {ambiguity_info.type}")
        print(f"   アイテム名: {ambiguity_info.item_name}")
        print(f"   アイテム数: {len(ambiguity_info.items)}")
        print(f"   確認必要: {ambiguity_info.needs_confirmation}")
        
        return True
    
    def test_confirmation_response_generation(self) -> bool:
        """確認レスポンス生成のテスト"""
        print("\n=== 確認レスポンス生成テスト ===")
        
        inventory = self.create_test_inventory()
        task = self.create_test_task()
        
        # 曖昧性検出
        ambiguity_info = self.ambiguity_detector.detect_ambiguity(task, inventory)
        
        if ambiguity_info is None:
            print("❌ 曖昧性が検出されませんでした")
            return False
        
        # 確認レスポンス生成
        response = self.confirmation_processor.generate_confirmation_response(ambiguity_info)
        
        print("✅ 確認レスポンス生成成功:")
        print(response)
        
        return True
    
    def test_task_chain_management(self) -> bool:
        """タスクチェーン管理のテスト"""
        print("\n=== タスクチェーン管理テスト ===")
        
        # テスト用のタスクチェーンを作成
        tasks = [
            Task(id="task1", tool="inventory_delete_by_name", parameters={"item_name": "牛乳"}, description="牛乳を削除"),
            Task(id="task2", tool="inventory_list", parameters={}, description="在庫一覧を取得"),
            Task(id="task3", tool="generate_menu_plan_with_history", parameters={}, description="献立を生成")
        ]
        
        # タスクチェーンを設定
        self.task_chain_manager.set_task_chain(tasks)
        
        # 進捗情報を確認
        progress_info = self.task_chain_manager.get_progress_info()
        print(f"✅ タスクチェーン設定成功:")
        print(f"   総タスク数: {progress_info['total_tasks']}")
        print(f"   完了タスク数: {progress_info['completed_tasks']}")
        print(f"   残りタスク数: {progress_info['remaining_tasks']}")
        
        # 残りのタスクを確認
        remaining_tasks = self.task_chain_manager.get_remaining_tasks()
        print(f"   残りのタスク: {[task.description for task in remaining_tasks]}")
        
        return True
    
    def test_confirmation_response_processing(self) -> bool:
        """確認応答処理のテスト"""
        print("\n=== 確認応答処理テスト ===")
        
        # テスト用のコンテキスト
        context = {
            "item_name": "牛乳",
            "original_task": self.create_test_task(),
            "token": "test_token",
            "remaining_task_chain": [
                Task(id="task2", tool="inventory_list", parameters={}, description="在庫一覧を取得")
            ]
        }
        
        # 各種選択肢をテスト
        test_cases = [
            ("古い牛乳を削除", "oldest"),
            ("新しい牛乳を削除", "latest"), 
            ("全部削除", "all"),
            ("キャンセル", "cancel")
        ]
        
        for user_input, expected_type in test_cases:
            try:
                execution_plan = self.confirmation_processor.process_confirmation_response(user_input, context)
                
                if expected_type == "cancel":
                    if execution_plan.cancel:
                        print(f"✅ '{user_input}' → キャンセル処理成功")
                    else:
                        print(f"❌ '{user_input}' → キャンセル処理失敗")
                        return False
                else:
                    if not execution_plan.cancel and execution_plan.continue_execution:
                        print(f"✅ '{user_input}' → 実行計画生成成功")
                        print(f"   タスク数: {len(execution_plan.tasks)}")
                    else:
                        print(f"❌ '{user_input}' → 実行計画生成失敗")
                        return False
                        
            except Exception as e:
                print(f"❌ '{user_input}' → エラー: {str(e)}")
                return False
        
        return True
    
    def test_exception_handling(self) -> bool:
        """例外処理のテスト"""
        print("\n=== 例外処理テスト ===")
        
        try:
            # UserConfirmationRequired例外のテスト
            confirmation_context = {
                "action": "delete",
                "item_name": "牛乳",
                "options": []
            }
            
            executed_tasks = [self.create_test_task()]
            remaining_tasks = [
                Task(id="task2", tool="inventory_list", parameters={}, description="在庫一覧を取得")
            ]
            
            exception = UserConfirmationRequired(
                confirmation_context=confirmation_context,
                executed_tasks=executed_tasks,
                remaining_tasks=remaining_tasks
            )
            
            print(f"✅ UserConfirmationRequired例外作成成功")
            print(f"   確認コンテキスト: {exception.confirmation_context['action']}")
            print(f"   実行済みタスク数: {len(exception.executed_tasks)}")
            print(f"   残りタスク数: {len(exception.remaining_tasks)}")
            
            return True
            
        except Exception as e:
            print(f"❌ 例外処理テスト失敗: {str(e)}")
            return False
    
    def run_all_tests(self) -> bool:
        """全てのテストを実行"""
        print("🚀 Phase 4.4.1: 基本確認プロセスのテスト開始")
        print("="*60)
        
        test_results = []
        
        # 各テストを実行
        test_results.append(("曖昧性検出", self.test_ambiguity_detection()))
        test_results.append(("確認レスポンス生成", self.test_confirmation_response_generation()))
        test_results.append(("タスクチェーン管理", self.test_task_chain_management()))
        test_results.append(("確認応答処理", self.test_confirmation_response_processing()))
        test_results.append(("例外処理", self.test_exception_handling()))
        
        # 結果サマリー
        print("\n" + "="*60)
        print("📊 テスト結果サマリー")
        print("="*60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n🎯 総合結果: {passed}/{total} テストが成功")
        
        if passed == total:
            print("🎉 全ての基本確認プロセステストが成功しました!")
            print("   Phase 4.4.1の基本実装が正常に動作しています")
        else:
            print("⚠️  一部のテストが失敗しました")
            print("   ログを確認して問題を特定してください")
        
        return passed == total


async def main():
    """メイン関数"""
    tester = ConfirmationProcessTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎊 Phase 4.4.1: 基本確認プロセスの実装が完了しました!")
        print("   次のステップ: TrueReactAgentとの統合")
        sys.exit(0)
    else:
        print("\n❌ テストが失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
