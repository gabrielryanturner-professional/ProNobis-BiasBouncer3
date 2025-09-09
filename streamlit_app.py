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

For each team member, you must provide a detailed description formatted as a bulleted list (using markdown like `- Point 1`). This description must cover at least three points:
1.  A more detailed explanation of its role and core responsibilities.
2.  How it will go about accomplishing its tasks (its methodology or process).
3.  What the ideal end product or outcome of its specific role is.

Do not just list the team members in text; you must use the provided tool to create them.
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
                                "description": {
                                    "type": "string",
                                    "description": "A detailed, multi-point description of the member's responsibilities, formatted as a markdown bulleted list. Must cover their detailed role, their process, and the ideal outcome of their work."
                                }
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
                st.subheader(member["name"])
                st.divider()
                st.markdown(f"**Role:** {member['role']}")
                st.markdown("**Description:**")
                st.markdown(member["description"])
        st.divider()
    else:
        st.error("Team details not found in session state.")


def start_team():
    """Displays concurrent progress bars."""
    start_container = st.container(border=True)
    with start_container:
        st.write("Teamwork now in progress...")
        progress_bars = {
            f"progress_{i}": st.progress(0, text=f"{st.session_state.team_details[i]['name']} - Initializing...")
            for i in range(len(st.session_state.get("team_details", [])))
        }

        # Simulate work
        for percent_complete in range(100):
            time.sleep(0.03)
            for i, bar in enumerate(progress_bars.values()):
                bar.progress(percent_complete + 1, text=f"{st.session_state.team_details[i]['name']} - Operational")
        
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
            if st.session_state.team_details:
                start_status = st.status("Starting Team...", expanded=True)
                with start_status:
                    st.write("Initializing systems...")
                    time.sleep(1)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": {"type": "start_team"}
                })
            else:
                st.warning("Please create a team before starting one.")
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "You need to create a team first! How can I help you build one?"
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
                            function_args = json.loads(tool_call.function.arguments)
                            function_response = create_team(
                                team_members=function_args.get("team_members")
                            )
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