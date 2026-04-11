from mcp.server.fastmcp import FastMCP
import tools

mcp = FastMCP("my-tools")


# =========================
# PYTHON TOOLS
# =========================
@mcp.tool()
def run_python(code: str) -> str:
    """Execute Python code and return output"""
    return tools.run_python(code)


@mcp.tool()
def debug_python(code: str) -> dict:
    """Run Python code with structured debug info"""
    return tools.debug_python(code)


# =========================
# FILESYSTEM TOOLS
# =========================
@mcp.tool()
def read_file(filename: str) -> str:
    """Read file content"""
    return tools.read_file(filename)


@mcp.tool()
def write_file(filename: str, content: str) -> str:
    """Write content to file"""
    return tools.write_file(filename, content)


@mcp.tool()
def delete_file(filename: str) -> str:
    """Delete a file"""
    return tools.delete_file(filename)


@mcp.tool()
def move_file(src: str, dst: str) -> str:
    """Move a file from source to destination"""
    return tools.move_file(src, dst)


@mcp.tool()
def create_folder(foldername: str) -> str:
    """Create a folder"""
    return tools.create_folder(foldername)


@mcp.tool()
def list_files(path: str = ".") -> str:
    """List files in a directory"""
    return tools.list_files(path)


# =========================
# SEARCH TOOL
# =========================
@mcp.tool()
def search_web(query: str) -> str:
    """Search the web using DuckDuckGo"""
    return tools.search_web(query)


# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    mcp.run()