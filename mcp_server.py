
from mcp.server.fastmcp import FastMCP
import tools


# =========================================================
# MCP SERVER
# =========================================================

mcp = FastMCP("my-tools")


# =========================================================
# PYTHON EXECUTION TOOLS
# =========================================================

@mcp.tool()
def run_python(code: str) -> str:
    """
    Execute Python code and return the output.

    Use this for calculations, data processing,
    transformations, and other Python-based tasks.
    """
    return tools.run_python(code)


@mcp.tool()
def debug_python(code: str) -> dict:
    """
    Execute Python code and return structured debugging information.

    Use this when Python code fails and the error,
    traceback, or failing line needs to be inspected.
    """
    return tools.debug_python(code)


# =========================================================
# FILESYSTEM TOOLS
# =========================================================

@mcp.tool()
def read_file(filename: str) -> str:
    """
    Read the contents of a file inside the workspace.
    """
    return tools.read_file(filename)


@mcp.tool()
def write_file(filename: str, content: str) -> str:
    """
    Create or overwrite a file inside the workspace.

    Use this when the user explicitly wants
    a file created or its contents changed.
    """
    return tools.write_file(filename, content)


@mcp.tool()
def delete_file(filename: str) -> str:
    """
    Delete a file inside the workspace.

    This is a destructive operation.
    """
    return tools.delete_file(filename)


@mcp.tool()
def move_file(src: str, dst: str) -> str:
    """
    Move or rename a file inside the workspace.
    """
    return tools.move_file(src, dst)


@mcp.tool()
def create_folder(foldername: str) -> str:
    """
    Create a folder inside the workspace.
    """
    return tools.create_folder(foldername)


@mcp.tool()
def list_files(path: str = ".") -> str:
    """
    List files and folders inside a workspace directory.

    Use this when you need to inspect the project structure
    before reading or modifying files.
    """
    return tools.list_files(path)


# =========================================================
# WEB SEARCH
# =========================================================

@mcp.tool()
def search_web(query: str) -> str:
    """
    Search the web using DuckDuckGo.

    Use this when current or external web information
    is required.
    """
    return tools.search_web(query)


# =========================================================
# SERVER ENTRY POINT
# =========================================================

if __name__ == "__main__":
    mcp.run()
