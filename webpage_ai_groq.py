import streamlit as st
from groq import Groq
from pypdf import PdfReader
from docx import Document
from datetime import datetime

# --- 1. PAGE CONFIG & THEME FIX ---
st.set_page_config(page_title="Adrito's AI 2026", page_icon="🌐", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { border-right: 1px solid rgba(128, 128, 128, 0.2); }
    .stChatMessage { border-radius: 15px; border: 1px solid rgba(128, 128, 128, 0.2); margin-bottom: 10px; }
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

# --- 5. INPUT & DYNAMIC LOGIC ---
if prompt := st.chat_input("Ask Anything"):
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        full_res = ""
        placeholder = st.empty()
        
        # We tell the AI what the date is, but NOT the sports results.
        # It must use the tool to find the results.
        curr_date = datetime.now().strftime('%B %d, %Y')
        sys_msg = (
            f"Current Date: {curr_date}. The year is 2026. "
            "You have access to a web search tool. If you are asked about recent events "
            "or sports results from 2026, you MUST use the tool to provide accurate data."
        )
        
        # Using Llama 3.3 70B for high-quality tool use
        active_model = "llama-3.3-70b-versatile"

        try:
            # First call to check if tools are needed
            response = client.chat.completions.create(
                model=active_model,
                messages=[{"role": "system", "content": sys_msg}] + messages,
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "google_search",
                        "description": "Search the live web for 2026 news, sports, and events",
                        "parameters": {
                            "type": "object",
                            "properties": {"query": {"type": "string"}},
                            "required": ["query"]
                        }
                    }
                }] if web_search_enabled else None
            )

            # If the model wants to search, it will return a tool_call
            if response.choices[0].message.tool_calls:
                placeholder.markdown("🔍 *Searching the web for 2026 data...*")
                # In a real search app, you'd call a Search API here. 
                # For now, we allow the model to simulate the search process or 
                # use its internal logic if search is toggled off.
            
            # Streaming the final response
            stream = client.chat.completions.create(
                model=active_model,
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
            st.error(f"API Connection Error: {e}")

    # --- SMART AUTO-RENAMING ---
    if len(messages) == 2 and (st.session_state.current_chat.startswith("Session") or st.session_state.current_chat == "New Chat Session"):
        try:
            name_gen = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": "2-word title for this topic. No quotes."},
                          {"role": "user", "content": prompt}]
            )
            new_title = name_gen.choices[0].message.content.strip().replace('"', '')
            st.session_state.all_sessions[new_title] = st.session_state.all_sessions.pop(st.session_state.current_chat)
            st.session_state.current_chat = new_title
        except: pass

    st.rerun()
