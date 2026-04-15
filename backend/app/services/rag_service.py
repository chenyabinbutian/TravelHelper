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

        # 核心：执行“静默直达”策略
        qa_system_prompt = """你是一个高冷的、只看结果的全球旅行影像专家系统。你的每一个字都必须是核心干货。

### 🚨 绝对禁令 (Negative Constraints)：
1. **禁止开场白**：严禁说“好的”、“已收到”、“我已锁定设备”、“以下是为您生成的计划”等任何废话。
2. **禁止状态复述**：不要向用户确认你已知的事实，直接开始输出回答。
3. **禁止互动辞令**：不需要“祝您旅行愉快”、“希望能帮到你”等任何礼貌用语。

### 🎯 专问专答执行标准：
- 场景一【行程交通】：首行直接输出 Markdown 表格。
- 场景二【摄影方案】：首行直接输出参数列表表格，并在最后附上一张对应地点的样图 ![photo](https://loremflickr.com/800/450/{{location}},scenery)。
- 场景三【住宿推荐】：首行直接开始介绍酒店，并附带 [MAP_LOCATION: 名称 | 地址 | 搜索词]

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
            if msg.role == "user": chat_history.append(HumanMessage(content=msg.content))
            else: chat_history.append(AIMessage(content=msg.content))

        # 流式输出
        async for chunk in rag_chain.astream({"input": query, "chat_history": chat_history, "location": location}):
            if "answer" in chunk:
                yield f"data: {json.dumps({'content': chunk['answer']}, ensure_ascii=False)}\n\n"
        
        yield "data: [DONE]\n\n"

rag_service = RAGService()
