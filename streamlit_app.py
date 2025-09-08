import streamlit as st
import time

st.markdown("<h1 style='text-align: center;'><span style='color: red;'>BiasBouncer</span></h1>", unsafe_allow_html=True)

prompt = st.chat_input("Create Team")

mock_answer = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."

def stream_data():
    for word in mock_answer.split(" "):
        yield word + " "
        time.sleep(0.02)

if prompt == "Create Team":
    col1, col2, col3 = st.columns(3, border=True)
    with col1:
        st.write("Member 1")
    with col2:
        st.write("Member 2")
    with col3:
        st.write("Member 3")
elif prompt == None:
    pass
else:
    st.write(stream_data)
