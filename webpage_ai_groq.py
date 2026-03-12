import streamlit as st
from groq import Groq

# Set up page
st.set_page_config(page_title="Adrito's AI + Attachments", page_icon="📎")
st.title("📎 Adrito's AI with Attachments")

# 1. API Key Setup (Best to use Streamlit Secrets for the Cloud)
# If testing locally, you can paste your key here.
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "your_key_here")
client = Groq(api_key=GROQ_API_KEY)

# --- Sidebar for File Uploads ---
with st.sidebar:
    st.header("Attachments")
    uploaded_file = st.file_uploader("Upload a file (.txt, .py, .md)", type=["txt", "py", "md"])
    
    file_content = ""
    if uploaded_file is not None:
        # Read the file as text
        file_content = uploaded_file.read().decode("utf-8")
        st.success(f"Attached: {uploaded_file.name}")
        st.info("The AI will now 'read' this file when you ask a question.")

# --- Chat Logic ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Ask about the file or just chat..."):
    # If a file is attached, inject it into the prompt silently
    final_prompt = prompt
    if file_content:
        final_prompt = f"Context from attached file '{uploaded_file.name}':\n\n{file_content}\n\nUser Question: {prompt}"

    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # We pass the full history + the context-aware prompt
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. If the user provides file context, use it to answer accurately."}
            ] + [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[:-1] # Old history
            ] + [{"role": "user", "content": final_prompt}], # Latest prompt with file context
            stream=True,
        )

        for chunk in completion:
            content = chunk.choices[0].delta.content
            if content:
                full_response += content
                response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
