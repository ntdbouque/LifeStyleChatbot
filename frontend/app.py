import requests
import streamlit as st
from datetime import datetime


# emojis: https://www.webfx.com/tools/emoji-cheat-sheet/
st.set_page_config(page_title="localbot", page_icon="🧑‍💼", layout="wide")


def send_query(user_id, query):
    headers = {"Content-Type": "application/json"}
    data = {"message": query, "user_id": user_id}
    resp = requests.post(
        "http://localhost:8386/chat", json=data, headers=headers, stream=True
    )
    return resp


def run_app(username):
    st.title("💬 Hospital AI CHATBOT - Powered by SIU AI LAB")
    st.caption("🚀 I'm a Medical Lifestyle Assistant ")

    # Function to append and display a new message
    def append_and_display_message(role, content, links=None):
        if links:
            # Embed each link as a Markdown hyperlink
            for link in links:
                st.page_link(link, label=link)
        st.session_state.messages.append({"role": role, "content": content})
        st.chat_message(role).write(content)

    if "messages" not in st.session_state:
        # Load chat history from the database
        st.session_state["messages"] = []

        # Start with a greeting from the assistant if no history is found
        st.session_state["messages"] = [
            {"role": "assistant", "content": "How can I help you?"}
        ]

    # Initialize a unique chatID and session state for messages if not already present
    if "chatID" not in st.session_state:
        st.session_state["chatID"] = f"{username}-{str(datetime.now())}"

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # Initialize the QA system using caching
    # translater = Translation(from_lang="en", to_lang='vi', mode='translate')
    if query := st.chat_input():
        append_and_display_message("user", query)

        res = send_query(username, query)

        res.raise_for_status()

        with st.chat_message("assistant"):
            # Create a placeholder for streaming messages
            message_placeholder = st.empty()
            full_response = ""

            for chunk in res.iter_content(chunk_size=64, decode_unicode=True):
                streaming_resp = chunk
                full_response += streaming_resp
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )

run_app("user_36")
