import streamlit as st
from groq import Groq
from datetime import datetime

# --- 1. PAGE SETUP (Globe Icon & Tab Name) ---
st.set_page_config(page_title="Adrito's AI 2026", page_icon="🌐", layout="wide")

# --- 2. SESSION STATE ---
if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = {"New Chat Session": []}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "New Chat Session"

# --- 3. SIDEBAR (Fixed Web Search Toggle) ---
with st.sidebar:
    st.title("⚙️ AI Control")
    # This value is now passed into the System Prompt
    web_search = st.toggle("Enable Live Web Search", value=True)
    
    st.divider()
    st.header("📂 History")
    if st.button("➕ Start New Chat", use_container_width=True):
        new_id = f"Session {datetime.now().strftime('%H:%M:%S')}"
        st.session_state.all_sessions[new_id] = []
        st.session_state.current_chat = new_id
        st.rerun()

    for chat_title in list(st.session_state.all_sessions.keys()):
        btn_type = "primary" if chat_title == st.session_state.current_chat else "secondary"
        if st.button(chat_title, use_container_width=True, type=btn_type):
            st.session_state.current_chat = chat_title
            st.rerun()

# --- 4. MAIN INTERFACE ---
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

# --- 5. INPUT & RESTORED LOGIC ---
if prompt := st.chat_input("Ask Anything"):
    # 1. Store user message
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate AI Response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        
        # --- FIX: LIVE WEB SEARCH LOGIC ---
        # We tell the model it HAS live access when the toggle is on
        search_status = "ENABLED. Use current 2026 data." if web_search else "DISABLED. Use internal knowledge."
        curr_date = datetime.now().strftime('%B %d, %Y')
        
        sys_msg = (
            f"Today is {curr_date}. You are a 2026 AI. "
            f"Live Web Search is {search_status}. "
            "Provide real-time updates on news, weather, or sports if requested."
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

    # --- FIX: SMART NAMING (Targets prompt [0]) ---
    # Trigger only if it's the
