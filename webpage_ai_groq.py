import streamlit as st
from groq import Groq
from pypdf import PdfReader
from datetime import datetime

# --- 1. Setup ---
st.set_page_config(page_title="Adrito's AI 2026", page_icon="💬", layout="wide")

# This is the "Memory Bank" for the current session
if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = {"Default Chat": []}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Default Chat"

# --- 2. Sidebar with History List ---
with st.sidebar:
    st.title("📂 Chat History")
    
    # New Chat Button
    if st.button("➕ New Chat", use_container_width=True):
        new_name = f"Chat {datetime.now().strftime('%H:%M:%S')}"
        st.session_state.all_sessions[new_name] = []
        st.session_state.current_chat = new_name
        st.rerun()

    st.divider()

    # This loop generates that list you saw in your screenshot
    for chat_title in list(st.session_state.all_sessions.keys()):
        # Highlights the active chat
        type_style = "primary" if chat_title == st.session_state.current_chat else "secondary"
        if st.button(chat_title, use_container_width=True, type=type_style):
            st.session_state.current_chat = chat_title
            st.rerun()

# --- 3. Main Chat UI ---
st.title(f"🚀 {st.session_state.current_chat}")
messages = st.session_state.all_sessions[st.session_state.current_chat]

# Display messages from the selected chat
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 4. AI Engine ---
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
client = Groq(api_key=GROQ_API_KEY)

if prompt := st.chat_input("Start a conversation..."):
    # Save and show user message
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Date awareness for 2026
    sys_msg = f"Today is {datetime.now().strftime('%B %d, %Y')}. You are an AI in 2026."

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": sys_msg}] + messages,
            stream=True,
        )

        for chunk in completion:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)
        messages.append({"role": "assistant", "content": full_response})
    
    # Update the "Title" of the chat based on the first question
    if len(messages) == 2: # After first Q&A
        new_title = prompt[:25] + "..." if len(prompt) > 25 else prompt
        st.session_state.all_sessions[new_title] = st.session_state.all_sessions.pop(st.session_state.current_chat)
        st.session_state.current_chat = new_title
    
    st.rerun()
