"""
MCP server handler for tool management
"""

import json
from fastmcp import Client as MCPClient
from ui.display import print_tool_call, print_tool_result, print_error

class MCPHandler:
    """Handler for MCP server interactions"""
    
    def __init__(self, config):
        self.url = config["url"]
        self.timeout = config.get("timeout", 30)
        self.client = None
        self.tools = []
        
    async def connect(self):
        """Connect to MCP server and get available tools"""
        try:
            self.client = MCPClient(self.url)
            await self.client.__aenter__()
            
            server_tools = await self.client.list_tools()
            self.tools = []
            
            for tool in server_tools:
                self.tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })
                
            return len(self.tools)
            
        except Exception as e:
            print_error(f"Failed to connect to MCP server: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        if self.client:
            try:
                await self.client.__aexit__(None, None, None)
            except Exception as e:
                print_error(f"Error disconnecting from MCP server: {e}")
    
    def get_tools(self):
        """Get the list of available tools"""
        return self.tools
    
    async def call_tool(self, tool_call):
        """Execute a tool call and return the result"""
        from datetime import datetime
        
        function_name = tool_call["function"]["name"]
        arguments_str = tool_call["function"]["arguments"]
        
        # Validate JSON before parsing
        if not arguments_str.strip():
            error_msg = f"Empty arguments for tool: {function_name}"
            print_error(error_msg)
            return error_msg, 0.0
        
        try:
            # Test if JSON is complete and valid
            arguments = json.loads(arguments_str)
        except json.JSONDecodeError as e:
            error_msg = f"Error parsing tool arguments for {function_name}: {e}"
            print_error(error_msg)
            print(f"   Raw arguments: {repr(arguments_str)}")
            return error_msg, 0.0
        
        try:
            print_tool_call(function_name, arguments)
            
            # Track tool execution time
            tool_start = datetime.now()
            result = await self.client.call_tool(function_name, arguments)
            tool_end = datetime.now()
            execution_time = (tool_end - tool_start).total_seconds()
            
            result_str = str(result)
            print_tool_result(result_str, success=True)
            return result_str, execution_time
            
        except Exception as e:
            tool_end = datetime.now()
            execution_time = (tool_end - tool_start).total_seconds() if 'tool_start' in locals() else 0.0
            error_msg = f"Error calling tool: {e}"
            print_tool_result(error_msg, success=False)
            return error_msg, execution_time