import os
import json
from dotenv import load_dotenv
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

class RAGService:
    def __init__(self):
        self.embeddings = DashScopeEmbeddings(
            model="text-embedding-v2",
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
        )
        self.db_path = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.vector_db = Chroma(persist_directory=self.db_path, embedding_function=self.embeddings)
        self.llm = ChatTongyi(
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"), 
            model_name="qwen-plus", 
            streaming=True
        )

    def add_documents(self, texts: list[str], metadata: list[dict] = None):
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_core.documents import Document
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = [Document(page_content=t, metadata=metadata[i] if metadata else {}) for i, t in enumerate(texts)]
        self.vector_db.add_documents(text_splitter.split_documents(docs))

    def _format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    async def stream_travel_advice(self, query: str, location: str, history: list = []):
        retriever = self.vector_db.as_retriever(search_kwargs={"k": 3})

        qa_system_prompt = """你是一个高冷的、只看结果的全球旅行影像专家系统。你的每一个字都必须是核心干货。

### 🎯 专问专答执行标准：
- 场景一【行程交通】：两列复合表格。
- 场景二【摄影方案】：两列复合表格。
- 场景三【住宿推荐】：直奔主题 + [MAP_LOCATION...]

上下文: {context}"""

        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

        # 核心修复：改用最纯粹的消息列表处理
        chain = (
            RunnablePassthrough.assign(context=lambda x: self._format_docs(retriever.get_relevant_documents(x["input"])))
            | qa_prompt
            | self.llm
            | StrOutputParser()
        )

        # 兼容性处理：将历史记录转为通用 Tuple 格式
        chat_history = []
        for msg in history:
            role = msg.get('role') if isinstance(msg, dict) else msg.role
            content = msg.get('content') if isinstance(msg, dict) else msg.content
            # 使用 (role, content) 元组提高不同 LLM 的兼容性
            if role == "user": chat_history.append(("human", content))
            else: chat_history.append(("ai", content))

        try:
            # 执行流式调用
            async for chunk in chain.astream({"input": query, "chat_history": chat_history}):
                if chunk:
                    yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'content': f'AI ERROR: {str(e)}'}, ensure_ascii=False)}\n\n"
        
        yield "data: [DONE]\n\n"

rag_service = RAGService()
