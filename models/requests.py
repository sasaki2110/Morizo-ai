"""
Pydantic models for requests and responses
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any


class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    response: str
    success: bool
    model_used: str
    user_id: Optional[str] = None
    confirmation_required: Optional[bool] = False
    confirmation_context: Optional[Dict[str, Any]] = None
