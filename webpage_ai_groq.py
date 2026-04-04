import streamlit as st
from groq import Groq
from PIL import Image
from datetime import datetime
import PyPDF2
from docx import Document
import io
import requests
import time

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Adrito's AI Chatbot", page_icon="🌐", layout="wide")

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

# --- 4. SIDEBAR ---
MODEL_MAP = {
    "🔥 Pro (GPT-OSS 120B)": "openai/gpt-oss-120b",
    "⚖️ Balanced (Llama 3.3 70B)": "llama-3.3-70b-versatile",
    "⚡ Lightning (GPT-OSS 20B)": "openai/gpt-oss-20b",
    "🎨 Nano Banana (Image Gen)": "NANO_MODE"
}

with st.sidebar:
    st.title("⚙️ AI Control")
    selected_label = st.selectbox("🧠 Choose Brain Power", options=list(MODEL_MAP.keys()), index=0, key="model_v5")
    model_choice = MODEL_MAP[selected_label]
    is_image_mode = (model_choice == "NANO_MODE")
    
    if not is_image_mode:
        web_search = st.toggle("Enable Live Web Search", value=True)
        uploaded_file = st.file_uploader("📎 Upload Context", type=['txt', 'py', 'md', 'pdf', 'docx'])
    
    st.divider()
    if st.button("➕ Start New Chat", use_container_width=True):
        new_id = f"Session {datetime.now().strftime('%H:%M:%S')}"
        st.session_state.all_sessions[new_id] = []
        st.session_state.current_chat = new_id
        st.rerun()

    st.subheader("Recent Chats")
    for chat_title in list(st.session_state.all_sessions.keys()):
        if st.button(chat_title, key=f"btn_{chat_title}", use_container_width=True, 
                     type="primary" if chat_title == st.session_state.current_chat else "secondary"):
            st.session_state.current_chat = chat_title
            st.rerun()

# --- 5. MAIN INTERFACE ---
st.title(f"🚀 {st.session_state.current_chat}")

try:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("Missing Groq API Key!")
    st.stop()

messages = st.session_state.all_sessions[st.session_state.current_chat]
for msg in messages:
    with st.chat_message(msg["role"]):
        if "image" in msg:
            st.image(msg["image"], caption="Nano Banana Output")
        else:
            st.markdown(msg["content"])

# --- 6. LOGIC ---
if prompt := st.chat_input("Message or Image Prompt..."):
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if is_image_mode:
            status_box = st.status("🍌 Nano Banana is peeling... (this can take 40s)")
            success = False
            for attempt in range(2): # Try twice if it times out
                try:
                    seed = datetime.now().microsecond
                    image_url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=1280&height=720&seed={seed}&model=flux&nologo=true"
                    
                    # Increased timeout to 60s
                    img_response = requests.get(image_url, timeout=60)
                    if img_response.status_code == 200:
                        image_bytes = io.BytesIO(img_response.content)
                        img_obj = Image.open(image_bytes)
                        status_box.update(label="✅ Image Peeled!", state="complete")
                        st.image(img_obj)
                        messages.append({"role": "assistant", "image": img_obj})
                        success = True
                        break
                except requests.exceptions.ReadTimeout:
                    if attempt == 0:
                        status_box.write("⏱️ Bridge is slow, retrying once...")
                        time.sleep(2)
                    else:
                        status_box.update(label="❌ Timeout Error", state="error")
                        st.error("The free bridge is too slow right now. Try a simpler prompt or wait 1 minute.")
            if not success and not st.session_state.get('error_shown'):
                st.warning("Server busy. Try again shortly.")
        else:
            # TEXT GENERATION
            placeholder = st.empty()
            full_res = ""
            context = ""
            if uploaded_file:
                file_text = extract_text(uploaded_file)
                context = f"\n\n[FILE DATA]\n{file_text}"
            
            try:
                stream = groq_client.chat.completions.create(
                    model=model_choice,
                    messages=[{"role": "system", "content": "You are a helpful 2026 AI."}] + messages[:-1] + [{"role": "user", "content": prompt + context}],
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        placeholder.markdown(full_res + "▌")
                placeholder.markdown(full_res)
                messages.append({"role": "assistant", "content": full_res})
            except Exception as e:
                st.error(f"API Error: {e}")
