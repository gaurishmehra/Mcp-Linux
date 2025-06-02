"""
Main MCP Chat Client implementation
"""

from datetime import datetime
from openai_client import OpenAIClient
from mcp_handler import MCPHandler
from ui.display import (
    print_processing, print_separator, print_goodbye, 
    print_error, print_connection_success, print_connection_info,
    print_timing
)
from ui.colors import Colors, Icons

class MCPChatClient:
    """Main MCP Chat Client class"""
    
    def __init__(self, config):
        self.config = config
        self.openai_client = OpenAIClient(config["openai"])
        self.mcp_handler = MCPHandler(config["mcp"])
        self.messages = [{"role": "system", "content": config["chat"]["system_message"]}]
        
    async def setup(self):
        """Setup the client by connecting to MCP server"""
        print_connection_info()
        tool_count = await self.mcp_handler.connect()
        print_connection_success(tool_count)
        
    async def cleanup(self):
        """Cleanup resources"""
        await self.mcp_handler.disconnect()
        
    def is_exit_command(self, user_input):
        """Check if user input is an exit command"""
        return user_input.lower() in self.config["ui"]["exit_commands"]
        
    async def process_user_input(self, user_input):
        """Process user input and generate response"""
        # Record start time for timing
        start_time = datetime.now()
        tool_timings = []
        
        # Add user message to conversation
        self.messages.append({"role": "user", "content": user_input})
        
        # Keep processing until we get a final response (no more tool calls)
        while True:
            # Create streaming response
            stream = await self.openai_client.create_streaming_response(
                self.messages, 
                self.mcp_handler.get_tools(),
                self.config["chat"]
            )
            
            if not stream:
                return
            
            # Handle the streaming response
            collected_content, collected_tool_calls = await self.openai_client.handle_streaming_response(stream)
            
            # Add assistant's response to conversation
            assistant_message = {
                "role": "assistant",
                "content": collected_content if collected_content else None
            }
            
            # Add tool calls if they exist
            if collected_tool_calls and any(tc["id"] for tc in collected_tool_calls):
                # Convert to the format expected by OpenAI
                formatted_tool_calls = []
                for tc in collected_tool_calls:
                    if tc["id"] and tc["function"]["name"]:  # Only include complete tool calls
                        formatted_tool_calls.append({
                            "id": tc["id"],
                            "type": tc["type"],
                            "function": tc["function"]
                        })
                
                if formatted_tool_calls:
                    assistant_message["tool_calls"] = formatted_tool_calls
            
            self.messages.append(assistant_message)
            
            if collected_tool_calls and any(tc["id"] for tc in collected_tool_calls):
                # Process tool calls
                for tool_call in collected_tool_calls:
                    if not tool_call["id"] or not tool_call["function"]["name"]:
                        continue
                        
                    # Execute the tool call
                    result, execution_time = await self.mcp_handler.call_tool(tool_call)
                    
                    # Track tool timing
                    tool_timings.append({
                        "name": tool_call["function"]["name"],
                        "duration": execution_time
                    })
                    
                    # Add tool result to conversation
                    self.messages.append({
                        "role": "tool",
                        "content": result,
                        "tool_call_id": tool_call["id"]
                    })
                
                # Continue the loop to get the assistant's response after tool calls
                continue
            else:
                # No tool calls, we're done with this turn
                break
        
        # Record end time and print timing
        end_time = datetime.now()
        
        print_timing(start_time, end_time, tool_timings)
    
    async def run(self):
        """Main run loop for the chat client"""
        try:
            await self.setup()
            
            while True:
                try:
                    # Get user input with colored prompt
                    print_separator()
                    user_input = input(f"{Colors.BRIGHT_GREEN}{Icons.USER} You: {Colors.RESET}").strip()
                    
                except (EOFError, KeyboardInterrupt):
                    print_goodbye()
                    break
                
                # Check for exit commands
                if self.is_exit_command(user_input):
                    print_goodbye()
                    break
                
                if not user_input:
                    continue
                
                # Show processing message after user input
                print_processing("Processing your input...")
                
                # Process the user input
                await self.process_user_input(user_input)
                
        except Exception as e:
            print_error(f"Error in chat client: {e}")
            
        finally:
            await self.cleanup()