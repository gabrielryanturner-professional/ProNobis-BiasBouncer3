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
    st.divider()

def start_team():
    """Displays three concurrent progress bars with different completion speeds."""
    start_container = st.container(height=300, border=True)
    with start_container:
        st.write("Teamwork now in progress...")
        
        # Initialize all progress bars first
        progress_1 = st.progress(0, text="Team Member 1 - Initializing...")
        progress_2 = st.progress(0, text="Team Member 2 - Initializing...")
        progress_3 = st.progress(0, text="Team Member 3 - Initializing...")

        # Define total duration for each bar to complete in seconds
        # This creates the effect of them loading at different speeds
        duration_1 = 2.0  # Fastest
        duration_2 = 4.0  # Slowest
        duration_3 = 3.0  # Medium
        
        # Use a small time step for a smooth animation
        time_step = 0.1
        max_duration = max(duration_1, duration_2, duration_3)
        num_steps = int(max_duration / time_step)

        # A single loop to update all bars simultaneously
        for i in range(num_steps + 1):
            elapsed_time = i * time_step
            
            # Calculate the current percentage for each bar
            p1_percent = min(100, int((elapsed_time / duration_1) * 100))
            p2_percent = min(100, int((elapsed_time / duration_2) * 100))
            p3_percent = min(100, int((elapsed_time / duration_3) * 100))
            
            # Update each progress bar's value and text
            status_1 = "Operational" if p1_percent == 100 else "Starting..."
            status_2 = "Operational" if p2_percent == 100 else "Starting..."
            status_3 = "Operational" if p3_percent == 100 else "Starting..."

            progress_1.progress(p1_percent, text=f"Team Member 1 - {status_1}")
            progress_2.progress(p2_percent, text=f"Team Member 2 - {status_2}")
            progress_3.progress(p3_percent, text=f"Team Member 3 - {status_3}")
            
            time.sleep(time_step)
        
        # Brief pause after completion before showing success message
        time.sleep(0.5)
        st.success("Work Complete")
        time.sleep(1)

    st.write(stream_data)
    st.button("View Documents")



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
            elif isinstance(message["content"], dict) and message["content"].get("type") == "start_team":
                start_team()
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
            creation_status = st.status("Creating Team...", expanded=True)
            with creation_status:
                st.write("Analyzing requirements...")
                time.sleep(2)
                st.write("Assembling the optimal team...")
                time.sleep(1)
            
            # Add a special dictionary to the history instead of the UI elements themselves.
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": {"type": "team_creation"}
            })

        elif prompt.lower() == "start team":
            start_status = st.status("Starting Team...", expanded=True)
            with start_status:
                st.write("Initializing systems...")
                time.sleep(1)
                st.write("Running diagnostics...")
                time.sleep(1)
            
            # Add a special dictionary to the history instead of the UI elements themselves.
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": {"type": "start_team"}
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