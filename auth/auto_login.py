"""
自動ログイン機能
環境変数からユーザーIDとパスワードを読み取り、Supabaseに自動ログイン
"""

import logging
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Optional, Dict, Any

# .envファイルを読み込み
load_dotenv()

logger = logging.getLogger('morizo_ai.auth.auto_login')


class AutoLoginManager:
    """自動ログインマネージャー"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.email = os.getenv("SUPABASE_EMAIL")
        self.password = os.getenv("SUPABASE_PASSWORD")
        
        if not all([self.supabase_url, self.supabase_key, self.email, self.password]):
            raise ValueError("必要な環境変数が設定されていません: SUPABASE_URL, SUPABASE_KEY, SUPABASE_EMAIL, SUPABASE_PASSWORD")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        self._cached_token: Optional[str] = None
    
    def login(self) -> str:
        """
        Supabaseに自動ログインしてトークンを取得
        
        Returns:
            str: 認証トークン
            
        Raises:
            Exception: ログインに失敗した場合
        """
        try:
            logger.info(f"🔐 [自動ログイン] ログイン開始: {self.email}")
            
            response = self.client.auth.sign_in_with_password({
                "email": self.email,
                "password": self.password
            })
            
            if response.user is None:
                raise Exception("ログインに失敗しました: ユーザー情報が取得できません")
            
            token = response.session.access_token
            self._cached_token = token
            
            logger.info(f"✅ [自動ログイン] ログイン成功: {response.user.email}")
            return token
            
        except Exception as e:
            logger.error(f"❌ [自動ログイン] ログイン失敗: {str(e)}")
            raise
    
    def get_token(self) -> str:
        """
        キャッシュされたトークンを取得、無効な場合は再ログイン
        
        Returns:
            str: 認証トークン
        """
        if self._cached_token:
            try:
                # トークンの有効性をチェック
                user = self.client.auth.get_user(self._cached_token)
                if user.user is not None:
                    logger.debug("🔐 [自動ログイン] キャッシュされたトークンを使用")
                    return self._cached_token
            except Exception:
                logger.debug("🔐 [自動ログイン] キャッシュされたトークンが無効、再ログイン")
        
        return self.login()
    
    def refresh_token(self) -> str:
        """
        トークンを強制的に更新
        
        Returns:
            str: 新しい認証トークン
        """
        logger.info("🔄 [自動ログイン] トークンを強制更新")
        self._cached_token = None
        return self.login()


# グローバルインスタンス
_auto_login_manager: Optional[AutoLoginManager] = None


def get_auto_login_manager() -> AutoLoginManager:
    """自動ログインマネージャーのシングルトンインスタンスを取得"""
    global _auto_login_manager
    
    if _auto_login_manager is None:
        _auto_login_manager = AutoLoginManager()
    
    return _auto_login_manager


def get_auto_token() -> str:
    """
    自動ログインでトークンを取得
    
    Returns:
        str: 認証トークン
    """
    manager = get_auto_login_manager()
    return manager.get_token()


def refresh_auto_token() -> str:
    """
    自動ログインでトークンを強制更新
    
    Returns:
        str: 新しい認証トークン
    """
    manager = get_auto_login_manager()
    return manager.refresh_token()
