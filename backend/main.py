from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import Request, UploadFile, File
import importlib
from fastapi import Request
import os
import base64
import binascii
import tempfile



import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from RAG.main import AgentRAG
from OpenAI.DallE2 import image_captioner


# Import whisper module (name has hyphen so use importlib)
whisper_module = importlib.import_module('OpenAI.whisper-1')
transcribe_vietnamese_audio = whisper_module.transcribe_vietnamese_audio
from icecream import ic

import psycopg
import msgpack
from typing import List, Dict, Any, Optional


from dotenv import load_dotenv
load_dotenv()

os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

from configs.configs import get_config

configs = get_config('./configs/configs.yaml')
app = FastAPI()

# ======== CORS Configuration ========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (change to specific URLs in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo RAG Agent 
rag_agent = AgentRAG(
    model_name=configs.services.vllm.model_name,
    qdrant_url=configs.services.qdrant.URI,
    collection_name=configs.RAG.qdrant.collection_name,
    base_url=configs.services.vllm.URI,
    postgres_uri=configs.services.postgres.URI,
    embedding_model=configs.services.embed_model.model_name
)

# ======== Models ========
class ChatRequest(BaseModel):
    message: str
    user_id: str
    session_id: str
    image: Optional[str] = None

class TranscribeRequest(BaseModel):
    audio: str  # base64 encoded audio

# ======== Health Check ========
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# ======== Chat Endpoint ========
@app.post("/chat")
async def chat(request: ChatRequest):
    message = request.message
    image = request.image

    # If image provided, get caption
    image_caption = None
    if image is not None:
        image_caption = image_captioner(image)
    
    # Build prompt with image caption if available
    full_message = message
    if image_caption:
        full_message = f"{message}\n\nImage description: {image_caption}"
    
    # Call RAG agent
    response = rag_agent.predict(user_id = request.user_id, thread_id = request.session_id, query= full_message)
    
    return response

@app.post("/transcribe")
async def transcribe(request: Request):
    body = await request.json()

    b64 = body.get("audio")
    if not b64:
        return {"success": False, "error": "Missing field: audio"}

    # Nếu client gửi kiểu: "data:audio/mp3;base64,AAA..."
    if "," in b64:
        b64 = b64.split(",", 1)[1]

    # Decode base64 có validate
    try:
        file_bytes = base64.b64decode(b64, validate=True)
    except binascii.Error as e:
        return {"success": False, "error": f"Invalid base64 audio: {e}"}

    if len(file_bytes) < 100:
        return {"success": False, "error": "Audio data too short or invalid"}

    # Debug: log header bytes
    ic(f"File header (hex): {file_bytes[:16].hex()}")

    # Đoán ext từ magic bytes
    # Search for ftyp which indicates MP4/M4A (can be offset)
    header4 = file_bytes[:4]
    header3 = file_bytes[:3]
    header2 = file_bytes[:2]
    
    # Check if ftyp exists anywhere in first 100 bytes (MP4/M4A can have offset)
    ftyp_index = file_bytes.find(b'ftyp')
    
    ext = ".wav"
    # ID3 tag (mp3)
    if header3 == b"ID3":
        ext = ".mp3"
    # MP3 frame (0xFF Ex)
    elif len(header2) >= 2 and header2[0] == 0xFF and (header2[1] & 0xE0) == 0xE0:
        ext = ".mp3"
    # M4A/MP4 - ftyp can be at offset
    elif ftyp_index >= 0:
        # Check what type of M4A (M4A, mp42, etc)
        if ftyp_index + 8 < len(file_bytes):
            brand = file_bytes[ftyp_index+4:ftyp_index+8]
            if b'M4A' in brand or b'mp42' in brand or b'isom' in brand:
                ext = ".m4a"
            else:
                ext = ".m4a"  # Default to m4a for ftyp
        else:
            ext = ".m4a"
    elif header4 == b"RIFF":
        ext = ".wav"
    # WebM format
    elif header4 == b"\x1aE\xdf\xa3":
        ext = ".webm"
    # OGG format
    elif header4 == b"OggS":
        ext = ".ogg"
    # FLAC format
    elif header4 == b"fLaC":
        ext = ".flac"
    # nếu không nhận diện được thì mặc định .m4a (common for mobile)
    else:
        ext = ".m4a"

    ic(f"Detected audio format: {ext}, header4={header4.hex()}, ftyp_index={ftyp_index}")

    # Tạo file tạm với đuôi tương ứng
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        temp_file_path = tmp.name
        tmp.write(file_bytes)

    # Gọi whisper
    try:
        text = transcribe_vietnamese_audio(temp_file_path)
    except Exception as e:
        ic(f"Transcribe error: {e}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return {"success": False, "error": f"Transcribe failed: {str(e)}"}

    # Dọn file tạm
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)

    return {
        "success": True,
        "text": text,
        "format": ext[1:]  # Return format without dot
    }


