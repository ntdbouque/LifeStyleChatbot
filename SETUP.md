# CHATBOT HYPERTENSION - SETUP GUIDE

## CÁC BƯỚC SETUP:

### 1. CÀI ĐẶT REQUIREMENTS

#### 1.1 Tạo Virtual Environment (nếu chưa có)
```bash
# Nếu dùng conda
conda create -n hpert python=3.10
conda activate hpert

# Hoặc dùng venv
python3.10 -m venv venv
source venv/bin/activate
```

#### 1.2 Cài đặt dependencies
```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Cài vllm (phiên bản 0.4.2 hỗ trợ Python 3.10)
pip install vllm==0.4.2

# Cài requirements
pip install -r requirements.txt
```

**Lưu ý:** Nếu gặp lỗi `pkg_resources==0.0.0`, xóa dòng này khỏi requirements.txt (package không tồn tại).

---

### 2. CÀI ĐẶT BIẾN MÔI TRƯỜNG

#### 2.1 Tạo file `.env`
```bash
cd ~/Chatbot_HyperTension
cp .env.example .env  # (nếu có)
# Hoặc tạo file mới
touch .env
```

#### 2.2 Thêm các biến cần thiết
```env
# OpenAI API (cho DallE2, Whisper)
OPENAI_API_KEY=sk_your_openai_key_here

# HuggingFace Token (để download models)
HF_TOKEN=hf_your_hf_token_here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/chatbot

# vLLM Config
VLLM_PORT=8100
VLLM_MODEL=meta-llama/Meta-Llama-3-8B-Instruct

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8386
```

#### 2.3 HuggingFace Login (required để download models)
```bash
# Interactive login
huggingface-cli login
# → Vào https://huggingface.co/settings/tokens copy token
# → Paste vào terminal

# Hoặc one-liner
huggingface-cli login --token hf_YOUR_TOKEN_HERE
```

---

### 3. THIẾT LẬP MÔ HÌNH VLLM

#### 3.1 Kiểm tra GPU (nếu có)
```bash
# Check CUDA
nvidia-smi
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# Check GPU memory
nvidia-smi --query-gpu=memory.free --format=csv
```

#### 3.2 Start vLLM Server
```bash
# Basic command (dùng default config)
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Meta-Llama-3-8B-Instruct \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.7 \
    --port 8100

# Hoặc với auto tool choice (nếu model support)
vllm serve meta-llama/Meta-Llama-3-8B-Instruct \
    --trust-remote-code \
    --enable-auto-tool-choice \
    --gpu-memory-utilization 0.7 \
    --port 8100
```

**⏱️ Lần đầu sẽ download model (~7GB), chờ ~5-10 phút**

#### 3.3 Test vLLM
```bash
# Kiểm tra vLLM chạy
curl http://localhost:8100/health

# Test API
curl -X POST http://localhost:8100/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello",
    "max_tokens": 50,
    "temperature": 0.7
  }'
```

---

### 4. CHẠY ỨNG DỤNG VỚI BACKEND

#### 4.1 Chạy PostgreSQL (nếu dùng Docker)
```bash
docker-compose up -d postgres

# Hoặc check đã chạy
docker ps | grep postgres
```

#### 4.2 Start Backend FastAPI
```bash
cd ~/Chatbot_HyperTension

# Activate venv
source venv/bin/activate  # hoặc conda activate hpert

# Run backend
uvicorn backend.main:app --host 0.0.0.0 --port 8386 --reload

# Hoặc
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8386 --reload
```

#### 4.3 Test Backend
```bash
# Health check
curl http://localhost:8386/health

# Test chat endpoint
curl -X POST http://localhost:8386/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Làm sao để giảm huyết áp?",
    "user_id": "test-user",
    "session_id": "test-session"
  }'
```

---

### 5. TUNNEL LOCALHOST VỚI CLOUDFLARE (hoặc NGROK)

#### 5.1 Dùng Cloudflare Tunnel (Recommended)
```bash
# Cài cloudflared (nếu chưa)
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
  -o ~/.local/bin/cloudflared && chmod +x ~/.local/bin/cloudflared

# Run tunnel
cloudflared tunnel --url http://localhost:8386

# Output: https://abc123xyz.trycloudflare.com
```

