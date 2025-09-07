import streamlit as st

st.title("BiasBouncer")
prompt = st.chat_input("Type 'Create Team' to create a team")
if prompt == "Create Team":
    col1, col2, col3 = st.columns(3, border=True, width="stretch")
    with col1:
        st.write("Member 1")
    with col2:
        st.write("Member 2")
    with col3:
        st.write("Member 3")

else:
    st.write(f"User has sent the following prompt: {prompt}")
