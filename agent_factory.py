# agent_factory.py
import json
from openai import OpenAI
from agents import Agent

# We import our tool library
from tools import AVAILABLE_TOOLS

print("Loading Agent Factory...")

def create_instructions_from_spec(spec: dict) -> str:
    """Formats the agent's specification into a detailed system prompt."""
    return f"""You are a specialized AI agent named '{spec['name']}'.
Your designated role is: {spec['role']}.

Your primary objective and methodology are defined by the following detailed instructions:
{spec['description']}

You must strictly adhere to these instructions to fulfill your role in the team.
"""

def assign_tools(client: OpenAI, agent_instructions: str) -> list:
    """
    Uses an LLM to dynamically select the most relevant tools for an agent
    based on its instructions.
    """
    print("Assigning tools...")
    
    # We get the descriptions of the tools to help the LLM decide
    tool_descriptions = "\n".join([
        f"- {name}: {func.description}" for name, func in AVAILABLE_TOOLS.items()
    ])

    prompt = f"""
Given the following agent's instructions and a list of available tools, select the tools that
are most relevant for the agent to perform its duties.

**Agent Instructions:**
---
{agent_instructions}
---

**Available Tools:**
---
{tool_descriptions}
---

Respond with a JSON object containing a single key "tools" which is a list of the names
of the recommended tools. For example: {{"tools": ["web_search", "write_to_file"]}}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Using a smaller model for this is cost-effective
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0,
        )
        
        choice = response.choices[0].message.content
        tool_names = json.loads(choice).get("tools", [])
        
        # Map the names back to the actual tool functions
        assigned_tools = [AVAILABLE_TOOLS[name] for name in tool_names if name in AVAILABLE_TOOLS]
        
        print(f"✅ Tools assigned: {[tool.__name__ for tool in assigned_tools]}")
        return assigned_tools

    except (json.JSONDecodeError, KeyError, Exception) as e:
        print(f"⚠️ Error assigning tools: {e}. The agent will have no tools.")
        return []

def create_agent_from_spec(client: OpenAI, spec: dict) -> Agent:
    """
    Creates a single, fully configured agent from a specification dictionary.
    """
    print(f"Creating agent: {spec['name']}...")
    
    instructions = create_instructions_from_spec(spec)
    
    # Dynamically assign tools based on the instructions
    assigned_tools = assign_tools(client, instructions)
    
    # Instantiate the agent object from the SDK
    agent = Agent(
        client=client,
        model="gpt-4o", # Using a fast and capable model for the agents
        name=spec['name'].replace(" ", "_"), # Agent names cannot have spaces
        instructions=instructions,
        tools=assigned_tools,
    )
    print(f"✅ Agent '{spec['name']}' created.")
    return agent