**📌 Copy URL này - sẽ dùng cho mobile app**

#### 5.2 (Alternative) Dùng ngrok
```bash
# Login ngrok
ngrok config add-authtoken YOUR_NGROK_TOKEN

# Run tunnel
ngrok http 8386

# Output: https://abc123.ngrok-free.dev
```

---

### 6. KẾT NỐI ỨNG DỤNG VỚI MOBILE

#### 6.1 Update API config
```bash
# Mở file config
vi ~/MobileLifestyle/src/config/api.ts
```

**Thay đổi API_BASE_URL:**
```typescript
// TRƯỚC
const API_BASE_URL = "http://localhost:8386";

// SAU (dùng URL từ Cloudflare tunnel)
const API_BASE_URL = "https://abc123xyz.trycloudflare.com";
```

#### 6.2 Run Expo App
```bash
cd ~/MobileLifestyle

# Install dependencies (nếu chưa)
npm install

# Start Expo
npx expo start

# Hoặc
npm start
```

#### 6.3 Connect từ phone
- **Cách 1:** Cài app **Expo Go** trên phone → Scan QR code
- **Cách 2:** Web browser → Chọn `w` để run web version
- **Cách 3:** iOS Simulator/Android Emulator → Chọn `i` hoặc `a`

---

## 📋 QUICK START - 3 TERMINALS

Chạy lệnh này trên 3 terminal khác nhau:

**Terminal 1 - vLLM Server:**
```bash
cd ~/Chatbot_HyperTension
conda activate hpert
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Meta-Llama-3-8B-Instruct \
    --port 8100 \
    --gpu-memory-utilization 0.7
```

**Terminal 2 - Backend API:**
```bash
cd ~/Chatbot_HyperTension
conda activate hpert
uvicorn backend.main:app --host 0.0.0.0 --port 8386 --reload
```

**Terminal 3 - Cloudflare Tunnel + Mobile:**
```bash
# Run tunnel
cloudflared tunnel --url http://localhost:8386

# Copy URL và update api.ts

# Rồi start Expo
cd ~/MobileLifestyle
npm start
```

---

## 🔍 TROUBLESHOOTING

### vLLM Connection Error
```
❌ Connection refused [Errno 111]
✅ Giải pháp: Start vLLM trước (Terminal 1)
```

### CORS Error
```
❌ Access to fetch has been blocked by CORS policy
✅ Giải pháp: CORS đã config trong backend/main.py (allow_origins=["*"])
```

### Model Download Fails
```
❌ Repository Not Found for url
✅ Giải pháp: 
   - Check HF token: huggingface-cli whoami
   - Accept license: https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct
```

### Tunnel Disconnects
```
❌ Tunnel closed after 3 hours
✅ Giải pháp: 
   - Restart cloudflared (copy URL mới)
   - Update api.ts với URL mới
```

---

## 📊 PORTS REFERENCE

| Service | Port | URL |
|---------|------|-----|
| vLLM | 8100 | http://localhost:8100 |
| Backend | 8386 | http://localhost:8386 |
| Expo Dev | 19000 | http://localhost:19000 |
| Cloudflare | N/A | https://xyz.trycloudflare.com |
| PostgreSQL | 5432 | localhost:5432 |
| Qdrant | 6333 | http://localhost:6333 |

---

## ✅ VERIFICATION CHECKLIST

- [ ] Environment variables set (`.env` file)
- [ ] vLLM server running (port 8100)
- [ ] Backend running (port 8386, health check OK)
- [ ] Cloudflare tunnel active (URL copied)
- [ ] Mobile API config updated
- [ ] Expo app running & connected to backend
- [ ] Chat endpoint working (test message)
- [ ] History endpoint working (get past messages)

---

## 📚 USEFUL COMMANDS

```bash
# Check if port is in use
lsof -i :8100
lsof -i :8386

# Kill process on port
kill -9 $(lsof -t -i :8100)

# Check service status
curl http://localhost:8100/health
curl http://localhost:8386/health

# View logs
tail -f nohup.out

# Run in background
nohup python -m vllm.entrypoints.openai.api_server --model ... &
```

---

**Last Updated:** Dec 10, 2025