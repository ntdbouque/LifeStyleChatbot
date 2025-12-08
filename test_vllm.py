import openai

client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"  # vLLM không cần key
)

def chat():
    print("🤖 Chat với Llama-3-8B (gõ 'quit' để thoát)\n")
    messages = []
    
    while True:
        user_input = input("Bạn: ")
        if user_input.lower() in ["quit", "exit"]:
            break
            
        messages.append({"role": "user", "content": user_input})
        
        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            messages=messages,
            max_tokens=512,
            temperature=0.7
        )
        
        bot_reply = response.choices[0].message.content
        print(f"Bot: {bot_reply}\n")
        messages.append({"role": "assistant", "content": bot_reply})

chat()