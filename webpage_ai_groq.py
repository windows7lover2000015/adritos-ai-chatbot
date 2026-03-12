import streamlit as st
from groq import Groq
from pypdf import PdfReader
from datetime import datetime

# --- 1. Setup & Memory ---
st.set_page_config(page_title="Adrito's AI Explorer", page_icon="💬", layout="wide")

# This stores ALL your different chat threads
if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = {} # Dictionary: { "Chat Title": [messages] }
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "New Chat"

# --- 2. Sidebar: Chat History List ---
with st.sidebar:
    st.title("📂 Chat History")
    
    # "New Chat" Button
    if st.button("➕ New Chat", use_container_width=True):
        now = datetime.now().strftime("%H:%M:%S")
        st.session_state.current_chat = f"Chat {now}"
        st.rerun()

    st.divider()

    # List of previous chats (Like your image!)
    for chat_title in st.session_state.all_sessions.keys():
        if st.button(chat_title, use_container_width=True, key=chat_title):
            st.session_state.current_chat = chat_title
            st.rerun()

    st.divider()
    # File Uploader moved here to keep it tidy
    uploaded_file = st.file_uploader("Attach Context", type=["pdf", "txt", "py"])

# --- 3. Load Current Chat Messages ---
if st.session_state.current_chat not in st.session_state.all_sessions:
    st.session_state.all_sessions[st.session_state.current_chat] = []

messages = st.session_state.all_sessions[st.session_state.current_chat]

# --- 4. Display the Chat UI ---
st.title(f"💬 {st.session_state.current_chat}")

# Display history
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. AI Logic ---
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
client = Groq(api_key=GROQ_API_KEY)

if prompt := st.chat_input("Ask me anything..."):
    # Show user message
    with st.chat_message("user"):
        st.markdown(prompt)
    messages.append({"role": "user", "content": prompt})

    # AI Response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # Injected Year 2026 Context
        sys_msg = f"Today is {datetime.now().strftime('%B %d, %Y')}. Year is 2026."
        
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
    
    st.rerun()
