# orchestrator.py
from openai import OpenAI
import streamlit as st
from agents import Agent, tool, AgentHooks # CORRECTED: AgentHooks is the proper way to observe runs
from typing import List, Any
import json

print("Loading Orchestrator...")

# System prompt for our manager agent (No changes here)
MANAGER_SYSTEM_PROMPT = """
You are the Project Manager, a master AI agent responsible for coordinating a team of specialist agents.
Your primary goal is to achieve the user's objective by breaking it down into logical sub-tasks
and delegating them to the appropriate team member.

Here are your team members and their roles:
{team_description}

**Your Core Responsibilities:**
1.  **Analyze the Goal:** Carefully review the user's request to fully understand the desired outcome.
2.  **Formulate a Plan:** Create a step-by-step plan to achieve the goal.
3.  **Delegate Tasks:** For each step, identify the most suitable agent from your team and call them
    using their designated tool function. Provide them with all the necessary context and information.
4.  **Synthesize Results:** After a team member completes a task, analyze their output. Decide whether
    the task is complete or if another agent needs to continue the work.
5.  **Report to User:** Keep the user informed of the plan, progress, and the final outcome. Your final
    response should be a comprehensive answer to the user's original request, synthesized from the
    work of your team.

You must exclusively use your team members (the provided tools) to accomplish the goal. Do not attempt
to answer directly without delegating.
"""

# create_team_description function (No changes here)
def create_team_description(team: List[Agent]) -> str:
    description = ""
    for agent in team:
        try:
            role = agent.instructions.split("Your designated role is: ")[1].split("\n")[0]
        except IndexError:
            role = "Specialist Agent"
        description += f"- **{agent.name}**: {role}\n"
    return description

# create_project_manager function (Keeping your updated model choice)
def create_project_manager(client: OpenAI, team: List[Agent]) -> Agent:
    print("Creating Project Manager...")
    
    team_desc = create_team_description(team)
    manager_instructions = MANAGER_SYSTEM_PROMPT.format(team_description=team_desc)

    manager_tools = []
    for agent in team:
        try:
            role_description = agent.instructions.split("Your designated role is: ")[1].split("\n\n")[0]
        except IndexError:
            role_description = f"A specialist agent named {agent.name}."

        manager_tools.append(
            tool(name=agent.name, description=role_description)(agent)
        )

    manager = Agent(
        client=client,
        model="gpt-4o", # Using your preferred model
        name="ProjectManager",
        instructions=manager_instructions,
        tools=manager_tools,
    )
    print("✅ Project Manager created with the following tools:", [t.__name__ for t in manager_tools])
    return manager


# --- NEW AND CORRECTED SECTION ---

# We define a custom hooks class to stream updates to the Streamlit UI.
class MissionLogHooks(AgentHooks):
    def __init__(self, container):
        super().__init__()
        self.container = container

    def on_tool_start(self, tool_name: str, args: dict, **kwargs) -> None:
        """Called when the manager is about to call a worker agent."""
        with self.container:
            st.info(f"MANAGER: Delegating task to **{tool_name}** with args: `{json.dumps(args)}`")

    def on_tool_end(self, tool_name: str, output: Any, **kwargs) -> None:
        """Called after a worker agent finishes its task."""
        with self.container:
            with st.expander(f"Output from **{tool_name}**", expanded=False):
                # The output from another agent is also an AgentOutput object
                if hasattr(output, 'content') and output.content:
                     st.markdown(output.content[0].text.value)
                else:
                     st.text(str(output))

def run_team(manager: Agent, goal: str, chat_container):
    """
    Runs the multi-agent team to accomplish a given goal using AgentHooks for live updates.
    """
    print(f"Executing goal: {goal}")

    # 1. Instantiate our custom hooks to connect the run to our UI
    hooks = MissionLogHooks(chat_container)

    # 2. Use the agent's .run() method, which is the correct way to execute it.
    # The hooks will be called at each step of the lifecycle.
    final_response = None
    try:
        # The .run() method blocks until the entire execution is complete.
        output = manager.run(input=goal, hooks=[hooks])
        
        # The final, synthesized response is in the output object
        if output.content:
            final_response = output.content[0].text.value
            with chat_container:
                st.success("Manager has synthesized the final response:")
                st.markdown(final_response)

    except Exception as e:
        st.error(f"An error occurred during execution: {e}")
        print(f"ERROR: {e}")

    return final_response