import streamlit as st
from openai import OpenAI

from langchain.agents import create_agent


def get_weather(city: str) -> str:
    """Get weather for a given city."""

    return f"It's always sunny in {city}!"
import os
OPENAI_API_KEY = "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"
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

agent = create_agent(
    model="openai:gpt-4o-mini",
    tools=[get_weather],
)


st.title('Chat GPT-like clone')
client = OpenAI(api_key = OPENAI_API_KEY)

# set a default model
if 'openai_model' not in st.session_state:
    st.session_state['openai_model'] = "gpt-4o-mini"

# Initialize chat history:
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

# Display chat messages from history on app return 
for message in st.session_state['messages']:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("what is up"):
    # add user input to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)    

    # display bot response in chat message container
    with st.chat_message("assistant"):
        for chunk in  agent.stream(
            {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
            stream_mode = 'messages'
        ):
            latest_message = chunk['message'][-1]
            print(latest_message)
        
    #     response = st.write_stream(stream)
    # st.session_state.messages.append({"role": "assistant", "content": response})
    