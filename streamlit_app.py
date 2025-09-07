import streamlit as st

st.set_page_config(layout="wide")

st.markdown("<h1 style='text-align: center;'><span style='color: red;'>BiasBouncer</span></h1>", unsafe_allow_html=True)
prompt = st.chat_input("Type 'Create Team' to create a team")
if prompt == "Create Team":
    col1, col2, col3 = st.columns(3, border=True, width="stretch")
    with col1:
        st.subheader("Member 1")
    with col2:
        st.subheader("Member 2")
    with col3:
        st.subheader("Member 3")
else:
    st.write(f"User has sent the following prompt: {prompt}")
