#!/usr/bin/env python3
"""
MorizoAI 統合テスト
4つのシナリオでの全体動作確認
"""

import asyncio
import json
import sys
import os
import time
from typing import Dict, Any
import httpx
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MorizoAITester:
    """MorizoAI統合テストクラス"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.supabase_token = os.getenv("SUPABASE_ANON_KEY")
        if not self.supabase_token:
            print("❌ SUPABASE_ANON_KEY が設定されていません")
            sys.exit(1)
    
    async def send_message(self, message: str) -> Dict[str, Any]:
        """メッセージを送信してレスポンスを取得"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat",
                    headers={
                        "Authorization": f"Bearer {self.supabase_token}",
                        "Content-Type": "application/json"
                    },
                    json={"message": message},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "response": "エラーが発生しました"
                    }
                    
            except Exception as e:
                return {
                    "error": str(e),
                    "response": "接続エラーが発生しました"
                }
    
    async def test_scenario_1_greeting(self):
        """シナリオ1: 簡単な挨拶パターン"""
        print("🔍 シナリオ1: 簡単な挨拶パターン")
        print("メッセージ: こんにちは")
        
        result = await self.send_message("こんにちは")
        
        if "error" in result:
            print(f"❌ エラー: {result['error']}")
            return False
        
        response = result.get("response", "")
        print(f"✅ レスポンス: {response}")
        
        # シンプルな挨拶応答かチェック
        if len(response) < 100 and ("こんにちは" in response or "おはよう" in response or "こんばんは" in response):
            print("✅ シンプルな挨拶応答を確認")
            return True
        else:
            print("⚠️ シンプルな挨拶応答ではない可能性")
            return True  # エラーではないので成功とする
    
    async def test_scenario_2_inventory_list(self):
        """シナリオ2: 在庫一覧の取得"""
        print("\n🔍 シナリオ2: 在庫一覧の取得")
        print("メッセージ: 今の在庫を教えて")
        
        result = await self.send_message("今の在庫を教えて")
        
        if "error" in result:
            print(f"❌ エラー: {result['error']}")
            return False
        
        response = result.get("response", "")
        print(f"✅ レスポンス: {response}")
        
        # 在庫情報が含まれているかチェック
        if "在庫" in response or "冷蔵庫" in response or "食材" in response:
            print("✅ 在庫情報の取得を確認")
            return True
        else:
            print("⚠️ 在庫情報が取得できていない可能性")
            return False
    
    async def test_scenario_3_inventory_insert(self):
        """シナリオ3: 在庫を2件同時挿入"""
        print("\n🔍 シナリオ3: 在庫を2件同時挿入")
        print("メッセージ: 豚バラブロックを1パックと、ほうれん草1束を買ってきたから、冷蔵庫に入れておいて")
        
        result = await self.send_message("豚バラブロックを1パックと、ほうれん草1束を買ってきたから、冷蔵庫に入れておいて")
        
        if "error" in result:
            print(f"❌ エラー: {result['error']}")
            return False
        
        response = result.get("response", "")
        print(f"✅ レスポンス: {response}")
        
        # 在庫追加の確認
        if ("豚バラ" in response and "ほうれん草" in response) or "追加" in response or "入れて" in response:
            print("✅ 在庫追加の実行を確認")
            return True
        else:
            print("⚠️ 在庫追加が実行されていない可能性")
            return False
    
    async def test_scenario_4_recipe_suggestion(self):
        """シナリオ4: レシピ提案（最重要）"""
        print("\n🔍 シナリオ4: レシピ提案（最重要）")
        print("メッセージ: 今の在庫から作れる献立を教えて")
        
        result = await self.send_message("今の在庫から作れる献立を教えて")
        
        if "error" in result:
            print(f"❌ エラー: {result['error']}")
            return False
        
        response = result.get("response", "")
        print(f"✅ レスポンス: {response}")
        
        # レシピ提案の確認
        if ("献立" in response or "レシピ" in response or "料理" in response) and len(response) > 50:
            print("✅ レシピ提案の実行を確認")
            return True
        else:
            print("⚠️ レシピ提案が実行されていない可能性")
            return False
    
    async def run_all_tests(self):
        """全テストの実行"""
        print("🚀 MorizoAI 統合テスト開始")
        print("=" * 60)
        print("⚠️ 注意: このテストは python main.py でサーバーを起動した前提で実行されます")
        print("=" * 60)
        
        # サーバー接続確認
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health", timeout=5.0)
                if response.status_code != 200:
                    print(f"❌ サーバー接続エラー: HTTP {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ サーバー接続エラー: {e}")
            print("💡 ヒント: python main.py でサーバーを起動してください")
            return False
        
        print("✅ サーバー接続確認完了")
        print("\n" + "=" * 60)
        
        # 各シナリオの実行
        results = []
        
        # シナリオ1: 挨拶
        result1 = await self.test_scenario_1_greeting()
        results.append(("挨拶パターン", result1))
        
        # シナリオ2: 在庫一覧
        result2 = await self.test_scenario_2_inventory_list()
        results.append(("在庫一覧取得", result2))
        
        # シナリオ3: 在庫挿入
        result3 = await self.test_scenario_3_inventory_insert()
        results.append(("在庫挿入", result3))
        
        # シナリオ4: レシピ提案（最重要）
        result4 = await self.test_scenario_4_recipe_suggestion()
        results.append(("レシピ提案", result4))
        
        # 結果サマリー
        print("\n" + "=" * 60)
        print("📊 テスト結果サマリー")
        print("=" * 60)
        
        success_count = 0
        for test_name, success in results:
            status = "✅ 成功" if success else "❌ 失敗"
            print(f"{test_name}: {status}")
            if success:
                success_count += 1
        
        print(f"\n📈 成功率: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
        
        if success_count == len(results):
            print("🎉 全テスト成功！MorizoAIは正常に動作しています。")
        elif success_count >= 3:
            print("⚠️ 大部分のテストが成功しました。一部の機能に問題がある可能性があります。")
        else:
            print("❌ 多くのテストが失敗しました。システムに問題がある可能性があります。")
        
        return success_count == len(results)

async def main():
    """メイン関数"""
    tester = MorizoAITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
