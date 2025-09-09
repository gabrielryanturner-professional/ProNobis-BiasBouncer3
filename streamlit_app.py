import streamlit as st
import time
import json
import openai
from openai import OpenAI

# --- Page Config and Title ---
st.set_page_config(page_title="BiasBouncer", layout="centered")
st.markdown("<h1 style='text-align: center; color: red;'>BiasBouncer</h1>", unsafe_allow_html=True)

# --- System Prompts for the AI ---
MAIN_SYSTEM_PROMPT = """
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

# New system prompt for the editing dialog
EDIT_SYSTEM_PROMPT = """
You are an AI assistant helping a user edit a specific team member.
Your goal is to refine the agent's details based on the user's requests.
When the user asks for a change, you MUST call the `update_agent_details` function with all the new details (name, role, and description).
Do not just provide the updated text in your response; you must call the function to apply the changes.
If you are just answering a question, you can respond with text as normal.
"""


# --- API Key and Client Initialization ---
openai_api_key = st.secrets.get("OPENAI_API_KEY")

with st.sidebar:
    st.header("Chat Controls")
    if not openai_api_key:
        openai_api_key = st.text_input("Enter your OpenAI API Key:", type="password", key="api_key_input")
    
    if st.button("Clear Chat History & Team"):
        st.session_state.clear()
        st.rerun()

client = None
if openai_api_key:
    client = OpenAI(api_key=openai_api_key)
else:
    st.info("Please enter your OpenAI API key in the sidebar to start.")

# --- Tool & Function Definitions ---
def create_team(team_members):
    """Stores the generated team member details in the session state."""
    st.session_state.team_details = team_members
    return f"Successfully created a team with {len(team_members)} members."

def update_agent_details(index, name, role, description):
    """Updates the details of a specific agent in the session state."""
    if 0 <= index < len(st.session_state.team_details):
        st.session_state.team_details[index] = {"name": name, "role": role, "description": description}
        # Clear the agent's chat history after an update to start fresh
        st.session_state.agent_chat_histories[index] = []
        return "Agent details updated successfully."
    return "Error: Invalid agent index."

# Schemas for the AI tools
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
                                "description": {"type": "string", "description": "A detailed, multi-point description formatted as a markdown bulleted list."}
                            }, "required": ["name", "role", "description"]
                        }
                    }
                }, "required": ["team_members"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_agent_details",
            "description": "Updates the details for a single agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer", "description": "The index of the agent to update."},
                    "name": {"type": "string", "description": "The new name of the team member."},
                    "role": {"type": "string", "description": "The new role of the team member."},
                    "description": {"type": "string", "description": "The new detailed description of the team member, as a markdown bulleted list."}
                }, "required": ["index", "name", "role", "description"]
            }
        }
    }
]

# --- UI Helper Functions ---
def handle_agent_detail_change(agent_index, field):
    """Callback to update session state when a text field is changed in the dialog."""
    new_value = st.session_state[f"edit_{agent_index}_{field}"]
    st.session_state.team_details[agent_index][field] = new_value

def create_team_tabs():
    """Renders team member tabs and the edit button for each."""
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
                if st.button("Edit Agent", key=f"edit_btn_{i}"):
                    st.session_state.editing_agent_index = i
                    st.rerun()
        st.divider()

agent_index = st.session_state.editing_agent_index if "editing_agent_index" in st.session_state else None
agent = st.session_state.team_details[agent_index] if agent_index is not None else None
@st.dialogue(f"Editing {agent['name']}")
def render_edit_dialog():
    """Renders the m dialog for editing an agent."""

    st.subheader("Edit Agent Details")
        
        # Manual editing fields with auto-saving
    st.text_input("Name", value=agent["name"], key=f"edit_{agent_index}_name", on_change=handle_agent_detail_change, args=(agent_index, "name"))
    st.text_input("Role", value=agent["role"], key=f"edit_{agent_index}_role", on_change=handle_agent_detail_change, args=(agent_index, "role"))
    st.text_area("Description", value=agent["description"], key=f"edit_{agent_index}_description", height=250, on_change=handle_agent_detail_change, args=(agent_index, "description"))
        
    st.divider()

    st.subheader("AI-Assisted Editing")
        
        # Display agent-specific chat history
    for message in st.session_state.agent_chat_histories.get(agent_index, []):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

        # Agent-specific chat input
    if agent_prompt := st.chat_input("Ask AI to make changes..."):
        st.session_state.agent_chat_histories[agent_index].append({"role": "user", "content": agent_prompt})
            
            # Construct the context for the editing AI
        current_details = f"Current Agent Details:\nName: {agent['name']}\nRole: {agent['role']}\nDescription:\n{agent['description']}"
            
        edit_api_messages = [
            {"role": "system", "content": f"{EDIT_SYSTEM_PROMPT}\n\n{current_details}"}
        ] + st.session_state.agent_chat_histories[agent_index]

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=edit_api_messages,
                tools=tools,
                tool_choice="auto"
            )
            response_message = response.choices[0].message
                
            if response_message.tool_calls:
                tool_call = response_message.tool_calls[0]
                if tool_call.function.name == "update_agent_details":
                    function_args = json.loads(tool_call.function.arguments)
                    # The AI doesn't know the index, so we add it
                    function_args['index'] = agent_index
                    update_agent_details(**function_args)
            else:
                # Regular text response from the edit AI
                st.session_state.agent_chat_histories[agent_index].append({"role": "assistant", "content": response_message.content})
                
            st.rerun()

        except Exception as e:
            st.error(f"An error occurred: {e}")

    if st.button("Close"):
        del st.session_state.editing_agent_index
        st.rerun()
        


# --- Session State Initialization ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "team_details" not in st.session_state:
    st.session_state.team_details = []
if "agent_chat_histories" not in st.session_state:
    st.session_state.agent_chat_histories = {}


# --- Main App Logic ---

# Display the main chat history
chat_container = st.container(height=600, border=False)
with chat_container:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            if isinstance(message["content"], dict):
                content_type = message["content"].get("type")
                if content_type == "team_creation":
                    create_team_tabs()
            else:
                st.markdown(message["content"])

# If we are in editing mode, display the dialog
if "editing_agent_index" in st.session_state:
    render_edit_dialog()

# Handle new user input in the main chat
if prompt := st.chat_input("Describe the team you want to create..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        if not client:
            st.warning("Please provide your OpenAI API key.")
            st.stop()
        
        with st.spinner("Thinking..."):
            try:
                api_messages = [{"role": "system", "content": MAIN_SYSTEM_PROMPT}] + [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in st.session_state.chat_history if isinstance(msg["content"], str)
                ]

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=api_messages,
                    tools=tools,
                    tool_choice="auto"
                )
                response_message = response.choices[0].message

                if response_message.tool_calls:
                    tool_call = response_message.tool_calls[0]
                    if tool_call.function.name == "create_team":
                        function_args = json.loads(tool_call.function.arguments)
                        create_team(**function_args)
                        
                        # Initialize chat histories for the new team members
                        num_members = len(function_args.get("team_members", []))
                        st.session_state.agent_chat_histories = {i: [] for i in range(num_members)}

                        st.session_state.chat_history.append({"role": "assistant", "content": {"type": "team_creation"}})
                else:
                    full_response = response_message.content
                    st.session_state.chat_history.append({"role": "assistant", "content": full_response})

            except openai.AuthenticationError:
                st.error("Authentication Error: Please check your OpenAI API key.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

    st.rerun()