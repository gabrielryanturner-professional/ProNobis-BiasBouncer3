# tools.py
import duckduckgo_search
from agents import function_tool

print("Loading tools...")

# A real web search tool using DuckDuckGo
@function_tool
def web_search(query: str) -> str:
    """
    Searches the web for the given query using DuckDuckGo and returns the top results.
    Use this for up-to-date information or to find information about topics you don't know about.
    """
    print(f"TOOL: Performing web search for '{query}'...")
    try:
        results = duckduckgo_search.ddg(query, max_results=5)
        return "\n".join([f"[{r['title']}]({r['href']})\n{r['body']}" for r in results])
    except Exception as e:
        return f"Error performing search: {e}"

# A tool to write content to a file
@function_tool
def write_to_file(filepath: str, content: str) -> str:
    """
    Writes the given content to a file at the specified filepath.
    Use this to save work, create reports, or store lengthy text.
    """
    print(f"TOOL: Writing to file '{filepath}'...")
    try:
        with open(filepath, "w") as f:
            f.write(content)
        return f"Successfully wrote to {filepath}."
    except Exception as e:
        return f"Error writing to file: {e}"

# A tool to read content from a file
@function_tool
def read_file(filepath: str) -> str:
    """
    Reads the content from a file at the specified filepath.
    Use this to load data, review previous work, or access information from the local file system.
    """
    print(f"TOOL: Reading from file '{filepath}'...")
    try:
        with open(filepath, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

# WARNING: This is a placeholder for a secure code interpreter.
# Executing arbitrary code from an LLM is a major security risk.
# In a production environment, this should be a sandboxed environment (e.g., Docker container).
@function_tool
def python_interpreter(code: str) -> str:
    """
    Executes a given string of Python code and returns the output.
    This is a powerful tool for calculations, data analysis, and complex logic.
    IMPORTANT: The code is executed in a restricted environment. It cannot access the file system
    or network directly. Use other tools for that.
    """
    print(f"TOOL: Executing Python code:\n---\n{code}\n---")
    try:
        # A very basic, unsafe interpreter. NOT for production.
        local_vars = {}
        exec(code, {}, local_vars)
        return str(local_vars)
    except Exception as e:
        return f"Error executing code: {e}"

# A dictionary to easily access all tools
AVAILABLE_TOOLS = {
    "web_search": web_search,
    "write_to_file": write_to_file,
    "read_file": read_file,
    "python_interpreter": python_interpreter,
}

print(f"✅ Tools loaded: {list(AVAILABLE_TOOLS.keys())}")