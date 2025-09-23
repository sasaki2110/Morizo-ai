"""
CORS設定
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI):
    """CORS設定を適用"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 本番環境では適切なドメインに制限
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
