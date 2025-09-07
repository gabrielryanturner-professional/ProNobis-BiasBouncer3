import streamlit as st

st.markdown("<h1 style='text-align: center;'><span style='color: red;'>BiasBouncer</span></h1>", unsafe_allow_html=True)
prompt = st.chat_input("Type 'Create Team' to create a team")
if prompt == "Create Team":
    col1, col2, col3 = st.columns(3, border=True, width="stretch")
    with col1:
        st.header("Member 1")
    with col2:
        st.header("Member 2")
    with col3:
        st.header("Member 3")

else:
    st.write(f"User has sent the following prompt: {prompt}")
