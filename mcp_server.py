from mcp.server.fastmcp import FastMCP
import tools

mcp = FastMCP("my-tools")

@mcp.tool()
def run_python(code: str) -> str:
    return tools.run_python(code)

@mcp.tool()
def debug_python(code: str) -> dict:
    return tools.debug_python(code)

@mcp.tool()
def read_file(filename: str) -> str:
    return tools.read_file(filename)

@mcp.tool()
def write_file(filename: str, content: str) -> str:
    return tools.write_file(filename, content)

@mcp.tool()
def search_web(query: str) -> str:
    return tools.search_web(query)

if __name__ == "__main__":
    # Use the default transport (probably stdio or http depending on library version)
    mcp.run()