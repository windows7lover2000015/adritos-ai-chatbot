import streamlit as st
from groq import Groq
from datetime import datetime
import PyPDF2
from docx import Document
import io

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Adrito's AI 2026", page_icon="🌐", layout="wide")

# --- 2. SESSION STATE ---
if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = {"New Chat Session": []}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "New Chat Session"

# --- 3. FILE PROCESSING FUNCTIONS ---
def extract_text(file):
    fname = file.name.lower()
    if fname.endswith(('.txt', '.py', '.md')):
        return file.read().decode("utf-8")
    elif fname.endswith('.pdf'):
        pdf_reader = PyPDF2.PdfReader(file)
        return "\n".join([page.extract_text() for page in pdf_reader.pages])
    elif fname.endswith('.docx'):
        doc = Document(io.BytesIO(file.read()))
        return "\n".join([para.text for para in doc.paragraphs])
    return ""

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("⚙️ AI Control")
    web_search = st.toggle("Enable Live Web Search", value=True)
    
    uploaded_file = st.file_uploader("📎 Upload File (.txt, .py, .pdf, .docx)", type=['txt', 'py', 'md', 'pdf', 'docx'])
    
    st.divider()
    if st.button("➕ Start New Chat", use_container_width=True):
        new_id = f"Session {datetime.now().strftime('%H:%M:%S')}"
        st.session_state.all_sessions[new_id] = []
        st.session_state.current_chat = new_id
        st.rerun()

    for chat_title in list(st.session_state.all_sessions.keys()):
        if st.button(chat_title, use_container_width=True, type="primary" if chat_title == st.session_state.current_chat else "secondary"):
            st.session_state.current_chat = chat_title
            st.rerun()

# --- 5. MAIN INTERFACE ---
st.title(f"🚀 {st.session_state.current_chat}")

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("Missing GROQ_API_KEY!")
    st.stop()

messages = st.session_state.all_sessions[st.session_state.current_chat]
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. INPUT & LOGIC ---
if prompt := st.chat_input("Ask Anything"):
    # Process file context
    context = ""
    if uploaded_file:
        with st.spinner("Reading file..."):
            file_text = extract_text(uploaded_file)
            context = f"\n\n[ATTACHED FILE: {uploaded_file.name}]\n{file_text}"
    
    full_prompt = prompt + context
    messages.append({"role": "user", "content": full_prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        sys_msg = f"Today is {datetime.now().strftime('%B %d, %Y')}. Web Search: {web_search}. Use attached file data if present."
        
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": sys_msg}] + messages,
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_res += chunk.choices[0].delta.content
                placeholder.markdown(full_res + "▌")
        placeholder.markdown(full_res)
        messages.append({"role": "assistant", "content": full_res})

    # SMART NAMING (Restored & Tested)
    if len(messages) == 2 and ("Session" in st.session_state.current_chat or "New Chat" in st.session_state.current_chat):
        try:
            name_gen = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": "2-word title for this query. No quotes."},
                          {"role": "user", "content": prompt}]
            )
            smart_title = name_gen.choices[0].message.content.strip().replace('"', '')
            st.session_state.all_sessions[smart_title] = st.session_state.all_sessions.pop(st.session_state.current_chat)
            st.session_state.current_chat = smart_title
            st.rerun()
        except: pass
   
