import streamlit as st

st.set_page_config(layout="wide")

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

st.markdown("<h1 style='text-align: center;'><span style='color: red;'>BiasBouncer</span></h1>", unsafe_allow_html=True)
messages_container = st.container(height=575, border=None)

with messages_container:
    for msg in st.session_state["chat_history"]:
        role = msg["role"]
        content = msg["content"]

        if role == "user":
            st.chat_message("user").write(content)
        else:
            st.chat_message("assistant").write(f"**{role}**: {content}")


user_input = st.chat_input("Work with the Agents")
