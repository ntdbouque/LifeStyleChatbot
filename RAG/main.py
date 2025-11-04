import os
from langchain_ollama import ChatOllama
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant
from langchain.tools import tool
from langchain.agents import create_agent
from qdrant_client import QdrantClient

from langchain.agents.middleware import SummarizationMiddleware
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.runnables import RunnableConfig

import psycopg
from starlette.responses import StreamingResponse, Response
from icecream import ic

class AgentRAGOllama:
    """
    Agent RAG dùng Ollama (ví dụ: mistral) + Qdrant + PostgreSQL checkpointer.
    Có SummarizationMiddleware để tự tóm tắt khi hội thoại dài.
    """

    def __init__(
        self,
        model_name: str,
        qdrant_url: str,
        collection_name: str,
        embedding_model: str,
        base_url: str,
        postgres_uri: str,
    ):
        # ------------------------------
        # 1️⃣ Embedding & Vector store (Qdrant)
        # ------------------------------
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.qdrant_client = QdrantClient(url=qdrant_url)
        self.vector_store = Qdrant(
            client=self.qdrant_client,
            collection_name=collection_name,
            embeddings=self.embeddings,
        )

        # ------------------------------
        # 2️⃣ Model Ollama
        # ------------------------------
        self.model = ChatOllama(
            model=model_name,
            temperature=0.7,
            base_url=base_url,
        )

        # ------------------------------
        # 3️⃣ Tool retrieve_context
        # ------------------------------
        self.tools = [self._create_retrieve_tool()]

        # ------------------------------
        # 4️⃣ PostgreSQL checkpointer
        # ------------------------------
        # QUAN TRỌNG: autocommit=True để PostgresSaver tự động commit checkpoints
        conn = psycopg.connect(
            postgres_uri,
            autocommit=True,  # Bắt buộc cho checkpointer
        )

        self.checkpointer = PostgresSaver(conn)
        self.checkpointer.setup()  # Tạo tables nếu chưa có

        # ------------------------------
        # 5️⃣ Middleware: Summarization
        # ------------------------------
        self.middleware = [
            SummarizationMiddleware(
                model=self.model,
                max_tokens_before_summary=2500,  
                messages_to_keep=8,  # giữ lại 20 tin gần nhất
            )
        ]

        # ------------------------------
        # 6️⃣ Prompt hệ thống & Tạo agent
        # ------------------------------
        self.system_prompt = (
        "You have access to a tool that retrieves context from a high blood pressure documents. "
        "Use the tool to help answer user queries."
        )

        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.system_prompt,
            middleware=self.middleware,
            checkpointer=self.checkpointer,
        )

    # ------------------------------
    # 🧩 Tool: Retrieval từ Qdrant
    # ------------------------------
    def _create_retrieve_tool(self):
        @tool(response_format="content_and_artifact")
        def retrieve_context(query: str):
            """Retrieve information to help answer a query."""
            retrieved_docs = self.vector_store.similarity_search(query, k=3)
            serialized = "\n\n".join(
                f"Source: {doc.metadata}\nContent: {doc.page_content}"
                for doc in retrieved_docs
            )
            return serialized, retrieved_docs

        return retrieve_context

    # ------------------------------
    # 🚀 Gửi truy vấn (giữ state theo thread_id)
    # ------------------------------
    def predict(self, query: str, thread_id: str = "1") -> StreamingResponse:
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

        return self.agent.invoke({"messages": [{"role": "user", "content": query}]}, config)                   