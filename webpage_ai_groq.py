import streamlit as st
from groq import Groq
from pypdf import PdfReader

# Set up page
st.set_page_config(page_title="Adrito's AI Explorer", page_icon="📄")
st.title("📄 Adrito's AI + Documents")

# API Key from Streamlit Secrets
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
client = Groq(api_key=GROQ_API_KEY)

# --- Sidebar: File Upload ---
with st.sidebar:
    st.header("Upload Center")
    uploaded_file = st.file_uploader("Upload PDF or Text", type=["pdf", "txt", "py"])
    
    context_text = ""
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            # Extract text from PDF
            pdf_reader = PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                context_text += page.extract_text() + "\n"
        else:
            # Read plain text files
            context_text = uploaded_file.read().decode("utf-8")
        
        st.success(f"Loaded: {uploaded_file.name}")

# --- Chat Interface ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question about your file..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Prepare the prompt with file context if available
    full_prompt = prompt
    if context_text:
        full_prompt = f"DOCUMENT CONTEXT:\n{context_text[:10000]}\n\nUSER QUESTION: {prompt}"

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": full_prompt}],
            stream=True,
        )

        for chunk in completion:
            content = chunk.choices[0].delta.content
            if content:
                full_response += content
                response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
