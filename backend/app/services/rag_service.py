import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatTongyi
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain.chains import RetrievalQA

load_dotenv()

class RAGService:
    def __init__(self):
        # 1. 初始化 Embedding 模型 (OpenAI text-embedding-3-small)
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # 2. 初始化持久化向量库
        self.db_path = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
        self.vector_db = Chroma(
            persist_directory=self.db_path,
            embedding_function=self.embeddings
        )
        
        # 3. 初始化 LLM (阿里云通义千问)
        self.llm = ChatTongyi(
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
            model_name="qwen-plus"
        )

    def add_documents(self, texts: list[str], metadata: list[dict] = None):
        """将文本数据添加到向量库"""
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = [Document(page_content=t, metadata=metadata[i] if metadata else {}) for i, t in enumerate(texts)]
        chunks = text_splitter.split_documents(docs)
        self.vector_db.add_documents(chunks)
        self.vector_db.persist()

    async def get_travel_advice(self, query: str, location: str = "北京"):
        """获取综合旅游与摄影建议"""
        # 构造检索器
        retriever = self.vector_db.as_retriever(search_kwargs={"k": 3})
        
        # 定义 Prompt 模板 - 面试亮点：针对摄影参数的结构化 Prompt
        template = """你是一位专业的私人旅游管家和摄影师。
基于以下参考信息，为用户提供关于 {location} 的针对性建议。

参考信息:
{context}

用户问题: {question}

回答要求:
1. 风格亲切且专业。
2. 包含具体的推荐方案（美食/住宿/路线）。
3. **特别重点**：提供具体的摄影建议。包括：
   - 构图思路（如：三分法、引导线）。
   - 拍摄设备设置（针对 iPhone/Android/DJI Pocket/相机）。
   - 推荐的拍摄参数（光圈、快门、ISO 等）。

请以 Markdown 格式回复。
"""
        prompt = ChatPromptTemplate.from_template(template)
        
        # 构造 QA Chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt}
        )
        
        # 执行检索生成
        response = await qa_chain.ainvoke({"query": query, "location": location})
        return response["result"]

# 单例模式
rag_service = RAGService()
