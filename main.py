from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import os
from typing import Optional
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

app = FastAPI(title="Morizo AI", description="Smart Pantry AI Agent")

# OpenAI API設定
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# サーバー起動時にモデル情報を表示
print(f"🚀 Morizo AI Server starting...")
print(f"📋 Using OpenAI Model: {model_name}")
print(f"🔑 API Key configured: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    success: bool
    model_used: str

@app.get("/")
async def root():
    return {"message": "Morizo AI is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Morizo AI"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    ユーザーのメッセージをLLMに送信し、レスポンスを返す
    """
    try:
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # OpenAI APIにリクエストを送信
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # デフォルトはgpt-4o-mini
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "あなたはMorizoという名前のスマートパントリーアシスタントです。食材管理とレシピ提案を手伝います。日本語で親しみやすく回答してください。"},
                {"role": "user", "content": request.message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        actual_model = response.model  # 実際に使用されたモデル名を取得
        
        return ChatResponse(
            response=ai_response,
            success=True,
            model_used=actual_model
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
