import streamlit as st
import json
import openai
from openai import OpenAI
import asyncio
try:
    from agents import Agent, Runner
    AGENTS_SDK_AVAILABLE = True
except ImportError:
    AGENTS_SDK_AVAILABLE = False
    st.warning("OpenAI Agents SDK not installed. Run: pip install openai-agents")

# --- Page Config and Title ---
st.set_page_config(page_title="BiasBouncer", layout="centered")
st.markdown("<h1 style='text-align: center; color: red;'>BiasBouncer<span style='text-align: center; color: white;'> 3</span></h1>", unsafe_allow_html=True)

# --- System Prompts for the AI ---
MAIN_SYSTEM_PROMPT = """
You are BiasBouncer, an expert AI team creation assistant. 
Your primary goal is to help users build a diversified team of AI agents to accomplish a specific task.
When a user wants to create a team, you must gently guide them. Ask them at most two relatively simple clarifying questions to understand their goal if you can. 
You should not ask questions if they do not seem necessary or want to immediately create a team.
Once you have enough information, you MUST call the `create_team` function to generate the team members.

For each team member, you must provide a detailed description formatted as a bulleted list (using markdown like `- Point 1`). This description must cover at least three points:
1.  A more detailed explanation of its role and core responsibilities.
2.  How it will go about accomplishing its tasks (its methodology or process).
3.  What the ideal end product or outcome of its specific role is.

Do not just list the team members in text; you must use the provided tool to create them. Also, do not name agents with personal names unless excplicitly instructed by the user.

After creating the team, use the `create_agents` function to instantiate the actual AI agents based on the team details. DO NOT CALL THIS TOOL UNTIL USER APPROVES.
"""

EDIT_SYSTEM_PROMPT = """
You are an AI assistant impersonating and temporarily taking on the role of a specific team member who helps with informing the user and editing details.
Your primary goal is to refine the agent's details based on the user's requests; mention at the end of your response that you can edit details from the chat if necessary.
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
    
    # Display agent creation status
    if "agents_created" in st.session_state and st.session_state.agents_created:
        st.success(f"{len(st.session_state.agent_objects)} agents created")
        if st.button("View Agent Details"):
            st.session_state.show_agent_details = not st.session_state.get("show_agent_details", False)
        
        if st.session_state.get("show_agent_details", False):
            for idx, agent in enumerate(st.session_state.agent_objects):
                with st.expander(f"Agent {idx+1}: {agent['name']}"):
                    st.write(f"**Role:** {agent['role']}")
                    st.write("**Instructions:**")
                    st.code(agent['instructions'], language='text')

# Cache the OpenAI client in session state to avoid recreating it on every rerun
if openai_api_key:
    if "client" not in st.session_state:
        st.session_state.client = OpenAI(api_key=openai_api_key)
else:
    st.info("Please enter your OpenAI API key in the sidebar to start.")

client = st.session_state.get("client")

# --- Tool & Function Definitions ---
def create_team(team_members):
    """Stores the generated team member details in the session state."""
    st.session_state.team_details = team_members
    st.session_state.agents_created = False  # Reset agent creation status
    return f"Successfully created a team with {len(team_members)} members."

def update_agent_details(index, name, role, description):
    """Updates the details of a specific agent in the session state."""
    if 0 <= index < len(st.session_state.team_details):
        st.session_state.team_details[index] = {"name": name, "role": role, "description": description}
        # If agents were already created, update the corresponding agent object
        if "agent_objects" in st.session_state and st.session_state.agents_created:
            st.session_state.agent_objects[index] = create_single_agent(name, role, description)
        return "Agent details updated successfully."
    return "Error: Invalid agent index."

def create_single_agent(name, role, description):
    """Helper function to create a single agent object with instructions based on team details."""
    # Combine role and description into comprehensive instructions
    instructions = f"""You are {name}, a specialist AI agent with the role of {role}.

Your core responsibilities and approach:
{description}

You should:
1. Focus on your specific area of expertise as defined by your role
2. Provide detailed, actionable insights and recommendations
3. Collaborate effectively with other team members when needed
4. Use web research tools when necessary to gather current information
5. Maintain a professional and helpful demeanor while fulfilling your responsibilities

