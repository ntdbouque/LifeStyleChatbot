from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import Request


from .redis_client import get_cached_response, set_cached_response
from .logger import log_to_loki

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from RAG.main import AgentRAGOllama
from icecream import ic

from dotenv import load_dotenv
load_dotenv()

os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

from configs.configs import get_config

configs = get_config('./configs/configs.yaml')
app = FastAPI()

# Khởi tạo RAG Agent singleton (dùng chung cho tất cả requests)
rag_agent = AgentRAGOllama(
    model_name=configs.services.LLM.model_name,
    qdrant_url=configs.services.qdrant.URI,
    collection_name=configs.RAG.qdrant.collection_name,
    base_url=configs.services.ollama.URI,
    postgres_uri=configs.services.postgres.URI,
    embedding_model=configs.services.embed_model.model_name
)

@app.get('Welcome to our Homepage')
def welcome():
    return 'Hi'

@app.post("/chat")
async def chat_stream(req: Request):
    data = await req.json()
    query = data.get("message")
    user_id = data.get("user_id")
    response = rag_agent.predict(
        query=query,
        thread_id=user_id
    )
    return response