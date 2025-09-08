import streamlit as st
import time
import openai
from openai import OpenAI

# --- Page Config and Title ---
# Set the page configuration at the beginning of the script.
st.set_page_config(page_title="BiasBouncer", layout="centered")

st.markdown("<h1 style='text-align: center; color: red;'>BiasBouncer</h1>", unsafe_allow_html=True)

# --- API Key and Client Initialization ---
# Get the API key from Streamlit secrets or sidebar input.
openai_api_key = st.secrets.get("OPENAI_API_KEY")

with st.sidebar:
    st.header("Chat Controls")
    # Allow user to enter their API key if not found in secrets
    if not openai_api_key:
        openai_api_key = st.text_input("Enter your OpenAI API Key:", type="password", key="api_key_input")
    
    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

# Initialize the OpenAI client if the key is available.
client = None
if openai_api_key:
    client = OpenAI(api_key=openai_api_key)
else:
    # Display a warning message in the main chat area if no key is provided.
    st.info("Please enter your OpenAI API key in the sidebar to start chatting.")


# --- Helper Functions for UI Rendering ---
def get_ai_response_stream(api_client, history):
    """
    Yields chunks from the OpenAI API stream for a real-time chat effect.
    """
    # Filter out internal, non-string messages before sending to the API.
    api_messages = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in history
        if isinstance(msg["content"], str)
    ]

    try:
        # Create a streaming chat completion request.
        stream = api_client.chat.completions.create(
            model="gpt-4o",  # Using a powerful and efficient model
            messages=api_messages,
            stream=True,
        )
        # Yield each content chunk as it arrives.
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
    except openai.AuthenticationError:
        # Handle cases where the API key is invalid.
        yield "Authentication Error: Please check your OpenAI API key in the sidebar."
    except Exception as e:
        # Handle other potential API errors.
        yield f"An error occurred: {e}"


def create_team_tabs():
    """Renders the team member tabs consistently."""
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
    st.divider()

def start_team():
    """Displays concurrent progress bars with different completion speeds."""
    start_container = st.container(border=True)
    with start_container:
        st.write("Teamwork now in progress...")
        
        progress_1 = st.progress(0, text="Team Member 1 - Initializing...")
        progress_2 = st.progress(0, text="Team Member 2 - Initializing...")
        progress_3 = st.progress(0, text="Team Member 3 - Initializing...")

        duration_1, duration_2, duration_3 = 2.0, 4.0, 3.0
        time_step = 0.1
        num_steps = int(max(duration_1, duration_2, duration_3) / time_step)

        for i in range(num_steps + 1):
            elapsed_time = i * time_step
            p1 = min(100, int((elapsed_time / duration_1) * 100))
            p2 = min(100, int((elapsed_time / duration_2) * 100))
            p3 = min(100, int((elapsed_time / duration_3) * 100))
            
            progress_1.progress(p1, text="Team Member 1 - Operational")
            progress_2.progress(p2, text="Team Member 2 - Operational")
            progress_3.progress(p3, text="Team Member 3 - Operational")
            
            time.sleep(time_step)
        
        time.sleep(0.5)
        success_message = st.success("Work Complete")
        time.sleep(2)
        success_message.empty()
        time.sleep(1)

    # Placeholder for displaying team output - currently inactive
    # st.write("Team output will be displayed here.")
    st.button("View Documents")


# --- Session State Initialization ---
# Initialize chat history if it doesn't already exist.
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# --- Display Chat History ---
# Use a container with a fixed height to make the chat scrollable.
chat_container = st.container(height=600, border=False)
with chat_container:
    # This loop is the single source of truth for what is displayed.
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            # Check for special content types to render custom UI components.
            if isinstance(message["content"], dict):
                content_type = message["content"].get("type")
                if content_type == "team_creation":
                    create_team_tabs()
                elif content_type == "start_team":
                    start_team()
            else:
                # Render regular text messages.
                st.markdown(message["content"])


# --- Handle New User Input ---
if prompt := st.chat_input("Create a team or ask a question..."):
    # 1. Add the user's message to the chat history.
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    # 2. Process the prompt and generate the assistant's response.
    with st.chat_message("assistant"):
        # Handle the specific "create team" command.
        if prompt.lower() == "create team":
            with st.status("Creating Team...", expanded=True):
                st.write("Analyzing requirements...")
                time.sleep(2)
                st.write("Assembling the optimal team...")
                time.sleep(0.5)
                success_message = st.success("Team Creation Complete")
                time.sleep(2)
                success_message.empty()
            
            # Add a special dictionary to history to trigger UI rendering on rerun.
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": {"type": "team_creation"}
            })

        # Handle the specific "start team" command.
        elif prompt.lower() == "start team":
            with st.status("Starting Team...", expanded=True):
                st.write("Initializing systems...")
                time.sleep(1)
                st.write("Running diagnostics...")
                time.sleep(1)
            
            # Add a special dictionary to history.
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": {"type": "start_team"}
            })

        # Handle all other prompts by calling the OpenAI API.
        else:
            if not client:
                st.warning("Please provide your OpenAI API key in the sidebar to continue.")
                st.stop()
            
            # Display the streaming response and capture the full text.
            stream_generator = get_ai_response_stream(client, st.session_state.chat_history)
            full_response = st.write_stream(stream_generator)
            
            # Add the complete assistant response to the history.
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})

    # 3. Rerun the script to display the new messages.
    st.rerun()