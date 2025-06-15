import streamlit as st

from main import GraChalleInterface

# Streamlitアプリのタイトル
st.title("GraChalle: 会話式外国語試験Bot")

# インターフェースの初期化
if "interface" not in st.session_state:
    st.session_state.interface = GraChalleInterface()
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("What would you like to ask?")
print(prompt)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = st.session_state.interface.run(prompt)
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
