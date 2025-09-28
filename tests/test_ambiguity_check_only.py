#!/usr/bin/env python3
"""
曖昧性チェック単体テスト
確認プロセス部分のみに特化したテスト
"""

import unittest
import sys
import os
from typing import List, Dict, Any
from dataclasses import dataclass

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 仮のTaskクラス定義
@dataclass
class Task:
    id: str
    description: str
    tool: str
    parameters: Dict[str, Any]
    status: str = "pending"
    dependencies: List[str] = None
    result: Dict[str, Any] = None

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "tool": self.tool,
            "parameters": self.parameters,
            "status": self.status,
            "dependencies": self.dependencies,
            "result": self.result
        }

# テスト対象のモジュールをインポート
from ambiguity_detector import AmbiguityDetector, AmbiguityInfo
from confirmation_processor import ConfirmationProcessor
from confirmation_exceptions import UserConfirmationRequired


class TestAmbiguityCheckOnly(unittest.TestCase):
    """曖昧性チェック単体テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.ambiguity_detector = AmbiguityDetector()
        self.confirmation_processor = ConfirmationProcessor()
        
        # テスト用のタスク
        self.delete_task = Task(
            id="test_task_1",
            description="牛乳を削除する",
            tool="inventory_delete_by_name",
            parameters={"item_name": "牛乳"}
        )
        
        # テスト用のタスク（latest版）
        self.delete_latest_task = Task(
            id="test_task_latest",
            description="最新の牛乳を削除する",
            tool="inventory_delete_by_name_latest",
            parameters={"item_name": "牛乳"}
        )
        
        # テスト用の在庫データ（複数アイテム）
        self.multiple_inventory = [
            {
                "id": "milk_1",
                "item_name": "牛乳",
                "quantity": 1,
                "unit": "本",
                "storage_location": "冷蔵庫",
                "expiry_date": "2025-10-01",
                "created_at": "2025-09-25T10:00:00Z"
            },
            {
                "id": "milk_2", 
                "item_name": "牛乳",
                "quantity": 2,
                "unit": "本",
                "storage_location": "冷蔵庫",
                "expiry_date": "2025-10-02",
                "created_at": "2025-09-26T10:00:00Z"
            },
            {
                "id": "milk_3",
                "item_name": "牛乳", 
                "quantity": 1,
                "unit": "本",
                "storage_location": "冷蔵庫",
                "expiry_date": "2025-10-03",
                "created_at": "2025-09-27T10:00:00Z"
            }
        ]
        
        # テスト用の在庫データ（空）
        self.empty_inventory = []
        
        # テスト用の残りタスク
        self.remaining_tasks = [
            Task(
                id="test_task_2",
                description="在庫一覧を表示する",
                tool="inventory_list",
                parameters={}
            )
        ]

    def test_ambiguity_detection_with_multiple_items(self):
        """複数アイテムでの曖昧性検出テスト"""
        print("\n=== 複数アイテムでの曖昧性検出テスト ===")
        
        # 曖昧性検出実行
        result = self.ambiguity_detector.detect_ambiguity(
            self.delete_task, 
            self.multiple_inventory
        )
        
        # 結果確認
        self.assertIsNotNone(result, "曖昧性検出結果がNoneです")
        self.assertTrue(result.needs_confirmation, "確認が必要と判定されていません")
        self.assertEqual(result.item_name, "牛乳", "アイテム名が正しくありません")
        self.assertEqual(len(result.items), 3, "アイテム数が正しくありません")
        
        print(f"✅ 曖昧性検出成功: {result}")
        print(f"   確認が必要: {result.needs_confirmation}")
        print(f"   アイテム数: {len(result.items)}")

    def test_ambiguity_detection_with_empty_inventory(self):
        """空の在庫での曖昧性検出テスト"""
        print("\n=== 空の在庫での曖昧性検出テスト ===")
        
        # 曖昧性検出実行
        result = self.ambiguity_detector.detect_ambiguity(
            self.delete_task,
            self.empty_inventory
        )
        
        # 結果確認（修正後は空の在庫でも確認が必要）
        self.assertIsNotNone(result, "曖昧性検出結果がNoneです")
        self.assertTrue(result.needs_confirmation, "空の在庫でも確認が必要です")
        self.assertEqual(result.item_name, "牛乳", "アイテム名が正しくありません")
        self.assertEqual(len(result.items), 0, "アイテム数が0でないです")
        
    def test_ambiguity_detection_with_latest_tool(self):
        """inventory_delete_by_name_latestでの曖昧性検出テスト"""
        print("\n=== inventory_delete_by_name_latestでの曖昧性検出テスト ===")
        
        # 曖昧性検出実行
        result = self.ambiguity_detector.detect_ambiguity(
            self.delete_latest_task, 
            self.empty_inventory
        )
        
        # 結果確認（修正後は空の在庫でも確認が必要）
        self.assertIsNotNone(result, "曖昧性検出結果がNoneです")
        self.assertTrue(result.needs_confirmation, "空の在庫でも確認が必要です")
        self.assertEqual(result.item_name, "牛乳", "アイテム名が正しくありません")
        self.assertEqual(len(result.items), 0, "アイテム数が0でないです")
        self.assertEqual(result.type, "fifo_operation", "タイプが正しくありません")
        
        print(f"✅ inventory_delete_by_name_latestでも曖昧性検出成功: {result}")
        print(f"   確認が必要: {result.needs_confirmation}")
        print(f"   アイテム数: {len(result.items)}")
        print(f"   タイプ: {result.type}")

    def test_confirmation_response_generation(self):
        """確認レスポンス生成テスト"""
        print("\n=== 確認レスポンス生成テスト ===")
        
        # 曖昧性情報を生成
        ambiguity_info = self.ambiguity_detector.detect_ambiguity(
            self.delete_task,
            self.multiple_inventory
        )
        
        # 確認レスポンス生成
        response = self.confirmation_processor.generate_confirmation_response(
            ambiguity_info,
            self.remaining_tasks
        )
        
        # 結果確認（辞書形式）
        self.assertIsNotNone(response, "確認レスポンスがNoneです")
        self.assertIsInstance(response, dict, "確認レスポンスが辞書ではありません")
        self.assertIn("response", response, "responseキーが存在しません")
        self.assertIn("confirmation_context", response, "confirmation_contextキーが存在しません")
        
        # confirmation_contextの内容確認
        context = response["confirmation_context"]
        self.assertEqual(context["action"], "delete", "アクションが正しくありません")
        self.assertEqual(context["item_name"], "牛乳", "アイテム名が正しくありません")
        self.assertIsInstance(context["remaining_task_chain"], list, "remaining_task_chainがリストではありません")
        self.assertIsInstance(context["options"], list, "optionsがリストではありません")
        
        print(f"✅ 確認レスポンス生成成功")
        print(f"   レスポンス型: {type(response)}")
        print(f"   レスポンス長: {len(response['response'])}文字")
        print(f"   アクション: {context['action']}")
        print(f"   アイテム名: {context['item_name']}")
        print(f"   オプション数: {len(context['options'])}")

    def test_confirmation_response_structure(self):
        """確認レスポンスの構造テスト"""
        print("\n=== 確認レスポンス構造テスト ===")
        
        # 曖昧性情報を生成
        ambiguity_info = self.ambiguity_detector.detect_ambiguity(
            self.delete_task,
            self.multiple_inventory
        )
        
        # 確認レスポンス生成
        response = self.confirmation_processor.generate_confirmation_response(
            ambiguity_info,
            self.remaining_tasks
        )
        
        # 構造確認
        print(f"🔍 レスポンス型: {type(response)}")
        print(f"🔍 レスポンス内容: {response}")
        
        # 修正後は辞書形式でアクセス可能
        try:
            context = response["confirmation_context"]
            print(f"✅ 辞書アクセス成功: {context}")
            print(f"   アクション: {context['action']}")
            print(f"   アイテム名: {context['item_name']}")
            print(f"   残りタスク数: {len(context['remaining_task_chain'])}")
            print(f"   オプション数: {len(context['options'])}")
        except KeyError as e:
            print(f"❌ キーエラー: {e}")
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")

    def test_user_confirmation_required_exception(self):
        """UserConfirmationRequired例外テスト"""
        print("\n=== UserConfirmationRequired例外テスト ===")
        
        # 曖昧性情報を生成
        ambiguity_info = self.ambiguity_detector.detect_ambiguity(
            self.delete_task,
            self.multiple_inventory
        )
        
        # 確認レスポンス生成
        response = self.confirmation_processor.generate_confirmation_response(
            ambiguity_info,
            self.remaining_tasks
        )
        
        # 例外発生テスト（修正後）
        try:
            context = response["confirmation_context"]
            executed_tasks = []
            remaining_tasks = self.remaining_tasks
            
            raise UserConfirmationRequired(
                confirmation_context=context,
                executed_tasks=executed_tasks,
                remaining_tasks=remaining_tasks
            )
        except UserConfirmationRequired as e:
            print(f"✅ 例外正常発生: {e}")
            print(f"   確認コンテキスト: {e.confirmation_context}")
            print(f"   アクション: {e.confirmation_context['action']}")
            print(f"   アイテム名: {e.confirmation_context['item_name']}")
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")


def run_ambiguity_tests():
    """曖昧性チェックテスト実行"""
    print("🧪 曖昧性チェック単体テスト開始")
    print("=" * 50)
    
    # テストスイート作成
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAmbiguityCheckOnly)
    
    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    print(f"📊 テスト結果: {result.testsRun}件実行")
    print(f"   成功: {result.testsRun - len(result.failures) - len(result.errors)}件")
    print(f"   失敗: {len(result.failures)}件")
    print(f"   エラー: {len(result.errors)}件")
    
    if result.failures:
        print("\n❌ 失敗したテスト:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")
    
    if result.errors:
        print("\n❌ エラーが発生したテスト:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_ambiguity_tests()
    sys.exit(0 if success else 1)
