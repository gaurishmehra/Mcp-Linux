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
    "model": "Qwen/Qwen3-32B-fast"
}

# MCP Server Configuration
MCP_CONFIG = {
    "url": "http://127.0.0.1:8000/mcp",
    "timeout": 30
}

# Chat Configuration
CHAT_CONFIG = {
    "max_tokens": 8192,
    "temperature": 0.6,
    "top_p": 0.95,
    "top_k": 20,
    "min_p": 0,
    "system_message": """
You have been given access to a MCP (model context protocol) server, by this access you have gained access to a few tools and resources.
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
    "name": "MCP Chat Client",
    "version": "2.1",
    "author": "gaurishmehra",
    "description": "Enhanced Multi-turn Chat Interface"
}

# Combined client configuration
CLIENT_CONFIG = {
    "openai": OPENAI_CONFIG,
    "mcp": MCP_CONFIG,
    "chat": CHAT_CONFIG,
    "ui": UI_CONFIG,
    "app": APP_INFO
}