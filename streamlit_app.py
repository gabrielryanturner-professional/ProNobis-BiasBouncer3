import streamlit as st
import time

st.markdown("<h1 style='text-align: center;'><span style='color: red;'>BiasBouncer</span></h1>", unsafe_allow_html=True)

prompt = st.chat_input("Create Team")

mock_answer = "This is a mock AI answer. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."

def stream_data():
    for word in mock_answer.split(" "):
        yield word + " "
        time.sleep(0.02)

if prompt == "Create Team":
    with st.status("Creating Team..."):
        st.write("Doing Research...")
        time.sleep(2)
        st.write("Finalizing Roles...")
        time.sleep(2)

    tab1, tab2, tab3 = st.tabs(["Member 1", "Member 2", "Member 3"])
    with tab1:
        st.subheader("Member 1")
        st.divider()
        st.write("Info")
    with tab2:
        st.subheader("Member 2")
        st.divider()
        st.write("Info")
    with tab3:
        st.subheader("Member 3")
        st.divider()
        st.write("Info")
elif prompt == None:
    pass
else:
    st.write(stream_data)

with st.sidebar:
    st.header("Previous Chats")
