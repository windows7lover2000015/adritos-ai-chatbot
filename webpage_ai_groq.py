import streamlit as st
from groq import Groq
from pypdf import PdfReader
from docx import Document
from datetime import datetime

# --- 1. PAGE CONFIG & THEME-FRIENDLY STYLING ---
st.set_page_config(page_title="Adrito's AI 2026", page_icon="🌐", layout="wide")

# CSS to ensure high contrast and readability in both Light and Dark modes
st.markdown("""
    <style>
    [data-testid="stSidebar"] { border-right: 1px solid rgba(128, 128, 128, 0.2); }
    .stChatMessage { border-radius: 15px; border: 1px solid rgba(128, 128, 128, 0.2); margin-bottom: 10px; padding: 10px; }
    /* Force text to follow theme colors */
    .st-emotion-cache-16idsys p, .st-emotion-cache-zt5igj { color: inherit !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE (Memory) ---
if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = {"New Chat Session": []}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "New Chat Session"

# --- 3. SIDEBAR (Tools & History) ---
with st.sidebar:
    st.title("⚙️ AI Control")
    web_search_enabled = st.toggle("Enable Live Web Search", value=True)
    
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
    st.error("Missing GROQ_API_KEY in Streamlit Secrets!")
    st.stop()

messages = st.session_state.all_sessions[st.session_state.current_chat]
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. INPUT & LIVE LOGIC ---
if prompt := st.chat_input("Ask Adrito AI anything..."):
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        full_res = ""
        placeholder = st.empty()
        
        # SYSTEM PROMPT (Fixed for 2026)
        curr_date = datetime.now().strftime('%B %d, %Y')
        sys_msg = (
            f"Today is {curr_date}. You are a 2026 AI. "
            "If Web Search is enabled, you have access to live news. "
            "You are helpful, concise, and smart."
        )
        
        active_model = "groq/compound" if web_search_enabled else "llama-3.3-70b-versatile"
        
        final_prompt = prompt
        if context_text:
            final_prompt = f"FILE CONTEXT:\n{context_text[:8000]}\n\nUSER QUESTION: {prompt}"

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

    # --- ENHANCED UNIVERSAL SMART RENAMING ---
    # Renames after the 1st exchange if the name is still a "Session" default
    if len(messages) == 2 and (st.session_state.current_chat.startswith("Session") or st.session_state.current_chat == "New Chat Session"):
        try:
            # We use a very direct instruction to the AI to name the chat based on user intent
            naming_res = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{
                    "role": "system", 
                    "content": "Analyze the user's message and create a 2-3 word title. "
                               "Examples: 'Himachal Trip', '2026 News', 'Python Bug', 'Music Chat'. "
                               "Return ONLY the words, no quotes or periods."
                }, {"role": "user", "content": prompt}]
            )
            smart_title = naming_res.choices[0].message.content.strip().replace('"', '')
            
            # Transfer the chat history to the new name
            st.session_state.all_sessions[smart_title] = st.session_state.all_sessions.pop(st.session_state.current_chat)
            st.session_state.current_chat = smart_title
        except:
            pass

    st.rerun()