# ======== Helper: Extract content from LangChain msgpack blob ========
def extract_message_content(ext_type_data: bytes) -> tuple:
    """
    Extract content and role from LangChain serialized message (msgpack ExtType code 5)
    Returns: (role, content) tuple
    """
    try:
        # Determine message type
        if b'HumanMessage' in ext_type_data:
            role = "user"
        elif b'AIMessage' in ext_type_data:
            role = "bot"
        else:
            role = "unknown"
        
        # Extract content - it appears after the "content" marker (msgpack key)
        # \xa7 is msgpack fixstr of length 7 for the key "content"
        content_start = ext_type_data.find(b'\xa7content')
        if content_start == -1:
            return role, ""
        
        content_start += 8  # Skip past "\xa7content"
        
        # Next byte indicates the msgpack type and length
        if content_start >= len(ext_type_data):
            return role, ""
        
        next_byte = ext_type_data[content_start]
        
        # Handle different msgpack string formats
        if next_byte >= 0xa0 and next_byte <= 0xbf:  # fixstr (length in lower 5 bits)
            length = next_byte - 0xa0
            content = ext_type_data[content_start+1:content_start+1+length].decode('utf-8', errors='ignore')
        elif next_byte == 0xd9:  # str8 (1-byte length)
            length = ext_type_data[content_start+1]
            content = ext_type_data[content_start+2:content_start+2+length].decode('utf-8', errors='ignore')
        elif next_byte == 0xda:  # str16 (2-byte length, big-endian)
            length = int.from_bytes(ext_type_data[content_start+1:content_start+3], 'big')
            content = ext_type_data[content_start+3:content_start+3+length].decode('utf-8', errors='ignore')
        elif next_byte == 0xdb:  # str32 (4-byte length, big-endian)
            length = int.from_bytes(ext_type_data[content_start+1:content_start+5], 'big')
            content = ext_type_data[content_start+5:content_start+5+length].decode('utf-8', errors='ignore')
        else:
            return role, ""
        
        return role, content
    except Exception as e:
        ic(f"Extract error: {e}")
        return "unknown", ""

# ======== History Endpoint ========
@app.get("/history/{thread_id}")
async def get_history(thread_id: str):
    try:
        # Connect to postgres
        conn = psycopg.connect(configs.services.postgres.URI)
        cur = conn.cursor()
        
        # Get messages blob for this thread
        cur.execute(
            """SELECT blob FROM checkpoint_blobs 
               WHERE thread_id = %s AND channel = 'messages'
               ORDER BY version DESC LIMIT 1""",
            (thread_id,)
        )
        blob_row = cur.fetchone()
        
        history = []
        
        if blob_row and blob_row[0]:
            try:
                blob_data = blob_row[0]
                
                # Unpack msgpack (messages are stored as list of ExtType objects)
                decoded = msgpack.unpackb(blob_data, raw=False, strict_map_key=False)
                
                if isinstance(decoded, list):
                    for msg_ext in decoded:
                        # Each message is msgpack ExtType with code 5 (LangChain serialization)
                        if isinstance(msg_ext, msgpack.ext.ExtType) and msg_ext.code == 5:
                            role, content = extract_message_content(msg_ext.data)
                            if content:  # Only add non-empty messages
                                history.append({
                                    "role": role,
                                    "message": content
                                })
            except Exception as e:
                ic(f"Blob parse error: {e}")
                return {
                    "success": False,
                    "error": f"Failed to parse messages: {str(e)}"
                }
        
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "count": len(history),
            "thread_id": thread_id,
            "history": history
        }
    except Exception as e:
        ic(f"History error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# ======== Run ========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8386)
