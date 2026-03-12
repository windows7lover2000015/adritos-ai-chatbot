import streamlit as st
from groq import Groq

st.title("Adrito's Cloud AI")

# Enter your API Key here or set it in Streamlit Secrets
client = Groq(api_key="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")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=st.session_state.messages,
        )
        full_response = response.choices[0].message.content
        st.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})