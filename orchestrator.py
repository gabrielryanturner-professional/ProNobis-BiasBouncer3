# orchestrator.py
from openai import OpenAI
import streamlit as st
from agents import Agent, Chat, stream, tool
from typing import List

print("Loading Orchestrator...")

# System prompt for our manager agent
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

def create_team_description(team: List[Agent]) -> str:
    """Creates a formatted string describing the team for the manager's prompt."""
    description = ""
    for agent in team:
        # We access the original role from the agent's instructions.
        # This is a bit of a hack, but effective.
        try:
            role = agent.instructions.split("Your designated role is: ")[1].split("\n")[0]
        except IndexError:
            role = "Specialist Agent"
        description += f"- **{agent.name}**: {role}\n"
    return description

def create_project_manager(client: OpenAI, team: List[Agent]) -> Agent:
    """Creates and configures the Project Manager agent."""
    print("Creating Project Manager...")
    
    team_desc = create_team_description(team)
    manager_instructions = MANAGER_SYSTEM_PROMPT.format(team_description=team_desc)

    # Convert the specialist agents into tools for the manager
    manager_tools = []
    for agent in team:
        # The tool's name is the agent's name, and its description is its role.
        # This gives the manager context on who to call for what task.
        try:
            role_description = agent.instructions.split("Your designated role is: ")[1].split("\n\n")[0]
        except IndexError:
            role_description = f"A specialist agent named {agent.name}."

        manager_tools.append(
            tool(name=agent.name, description=role_description)(agent)
        )

    manager = Agent(
        client=client,
        model="gpt-4o",
        name="ProjectManager",
        instructions=manager_instructions,
        tools=manager_tools,
    )
    print("✅ Project Manager created with the following tools:", [t.__name__ for t in manager_tools])
    return manager


def run_team(manager: Agent, goal: str, chat_container):
    """
    Runs the multi-agent team to accomplish a given goal and streams the output.
    """
    print(f"Executing goal: {goal}")

    # We use the Chat object for a persistent conversation
    chat = Chat()
    chat.add_user_message(goal)

    # Stream the response to get real-time updates
    with chat_container:
        with st.chat_message("assistant"):
            full_response = ""
            placeholder = st.empty()
            try:
                for event in stream(manager, chat):
                    if event.event == "thread.run.step.requires_action":
                        tool_call = event.data.required_action.submit_tool_outputs.tool_calls[0]
                        tool_name = tool_call.function.name
                        tool_args = tool_call.function.arguments
                        st.info(f"MANAGER: Delegating task to **{tool_name}** with args: `{tool_args}`")

                    elif event.event == "thread.message.delta":
                        full_response += event.data.delta.content[0].text.value
                        placeholder.markdown(full_response + "▌")

                placeholder.markdown(full_response)

            except Exception as e:
                st.error(f"An error occurred during execution: {e}")
                print(f"ERROR: {e}")

    return full_response