"""
API module for MCP Chat Client
Provides streaming chat functionality for frontend applications
"""

import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncGenerator, Union
from dataclasses import dataclass, asdict

from openai_client import OpenAIClient
from mcp_handler import MCPHandler
from ui.formatter import StreamingFormatter
from config.settings import CLIENT_CONFIG

@dataclass
class ToolUsage:
    """Information about a tool that was used"""
    name: str
    arguments: Dict[str, Any]
    result: str
    execution_time: float
    success: bool
    timestamp: str

@dataclass
class ChatResponse:
    """Complete response from the chat API"""
    content: str
    tools_used: List[ToolUsage]
    total_time: float
    thinking_time: Optional[float]
    token_count: Optional[int]
    finish_reason: str
    timestamp: str
    success: bool
    error: Optional[str] = None

@dataclass
class StreamChunk:
    """Single chunk of streaming response"""
    type: str  # 'content', 'tool_call', 'tool_result', 'thinking', 'complete'
    content: Optional[str] = None
    tool_name: Optional[str] = None
    tool_arguments: Optional[Dict[str, Any]] = None
    tool_result: Optional[str] = None
    tool_success: Optional[bool] = None
    execution_time: Optional[float] = None
    timestamp: Optional[str] = None

class MCPChatAPI:
    """API wrapper for MCP Chat Client functionality"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the API with optional custom configuration"""
        self.config = config or CLIENT_CONFIG
        self.openai_client = OpenAIClient(self.config["openai"])
        self.mcp_handler = MCPHandler(self.config["mcp"])
        self.is_connected = False
        
    async def connect(self) -> Dict[str, Any]:
        """Connect to MCP server and return connection info"""
        try:
            tool_count = await self.mcp_handler.connect()
            self.is_connected = True
            return {
                "success": True,
                "tool_count": tool_count,
                "tools": [tool["function"]["name"] for tool in self.mcp_handler.get_tools()],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        if self.is_connected:
            await self.mcp_handler.disconnect()
            self.is_connected = False
    
    async def chat_stream(
        self, 
        user_message: str, 
        messages: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream chat response with real-time updates
        
        Args:
            user_message: The user's message
            messages: Optional conversation history
            
        Yields:
            StreamChunk: Real-time updates about the response
        """
        if not self.is_connected:
            await self.connect()
        
        # Initialize conversation
        conversation = messages or [{"role": "system", "content": self.config["chat"]["system_message"]}]
        conversation.append({"role": "user", "content": user_message})
        
        start_time = datetime.now()
        formatter = StreamingFormatter()
        
        try:
            while True:
                # Create streaming response
                stream = await self.openai_client.create_streaming_response(
                    conversation,
                    self.mcp_handler.get_tools(),
                    self.config["chat"]
                )
                
                if not stream:
                    yield StreamChunk(
                        type="complete",
                        content="Error: Failed to create stream",
                        timestamp=datetime.now().isoformat()
                    )
                    return
                
                # Process streaming response
                collected_content = ""
                collected_tool_calls = []
                
                for chunk in stream:
                    choice = chunk.choices[0]
                    delta = choice.delta
                    
                    # Handle content streaming
                    if delta.content:
                        formatted_content = formatter.process_chunk(delta.content)
                        collected_content += delta.content
                        
                        # Determine if this is thinking content
                        chunk_type = "thinking" if formatter.in_think_tag else "content"
                        
                        yield StreamChunk(
                            type=chunk_type,
                            content=formatted_content,
                            timestamp=datetime.now().isoformat()
                        )
                    
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
                
                # Add assistant's response to conversation
                assistant_message = {
                    "role": "assistant",
                    "content": collected_content if collected_content else None
                }
                
                # Process tool calls if they exist
                if collected_tool_calls and any(tc["id"] for tc in collected_tool_calls):
                    # Format tool calls
                    formatted_tool_calls = []
                    for tc in collected_tool_calls:
                        if tc["id"] and tc["function"]["name"]:
                            formatted_tool_calls.append({
                                "id": tc["id"],
                                "type": tc["type"],
                                "function": tc["function"]
                            })
                    
                    if formatted_tool_calls:
                        assistant_message["tool_calls"] = formatted_tool_calls
                        
                        # Notify about tool calls
                        for tool_call in formatted_tool_calls:
                            try:
                                arguments = json.loads(tool_call["function"]["arguments"])
                            except:
                                arguments = {}
                            
                            yield StreamChunk(
                                type="tool_call",
                                tool_name=tool_call["function"]["name"],
                                tool_arguments=arguments,
                                timestamp=datetime.now().isoformat()
                            )
                
                conversation.append(assistant_message)
                
                # Execute tool calls if present
                if collected_tool_calls and any(tc["id"] for tc in collected_tool_calls):
                    for tool_call in collected_tool_calls:
                        if not tool_call["id"] or not tool_call["function"]["name"]:
                            continue
                        
                        # Execute the tool call
                        tool_start = datetime.now()
                        result, execution_time = await self.mcp_handler.call_tool(tool_call)
                        
                        # Notify about tool result
                        yield StreamChunk(
                            type="tool_result",
                            tool_name=tool_call["function"]["name"],
                            tool_result=result,
                            tool_success=not result.startswith("Error"),
                            execution_time=execution_time,
                            timestamp=datetime.now().isoformat()
                        )
                        
                        # Add tool result to conversation
                        conversation.append({
                            "role": "tool",
                            "content": result,
                            "tool_call_id": tool_call["id"]
                        })
                    
                    # Continue loop for assistant's response after tools
                    continue
                else:
                    # No tool calls, we're done
                    break
            
            # Calculate thinking time
            thinking_time = formatter.get_total_thinking_time(start_time)
            
            # Send completion notification
            yield StreamChunk(
                type="complete",
                timestamp=datetime.now().isoformat()
            )
                
        except Exception as e:
            yield StreamChunk(
                type="complete",
                content=f"Error: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
    
    async def chat(
        self, 
        user_message: str, 
        messages: Optional[List[Dict[str, str]]] = None
    ) -> ChatResponse:
        """
        Complete chat interaction with full response data
        
        Args:
            user_message: The user's message
            messages: Optional conversation history
            
        Returns:
            ChatResponse: Complete response with all data
        """
        start_time = datetime.now()
        tools_used = []
        collected_content = ""
        thinking_time = None
        error = None
        
        try:
            async for chunk in self.chat_stream(user_message, messages):
                if chunk.type == "content":
                    collected_content += chunk.content or ""
                elif chunk.type == "tool_result":
                    tools_used.append(ToolUsage(
                        name=chunk.tool_name,
                        arguments={},  # Arguments were in tool_call chunk
                        result=chunk.tool_result,
                        execution_time=chunk.execution_time,
                        success=chunk.tool_success,
                        timestamp=chunk.timestamp
                    ))
                elif chunk.type == "complete":
                    if chunk.content and chunk.content.startswith("Error"):
                        error = chunk.content
                        break
            
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            return ChatResponse(
                content=collected_content,
                tools_used=tools_used,
                total_time=total_time,
                thinking_time=thinking_time,
                token_count=None,  # Not available from streaming
                finish_reason="stop",
                timestamp=end_time.isoformat(),
                success=error is None,
                error=error
            )
            
        except Exception as e:
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            return ChatResponse(
                content="",
                tools_used=tools_used,
                total_time=total_time,
                thinking_time=None,
                token_count=None,
                finish_reason="error",
                timestamp=end_time.isoformat(),
                success=False,
                error=str(e)
            )
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools"""
        return self.mcp_handler.get_tools()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the API and connections"""
        try:
            if not self.is_connected:
                await self.connect()
            
            return {
                "status": "healthy",
                "connected": self.is_connected,
                "tool_count": len(self.mcp_handler.get_tools()),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Convenience functions for quick usage
async def quick_chat(message: str) -> ChatResponse:
    """Quick chat without managing API instance"""
    api = MCPChatAPI()
    try:
        return await api.chat(message)
    finally:
        await api.disconnect()

async def quick_chat_stream(message: str) -> AsyncGenerator[StreamChunk, None]:
    """Quick streaming chat without managing API instance"""
    api = MCPChatAPI()
    try:
        async for chunk in api.chat_stream(message):
            yield chunk
    finally:
        await api.disconnect()