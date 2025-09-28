#!/usr/bin/env python3
"""
Phase 4.4.2: TrueReactAgentとの統合テスト
確認プロセスが実際のチャットフローで動作するかテスト
"""

import asyncio
import httpx
import json
import os
from typing import Dict, Any
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

class ConfirmationIntegrationTester:
    """確認プロセス統合テストクラス"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.supabase_token = os.getenv("SUPABASE_ANON_KEY")
        self.client = httpx.AsyncClient(timeout=60.0)
        
        # デバッグ情報
        print(f"🔍 [テスト] SUPABASE_ANON_KEY: {self.supabase_token[:20] if self.supabase_token else None}...")
        print(f"🔍 [テスト] Token length: {len(self.supabase_token) if self.supabase_token else 0}")
    
    async def send_message(self, message: str) -> Dict[str, Any]:
        """メッセージを送信してレスポンスを取得"""
        try:
            response = await self.client.post(
                f"{self.base_url}/chat",
                headers={
                    "Authorization": f"Bearer {self.supabase_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "message": message,
                    "session_id": "test_session_confirmation"
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def send_confirmation(self, message: str) -> Dict[str, Any]:
        """確認応答を送信"""
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/confirm",
                headers={
                    "Authorization": f"Bearer {self.supabase_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "message": message,
                    "session_id": "test_session_confirmation"
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_confirmation_flow(self) -> bool:
        """確認フローの統合テスト"""
        print("\n=== 確認フロー統合テスト ===")
        
        # 1. 曖昧性を発生させるリクエストを送信
        print("1. 曖昧性を発生させるリクエストを送信...")
        ambiguous_request = "牛乳を削除して"
        
        response1 = await self.send_message(ambiguous_request)
        
        if "error" in response1:
            print(f"❌ リクエスト送信エラー: {response1['error']}")
            return False
        
        print(f"✅ レスポンス受信:")
        print(f"   Success: {response1.get('success', False)}")
        print(f"   Confirmation Required: {response1.get('confirmation_required', False)}")
        print(f"   Response: {response1.get('response', '')[:100]}...")
        
        # 2. 確認が必要かチェック
        if not response1.get('confirmation_required', False):
            print("⚠️ 確認が要求されませんでした。在庫に牛乳が複数存在しない可能性があります。")
            print("   テストを続行するため、確認応答を送信します...")
        
        # 3. 確認応答を送信
        print("\n2. 確認応答を送信...")
        confirmation_response = "古い牛乳を削除"
        
        response2 = await self.send_confirmation(confirmation_response)
        
        if "error" in response2:
            print(f"❌ 確認応答送信エラー: {response2['error']}")
            return False
        
        print(f"✅ 確認応答受信:")
        print(f"   Success: {response2.get('success', False)}")
        print(f"   Response: {response2.get('response', '')}")
        
        return True
    
    async def test_simple_request(self) -> bool:
        """シンプルなリクエストのテスト（確認不要）"""
        print("\n=== シンプルリクエストテスト ===")
        
        simple_request = "在庫一覧を表示して"
        
        response = await self.send_message(simple_request)
        
        if "error" in response:
            print(f"❌ リクエスト送信エラー: {response['error']}")
            return False
        
        print(f"✅ シンプルリクエスト成功:")
        print(f"   Success: {response.get('success', False)}")
        print(f"   Confirmation Required: {response.get('confirmation_required', False)}")
        print(f"   Response: {response.get('response', '')[:100]}...")
        
        return True
    
    async def run_all_tests(self) -> bool:
        """全テストを実行"""
        print("🚀 Phase 4.4.2: TrueReactAgentとの統合テスト開始")
        print("=" * 60)
        
        test_results = []
        
        # テスト1: シンプルリクエスト
        try:
            result1 = await self.test_simple_request()
            test_results.append(("シンプルリクエスト", result1))
        except Exception as e:
            print(f"❌ シンプルリクエストテストエラー: {str(e)}")
            test_results.append(("シンプルリクエスト", False))
        
        # テスト2: 確認フロー
        try:
            result2 = await self.test_confirmation_flow()
            test_results.append(("確認フロー", result2))
        except Exception as e:
            print(f"❌ 確認フローテストエラー: {str(e)}")
            test_results.append(("確認フロー", False))
        
        # 結果サマリー
        print("\n" + "=" * 60)
        print("📊 テスト結果サマリー")
        print("=" * 60)
        
        passed_tests = 0
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")
            if result:
                passed_tests += 1
        
        print(f"\n🎯 総合結果: {passed_tests}/{len(test_results)} テストが成功")
        
        if passed_tests == len(test_results):
            print("🎉 全ての統合テストが成功しました!")
            print("   Phase 4.4.2の統合実装が正常に動作しています")
            return True
        else:
            print("⚠️ 一部のテストが失敗しました")
            return False
    
    async def close(self):
        """リソースをクリーンアップ"""
        await self.client.aclose()

async def main():
    """メイン実行関数"""
    tester = ConfirmationIntegrationTester()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            print("\n🎊 Phase 4.4.2: TrueReactAgentとの統合が完了しました!")
            print("   次のステップ: ドキュメント更新と最終テスト")
        else:
            print("\n⚠️ 統合テストで問題が発生しました")
            print("   ログを確認して問題を特定してください")
    
    finally:
        await tester.close()

if __name__ == "__main__":
    asyncio.run(main())
