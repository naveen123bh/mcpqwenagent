from mcp.server.fastmcp import FastMCP
import tools


# =========================================================
# MCP SERVER
# =========================================================

mcp = FastMCP("my-tools")


# =========================================================
# PYTHON TOOLS
# =========================================================

@mcp.tool()
def run_python(code: str) -> str:
    """
    Run Python code for calculations, data processing,
    analysis, and transformations.

    Prefer this tool when Python can do the actual work
    faster and more accurately than the language model.
    """
    return tools.run_python(code)


@mcp.tool()
def debug_python(code: str) -> dict:
    """
    Run Python code when debugging is required.

    Returns structured information about success,
    errors, traceback, and the failing line.
    """
    return tools.debug_python(code)


# =========================================================
# FILESYSTEM TOOLS
# =========================================================

@mcp.tool()
def list_files(path: str = ".") -> str:
    """
    List files and folders inside the workspace.

    Use this first when you need to understand
    the workspace or project structure.
    """
    return tools.list_files(path)


@mcp.tool()
def read_file(filename: str) -> str:
    """
    Read a text file inside the workspace.

    Use this when you need to inspect existing
    code, configuration, or text.
    """
    return tools.read_file(filename)


@mcp.tool()
def write_file(filename: str, content: str) -> str:
    """
    Create or overwrite a file inside the workspace.

    Use only when the user wants a file created
    or its contents changed.
    """
    return tools.write_file(filename, content)


@mcp.tool()
def delete_file(filename: str) -> str:
    """
    Delete a file inside the workspace.

    This is a destructive operation.
    Use only when deletion is explicitly required.
    """
    return tools.delete_file(filename)


@mcp.tool()
def move_file(src: str, dst: str) -> str:
    """
    Move or rename a file inside the workspace.

    Use this when an existing file needs to be
    moved or renamed.
    """
    return tools.move_file(src, dst)


@mcp.tool()
def create_folder(foldername: str) -> str:
    """
    Create a folder inside the workspace.

    Use this when a new directory is required.
    """
    return tools.create_folder(foldername)


# =========================================================
# WEB SEARCH
# =========================================================

@mcp.tool()
def search_web(query: str) -> str:
    """
    Search the web using DuckDuckGo.

    Use this only when external or current
    web information is required.
    """
    return tools.search_web(query)


# =========================================================
# SERVER ENTRY POINT
# =========================================================

if __name__ == "__main__":
    mcp.run()