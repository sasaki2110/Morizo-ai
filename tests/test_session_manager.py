"""
Morizo AI - セッション管理システムテスト

セッション管理機能の動作確認とテスト
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
import time


def show_token_help():
    """トークン取得方法のヘルプを表示"""
    print("\n" + "="*60)
    print("🔑 Supabase Access Token の取得方法")
    print("="*60)
    print("1. Next.js側でブラウザのコンソールを開く")
    print("2. 以下のコマンドを実行:")
    print()
    print("   const { data: { session } } = await supabase.auth.getSession();")
    print("   console.log('Access Token:', session?.access_token);")
    print()
    print("3. コンソールに表示されたトークンをコピー")
    print("4. このプログラムに貼り付け")
    print("="*60)
    print()


async def test_session_endpoints(test_token: str):
    """セッション管理エンドポイントのテスト"""
    base_url = "http://localhost:8000"
    
    headers = {
        "Authorization": f"Bearer {test_token}",
        "Content-Type": "application/json"
    }
    
    print("🧪 セッション管理エンドポイントテスト開始")
    
    try:
        # 1. セッション状態確認
        print("\n1️⃣ セッション状態確認")
        async with httpx.AsyncClient(timeout=30.0) as client:  # 30秒のタイムアウト
            response = await client.get(f"{base_url}/session/status", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ セッション状態取得成功")
                print(f"   - セッションID: {data['session_info']['session_id']}")
                print(f"   - 継続時間: {data['session_info']['session_duration_minutes']:.1f}分")
                print(f"   - 操作履歴: {data['session_info']['operation_history_count']}件")
            elif response.status_code == 401:
                print(f"❌ 認証エラー: トークンが無効です")
                print(f"   - トークンの有効期限を確認してください")
                print(f"   - Next.js側で新しいトークンを取得してください")
                return
            else:
                print(f"❌ セッション状態取得失敗: {response.status_code}")
                print(f"   {response.text}")
        
        # 2. チャットで操作履歴を追加
        print("\n2️⃣ チャットで操作履歴を追加")
        chat_data = {
            "message": "在庫を教えて"
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:  # 60秒のタイムアウト
            response = await client.post(f"{base_url}/chat", headers=headers, json=chat_data)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ チャット成功: {data['response'][:50]}...")
            else:
                print(f"❌ チャット失敗: {response.status_code}")
                print(f"   {response.text}")
        
        # 3. 再度セッション状態確認（履歴が増えているか）
        print("\n3️⃣ 操作後のセッション状態確認")
        async with httpx.AsyncClient(timeout=30.0) as client:  # 30秒のタイムアウト
            response = await client.get(f"{base_url}/session/status", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ セッション状態取得成功")
                print(f"   - 操作履歴: {data['session_info']['operation_history_count']}件")
                if data['recent_operations']:
                    print(f"   - 最新操作: {data['recent_operations'][-1]['operation']}")
            else:
                print(f"❌ セッション状態取得失敗: {response.status_code}")
        
        # 4. 操作履歴のみクリア
        print("\n4️⃣ 操作履歴のみクリア")
        async with httpx.AsyncClient(timeout=30.0) as client:  # 30秒のタイムアウト
            response = await client.post(f"{base_url}/session/clear-history", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 履歴クリア成功: {data['message']}")
            else:
                print(f"❌ 履歴クリア失敗: {response.status_code}")
        
        # 5. セッション全体をクリア
        print("\n5️⃣ セッション全体をクリア")
        async with httpx.AsyncClient(timeout=30.0) as client:  # 30秒のタイムアウト
            response = await client.post(f"{base_url}/session/clear", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ セッションクリア成功: {data['message']}")
            else:
                print(f"❌ セッションクリア失敗: {response.status_code}")
        
        # 6. 全セッション情報取得（開発・テスト用）
        print("\n6️⃣ 全セッション情報取得")
        async with httpx.AsyncClient(timeout=30.0) as client:  # 30秒のタイムアウト
            response = await client.get(f"{base_url}/session/all", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 全セッション情報取得成功")
                print(f"   - 総セッション数: {data['sessions_info']['total_sessions']}")
            else:
                print(f"❌ 全セッション情報取得失敗: {response.status_code}")
        
        # 7. テスト用在庫クリア（牛乳を削除）
        print("\n7️⃣ テスト用在庫クリア")
        async with httpx.AsyncClient(timeout=30.0) as client:  # 30秒のタイムアウト
            response = await client.post(f"{base_url}/test/clear-inventory", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ テスト用在庫クリア成功: {data['message']}")
            else:
                print(f"❌ テスト用在庫クリア失敗: {response.status_code}")
                print(f"   {response.text}")
        
        print("\n🎉 セッション管理エンドポイントテスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {str(e)}")
        import traceback
        print(f"詳細エラー: {traceback.format_exc()}")


async def test_session_manager_direct():
    """セッション管理システムの直接テスト"""
    print("\n🧪 セッション管理システム直接テスト開始")
    
    try:
        from session_manager import session_manager, SessionContext
        
        # テストユーザー
        test_user = "test-user-direct-123"
        
        # 1. 新規セッション作成
        print("\n1️⃣ 新規セッション作成")
        session = session_manager.get_or_create_session(test_user)
        print(f"✅ セッション作成: {session.session_id}")
        
        # 2. 操作履歴の追加（10件を超えるテスト）
        print("\n2️⃣ 操作履歴の追加（上限テスト）")
        for i in range(12):  # 12件追加（上限10件を超える）
            session.add_operation("TEST_OPERATION", {
                "test_id": i,
                "timestamp": datetime.now().isoformat(),
                "description": f"テスト操作 {i+1}"
            })
        
        print(f"📝 操作履歴: {len(session.operation_history)}件")
        
        # 3. セッション状態確認
        print("\n3️⃣ セッション状態確認")
        status = session_manager.get_session_status(test_user)
        print(f"📊 セッション状態: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        # 4. タイムアウトテスト（30分後に期限切れ）
        print("\n4️⃣ タイムアウトテスト")
        # セッションの最終アクセス時間を30分前に設定
        session.last_activity = datetime.now() - timedelta(minutes=31)
        
        # 期限切れセッションのクリア
        session_manager.clear_expired_sessions()
        
        # セッションがクリアされているか確認
        if test_user not in session_manager.active_sessions:
            print("✅ タイムアウトセッションが正常にクリアされました")
        else:
            print("⚠️ タイムアウトセッションがクリアされていません")
        
        # 5. 全セッション情報
        print("\n5️⃣ 全セッション情報")
        all_info = session_manager.get_all_sessions_info()
        print(f"📋 全セッション情報: {json.dumps(all_info, indent=2, ensure_ascii=False)}")
        
        # 6. 全セッションクリア
        print("\n6️⃣ 全セッションクリア")
        session_manager.clear_all_sessions()
        print("✅ 全セッションをクリアしました")
        
        print("\n🎉 セッション管理システム直接テスト完了")
        
    except Exception as e:
        print(f"❌ 直接テストエラー: {str(e)}")


async def test_integration(test_token: str):
    """統合テスト: チャット + セッション管理"""
    print("\n🧪 統合テスト: チャット + セッション管理")
    
    base_url = "http://localhost:8000"
    
    headers = {
        "Authorization": f"Bearer {test_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # 複数のチャット操作を実行してセッション履歴を蓄積
        chat_messages = [
            "在庫を教えて",
            "牛乳を2本追加して",
            "在庫を確認して",
            "牛乳の数量を3本に変更して",
            "最新の牛乳の本数を3本に変えて",
            "在庫を教えて"
        ]
        
        for i, message in enumerate(chat_messages, 1):
            print(f"\n{i}️⃣ チャット操作: {message}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:  # 60秒のタイムアウト
                response = await client.post(f"{base_url}/chat", headers=headers, json={"message": message})
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ 成功: {data['response'][:50]}...")
                else:
                    print(f"❌ 失敗: {response.status_code}")
            
            # 各操作後にセッション状態を確認
            async with httpx.AsyncClient(timeout=30.0) as client:  # 30秒のタイムアウト
                response = await client.get(f"{base_url}/session/status", headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    print(f"   📱 セッション履歴: {data['session_info']['operation_history_count']}件")
        
        print("\n🎉 統合テスト完了")
        
    except Exception as e:
        print(f"❌ 統合テストエラー: {str(e)}")
        import traceback
        print(f"詳細エラー: {traceback.format_exc()}")


async def main():
    """メインテスト実行"""
    print("🚀 Morizo AI セッション管理システムテスト開始")
    
    # 1. 直接テスト
    await test_session_manager_direct()
    
    # 2. エンドポイントテスト（サーバーが起動している場合）
    print("\n" + "="*50)
    print("⚠️ エンドポイントテストは、サーバーが起動している場合のみ実行されます")
    print("   uvicorn main:app --reload --port 8000 でサーバーを起動してください")
    print("="*50)
    
    # サーバーが起動しているかチェック
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:  # 30秒のタイムアウト
            response = await client.get("http://localhost:8000/health", timeout=2.0)
            if response.status_code == 200:
                print("✅ サーバーが起動しています。エンドポイントテストを実行します。")
                
                # トークンを一度だけ入力
                show_token_help()
                test_token = input("Supabase Access Token を入力してください: ").strip()
                
                if not test_token:
                    print("❌ トークンが入力されませんでした。エンドポイントテストをスキップします。")
                else:
                    # トークンの簡単な検証
                    if len(test_token) < 50:
                        print("⚠️ トークンが短すぎるようです。正しいトークンか確認してください。")
                        continue_test = input("それでも続行しますか？ (y/N): ").strip().lower()
                        if continue_test != 'y':
                            print("❌ テストをスキップします。")
                            return
                    
                    await test_session_endpoints(test_token)
                    await test_integration(test_token)
            else:
                print("⚠️ サーバーが起動していません。エンドポイントテストをスキップします。")
    except Exception:
        print("⚠️ サーバーが起動していません。エンドポイントテストをスキップします。")
    
    print("\n🎉 全テスト完了")


if __name__ == "__main__":
    asyncio.run(main())
