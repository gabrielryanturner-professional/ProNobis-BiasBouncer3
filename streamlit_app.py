import streamlit as st
import time
import json
import openai
from openai import OpenAI

# --- Page Config and Title ---
st.set_page_config(page_title="BiasBouncer", layout="centered")
st.markdown("<h1 style='text-align: center; color: red;'>BiasBouncer</h1>", unsafe_allow_html=True)

# --- System Prompt for the AI ---
# This guides the AI on its role and how to interact with the user.
SYSTEM_PROMPT = """
You are BiasBouncer, an expert AI team creation assistant. 
Your primary goal is to help users build a diversified team of AI agents to accomplish a specific task.
When a user wants to create a team, you must guide them. Ask clarifying questions to understand their goal.
Once you have enough information, you MUST call the `create_team` function to generate the team members.
Do not just list the team members in text; you must use the provided tool to create them.
For example, if the user says "create a team for writing a blog post", you should call the `create_team` function with appropriate members like a "Researcher", a "Writer", and an "Editor", each with a descriptive role.
"""

# --- API Key and Client Initialization ---
openai_api_key = st.secrets.get("OPENAI_API_KEY")

with st.sidebar:
    st.header("Chat Controls")
    if not openai_api_key:
        openai_api_key = st.text_input("Enter your OpenAI API Key:", type="password", key="api_key_input")
    
    if st.button("Clear Chat History"):
        st.session_state.clear()
        st.rerun()

client = None
if openai_api_key:
    client = OpenAI(api_key=openai_api_key)
else:
    st.info("Please enter your OpenAI API key in the sidebar to start.")

# --- Tool & Function Definitions ---
def create_team(team_members):
    """
    Stores the generated team member details in the session state.
    This function is called by the AI model.
    """
    st.session_state.team_details = team_members
    # We return a confirmation message that can be shown to the user if needed.
    return f"Successfully created a team with {len(team_members)} members."

# This is the schema that describes the `create_team` function to the AI.
tools = [
    {
        "type": "function",
        "function": {
            "name": "create_team",
            "description": "Creates a team of AI agents with specified names, roles, and descriptions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_members": {
                        "type": "array",
                        "description": "A list of team members.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "The name of the team member."},
                                "role": {"type": "string", "description": "The specific role or job title of the member."},
                                "description": {"type": "string", "description": "A detailed description of the member's responsibilities and expertise."}
                            },
                            "required": ["name", "role", "description"]
                        }
                    }
                },
                "required": ["team_members"]
            }
        }
    }
]

# --- UI Helper Functions ---
def create_team_tabs():
    """Renders team member tabs from session state if details exist."""
    if "team_details" in st.session_state and st.session_state.team_details:
        team_members = st.session_state.team_details
        tabs = st.tabs([member["name"] for member in team_members])
        for i, member in enumerate(team_members):
            with tabs[i]:
                st.subheader(member["role"])
                st.write(member["description"])
        st.divider()
    else:
        st.error("Team details not found in session state.")


def start_team():
    """Displays concurrent progress bars."""
    start_container = st.container(border=True)
    with start_container:
        st.write("Teamwork now in progress...")
        progress_bars = {
            f"progress_{i}": st.progress(0, text=f"Team Member {i+1} - Initializing...")
            for i in range(len(st.session_state.get("team_details", [])))
        }

        # Simulate work
        for percent_complete in range(100):
            time.sleep(0.03)
            for bar in progress_bars.values():
                bar.progress(percent_complete + 1, text="Operational")
        
        time.sleep(0.5)
        success_message = st.success("Work Complete")
        time.sleep(2)
        success_message.empty()

    st.button("View Documents")


# --- Session State Initialization ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "team_details" not in st.session_state:
    st.session_state.team_details = []

# --- Display Chat History ---
chat_container = st.container(height=600, border=False)
with chat_container:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            if isinstance(message["content"], dict):
                content_type = message["content"].get("type")
                if content_type == "team_creation":
                    create_team_tabs()
                elif content_type == "start_team":
                    start_team()
            else:
                st.markdown(message["content"])

# --- Handle New User Input ---
if prompt := st.chat_input("Describe the team you want to create..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        # Handle "start team" command locally as it's a UI-only action
        if prompt.lower() == "start team":
            start_status = st.status("Starting Team...", expanded=True)
            with start_status:
                st.write("Initializing systems...")
                time.sleep(1)
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": {"type": "start_team"}
            })
        
        # For all other prompts, interact with the AI
        else:
            if not client:
                st.warning("Please provide your OpenAI API key.")
                st.stop()
            
            with st.spinner("Thinking..."):
                try:
                    # Prepare messages for the API, including the system prompt
                    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
                        {"role": msg["role"], "content": msg["content"]}
                        for msg in st.session_state.chat_history
                        if isinstance(msg["content"], str)
                    ]

                    # Call the OpenAI API with function calling enabled
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=api_messages,
                        tools=tools,
                        tool_choice="auto"
                    )
                    response_message = response.choices[0].message

                    # Check if the model wants to call a function
                    if response_message.tool_calls:
                        tool_call = response_message.tool_calls[0]
                        function_name = tool_call.function.name
                        
                        if function_name == "create_team":
                            # It wants to create a team, so we execute the function
                            function_args = json.loads(tool_call.function.arguments)
                            function_response = create_team(
                                team_members=function_args.get("team_members")
                            )
                            # Add a special message to history to render the tabs
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": {"type": "team_creation"}
                            })

                    else:
                        # It's a regular text response
                        full_response = response_message.content
                        st.session_state.chat_history.append({"role": "assistant", "content": full_response})

                except openai.AuthenticationError:
                    st.error("Authentication Error: Please check your OpenAI API key.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

    # Rerun the script to display the latest updates
    st.rerun()

