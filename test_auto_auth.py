#!/usr/bin/env python3
"""
自動認証テストスクリプト
ログインIDとパスワードで自動的にSupabase認証トークンを取得
"""

import asyncio
import json
import sys
import os
import time
from typing import Dict, Any, Optional
import httpx
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

class AutoAuthTester:
    """自動認証テストクラス"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_anon_key = os.getenv("SUPABASE_KEY")  # サービスキーを使用
        
        # 認証情報（.envから取得）
        self.email = os.getenv("TEST_EMAIL", "tonkatai2001@gmail.com")
        self.password = os.getenv("TEST_PASSWORD", "your_password_here")
        
        self.auth_token: Optional[str] = None
    
    async def get_auth_token(self) -> Optional[str]:
        """Supabaseにログインして認証トークンを取得"""
        try:
            print(f"🔐 Supabaseにログイン中: {self.email}")
            
            async with httpx.AsyncClient() as client:
                # Supabase Auth APIでログイン
                response = await client.post(
                    f"{self.supabase_url}/auth/v1/token?grant_type=password",
                    headers={
                        "apikey": self.supabase_anon_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "email": self.email,
                        "password": self.password
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data.get("access_token")
                    print(f"✅ 認証成功: {self.auth_token[:20]}...")
                    return self.auth_token
                else:
                    print(f"❌ 認証失敗: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ 認証エラー: {str(e)}")
            return None
    
    async def send_message(self, message: str) -> Dict[str, Any]:
        """メッセージを送信してレスポンスを取得"""
        if not self.auth_token:
            print("❌ 認証トークンがありません")
            return {"error": "No auth token", "response": "認証エラー"}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat",
                    headers={
                        "Authorization": f"Bearer {self.auth_token}",
                        "Content-Type": "application/json"
                    },
                    json={"message": message},
                    timeout=60.0
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
    
    async def test_confirmation_flow(self):
        """確認プロセスのテスト"""
        print("🧪 確認プロセステスト開始")
        
        # Step 1: 複雑な要求を送信
        print("📝 Step 1: 牛乳を削除してから、今ある在庫で作れる献立と、そのレシピを教えて")
        result1 = await self.send_message("牛乳を削除してから、今ある在庫で作れる献立と、そのレシピを教えて")
        
        if "error" in result1:
            print(f"❌ Step 1エラー: {result1['error']}")
            return False
        
        response1 = result1.get("response", "")
        print(f"✅ Step 1レスポンス: {response1[:100]}...")
        
        # 確認プロセスがトリガーされたかチェック
        if "どの牛乳" in response1 or "確認" in response1:
            print("✅ 確認プロセスがトリガーされました")
            
            # Step 2: 確認応答
            print("📝 Step 2: 新しいのを削除")
            result2 = await self.send_message("新しいのを削除")
            
            if "error" in result2:
                print(f"❌ Step 2エラー: {result2['error']}")
                return False
            
            response2 = result2.get("response", "")
            print(f"✅ Step 2レスポンス: {response2[:100]}...")
            
            # タスクチェーンが継続されたかチェック
            if "献立" in response2 or "レシピ" in response2:
                print("✅ タスクチェーンが継続されました")
                return True
            else:
                print("⚠️ タスクチェーンが継続されませんでした")
                return False
        else:
            print("⚠️ 確認プロセスがトリガーされませんでした")
            return False
    
    async def test_error_handling(self):
        """エラーハンドリングのテスト"""
        print("🧪 エラーハンドリングテスト開始")
        
        result = await self.send_message("存在しないアイテムを削除して")
        
        if "error" in result:
            print(f"❌ エラー: {result['error']}")
            return False
        
        response = result.get("response", "")
        print(f"✅ レスポンス: {response[:100]}...")
        
        # ユーザーフレンドリーなエラーメッセージかチェック
        if "申し訳ありません" in response and "認証エラー" not in response:
            print("✅ ユーザーフレンドリーなエラーメッセージ")
            return True
        else:
            print("⚠️ エラーメッセージが改善されていません")
            return False

async def main():
    """メイン実行関数"""
    print("🚀 自動認証テスト開始")
    print("=" * 60)
    
    # サーバー接続確認
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            if response.status_code == 200:
                print("✅ サーバー接続確認完了")
            else:
                print("❌ サーバーが応答しません")
                return
    except Exception as e:
        print(f"❌ サーバー接続エラー: {str(e)}")
        return
    
    # テスト実行
    tester = AutoAuthTester()
    
    # 認証トークン取得
    auth_token = await tester.get_auth_token()
    if not auth_token:
        print("❌ 認証に失敗しました")
        return
    
    # テスト実行
    test_results = []
    
    # 確認プロセステスト
    result1 = await tester.test_confirmation_flow()
    test_results.append(result1)
    
    # エラーハンドリングテスト
    result2 = await tester.test_error_handling()
    test_results.append(result2)
    
    # 結果表示
    print("\n" + "=" * 60)
    success_count = sum(test_results)
    total_count = len(test_results)
    success_rate = (success_count / total_count) * 100
    
    print(f"📊 テスト結果: {success_count}/{total_count} 成功")
    print(f"📈 成功率: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🎉 全てのテストが成功しました！")
    else:
        print("⚠️ 一部のテストが失敗しました")

if __name__ == "__main__":
    asyncio.run(main())
