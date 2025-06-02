from fastmcp import FastMCP
from tools.execute_command import execute_command, execute_command_description
from tools.websearch import scrape_web_content, websearch_description
from tools.code_execute import codeexecuter, codeexecuter_description
from tools.browser_tool import browser_tool, browser_tool_description
from tools.url_scrape import scrape_url, scrape_url_description

mcp = FastMCP("MCP Server")

@mcp.tool(description=execute_command_description)
def execute_linux_command(command: str) -> str:
    return execute_command(command)

@mcp.tool(description=websearch_description)
def websearch(query: str) -> str:
    return scrape_web_content(query, max_links=7, use_duckduckgo=True)

@mcp.tool(description=codeexecuter_description)
def code_execute(code: str) -> str:
    return codeexecuter(code)

@mcp.tool(description=browser_tool_description)
def browser_tab_tool(execute : str) -> str:
    return browser_tool(execute=execute)

@mcp.tool(description=scrape_url_description)
def scrape_url_content(url: str) -> str:
    return scrape_url(url)

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8000, path="/mcp")