Remember to stay within your defined role and expertise area while being thorough and comprehensive in your approach."""
    
    # Create agent object (or dict representation if SDK not available)
    if AGENTS_SDK_AVAILABLE:
        try:
            agent = Agent(
                name=name,
                instructions=instructions,
                handoff_description=f"Specialist agent for {role}",
                # Tools will be added here when web research tool is configured
                # tools=[web_research_tool] 
            )
            return {
                "name": name,
                "role": role,
                "instructions": instructions,
                "agent_object": agent,
                "sdk_created": True
            }
        except Exception as e:
            st.warning(f"Could not create SDK agent for {name}: {str(e)}")
            return {
                "name": name,
                "role": role,
                "instructions": instructions,
                "agent_object": None,
                "sdk_created": False
            }
    else:
        return {
            "name": name,
            "role": role,
            "instructions": instructions,
            "agent_object": None,
            "sdk_created": False
        }

def create_agents():
    """Creates actual AI agents based on the team details in session state."""
    if "team_details" not in st.session_state or not st.session_state.team_details:
        return "Error: No team details found. Please create a team first."
    
    agent_objects = []
    for member in st.session_state.team_details:
        agent_obj = create_single_agent(
            member["name"],
            member["role"],
            member["description"]
        )
        agent_objects.append(agent_obj)
    
    st.session_state.agent_objects = agent_objects
    st.session_state.agents_created = True
    
    # Create a manager agent if SDK is available
    if AGENTS_SDK_AVAILABLE and any(a["sdk_created"] for a in agent_objects):
        try:
            sdk_agents = [a["agent_object"] for a in agent_objects if a["sdk_created"]]
            manager_agent = Agent(
                name="Team Manager",
                instructions="You coordinate the team of specialist agents and determine which agent should handle each task based on their expertise.",
                handoffs=sdk_agents
            )
            st.session_state.manager_agent = manager_agent
            return f"Successfully created {len(agent_objects)} AI agents with a Team Manager for coordination."
        except Exception as e:
            return f"Created {len(agent_objects)} agent configurations. Manager creation failed: {str(e)}"
    
    return f"Successfully created {len(agent_objects)} agent configurations (SDK agents will be created when the Agents SDK is properly installed)."

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
                                "description": {"type": "string", "description": "A detailed, multi-point description formatted as a markdown bulleted list."},
                                "epilogue": {"type": "string", "description": "A brief 2-3 sentence description of the team that has been created, with team names and roles specified along with their intended team dynamics."}
                            }, "required": ["name", "role", "description", "epilogue"]
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
    },
    {
        "type": "function",
        "function": {
            "name": "create_agents",
            "description": "Creates actual AI agent objects based on the team details that have been defined.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
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
        # Ensure a unique key is generated once to avoid duplicate widget keys
        if "team_unique_key" not in st.session_state:
            import uuid
            st.session_state.team_unique_key = uuid.uuid4().hex
        team_members = st.session_state.team_details
        tabs = st.tabs([member["name"] for member in team_members])
        for i, member in enumerate(team_members):
            with tabs[i]:
                st.subheader(member["name"])
                st.divider()
                st.markdown(f"**Role:** {member['role']}")
                st.markdown("**Description:**")
                st.markdown(member["description"])
                
                # Show agent status if agents have been created
                if "agent_objects" in st.session_state and st.session_state.agents_created:
                    agent_obj = st.session_state.agent_objects[i]
                
                # Use a unique key by appending the team_unique_key from session_state
                if st.button("Edit Agent", key=f"edit_btn_{i}_{st.session_state.team_unique_key}"):
                    st.session_state.editing_agent_index = i
                    st.rerun()
        st.divider()
        if len(team_members) > 0 and "epilogue" in team_members[0]:
            st.write(team_members[0].get("epilogue", ""))
    
    # Optionally, you can clear the unique key after rendering if needed
    # st.session_state.pop("team_unique_key", None)

def render_edit_dialog():
    """Renders the dialog for editing an agent by defining and then calling a decorated function."""
    agent_index = st.session_state.editing_agent_index
    agent = st.session_state.team_details[agent_index]

    @st.dialog(f"{agent['name']}", width="large")
    def show_edit_dialog():
        """Defines and displays the content of the edit dialog."""
        col1, col2 = st.columns([1,1.5], gap="medium")
        with col1:
            st.subheader("Edit Agent Details")
            
            # Manual editing fields with auto-saving
            st.text_input("Name", value=agent["name"], key=f"edit_{agent_index}_name", on_change=handle_agent_detail_change, args=(agent_index, "name"))
            st.text_input("Role", value=agent["role"], key=f"edit_{agent_index}_role", on_change=handle_agent_detail_change, args=(agent_index, "role"))
            st.text_area("Description", value=agent["description"], key=f"edit_{agent_index}_description", height=285, on_change=handle_agent_detail_change, args=(agent_index, "description"))
        
        with col2:
            st.subheader(f"Chat with {agent['name']}")
            chat_container = st.container(height=400, border=True)
            with chat_container:
                
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
                        tools=tools[0:2],  # Only use update_agent_details tool for editing
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

    # Call the decorated function to actually display the dialog
    show_edit_dialog()


# --- Session State Initialization ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "team_details" not in st.session_state:
    st.session_state.team_details = []
if "agent_chat_histories" not in st.session_state:
    st.session_state.agent_chat_histories = {}
if "agents_created" not in st.session_state:
    st.session_state.agents_created = False


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
                    for tool_call in response_message.tool_calls:
                        if tool_call.function.name == "create_team":
                            function_args = json.loads(tool_call.function.arguments)
                            result = create_team(**function_args)
                            
                            num_members = len(function_args.get("team_members", []))
                            st.session_state.agent_chat_histories = {i: [] for i in range(num_members)}

                            st.session_state.chat_history.append({"role": "assistant", "content": {"type": "team_creation"}})
                            
                            # Automatically create agents after team creation
                            agents_result = create_agents()
                            st.success(agents_result)
                            
                        elif tool_call.function.name == "create_agents":
                            agents_result = create_agents()
                            st.success(agents_result)
                else:
                    full_response = response_message.content
                    st.session_state.chat_history.append({"role": "assistant", "content": full_response})

            except openai.AuthenticationError:
                st.error("Authentication Error: Please check your OpenAI API key.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

    st.rerun()