import os
import getpass
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http import models


# ===============================
# 1️⃣ Nhập API key và khởi tạo embeddings
# ===============================
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "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"

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")


# ===============================
# 2️⃣ Load tài liệu PDF
# ===============================
file_path = "/workspace/competitions/Sly/Chatbot_HyperTension/data/1.pdf"
loader = PyPDFLoader(file_path)

docs = loader.load()
print(f"📘 Loaded {len(docs)} documents from PDF.")


# ===============================
# 3️⃣ Chia nhỏ văn bản thành các đoạn (chunking)
# ===============================
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    add_start_index=True,
)

all_splits = text_splitter.split_documents(docs)
print(f"✂️ Split into {len(all_splits)} sub-documents.")


# ===============================
# 4️⃣ Kết nối đến Qdrant
# ===============================
# ⚙️ Qdrant có thể chạy local hoặc cloud
# Nếu bạn đang chạy Qdrant bằng Docker trên localhost:
# docker run -p 6333:6333 qdrant/qdrant

QDRANT_URL = "http://localhost:3636"
COLLECTION_NAME = "hypertension_docs"

client = QdrantClient(url=QDRANT_URL)

# ===============================
# 5️⃣ Tạo vectorstore Qdrant
# ===============================




vector_store = Qdrant(
    client=client,
    collection_name=COLLECTION_NAME,
    embeddings=embeddings,
)

# ===============================
# 6️⃣ Thêm tài liệu vào Qdrant
# ===============================
print("🚀 Uploading documents into Qdrant...")
ids = vector_store.add_documents(documents=all_splits)
print(f"✅ Added {len(ids)} chunks into collection '{COLLECTION_NAME}'")
print("🔹 Sample document IDs:", ids[:3])
