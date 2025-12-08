import os
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant
from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent
from qdrant_client import QdrantClient

from langchain.agents.middleware import SummarizationMiddleware
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.runnables import RunnableConfig

from dataclasses import dataclass

from langgraph.store.memory import InMemoryStore

import psycopg
from starlette.responses import StreamingResponse, Response
from icecream import ic

store = InMemoryStore()

from RAG.schema import (
    UserInfo,
)

@dataclass
class Context:
    user_id: str


@tool
def save_user_info(user_info: UserInfo, runtime: ToolRuntime[Context]) -> str:
    """
    Lưu/ cập nhật long-term memory y tế của user.
    LLM có thể truyền 1 hoặc nhiều phần:
    - profile
    - lifestyle
    - measurement_summary
    - preferences
    """
    store = runtime.store
    user_id = runtime.context.user_id

    # Namespace & key cho health memory của user
    namespace = (user_id, "health")
    key = "health_memory"

    # Lấy giá trị cũ (nếu đã có) để merge
    old = store.get(namespace, key)
    old_value = old.value if old else {}

    # Merge: chỉ overwrite những field có trong user_info
    new_value = {**old_value}
    for field in ("profile", "lifestyle", "measurement_summary", "preferences"):
        if field in user_info and user_info[field] is not None:
            new_value[field] = user_info[field]

    store.put(namespace, key, new_value)

    return f"Successfully saved health memory for user {user_id}."

@tool
def get_user_info(runtime: ToolRuntime[Context]) -> str:
    """
    Lấy full long-term memory y tế của user:
    - profile
    - lifestyle
    - measurement_summary
    - preferences
    """
    store = runtime.store
    user_id = runtime.context.user_id

    namespace = (user_id, "health")
    key = "health_memory"

    user_info = store.get(namespace, key)
    if not user_info:
        return f"No health memory found for user {user_id}."

    return f"Health memory for {user_id}: {user_info.value}"


class AgentRAG:
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

        self.model = ChatOpenAI(
            model=model_name,
            base_url=base_url,
            api_key="dummy",  # vLLM không cần key
        )

        # ------------------------------
        # 3️⃣ Tool retrieve_context
        # ------------------------------
        self.tools = [self._create_retrieve_tool(), save_user_info, get_user_info]

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
                messages_to_keep=8, 
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
            store = store,
            context_schema=Context,
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
    def predict(self, query: str, user_id: str, thread_id: str = "unknown") -> StreamingResponse:
        from langchain_core.messages import HumanMessage
        
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        
        def token_gen():
            # Stream the agent and collect tokens
            for token, metadata in self.agent.stream(
                {"messages": [HumanMessage(content=query)]},
                config,
                stream_mode='messages',
                context =Context(user_id=user_id)
            ):
                # Yield AI response tokens
                if metadata.get('langgraph_node') == 'model':
                    if token.content_blocks and token.content_blocks[0]['type'] == 'text':
                        yield token.content_blocks[0]['text']

        return StreamingResponse(token_gen(), media_type="application/text; charset=utf-8")
