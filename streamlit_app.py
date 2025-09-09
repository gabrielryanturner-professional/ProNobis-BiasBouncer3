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

If the user has uploaded files, you can use the file_search tool to answer questions about them.
Do not just list the team members in text; you must use the provided tool to create them.
"""

EDIT_SYSTEM_PROMPT = """
You are an AI assistant helping a user edit a specific team member.
Your goal is to refine the agent's details based on the user's requests.
When the user asks for a change, you MUST call the `update_agent_details` function with all the new details (name, role, and description).
Do not just provide the updated text in your response; you must call the function to apply the changes.
If you are just answering a question, you can respond with text as normal.
"""


# --- API Key and Client Initialization ---
openai_api_key = st.secrets.get("OPENAI_API_KEY")

client = None
if openai_api_key:
    client = OpenAI(api_key=openai_api_key)
else:
    st.info("Please enter your OpenAI API key in the sidebar to start.")

with st.sidebar:
    st.header("Chat Controls")
    if not openai_api_key:
        openai_api_key = st.text_input("Enter your OpenAI API Key:", type="password", key="api_key_input")
    
    if st.button("Clear Chat History & Team"):
        if "vector_store_id" in st.session_state and st.session_state.vector_store_id and client:
            try:
                client.beta.vector_stores.delete(st.session_state.vector_store_id)
            except Exception as e:
                print(f"Error deleting vector store: {e}")
        st.session_state.clear()
        st.rerun()

# --- Tool & Function Definitions ---
def create_team(team_members):
    st.session_state.team_details = team_members
    return f"Successfully created a team with {len(team_members)} members."

def update_agent_details(index, name, role, description):
    if 0 <= index < len(st.session_state.team_details):
        st.session_state.team_details[index] = {"name": name, "role": role, "description": description}
        return "Agent details updated successfully."
    return "Error: Invalid agent index."

base_tools = [
    {
        "type": "function",
        "function": {
            "name": "create_team", "description": "Creates a team of AI agents.", "parameters": {
                "type": "object", "properties": {
                    "team_members": { "type": "array", "description": "A list of team members.", "items": {
                            "type": "object", "properties": {
                                "name": {"type": "string"}, "role": {"type": "string"},
                                "description": {"type": "string", "description": "A detailed, multi-point markdown bulleted list."}
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
            "name": "update_agent_details", "description": "Updates details for a single agent.", "parameters": {
                "type": "object", "properties": {
                    "index": {"type": "integer"}, "name": {"type": "string"}, "role": {"type": "string"},
                    "description": {"type": "string", "description": "A detailed markdown bulleted list."}
                }, "required": ["index", "name", "role", "description"]
            }
        }
    }
]

# --- UI Helper Functions ---
def handle_agent_detail_change(agent_index, field):
    new_value = st.session_state[f"edit_{agent_index}_{field}"]
    st.session_state.team_details[agent_index][field] = new_value

def create_team_tabs():
    if "team_details" in st.session_state and st.session_state.team_details:
        tabs = st.tabs([member["name"] for member in st.session_state.team_details])
        for i, member in enumerate(st.session_state.team_details):
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

def render_edit_dialog():
    agent_index = st.session_state.editing_agent_index
    agent = st.session_state.team_details[agent_index]
    @st.dialog(f"Editing {agent['name']}")
    def show_edit_dialog():
        st.subheader("Edit Agent Details")
        st.text_input("Name", value=agent["name"], key=f"edit_{agent_index}_name", on_change=handle_agent_detail_change, args=(agent_index, "name"))
        st.text_input("Role", value=agent["role"], key=f"edit_{agent_index}_role", on_change=handle_agent_detail_change, args=(agent_index, "role"))
        st.text_area("Description", value=agent["description"], key=f"edit_{agent_index}_description", height=250, on_change=handle_agent_detail_change, args=(agent_index, "description"))
        st.divider()
        st.subheader("AI-Assisted Editing")
        for message in st.session_state.agent_chat_histories.get(agent_index, []):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        if agent_prompt := st.chat_input("Ask AI to make changes..."):
            st.session_state.agent_chat_histories[agent_index].append({"role": "user", "content": agent_prompt})
            current_details = f"Current Agent Details:\nName: {agent['name']}\nRole: {agent['role']}\nDescription:\n{agent['description']}"
            edit_api_input = [{"role": "system", "content": f"{EDIT_SYSTEM_PROMPT}\n\n{current_details}"}] + st.session_state.agent_chat_histories[agent_index]
            try:
                response = client.responses.create(model="gpt-4o", input=edit_api_input, tools=base_tools)
                if response.output and hasattr(response.output[0], 'to_json'):
                    tool_data = json.loads(response.output[0].to_json())
                    if tool_data.get("name") == "update_agent_details":
                        function_args = tool_data.get("arguments", {})
                        function_args['index'] = agent_index
                        result = update_agent_details(**function_args)
                        st.session_state.agent_chat_histories[agent_index].append({"role": "assistant", "content": result})
                elif response.output_text:
                    st.session_state.agent_chat_histories[agent_index].append({"role": "assistant", "content": response.output_text})
                st.rerun()
            except Exception as e:
                st.error(f"An error occurred: {e}")
        if st.button("Close"):
            del st.session_state.editing_agent_index
            st.rerun()
    show_edit_dialog()

def render_upload_dialog():
    @st.dialog("Upload & Manage Files")
    def show_upload_dialog():
        st.subheader("Upload New File")
        uploaded_file = st.file_uploader("Upload files to make them available for the AI to search.", type=['txt', 'pdf', 'md', 'docx', 'csv'], key="file_uploader")
        if uploaded_file:
            if uploaded_file.name not in st.session_state.uploaded_files:
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    try:
                        if not st.session_state.vector_store_id:
                            vector_store = client.beta.vector_stores.create(name="BiasBouncer Files")
                            st.session_state.vector_store_id = vector_store.id
                        client.beta.vector_stores.file_batches.upload_and_poll(vector_store_id=st.session_state.vector_store_id, files=[uploaded_file])
                        st.session_state.uploaded_files.append(uploaded_file.name)
                        st.success(f"File '{uploaded_file.name}' is now available for search.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to process file: {e}")
        st.divider()
        st.subheader("Available Files for Search")
        if st.session_state.uploaded_files:
            for f_name in st.session_state.uploaded_files:
                st.markdown(f"- {f_name}")
        else:
            st.info("No files uploaded yet.")
        if st.button("Close"):
            st.session_state.show_upload_dialog = False
            st.rerun()
    show_upload_dialog()

# --- Session State Initialization ---
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "team_details" not in st.session_state: st.session_state.team_details = []
if "agent_chat_histories" not in st.session_state: st.session_state.agent_chat_histories = {}
if "vector_store_id" not in st.session_state: st.session_state.vector_store_id = None
if "uploaded_files" not in st.session_state: st.session_state.uploaded_files = []

# --- Main App Logic ---
chat_container = st.container(height=500, border=False)
with chat_container:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            if isinstance(message["content"], dict):
                if message["content"].get("type") == "team_creation":
                    create_team_tabs()
            else:
                st.markdown(message["content"])

if "editing_agent_index" in st.session_state:
    render_edit_dialog()

if st.session_state.get("show_upload_dialog", False):
    render_upload_dialog()

if prompt := st.chat_input("Describe the team you want to create..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("assistant"):
        if not client:
            st.warning("Please provide your OpenAI API key.")
            st.stop()
        with st.spinner("Thinking..."):
            try:
                current_tools = list(base_tools)
                if st.session_state.vector_store_id:
                    file_search_tool = {"type": "file_search", "vector_store_ids": [st.session_state.vector_store_id]}
                    current_tools.append(file_search_tool)
                
                api_input = [{"role": "system", "content": MAIN_SYSTEM_PROMPT}] + [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in st.session_state.chat_history if isinstance(msg["content"], str)
                ]
                response = client.responses.create(model="gpt-4o", input=api_input, tools=current_tools)
                if response.output and hasattr(response.output[0], 'to_json'):
                    tool_data = json.loads(response.output[0].to_json())
                    if tool_data.get("name") == "create_team":
                        function_args = tool_data.get("arguments", {})
                        create_team(**function_args)
                        num_members = len(function_args.get("team_members", []))
                        st.session_state.agent_chat_histories = {i: [] for i in range(num_members)}
                        st.session_state.chat_history.append({"role": "assistant", "content": {"type": "team_creation"}})
                elif response.output_text:
                    full_response = response.output_text
                    st.session_state.chat_history.append({"role": "assistant", "content": full_response})
            except openai.AuthenticationError:
                st.error("Authentication Error: Please check your OpenAI API key.")
            except Exception as e:
                st.error(f"An error occurred: {e}")
    st.rerun()

# --- File Upload Button ---
st.divider()
if client:
    if st.button("Upload & Manage Files"):
        st.session_state.show_upload_dialog = True
        st.rerun()
else:
    st.info("Please enter your API key to enable file uploads.")