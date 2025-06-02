import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_client import MCPChatClient
from ui.display import print_header, print_goodbye, print_error
from config.settings import CLIENT_CONFIG

async def main():
    """Main entry point for the MCP Chat Client"""
    try:
        print_header()
        
        client = MCPChatClient(CLIENT_CONFIG)
        await client.run()
        
    except KeyboardInterrupt:
        print_goodbye()
    except Exception as e:
        print_error(f"Failed to start MCP Chat Client: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())