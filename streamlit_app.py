import streamlit as st
import time
import json
import openai
from openai import OpenAI
from agents import Agent

# --- Page Config and Title ---
st.set_page_config(page_title="BiasBouncer", layout="centered")
st.markdown("<h1 style='text-align: center; color: red;'>BiasBouncer</h1>", unsafe_allow_html=True)


# --- System Prompts for the AI ---
MAIN_SYSTEM_PROMPT = """
You are BiasBouncer, an expert AI team creation assistant. 
Your primary goal is to help users build a diversified team of AI agents to accomplish a specific task.
When a user wants to create a team, you must gently guide them. Ask them at most two relatively simple clarifying questions to understand their goal if you can. 
You should not ask questions if they do not seem necessary or want to immediately create a team.
Once you have enough information, you MUST call the `create_team` function to generate the team members.

After the team is created, the user will have a chance to review them. Once they are satisfied and indicate they want to start (e.g., by clicking the "Instantiate Team" button), you MUST call the `instantiate_team` function. This function takes a list of agents, each with a name, role, and description, and creates the actual agent objects.

For each team member, you must provide a detailed description formatted as a bulleted list (using markdown like `- Point 1`). This description must cover at least three points:
1.  A more detailed explanation of its role and core responsibilities.
2.  How it will go about accomplishing its tasks (its methodology or process).
3.  What the ideal end product or outcome of its specific role is.

Do not just list the team members in text; you must use the provided tool to create them.
"""

# New system prompt for the editing dialog
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
        return "Agent details updated successfully."
    return "Error: Invalid agent index."

def instantiate_team(agents_to_create):
    """
    Initializes AI agents using the OpenAI Agents SDK based on the provided details.
    """
    if not agents_to_create:
        return "Error: No agent details provided to instantiate the team."

    agent_instances = []
    for agent_data in agents_to_create:
        # Combine role and description to form the agent's instructions
        instructions = f"**Role:** {agent_data['role']}\n\n**Responsibilities & Process:**\n{agent_data['description']}"
        
        # Create an agent instance using the SDK's Agent class
        agent = Agent(
            name=agent_data['name'],
            instructions=instructions
        )
        agent_instances.append(agent)
    
    st.session_state.agent_instances = agent_instances
    st.session_state.team_started = True
    return "Team has been instantiated and is ready to go."


# Schemas for the AI tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "create_team",
            "description": "Creates a conceptual team of AI agents with specified names, roles, and descriptions.",
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
            "description": "Updates the details for a single conceptual agent.",
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
    },
    {
        "type": "function",
        "function": {
            "name": "instantiate_team",
            "description": "Finalizes the team composition and creates real agent objects using the Agents SDK. This should be called after the user confirms the team is correct.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agents_to_create": {
                        "type": "array",
                        "description": "The list of agents to instantiate.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "The name of the agent."},
                                "role": {"type": "string", "description": "The specific role for the agent."},
                                "description": {"type": "string", "description": "The detailed instructions and responsibilities for the agent."}
                            },
                            "required": ["name", "role", "description"]
                        }
                    }
                },
                "required": ["agents_to_create"]
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
    """Renders team member tabs and the edit/instantiate buttons."""
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
        
        if not st.session_state.get("team_started", False):
            if st.button("🚀 Instantiate Team", type="primary", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": "The team looks good, please instantiate the agents now."})
                st.rerun()


def render_edit_dialog():
    """Renders the dialog for editing an agent by defining and then calling a decorated function."""
    agent_index = st.session_state.editing_agent_index
    agent = st.session_state.team_details[agent_index]

    @st.dialog(f"{agent['name']}")
    def show_edit_dialog():
        """Defines and displays the content of the edit dialog."""
        st.subheader("Edit Agent Details")
        
        st.text_input("Name", value=agent["name"], key=f"edit_{agent_index}_name", on_change=handle_agent_detail_change, args=(agent_index, "name"))
        st.text_input("Role", value=agent["role"], key=f"edit_{agent_index}_role", on_change=handle_agent_detail_change, args=(agent_index, "role"))
        st.text_area("Description", value=agent["description"], key=f"edit_{agent_index}_description", height=100, on_change=handle_agent_detail_change, args=(agent_index, "description"))
        
        st.divider()

        st.subheader(f"Chat with {agent['name']}")

        chat_container = st.container(height=250, border=True)
        with chat_container:
            
            for message in st.session_state.agent_chat_histories.get(agent_index, []):
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if agent_prompt := st.chat_input("Ask AI to make changes..."):
                st.session_state.agent_chat_histories[agent_index].append({"role": "user", "content": agent_prompt})
                
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
                            function_args['index'] = agent_index
                            result = update_agent_details(**function_args)
                            st.session_state.agent_chat_histories[agent_index].append({"role": "assistant", "content": result})
                    else:
                        st.session_state.agent_chat_histories[agent_index].append({"role": "assistant", "content": response_message.content})
                    
                    st.rerun()

                except Exception as e:
                    st.error(f"An error occurred: {e}")

        if st.button("Apply Changes & Close", type="primary"):
            del st.session_state.editing_agent_index
            st.rerun()

    show_edit_dialog()


# --- Session State Initialization ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "team_details" not in st.session_state:
    st.session_state.team_details = []
if "agent_chat_histories" not in st.session_state:
    st.session_state.agent_chat_histories = {}
if "agent_instances" not in st.session_state:
    st.session_state.agent_instances = []
if "team_started" not in st.session_state:
    st.session_state.team_started = False


# --- Main App Logic ---

chat_container = st.container(height=600, border=False)
with chat_container:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            if isinstance(message["content"], dict):
                content_type = message["content"].get("type")
                if content_type == "team_creation":
                    create_team_tabs()
                elif content_type == "team_started":
                    with st.container(border=True):
                        st.success("Ready to Go.")
                        st.write("The following agents have been instantiated:")
                        st.write(st.session_state.agent_instances)
            else:
                st.markdown(message["content"])

if "editing_agent_index" in st.session_state:
    render_edit_dialog()

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

                # Special handling for instantiation prompt
                last_user_message = api_messages[-1]['content']
                if "instantiate the agents" in last_user_message:
                    # Pass the current team details directly to the model in this turn
                    # so it has the context to call instantiate_team correctly.
                    team_context = json.dumps(st.session_state.team_details, indent=2)
                    api_messages[-1]['content'] += f"\n\nHere are the current team details to instantiate:\n{team_context}"


                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=api_messages,
                    tools=tools,
                    tool_choice="auto"
                )
                response_message = response.choices[0].message

                if response_message.tool_calls:
                    tool_call = response_message.tool_calls[0]
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    if function_name == "create_team":
                        create_team(**function_args)
                        num_members = len(function_args.get("team_members", []))
                        st.session_state.agent_chat_histories = {i: [] for i in range(num_members)}
                        st.session_state.chat_history.append({"role": "assistant", "content": {"type": "team_creation"}})
                    
                    elif function_name == "instantiate_team":
                        instantiate_team(**function_args)
                        st.session_state.chat_history.append({"role": "assistant", "content": {"type": "team_started"}})

                else:
                    full_response = response_message.content
                    st.session_state.chat_history.append({"role": "assistant", "content": full_response})

            except openai.AuthenticationError:
                st.error("Authentication Error: Please check your OpenAI API key.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

    st.rerun()