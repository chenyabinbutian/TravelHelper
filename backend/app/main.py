from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from app.schemas.chat_schema import ChatRequest
from app.services.rag_service import rag_service
from app.core.constants import TRAVEL_KNOWLEDGE
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
    print("正在初始化向量数据库...")
    try:
        # 直接调用实例方法，此时路径已经彻底拉通
        rag_service.add_documents(TRAVEL_KNOWLEDGE)
        print("✅ 知识库加载成功！")
    except Exception as e:
        print(f"❌ 初始化异常: {e}")

@app.post("/api/v1/chat/stream")
async def stream_chat(request: ChatRequest):
    return StreamingResponse(
        rag_service.stream_travel_advice(request.query, request.location, request.history),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
