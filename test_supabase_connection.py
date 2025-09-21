#!/usr/bin/env python3
"""
Supabase接続テストスクリプト
基本的な接続とCRUD操作をテスト
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

def test_basic_connection():
    """基本的な接続テスト（認証なし）"""
    print("🔍 Supabase基本接続テスト開始...")
    
    # Supabaseクライアント作成
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase設定が不足しています")
        print(f"SUPABASE_URL: {'設定済み' if supabase_url else '未設定'}")
        print(f"SUPABASE_KEY: {'設定済み' if supabase_key else '未設定'}")
        return False
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabaseクライアント作成成功")
        return True
        
    except Exception as e:
        print(f"❌ Supabase接続エラー: {str(e)}")
        return False

def test_authenticated_connection(token: str):
    """認証付き接続テスト"""
    print(f"\n🔐 認証付き接続テスト開始...")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    try:
        # 認証トークン付きでクライアント作成
        supabase: Client = create_client(supabase_url, supabase_key)
        
        print("✅ 認証付きSupabaseクライアント作成成功")
        
        # ユーザー情報の取得（直接トークンを渡す）
        user = supabase.auth.get_user(token)
        print(f"👤 ユーザーID: {user.user.id}")
        print(f"📧 メール: {user.user.email}")
        
        return True, user.user.id
        
    except Exception as e:
        print(f"❌ 認証付き接続エラー: {str(e)}")
        return False, None

def test_basic_crud(user_id: str, token: str):
    """基本的なCRUD操作テスト"""
    print(f"\n📝 基本CRUD操作テスト開始...")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    try:
        # 認証トークン付きでクライアント作成
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # 認証トークンをヘッダーに直接設定
        supabase.postgrest.auth(token)
        
        # テスト用データ
        test_item = {
            "user_id": user_id,
            "item_name": "テスト牛乳",
            "quantity": 1.5,
            "unit": "L",
            "storage_location": "冷蔵庫"
        }
        
        # CREATE (Insert)
        print("1. INSERT テスト...")
        result = supabase.table("inventory").insert(test_item).execute()
        if result.data:
            item_id = result.data[0]["id"]
            print(f"✅ INSERT成功: ID = {item_id}")
        else:
            print("❌ INSERT失敗")
            return False
        
        # READ (Select)
        print("2. SELECT テスト...")
        result = supabase.table("inventory").select("*").eq("id", item_id).execute()
        if result.data:
            print(f"✅ SELECT成功: {result.data[0]['item_name']}")
        else:
            print("❌ SELECT失敗")
            return False
        
        # UPDATE
        print("3. UPDATE テスト...")
        result = supabase.table("inventory").update({"quantity": 2.0}).eq("id", item_id).execute()
        if result.data:
            print(f"✅ UPDATE成功: quantity = {result.data[0]['quantity']}")
        else:
            print("❌ UPDATE失敗")
            return False
        
        # DELETE
        print("4. DELETE テスト...")
        result = supabase.table("inventory").delete().eq("id", item_id).execute()
        if result.data:
            print("✅ DELETE成功")
        else:
            print("❌ DELETE失敗")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ CRUD操作エラー: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Supabase接続テスト開始\n")
    
    # Phase 1: 基本接続テスト
    if not test_basic_connection():
        print("\n❌ 基本接続テスト失敗")
        exit(1)
    
    print("\n" + "="*50)
    print("認証トークンが必要です")
    print("Next.js側でログイン後、トークンを取得してください")
    print("例: curl -H 'Authorization: Bearer <token>' http://localhost:8000/chat")
    print("="*50)
    
    # 認証トークンの入力待ち
    token = input("\n認証トークンを入力してください: ").strip()
    
    if not token:
        print("❌ トークンが入力されていません")
        exit(1)
    
    # Phase 2: 認証付き接続テスト
    success, user_id = test_authenticated_connection(token)
    if not success:
        print("\n❌ 認証付き接続テスト失敗")
        exit(1)
    
    # Phase 3: CRUD操作テスト
    if not test_basic_crud(user_id, token):
        print("\n❌ CRUD操作テスト失敗")
        exit(1)
    
    print("\n🎉 すべてのテストが成功しました！")
    print("Supabase接続とCRUD操作が正常に動作しています。")