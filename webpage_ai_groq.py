import streamlit as st
from groq import Groq
from datetime import datetime
import PyPDF2
from docx import Document
import io

# --- 1. PAGE SETUP (Globe Icon & Browser Tab) ---
st.set_page_config(page_title="Adrito's AI 2026", page_icon="🌐", layout="wide")

# --- 2. SESSION STATE ---
if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = {"New Chat Session": []}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "New Chat Session"

# --- 3. FILE PARSING LOGIC ---
def extract_text(file):
    try:
        fname = file.name.lower()
        if fname.endswith(('.txt', '.py', '.md')):
            return file.read().decode("utf-8")
        elif fname.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        elif fname.endswith('.docx'):
            doc = Document(io.BytesIO(file.read()))
            return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        st.sidebar.error(f"⚠️ File Error: {e}")
    return ""

# --- 4. SIDEBAR (Control Center) ---
with st.sidebar:
    st.title("⚙️ AI Control")
    web_search = st.toggle("Enable Live Web Search", value=True)
    
    # File Uploader for multiple formats
    uploaded_file = st.file_uploader("📎 Upload (.txt, .pdf, .docx)", type=['txt', 'py', 'md', 'pdf', 'docx'])
    
    st.divider()
    st.header("📂 Chat History")
    if st.button("➕ Start New Chat", use_container_width=True):
        new_id = f"Session {datetime.now().strftime('%H:%M:%S')}"
        st.session_state.all_sessions[new_id] = []
        st.session_state.current_chat = new_id
        st.rerun()

    # List all chat sessions
    for chat_title in list(st.session_state.all_sessions.keys()):
        is_active = (chat_title == st.session_state.current_chat)
        if st.button(chat_title, use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state.current_chat = chat_title
            st.rerun()

# --- 5. MAIN CHAT INTERFACE ---
st.title(f"🚀 {st.session_state.current_chat}")

try:
    # Key is safely pulled from Streamlit Advanced Settings -> Secrets
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("Missing GROQ_API_KEY! Add it to Streamlit Secrets.")
    st.stop()

# Display current chat history
messages = st.session_state.all_sessions[st.session_state.current_chat]
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. CHAT INPUT & LOGIC ---
if prompt := st.chat_input("Ask Anything"):
    # Handle File Context
    context = ""
    if uploaded_file:
        with st.status("Reading attached file...", expanded=False):
            file_text = extract_text(uploaded_file)
            context = f"\n\n[USER ATTACHED FILE: {uploaded_file.name}]\n{file_text}"
    
    # Update History
    full_user_msg = prompt + context
    messages.append({"role": "user", "content": full_user_msg})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        
        # 2026 Awareness & Search logic
        search_status = "ENABLED (Priority: Current News/Events)" if web_search else "DISABLED"
        sys_msg = (
            f"Today is {datetime.now().strftime('%B %d, %Y')}. You are a 2026 AI. "
            f"Live Web Search is {search_status}. Answer precisely."
        )
        
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

    # --- 7. SMART NAMING (THE FIX) ---
    # Trigger ONLY on the 1st exchange if the title is still a generic default
    is_default = any(x in st.session_state.current_chat for x in ["Session", "New Chat"])
    
    if len(messages) == 2 and is_default:
        try:
            # We use ONLY your first prompt (messages[0]) to generate the title
            name_gen = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Return exactly 2 words summarizing this topic. No quotes. No periods."},
                    {"role": "user", "content": prompt}
                ]
            )
            smart_title = name_gen.choices[0].message.content.strip().replace('"', '').replace('.', '')
            
            # Atomic swap of the session keys
            st.session_state.all_sessions[smart_title] = st.session_state.all_sessions.pop(st.session_state.current_chat)
            st.session_state.current_chat = smart_title
            
            # This is critical to refresh the sidebar buttons
            st.rerun()
        except:
            pass
