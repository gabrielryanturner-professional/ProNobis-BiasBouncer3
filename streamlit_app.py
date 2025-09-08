import streamlit as st
import time

st.markdown("<h1 style='text-align: center;'><span style='color: red;'>BiasBouncer</span></h1>", unsafe_allow_html=True)

prompt = st.chat_input("Create Team")

def stream_data():
    for word in prompt.split(" "):
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
