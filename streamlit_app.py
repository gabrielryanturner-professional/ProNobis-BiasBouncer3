import streamlit as st


st.markdown("<h1 style='text-align: center;'><span style='color: red;'>BiasBouncer</span></h1>", unsafe_allow_html=True)

prompt = st.chat_input("Create Team")
if prompt == "Create Team":
    col1, col2, col3 = st.columns()
    with col1:
        st.write("Member 1")
    with col2:
        st.write("Member 2")
    with col3:
        st.write("Member 3")
else:
    st.write(f"User said: {prompt}")
