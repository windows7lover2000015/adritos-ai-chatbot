import streamlit as st
from groq import Groq
from pypdf import PdfReader
from docx import Document
from datetime import datetime

# --- 1. PAGE CONFIG (Globe Icon) ---
st.set_page_config(page_title="Adrito's AI 2026", page_icon="🌐", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { border-right: 1px solid rgba(128, 128, 128, 0.2); }
    .stChatMessage { border-radius: 15px; border: 1px solid rgba(128, 128, 128, 0.2); margin-bottom: 10px; }
    /* Visibility Fix for Sidebar Text */
    .st-emotion-cache-16idsys p, .st-emotion-cache-zt5igj { color: inherit !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "all_sessions" not in st.session_state:
    st.session_state.all_sessions = {"New Chat Session": []}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "New Chat Session"

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("⚙️ AI Control")
    web_search_enabled = st.toggle("Enable Live Web Search", value=True)
    
    st.divider()
    st.header("📂 History")
    if st.button("➕ Start New Chat", use_container_width=True):
        new_id = f"Session {datetime.now().strftime('%H:%M:%S')}"
        st.session_state.all_sessions[new_id] = []
        st.session_state.current_chat = new_id
        st.rerun()

    # Fixed History Selection
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

# --- 5. INPUT & SMART LOGIC ---
if prompt := st.chat_input("Ask Anything"):
    # Store first prompt for naming logic
    first_prompt_of_session = prompt if not messages else None
    
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        full_res = ""
        placeholder = st.empty()
        
        curr_date = datetime.now().strftime('%B %d, %Y')
        sys_msg = (
            f"Today is {curr_date}. You are a 2026 AI. "
            "You have live web access. Answer accurately based on current data."
        )
        
        try:
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

        except Exception as e:
            st.error("Connection Error. Please check your API usage.")

    # --- RE-FIXED SMART RENAMING ---
    # Trigger ONLY on the very first exchange to prevent the AI response from becoming the title
    if len(messages) == 2 and (st.session_state.current_chat.startswith("Session") or st.session_state.current_chat == "New Chat Session"):
        try:
            # We use a smaller model for fast naming
            naming_res = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{
                    "role": "system", 
                    "content": "Summarize the user's first query into exactly 2 words. Return only those 2 words."
                }, {"role": "user", "content": messages[0]["content"]}]
            )
            smart_title = naming_res.choices[0].message.content.strip().replace('"', '').replace('.', '')
            
            # Transfer and update state
            st.session_state.all_sessions[smart_title] = st.session_state.all_sessions.pop(st.session_state.current_chat)
            st.session_state.current_chat = smart_title
        except:
            pass

    st.rerun()
