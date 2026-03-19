import streamlit as st
from groq import Groq
from pypdf import PdfReader
from docx import Document
from datetime import datetime

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Adrito's AI 2026", page_icon="🌐", layout="wide")

# Custom CSS for a clean "2026" interface
st.markdown("""
    <style>
    .stChatFloatingInputContainer { background-color: rgba(0,0,0,0); }
    .stChatMessage { border-radius: 12px; border: 1px solid #f0f2f6; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = {"New Chat Session": []}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "New Chat Session"

# --- 3. SIDEBAR (Settings & History) ---
with st.sidebar:
    st.title("⚙️ AI Control")
    
    # THE LIVE SEARCH TOGGLE
    web_search_enabled = st.toggle("Enable Live Web Search", value=True, help="Switch ON to access 2026 news and real-time events.")
    
    st.divider()
    st.header("📁 Document Center")
    uploaded_file = st.file_uploader("Upload PDF, Word, or Text", type=["pdf", "docx", "txt", "py"])
    
    context_text = ""
    if uploaded_file:
        try:
            ext = uploaded_file.name.split('.')[-1].lower()
            if ext == "pdf":
                reader = PdfReader(uploaded_file)
                context_text = "\n".join([p.extract_text() for p in reader.pages])
            elif ext == "docx":
                doc = Document(uploaded_file)
                context_text = "\n".join([para.text for para in doc.paragraphs])
            else:
                context_text = uploaded_file.read().decode("utf-8")
            st.success(f"Attached: {uploaded_file.name}")
        except Exception as e:
            st.error(f"Read Error: {e}")

    st.divider()
    st.header("📂 History")
    if st.button("➕ Start New Chat", use_container_width=True):
        new_id = f"Session {datetime.now().strftime('%H:%M:%S')}"
        st.session_state.all_sessions[new_id] = []
        st.session_state.current_chat = new_id
        st.rerun()

    # Chat list with Select & Delete [X]
    for chat_title in list(st.session_state.all_sessions.keys()):
        c1, c2 = st.columns([0.8, 0.2])
        with c1:
            btn_type = "primary" if chat_title == st.session_state.current_chat else "secondary"
            if st.button(chat_title, use_container_width=True, type=btn_type, key=f"sel_{chat_title}"):
                st.session_state.current_chat = chat_title
                st.rerun()
        with c2:
            if st.button("X", key=f"del_{chat_title}"):
                del st.session_state.all_sessions[chat_title]
                if not st.session_state.all_sessions:
                    st.session_state.all_sessions["New Chat Session"] = []
                st.session_state.current_chat = list(st.session_state.all_sessions.keys())[0]
                st.rerun()

# --- 4. API & MAIN CHAT ---
st.title(f"🚀 {st.session_state.current_chat}")

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("Missing GROQ_API_KEY in Secrets!")
    st.stop()

messages = st.session_state.all_sessions[st.session_state.current_chat]
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. INPUT & LIVE LOGIC ---
if prompt := st.chat_input("What is the latest 2026 news?"):
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        full_res = ""
        placeholder = st.empty()
        
        # SYSTEM PROMPT: Forces 2026 awareness
        curr_date = datetime.now().strftime('%B %d, %Y')
        sys_msg = f"Today is {curr_date}. You are a 2026 AI with real-time access. Year is 2026."
        
        # MODEL SELECTION: 'groq/compound' for search, 'llama-3.3-70b-versatile' for speed
        active_model = "groq/compound" if web_search_enabled else "llama-3.3-70b-versatile"
        
        final_prompt = prompt
        if context_text:
            final_prompt = f"FILE CONTEXT:\n{context_text[:8000]}\n\nUSER QUESTION: {prompt}"

        # Stream API call
        stream = client.chat.completions.create(
            model=active_model,
            messages=[{"role": "system", "content": sys_msg}] + messages[:-1] + [{"role": "user", "content": final_prompt}],
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_res += chunk.choices[0].delta.content
                placeholder.markdown(full_res + "▌")
        
        placeholder.markdown(full_res)
        messages.append({"role": "assistant", "content": full_res})

    # --- SMART AUTO-RENAMING ---
    if len(messages) == 2 and st.session_state.current_chat.startswith("Session "):
        try:
            name_gen = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": "Return a 2-word title for this topic. Words only."},
                          {"role": "user", "content": prompt}]
            )
            new_title = name_gen.choices[0].message.content.strip().replace('"', '')
            st.session_state.all_sessions[new_title] = st.session_state.all_sessions.pop(st.session_state.current_chat)
            st.session_state.current_chat = new_title
        except:
            pass

    st.rerun()
