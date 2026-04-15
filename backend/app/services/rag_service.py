import os
import json
from dotenv import load_dotenv
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

load_dotenv()

class RAGService:
    def __init__(self):
        self.embeddings = DashScopeEmbeddings(
            model="text-embedding-v2",
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
        )
        self.db_path = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.vector_db = Chroma(persist_directory=self.db_path, embedding_function=self.embeddings)
        self.llm = ChatTongyi(dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"), model_name="qwen-plus", streaming=True)

    def add_documents(self, texts: list[str], metadata: list[dict] = None):
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_core.documents import Document
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = [Document(page_content=t, metadata=metadata[i] if metadata else {}) for i, t in enumerate(texts)]
        self.vector_db.add_documents(text_splitter.split_documents(docs))

    async def stream_travel_advice(self, query: str, location: str, history: list = []):
        retriever = self.vector_db.as_retriever(search_kwargs={"k": 3})

        qa_system_prompt = """你是一个高冷的、只看结果的全球旅行影像专家系统。你的每一个字都必须是核心干货。

### 🚨 绝对禁令：
1. **禁止开场白**：严禁废话。
2. **禁止状态复述**：直接回答。

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

        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)

        chat_history = []
        for msg in history:
            if hasattr(msg, 'role'):
                role = msg.role
                content = msg.content
            else:
                role = msg.get('role')
                content = msg.get('content')
            
            if role == "user": chat_history.append(HumanMessage(content=content))
            else: chat_history.append(AIMessage(content=content))

        # 增加异常处理防止挂死
        try:
            async for chunk in rag_chain.astream({"input": query, "chat_history": chat_history, "location": location}):
                if "answer" in chunk:
                    # 关键修复：确保 JSON 序列化正确
                    text = chunk['answer']
                    yield f"data: {json.dumps({'content': text}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'content': f'发生错误: {str(e)}'}, ensure_ascii=False)}\n\n"
        
        yield "data: [DONE]\n\n"

rag_service = RAGService()
