from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from app.schemas.chat_schema import ChatRequest
from app.services.rag_service import rag_service
from app.core.init_db import TRAVEL_KNOWLEDGE
import uvicorn

app = FastAPI(title="TravelHelper AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("正在检查向量数据库状态...")
    try:
        rag_service.add_documents(TRAVEL_KNOWLEDGE)
        print("知识库自动初始化完成！")
    except Exception as e:
        print(f"初始化说明: {e}")

@app.post("/api/v1/chat/stream")
async def stream_chat(request: ChatRequest):
    """SSE 流式对话接口"""
    return StreamingResponse(
        rag_service.stream_travel_advice(request.query, request.location),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
