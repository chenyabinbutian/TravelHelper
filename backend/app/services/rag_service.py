import os
import json
from dotenv import load_dotenv
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatTongyi
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

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
            streaming=True
        )

    def add_documents(self, texts: list[str], metadata: list[dict] = None):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = [Document(page_content=t, metadata=metadata[i] if metadata else {}) for i, t in enumerate(texts)]
        chunks = text_splitter.split_documents(docs)
        self.vector_db.add_documents(chunks)

    async def stream_travel_advice(self, query: str, location: str = "北京"):
        retriever = self.vector_db.as_retriever(search_kwargs={"k": 3})
        docs = await retriever.ainvoke(query)
        context = "\n".join([doc.page_content for doc in docs])

        # 核心：引入极度严格的领域隔离逻辑
        system_prompt = """你是一个极度严谨的全球旅行咨询系统。为了确保用户体验，你必须执行严格的【领域隔离】策略。

### 🚫 禁止列表 (Negative Constraints)：
- 如果用户的问题属于【住宿】或【行程】，则回答中**严禁**出现任何关于“拍照”、“摄影”、“快门”、“感光度”、“Pocket”、“参数”的内容。
- 如果用户的问题属于【摄影】，则回答中**严禁**提供酒店推荐或路线规划。
- 禁止在回答中出现任何指令类字样（如“领域隔离”、“专问专答”）。

### ✅ 各领域格式规范：
1. 【行程规划】：必须表格化导出。
2. 【住宿推荐】：必须包含地图标记语法：[MAP_LOCATION: 名称 | 地址 | 搜索词]
3. 【摄影建议】：必须包含高清样图链接（https://loremflickr.com/800/450/{location},photography），并提供具体的参数表。

用户目前在：{location}
参考知识库: {context}
"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "用户提问: {input}"),
        ])
        
        final_prompt = prompt.format(location=location, context=context, input=query)
        
        async for chunk in self.llm.astream(final_prompt):
            content = chunk.content
            if content:
                yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
        
        yield "data: [DONE]\n\n"

rag_service = RAGService()
