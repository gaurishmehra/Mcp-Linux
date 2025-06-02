"""
Configuration settings for MCP Chat Client
"""

# OpenAI API Configuration
OPENAI_CONFIG = {
    "api_key": "eyJhbGciOiJIUzI1NiIsImtpZCI6IlV6SXJWd1h0dnprLVRvdzlLZWstc0M1akptWXBvX1VaVkxUZlpnMDRlOFUiLCJ0eXAiOiJKV1QifQ.eyJzdWIiOiJnb29nbGUtb2F1dGgyfDExMTc5NjU2NDUwODg5MzY2MTEwMiIsInNjb3BlIjoib3BlbmlkIG9mZmxpbmVfYWNjZXNzIiwiaXNzIjoiYXBpX2tleV9pc3N1ZXIiLCJhdWQiOlsiaHR0cHM6Ly9uZWJpdXMtaW5mZXJlbmNlLmV1LmF1dGgwLmNvbS9hcGkvdjIvIl0sImV4cCI6MTkwNTYwNzk3MSwidXVpZCI6IjcwZjMwYzlhLTRmN2MtNDEwOS1iM2NjLTU3OTExZWMzYTE4YSIsIm5hbWUiOiJtY3AiLCJleHBpcmVzX2F0IjoiMjAzMC0wNS0yMVQxNTozMjo1MSswMDAwIn0.uJZCgdCCZamazRCJKxLu5Ro9IjkypDamD2JAIJiPEpo",
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