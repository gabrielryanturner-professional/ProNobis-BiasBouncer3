import streamlit as st
import time

# --- Page Config and Title ---
# It's good practice to set the page config at the start.
st.set_page_config(page_title="BiasBouncer", layout="centered")

st.markdown("<h1 style='text-align: center; color: red;'>BiasBouncer</h1>", unsafe_allow_html=True)


# --- Mock Data and Helper Functions ---
mock_answer = (
    "This is a mock AI answer. Lorem ipsum dolor sit amet, consectetur "
    "adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore "
    "magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco "
    "laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor "
    "in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
    "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa "
    "qui officia deserunt mollit anim id est laborum."
)

def stream_data():
    """Yields words from the mock answer to simulate a streaming response."""
    for word in mock_answer.split(" "):
        yield word + " "
        time.sleep(0.02)

def create_team_tabs():
    """A helper function to render the team member tabs consistently."""
    tab1, tab2, tab3 = st.tabs(["Member 1", "Member 2", "Member 3"])
    with tab1:
        st.subheader("Team Member 1")
        st.write("Detailed information and profile for Member 1.")
    with tab2:
        st.subheader("Team Member 2")
        st.write("Detailed information and profile for Member 2.")
    with tab3:
        st.subheader("Team Member 3")
        st.write("Detailed information and profile for Member 3.")
    time.sleep(2)
    st.divider()
    st.write(stream_data)


# --- Session State Initialization ---
# Initialize chat history if it doesn't exist.
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# --- Display Chat History ---
# We'll use a container with a fixed height to make the chat scrollable.
chat_container = st.container(height=600, border=False)
with chat_container:
    # This loop is the single source of truth for what is displayed on the screen.
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            # Check if the content is our special dictionary for rendering tabs.
            if isinstance(message["content"], dict) and message["content"].get("type") == "team_creation":
                create_team_tabs()
            else:
                # Otherwise, it's a regular text message.
                st.markdown(message["content"])


# --- Handle New User Input ---
# The 'if prompt := ...' syntax assigns the input to 'prompt' and checks if it's not None in one go.
if prompt := st.chat_input("Create a team or ask a question..."):
    # 1. Add the user's message to the chat history.
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    # 2. Process the prompt and generate the assistant's response.
    # We show the response inside a chat message block.
    with st.chat_message("assistant"):
        # Handle the specific "Create Team" command
        if prompt.lower() == "create team":
            with st.status("Creating Team...", expanded=True):
                st.write("Analyzing requirements...")
                time.sleep(1)
                st.write("Assembling the optimal team...")
                time.sleep(1)
            
            # Add a special dictionary to the history instead of the UI elements themselves.
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": {"type": "team_creation"}
            })

        # Handle all other prompts
        else:
            # st.write_stream is the recommended way to display streaming responses.
            # It also conveniently returns the full response once the stream is complete.
            full_response = st.write_stream(stream_data)
            
            # Add the complete assistant response to the history.
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})

    # 3. Rerun the script to display the latest messages from the updated history.
    st.rerun()


# --- Sidebar ---
with st.sidebar:
    st.header("Chat Controls")
    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

