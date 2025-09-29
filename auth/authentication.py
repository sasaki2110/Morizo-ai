"""
認証とセキュリティ機能
"""

import logging
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
import os

logger = logging.getLogger('morizo_ai.auth')


def mask_email(email: str) -> str:
    """メールアドレスをマスク"""
    if "@" not in email:
        return email
    
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "*" * (len(local) - 1)
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    
    return f"{masked_local}@{domain}"


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """
    Supabaseトークンを検証し、ユーザー情報を返す
    """
    logger.debug("🔍 [AUTH] 認証処理開始")
    
    # Supabase設定
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    logger.debug(f"🔍 [AUTH] Supabase設定確認: URL={supabase_url is not None}, KEY={supabase_key is not None}")
    
    if not supabase_url or not supabase_key:
        logger.error("❌ [AUTH] Supabase設定不備")
        raise HTTPException(
            status_code=500, 
            detail="Supabase not configured"
        )
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # トークンの前処理（角括弧の除去）
        raw_token = credentials.credentials
        if raw_token.startswith('[') and raw_token.endswith(']'):
            raw_token = raw_token[1:-1]
        
        # トークンを省略表示
        token_preview = f"{raw_token[:20]}...{raw_token[-20:]}" if len(raw_token) > 40 else raw_token
        logger.debug(f"🔍 [AUTH] Token received: {token_preview}")
        logger.debug(f"🔍 [AUTH] Token length: {len(raw_token)}")
        
        # トークンからユーザー情報を取得
        response = supabase.auth.get_user(raw_token)
        
        if response.user is None:
            print(f"❌ [ERROR] User is None in response")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )
        
        # メールアドレスをマスク
        email = response.user.email
        masked_email = mask_email(email)
        logger.info(f"✅ [SUCCESS] User authenticated: {masked_email}")
        
        # ユーザー情報とトークンを辞書で返す
        return {
            "user": response.user,
            "raw_token": raw_token
        }
    except Exception as e:
        logger.error(f"❌ [ERROR] Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )
