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

# --- 3. FILE PARSERS ---
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
        st.sidebar.error(f"File Error: {e}")
    return ""

# --- 4. SIDEBAR (User-Friendly Model Mapping) ---
# This maps "Friendly Names" to "Groq Model IDs"
MODEL_MAP = {
    "🔥 Pro (Ultra Smart)": "openai/gpt-oss-120b",
    "⚖️ Balanced (Smart & Fast)": "llama-3.3-70b-versatile",
    "⚡ Lightning (Instant Replies)": "llama-3.1-8b-instant",
    "🧠 Research (Deep Reasoning)": "openai/gpt-oss-20b"
}

with st.sidebar:
    st.title("⚙️ AI Control")
    
    # Show friendly names to the user
    selected_friendly_name = st.selectbox(
        "🧠 Choose Brain Power",
        options=list(MODEL_MAP.keys()),
        index=1,
        help="Pro is best for code; Lightning is best for quick chats."
    )
    # Get the actual ID for the API
    model_id = MODEL_MAP[selected_friendly_name]
    
    web_search = st.toggle("Enable Live Web Search", value=True)
    uploaded_file = st.file_uploader("📎 Upload (.txt, .pdf, .docx)", type=['txt', 'py', 'md', 'pdf', 'docx'])
    
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
    st.error("Missing GROQ_API_KEY in Secrets!")
    st.stop()

messages = st.session_state.all_sessions[st.session_state.current_chat]
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. CHAT LOGIC ---
if prompt := st.chat_input("Ask Anything"):
    context = ""
    if uploaded_file:
        file_text = extract_text(uploaded_file)
        context = f"\n\n[FILE DATA: {uploaded_file.name}]\n{file_text}"
    
    full_prompt = prompt + context
    messages.append({"role": "user", "content": full_prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        sys_msg = f"Today is {datetime.now().strftime('%B %d, %Y')}. Web Search: {web_search}. You are a 2026 AI."
        
        try:
            stream = client.chat.completions.create(
                model=model_id, # Uses the technical ID
                messages=[{"role": "system", "content": sys_msg}] + messages,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    placeholder.markdown(full_res + "▌")
            placeholder.markdown(full_res)
            messages.append({"role": "assistant", "content": full_res})
        except Exception as e:
            st.error(f"Model Error: {e}")

    # --- 7. SMART NAMING ---
    is_default = any(x in st.session_state.current_chat for x in ["Session", "New Chat"])
    if len(messages) == 2 and is_default:
        try:
            name_gen = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Return exactly 2 words summarizing this topic. No quotes."},
                    {"role": "user", "content": prompt}
                ]
            )
            smart_title = name_gen.choices[0].message.content.strip().replace('"', '')
            st.session_state.all_sessions[smart_title] = st.session_state.all_sessions.pop(st.session_state.current_chat)
            st.session_state.current_chat = smart_title
            st.rerun()
        except: pass
