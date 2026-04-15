# TravelHelper AI ✈️

一款基于 RAG (检索增强生成) 技术的全栈 AI 旅游助手。本应用专为 AI 开发岗位面试演示设计，集成了旅游规划、美图摄影指导与全端自适应 UI。

## ✨ 技术亮点

- **RAG 架构**: 联动 **ChromaDB** 与 **LangChain**，实现针对性摄影知识（如 Pocket 3/相机参数）的精准检索。
- **混合模型**: 采用 **OpenAI `text-embedding-3-small`** 进行语义向量化，由 **阿里云通义千问 (Qwen-Plus)** 提供高质量逻辑回复。
- **现代化 UI/UX**: 使用 **Vue 3 + Vite + TypeScript** 打造沉浸式毛玻璃视觉风格，支持 Markdown 渲染。
- **云原生部署**: 全链路 **Docker** 容器化配置，支持一键部署至阿里云等主流云平台。

## 🛠️ 技术栈

- **Frontend**: Vue 3, Vite, TypeScript, Lucide Icons, Marked
- **Backend**: Python FastAPI, LangChain, Pydantic
- **Vector DB**: ChromaDB
- **LLM/Embedding**: Aliyun Qwen, OpenAI Embedding
- **Infrastructure**: Docker, Docker Compose

## 🚀 快速启动

### 1. 配置环境变量
在 `backend/` 目录下创建 `.env` 文件（参考 `.env.example`）：
```bash
DASHSCOPE_API_KEY=你的阿里云Key
OPENAI_API_KEY=你的OpenAI Key (用于Embedding)
```

### 2. 初始化知识库 (推荐)
```bash
cd backend
pip install -r requirements.txt
python -m app.core.init_db
```

### 3. 一键启动 (Docker)
在项目根目录下运行：
```bash
docker-compose up --build
```
- 前端地址: `http://localhost:80`
- 后端地址: `http://localhost:8000`

---

## 📷 核心功能演示建议

在面试现场，你可以尝试提问以下问题，展示 RAG 的威力：
1. **“我要在北京故宫拍红墙人像，Pocket 3 应该怎么设置？”** (展示特定器材检索能力)
2. **“推荐一些北京地道美食和胡同游玩路线。”** (展示综合规划能力)
