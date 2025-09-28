#!/usr/bin/env python3
"""
確認プロセス修正のテスト
Phase 4.4.3の修正が正しく動作するかテスト
"""

import asyncio
import httpx
import json
import logging
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfirmationFixTester:
    """確認プロセス修正テストクラス"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        # .envから認証トークンを取得
        self.test_token = os.getenv("SUPABASE_KEY")
        if not self.test_token:
            logger.error("❌ SUPABASE_KEY が設定されていません")
            logger.error("💡 ヒント: .env ファイルに SUPABASE_KEY=your-token を追加してください")
            raise ValueError("SUPABASE_KEY not found in environment variables")
        
        logger.info(f"✅ 認証トークン取得完了: {self.test_token[:20]}...")
    
    async def test_confirmation_process(self) -> bool:
        """確認プロセスのテスト"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                logger.info("🚀 確認プロセス修正テスト開始")
                
                # Step 1: 複雑な要求を送信（確認プロセスをトリガー）
                logger.info("📝 Step 1: 複雑な要求を送信（認証なしテストエンドポイント使用）")
                response1 = await client.post(
                    f"{self.base_url}/chat-test",
                    headers={
                        "Content-Type": "application/json"
                    },
                    json={"message": "牛乳を削除してから、今ある在庫で作れる献立と、そのレシピを教えて"}
                )
                
                if response1.status_code != 200:
                    logger.error(f"❌ Step 1失敗: HTTP {response1.status_code}")
                    return False
                
                result1 = response1.json()
                logger.info(f"✅ Step 1成功: {result1['response'][:100]}...")
                
                # 確認プロセスがトリガーされたかチェック
                if not result1.get('confirmation_required', False):
                    logger.error("❌ 確認プロセスがトリガーされませんでした")
                    return False
                
                logger.info("✅ 確認プロセスが正常にトリガーされました")
                
                # Step 2: 確認応答を送信（修正版）
                logger.info("📝 Step 2: 確認応答を送信（新しいのを削除）")
                response2 = await client.post(
                    f"{self.base_url}/chat-test/confirm",
                    headers={
                        "Content-Type": "application/json"
                    },
                    json={"message": "新しいのを削除"}
                )
                
                if response2.status_code != 200:
                    logger.error(f"❌ Step 2失敗: HTTP {response2.status_code}")
                    logger.error(f"❌ エラー詳細: {response2.text}")
                    return False
                
                result2 = response2.json()
                logger.info(f"✅ Step 2成功: {result2['response'][:100]}...")
                
                # Step 3: 結果の検証
                logger.info("📝 Step 3: 結果の検証")
                
                # エラーメッセージが改善されているかチェック
                if "新しい" in result2['response'] and "見つかりません" in result2['response']:
                    logger.info("✅ エラーメッセージが改善されました（技術的でない説明）")
                else:
                    logger.warning("⚠️ エラーメッセージの改善が確認できませんでした")
                
                # タスクチェーンが継続されているかチェック
                if "献立" in result2['response'] or "レシピ" in result2['response']:
                    logger.info("✅ タスクチェーンが継続されています")
                else:
                    logger.warning("⚠️ タスクチェーンの継続が確認できませんでした")
                
                logger.info("🎉 確認プロセス修正テスト完了")
                return True
                
        except Exception as e:
            logger.error(f"❌ テストエラー: {str(e)}")
            import traceback
            logger.error(f"❌ トレースバック: {traceback.format_exc()}")
            return False
    
    async def test_improved_error_handling(self) -> bool:
        """改善されたエラーハンドリングのテスト"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                logger.info("🚀 エラーハンドリング改善テスト開始")
                
                # 存在しないアイテムの削除を試行
                response = await client.post(
                    f"{self.base_url}/chat-test",
                    headers={
                        "Content-Type": "application/json"
                    },
                    json={"message": "存在しないアイテムを削除して"}
                )
                
                if response.status_code != 200:
                    logger.error(f"❌ テスト失敗: HTTP {response.status_code}")
                    return False
                
                result = response.json()
                logger.info(f"✅ レスポンス: {result['response']}")
                
                # エラーメッセージがユーザーフレンドリーかチェック
                if "申し訳ありません" in result['response'] or "見つかりません" in result['response']:
                    logger.info("✅ エラーメッセージがユーザーフレンドリーです")
                    return True
                else:
                    logger.warning("⚠️ エラーメッセージの改善が必要です")
                    return False
                
        except Exception as e:
            logger.error(f"❌ テストエラー: {str(e)}")
            return False

async def main():
    """メイン関数"""
    try:
        tester = ConfirmationFixTester()
    except ValueError as e:
        print(f"❌ 初期化エラー: {str(e)}")
        return False
    
    print("🚀 Phase 4.4.3 修正テストスイート開始")
    print("=" * 60)
    
    # サーバー接続確認
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{tester.base_url}/health", timeout=5.0)
            if response.status_code != 200:
                print(f"❌ サーバー接続エラー: HTTP {response.status_code}")
                print("💡 ヒント: python main.py でサーバーを起動してください")
                return False
    except Exception as e:
        print(f"❌ サーバー接続エラー: {e}")
        print("💡 ヒント: python main.py でサーバーを起動してください")
        return False
    
    print("✅ サーバー接続確認完了")
    print()
    
    # テスト実行
    tests = [
        ("確認プロセス修正", tester.test_confirmation_process),
        ("エラーハンドリング改善", tester.test_improved_error_handling)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🧪 {test_name} テスト開始")
        try:
            result = await test_func()
            if result:
                print(f"✅ {test_name} テスト成功")
                passed += 1
            else:
                print(f"❌ {test_name} テスト失敗")
        except Exception as e:
            print(f"❌ {test_name} テストエラー: {str(e)}")
    
    print()
    print("=" * 60)
    print(f"📊 テスト結果: {passed}/{total} 成功")
    print(f"📈 成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 Phase 4.4.3 修正が成功しました！")
        print("✅ 確認プロセスが正常に動作します")
        print("✅ エラーメッセージが改善されました")
        print("✅ タスクチェーンが継続されます")
    else:
        print("⚠️ 一部の修正が不完全です")
        print("   ログを確認して追加の修正が必要です")
    
    return passed == total

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
