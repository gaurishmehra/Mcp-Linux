"""
Configuration settings for MCP Chat Client
"""
import os
import dotenv
dotenv.load_dotenv()
# OpenAI API Configuration
OPENAI_CONFIG = {
    "api_key": os.getenv("key"),
    "base_url": "https://api.studio.nebius.ai/v1",
    "model": "Qwen/Qwen3-235B-A22B"
}

# MCP Server Configuration
MCP_CONFIG = {
    "url": "http://127.0.0.1:8000/mcp",
    "timeout": 30
}

# Chat Configuration
CHAT_CONFIG = {
    "max_tokens": 32768,
    "temperature": 0.6,
    "top_p": 0.95,
    "top_k": 20,
    "min_p": 0,
    "system_message": """
You are an advanced AI helper, named Gaurika.
"""
}

# UI Configuration
UI_CONFIG = {
    "max_result_length": 500,
    "clear_screen_on_start": True,
    "show_timestamps": True,
    "exit_commands": ['quit', 'exit', 'bye', 'q']
}

# Application Information
APP_INFO = {
    "name": "MCP Linux",
    "version": "6.9",
    "author": "gaurishmehra",
    "description": "Just calling an llm with some tools I deem useful",
}

# Combined client configuration
CLIENT_CONFIG = {
    "openai": OPENAI_CONFIG,
    "mcp": MCP_CONFIG,
    "chat": CHAT_CONFIG,
    "ui": UI_CONFIG,
    "app": APP_INFO
}