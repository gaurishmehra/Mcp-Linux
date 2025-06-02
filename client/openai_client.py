"""
OpenAI client wrapper for MCP Chat Client
"""

import json
from openai import OpenAI
from ui.formatter import StreamingFormatter, print_streaming_response
from ui.display import print_assistant_start, print_error
from ui.colors import Colors

class OpenAIClient:
    """Wrapper for OpenAI client with streaming support"""
    
    def __init__(self, config):
        self.client = OpenAI(
            api_key=config["api_key"],
            base_url=config["base_url"]
        )
        self.model = config["model"]
        
    async def create_streaming_response(self, messages, tools, chat_config):
        """Create a streaming response from OpenAI"""
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                top_p=chat_config["top_p"],
                temperature=chat_config["temperature"],
                max_tokens=chat_config["max_tokens"],
                stream=True,
                extra_body={
                    "top_k": chat_config["top_k"],
                    "min_p": chat_config["min_p"]
                }
            )
            return stream
        except Exception as e:
            print_error(f"Error creating OpenAI stream: {e}")
            return None

    async def handle_streaming_response(self, stream):
        """Handle streaming response and collect tool calls"""
        collected_content = ""
        collected_tool_calls = []
        finish_reason = None
        
        print_assistant_start()
        
        # Initialize the streaming formatter
        formatter = StreamingFormatter()
        
        # Set initial color to white for assistant messages
        print(f"{Colors.WHITE}", end='', flush=True)
        
        try:
            for chunk in stream:
                choice = chunk.choices[0]
                delta = choice.delta
                
                # Track finish reason
                if choice.finish_reason:
                    finish_reason = choice.finish_reason
                
                # Handle content streaming
                if delta.content:
                    print_streaming_response(delta.content, formatter)
                    collected_content += delta.content
                
                # Handle tool calls
                if delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        # Ensure we have enough tool calls in our collection
                        while len(collected_tool_calls) <= tool_call_delta.index:
                            collected_tool_calls.append({
                                "id": None,
                                "type": "function",
                                "function": {"name": "", "arguments": ""}
                            })
                        
                        # Update the tool call at the correct index
                        if tool_call_delta.id:
                            collected_tool_calls[tool_call_delta.index]["id"] = tool_call_delta.id
                        
                        if tool_call_delta.function:
                            if tool_call_delta.function.name:
                                collected_tool_calls[tool_call_delta.index]["function"]["name"] = tool_call_delta.function.name
                            if tool_call_delta.function.arguments:
                                collected_tool_calls[tool_call_delta.index]["function"]["arguments"] += tool_call_delta.function.arguments
        
        except Exception as e:
            print_error(f"Error during streaming: {e}")
            return collected_content, []
        
        # Reset color at the end
        print(f"{Colors.RESET}", end='', flush=True)
        
        if collected_content:
            print()  # New line after streaming content
        
        return collected_content, collected_tool_calls