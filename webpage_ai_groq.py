import streamlit as st
from groq import Groq
from pypdf import PdfReader
from docx import Document # For Word Docs
from datetime import datetime

# --- 1. SETUP ---
st.set_page_config(page_title="Adrito's AI 2026", layout="wide")

if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = {"New Chat Session": []}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "New Chat Session"

# --- 2. SIDEBAR (Enhanced Document Center) ---
with st.sidebar:
    st.header("📁 Document Center")
    # Added 'docx', 'jpg', 'png' to the allowed types
    uploaded_file = st.file_uploader("Upload PDF, Word, or Text", type=["pdf", "txt", "py", "docx", "jpg", "png"])
    
    context_text = ""
    if uploaded_file:
        try:
            file_type = uploaded_file.name.split('.')[-1].lower()
            
            if file_type == "pdf":
                reader = PdfReader(uploaded_file)
                context_text = "\n".join([p.extract_text() for p in reader.pages])
            elif file_type == "docx":
                doc = Document(uploaded_file)
                context_text = "\n".join([para.text for para in doc.paragraphs])
            elif file_type in ["jpg", "png", "jpeg"]:
                context_text = f"[User uploaded an image named: {uploaded_file.name}]"
                st.image(uploaded_file, caption="Image Preview", use_container_width=True)
            else:
                context_text = uploaded_file.read().decode("utf-8")
            
            st.success(f"Loaded: {uploaded_file.name}")
        except Exception as e:
            st.error(f"Could not read file: {e}")

    st.divider()
    st.header("📂 Chat History")
    
    if st.button("➕ Start New Chat", use_container_width=True):
        name = f"Session {datetime.now().strftime('%H:%M:%S')}"
        st.session_state.all_sessions[name] = []
        st.session_state.current_chat = name
        st.rerun()

    # History List with Deletion
    for chat_title in list(st.session_state.all_sessions.keys()):
        c1, c2 = st.columns([0.8, 0.2])
        with c1:
            style = "primary" if chat_title == st.session_state.current_chat else "secondary"
            if st.button(chat_title, use_container_width=True, type=style, key=f"b_{chat_title}"):
                st.session_state.current_chat = chat_title
                st.rerun()
        with c2:
            if st.button("X", key=f"d_{chat_title}"):
                del st.session_state.all_sessions[chat_title]
                if not st.session_state.all_sessions: st.session_state.all_sessions["New Chat Session"] = []
                st.session_state.current_chat = list(st.session_state.all_sessions.keys())[0]
                st.rerun()

# --- 3. MAIN AI ENGINE ---
st.title(f"🚀 {st.session_state.current_chat}")

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("🔑 API Key Missing in Secrets!")
    st.stop()

messages = st.session_state.all_sessions[st.session_state.current_chat]
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about your files..."):
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        full_res = ""
        placeholder = st.empty()
        
        # 2026 Logic
        sys_msg = f"System: Today is {datetime.now().strftime('%B %d, %Y')}. Year is 2026."
        
        # Combine prompt with file context
        combined_prompt = prompt
        if context_text:
            combined_prompt = f"FILE CONTENT:\n{context_text[:7000]}\n\nUSER QUESTION: {prompt}"

        stream = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": sys_msg}] + messages[:-1] + [{"role": "user", "content": combined_prompt}],
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_res += chunk.choices[0].delta.content
                placeholder.markdown(full_res + "▌")
        placeholder.markdown(full_res)
        messages.append({"role": "assistant", "content": full_res})

    # SMART RENAMING
    if len(messages) == 2 and st.session_state.current_chat.startswith("Session "):
        try:
            name_gen = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": "Create a 2-word title for this topic. Return ONLY the title."},
                          {"role": "user", "content": prompt}]
            )
            new_title = name_gen.choices[0].message.content.strip().replace('"', '')
            st.session_state.all_sessions[new_title] = st.session_state.all_sessions.pop(st.session_state.current_chat)
            st.session_state.current_chat = new_title
        except: pass

    st.rerun()
