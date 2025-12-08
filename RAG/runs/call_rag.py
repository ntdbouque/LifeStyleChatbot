from RAG.main import AgentRAGOllama

def main():
    # Khởi tạo Agent
    agent = AgentRAGOllama(
        model_name="mistral:latest",
        qdrant_url="http://localhost:3636",
        collection_name="hypertension_docs",
        base_url="http://localhost:11434"
    )

    print("🤖 Agent RAG Ollama đã sẵn sàng!")

    while True:
        query = input("\n🔎 Nhập câu hỏi (hoặc 'exit' để thoát): ")
        if query.lower() in ["exit", "quit"]:
            break

        answer = agent.predict(query, thread_id = "user_10")
        print("\n🧠 Trả lời:\n", answer)

if __name__ == "__main__":
    main()

