"""
FastAPI server for MCP Chat API
Provides HTTP endpoints for chat functionality with streaming support
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from api import MCPChatAPI, StreamChunk, ChatResponse

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str
    messages: Optional[List[Dict[str, str]]] = None
    stream: bool = False

class ChatMessage(BaseModel):
    role: str
    content: str

class ConversationRequest(BaseModel):
    messages: List[ChatMessage]
    stream: bool = False

# Initialize FastAPI app
app = FastAPI(
    title="MCP Chat API",
    description="API for MCP Chat Client with streaming support",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global API instance
chat_api = None

@app.on_event("startup")
async def startup_event():
    """Initialize the chat API on startup"""
    global chat_api
    chat_api = MCPChatAPI()
    connection_result = await chat_api.connect()
    if not connection_result["success"]:
        raise Exception(f"Failed to connect to MCP server: {connection_result['error']}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global chat_api
    if chat_api:
        await chat_api.disconnect()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not chat_api:
        raise HTTPException(status_code=503, detail="Chat API not initialized")
    return await chat_api.health_check()

@app.get("/tools")
async def get_tools():
    """Get available tools"""
    if not chat_api:
        raise HTTPException(status_code=503, detail="Chat API not initialized")
    return {"tools": chat_api.get_available_tools()}

@app.post("/chat")
async def chat(request: ChatRequest):
    """Chat endpoint with optional streaming"""
    if not chat_api:
        raise HTTPException(status_code=503, detail="Chat API not initialized")
    
    try:
        if request.stream:
            # Return streaming response
            async def generate_stream():
                async for chunk in chat_api.chat_stream(request.message, request.messages):
                    # Convert chunk to JSON and add newline for SSE format
                    chunk_data = {
                        "type": chunk.type,
                        "content": chunk.content,
                        "tool_name": chunk.tool_name,
                        "tool_arguments": chunk.tool_arguments,
                        "tool_result": chunk.tool_result,
                        "tool_success": chunk.tool_success,
                        "execution_time": chunk.execution_time,
                        "timestamp": chunk.timestamp
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                
                # Send end marker
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream"
                }
            )
        else:
            # Return complete response
            response = await chat_api.chat(request.message, request.messages)
            return response
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/conversation")
async def chat_conversation(request: ConversationRequest):
    """Chat with full conversation history"""
    if not chat_api:
        raise HTTPException(status_code=503, detail="Chat API not initialized")
    
    try:
        # Convert Pydantic models to dict
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        if request.stream:
            # For conversation, we need the last user message
            user_message = None
            conversation_history = []
            
            for msg in messages:
                if msg["role"] == "user":
                    user_message = msg["content"]
                else:
                    conversation_history.append(msg)
            
            if not user_message:
                raise HTTPException(status_code=400, detail="No user message found in conversation")
            
            async def generate_stream():
                async for chunk in chat_api.chat_stream(user_message, conversation_history):
                    chunk_data = {
                        "type": chunk.type,
                        "content": chunk.content,
                        "tool_name": chunk.tool_name,
                        "tool_arguments": chunk.tool_arguments,
                        "tool_result": chunk.tool_result,
                        "tool_success": chunk.tool_success,
                        "execution_time": chunk.execution_time,
                        "timestamp": chunk.timestamp
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream"
                }
            )
        else:
            # For non-streaming, process the conversation
            user_message = None
            conversation_history = []
            
            for msg in messages:
                if msg["role"] == "user":
                    user_message = msg["content"]
                else:
                    conversation_history.append(msg)
            
            if not user_message:
                raise HTTPException(status_code=400, detail="No user message found in conversation")
            
            response = await chat_api.chat(user_message, conversation_history)
            return response
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )