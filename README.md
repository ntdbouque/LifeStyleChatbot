# CHATBOT TƯ VẤN LỐI SỐNG BỆNH TIỂU ĐƯỜNG - BỆNH TĂNG HUYẾT ÁP

### 1. Setup
#### 1.1. Installing Dependency
```python
cd Chatbot_Hypertension
pip install -r requirements.txt
```
#### 1.2. Initialize third-party services
```bash
docker compose up -d
```
#### 1.3. Pulling mistral 8b-Instruct
```bash
docker exec -it Duy_mc_ollama bash
```
And then
```bash
ollama pull mistral
```
#### 1.xx (Optional) Customize configuration or Use default
Initialize (Change) configuration in configs/configs.yaml


### 2. Usage
Ingest: 
```python
python RAG/runs/ingest.py
```
FastAPI Server: 
```python
cd Chatbot_Hypertension
uvicorn ./backend/main:app --host 0.0.0.0 --port 8386 --reload
```
GUI:
```python
streamlit run frontend/app.py --server.port 8387  
```

### 3. Features
### 4. Contributing
### 5. License