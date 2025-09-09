# app.py
import streamlit as st
import json
import openai
from openai import OpenAI

# --- NEW IMPORTS ---
from agent_factory import create_agent_from_spec
from orchestrator import create_project_manager, run_team

# --- Page Config and Title ---
st.set_page_config(page_title="BiasBouncer HQ", layout="wide") # Changed to wide for more space
st.markdown("<h1 style='text-align: center; color: red;'>BiasBouncer HQ</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>Design & Deploy Autonomous AI Teams</h3>", unsafe_allow_html=True)

# --- System Prompts for the AI ---
# (No changes to system prompts, keeping them as they were)
MAIN_SYSTEM_PROMPT = """
You are BiasBouncer, an expert AI team creation assistant.
Your primary goal is to help users build a diversified team of AI agents to accomplish a specific task.
When a user wants to create a team, you must gently guide them. Ask them at most two relatively simple clarifying questions to understand their goal if you can.
You should not ask questions if they do not seem necessary or want to immediately create a team.
Once you have enough information, you MUST call the `create_team` function to generate the team members, ensuring some roles are designed to challenge assumptions and mitigate bias (e.g., 'Red Teamer', 'Ethics Auditor').

For each team member, you must provide a detailed description formatted as a bulleted list (using markdown like `- Point 1`). This description must cover at least three points:
1.  A more detailed explanation of its role and core responsibilities.
2.  How it will go about accomplishing its tasks (its methodology or process).
3.  What the ideal end product or outcome of its specific role is.

Do not just list the team members in text; you must use the provided tool to create them.
"""
EDIT_SYSTEM_PROMPT = """
You are an AI assistant helping a user edit a specific team member.
Your goal is to refine the agent's details based on the user's requests; mention at the end of your response that you can edit details from the chat if necessary.
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
    
    if st.button("Clear Chat History & Team", type="primary"):
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
    st.session_state.messages.append({"role": "assistant", "content": {"type": "team_creation_signal"}})
    return f"Successfully created a team with {len(team_members)} members. Now instantiating agents..."

def update_agent_details(index, name, role, description):
    """Updates the details of a specific agent in the session state."""
    # (No changes to this function)
    if 0 <= index < len(st.session_state.team_details):
        st.session_state.team_details[index] = {"name": name, "role": role, "description": description}
        # --- NEW ---: We need to reinstantiate the agent after editing
        st.session_state.agent_objects[index] = create_agent_from_spec(client, st.session_state.team_details[index])
        # --- NEW ---: And recreate the manager with the updated team
        st.session_state.manager_agent = create_project_manager(client, st.session_state.agent_objects)
        return "Agent details updated successfully. The agent and project manager have been re-configured."
    return "Error: Invalid agent index."

# Schemas for the AI tools (No changes)
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

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "team_details" not in st.session_state:
    st.session_state.team_details = []
if "agent_chat_histories" not in st.session_state:
    st.session_state.agent_chat_histories = {}
# --- NEW SESSION STATE KEYS ---
if "agent_objects" not in st.session_state:
    st.session_state.agent_objects = []
if "manager_agent" not in st.session_state:
    st.session_state.manager_agent = None


# --- UI: Display Chat and Team ---
st.header("Phase 1: Design Your Team")

# Display the main chat history for team creation
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if isinstance(message["content"], str):
            st.markdown(message["content"])

# Display the team tabs once created
if st.session_state.team_details:
    team_members = st.session_state.team_details
    tabs = st.tabs([member["name"] for member in team_members])
    for i, member in enumerate(team_members):
        with tabs[i]:
            st.subheader(member["name"])
            st.markdown(f"**Role:** {member['role']}")
            st.markdown("**Description:**")
            st.markdown(member["description"])
            # Edit button logic could be added here if desired

st.divider()

# --- NEW UI: Mission Control for Execution ---
if st.session_state.manager_agent:
    st.header("Phase 2: Mission Control")
    st.info("Your team is assembled and ready for deployment. Assign them a high-level goal.")

    goal_input = st.text_area("Enter the team's overall mission:", height=100, key="goal_input")
    
    if st.button("🚀 Deploy Team", type="primary"):
        if goal_input:
            st.subheader("Mission Log")
            mission_log_container = st.container(height=500, border=True)
            with st.spinner("The team is working... Please wait."):
                run_team(st.session_state.manager_agent, goal_input, mission_log_container)
            st.success("Mission accomplished!")
        else:
            st.warning("Please enter a mission goal before deploying the team.")

# Main chat input for team creation
if prompt := st.chat_input("Describe the team you want to create..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        if not client:
            st.warning("Please provide your OpenAI API key.")
            st.stop()
        
        with st.spinner("Designing team..."):
            api_messages = [{"role": "system", "content": MAIN_SYSTEM_PROMPT}] + [
                {"role": msg["role"], "content": msg["content"]}
                for msg in st.session_state.messages if isinstance(msg["content"], str)
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
                    result = create_team(**function_args)
                    st.session_state.messages.append({"role": "function", "name": "create_team", "content": result})
            else:
                full_response = response_message.content
                st.session_state.messages.append({"role": "assistant", "content": full_response})

    st.rerun()

# --- NEW LOGIC: Agent Instantiation Trigger ---
# This checks if the last message was the signal to create the team
if st.session_state.messages and isinstance(st.session_state.messages[-1]["content"], dict):
    if st.session_state.messages[-1]["content"].get("type") == "team_creation_signal":
        # Avoid re-running this block by removing the signal
        st.session_state.messages[-1]["content"] = "Team has been created. See tabs above."

        if client and st.session_state.team_details:
            with st.spinner("Instantiating agents and assigning tools... This may take a moment."):
                # Create each specialist agent
                st.session_state.agent_objects = [
                    create_agent_from_spec(client, spec) for spec in st.session_state.team_details
                ]
                # Create the project manager with the list of specialist agents
                st.session_state.manager_agent = create_project_manager(client, st.session_state.agent_objects)
            st.success("All agents are online and ready for deployment!")
            st.rerun()