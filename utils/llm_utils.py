"""
LLM関連のユーティリティ関数
"""

import os
import logging
from openai import OpenAI

logger = logging.getLogger('morizo_ai.llm_utils')


async def get_llm_response(message: str, current_user) -> str:
    """LLMからレスポンスを取得"""
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "あなたはMorizoという名前のスマートパントリーアシスタントです。食材管理とレシピ提案を手伝います。日本語で親しみやすく回答してください。"},
                {"role": "user", "content": message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"❌ [ERROR] LLM response error: {str(e)}")
        return f"申し訳ありません。AI応答でエラーが発生しました: {str(e)}"
