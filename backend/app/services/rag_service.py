import os
import json
from dotenv import load_dotenv
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatTongyi
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

load_dotenv()

class RAGService:
    def __init__(self):
        self.embeddings = DashScopeEmbeddings(
            model="text-embedding-v2",
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
        )
        
        self.db_path = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
        self.vector_db = Chroma(
            persist_directory=self.db_path,
            embedding_function=self.embeddings
        )
        
        self.llm = ChatTongyi(
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
            model_name="qwen-plus",
            streaming=True  # 核心：开启 LLM 流式
        )

    def add_documents(self, texts: list[str], metadata: list[dict] = None):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = [Document(page_content=t, metadata=metadata[i] if metadata else {}) for i, t in enumerate(texts)]
        chunks = text_splitter.split_documents(docs)
        self.vector_db.add_documents(chunks)

    async def stream_travel_advice(self, query: str, location: str = "北京"):
        """流式获取建议"""
        retriever = self.vector_db.as_retriever(search_kwargs={"k": 3})
        
        system_prompt = (
            "你是一位专业的私人旅游管家和摄影师。基于以下参考信息，为用户提供关于 {location} 的针对性建议。\n\n"
            "{context}"
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        
        # 为了稳定流式输出，我们在这里直接调用 llm.astream
        # 先检索文档
        docs = await retriever.ainvoke(query)
        context = "\n".join([doc.page_content for doc in docs])
        
        # 填充 Prompt
        final_prompt = prompt.format(location=location, context=context, input=query)
        
        # 流式返回每一个 token
        async for chunk in self.llm.astream(final_prompt):
            content = chunk.content
            if content:
                # SSE 格式：data: 内容\n\n
                yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
        
        yield "data: [DONE]\n\n"

rag_service = RAGService()
