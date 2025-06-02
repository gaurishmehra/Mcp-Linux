"""
Display utilities for the MCP Chat Client UI
"""

import json
from datetime import datetime
from .colors import Colors, Icons
from config.settings import APP_INFO, UI_CONFIG

def print_timestamp():
    """Print current timestamp if enabled"""
    if UI_CONFIG["show_timestamps"]:
        now = datetime.now().strftime("%H:%M:%S")
        return f"{Colors.DIM}[{now}]{Colors.RESET}"
    return ""

def print_header():
    """Print a clean header for the application"""
    if UI_CONFIG["clear_screen_on_start"]:
        print("\033[2J\033[H")  # Clear screen and move cursor to top
    
    app_name = APP_INFO["name"]
    version = APP_INFO["version"]
    author = APP_INFO["author"]
    
    header = f"""
{Colors.BRIGHT_CYAN}MCP Chat Client v{version}{Colors.RESET}
{Colors.DIM}By {author} | 2025-05-23{Colors.RESET}

{Colors.CYAN}{Icons.BULLET} Type your message to start chatting
{Icons.BULLET} Commands: {', '.join(UI_CONFIG["exit_commands"])} to exit{Colors.RESET}

{Colors.DIM}{"─" * 50}{Colors.RESET}"""
    print(header)

def print_assistant_start():
    """Print assistant response header"""
    timestamp = print_timestamp()
    print(f"\n{timestamp} {Colors.BRIGHT_BLUE}{Icons.ASSISTANT} Assistant:{Colors.RESET} ", end='', flush=True)

def print_processing(message):
    """Print processing message"""
    print(f"\n{Colors.YELLOW}{Icons.PROCESSING} {message}{Colors.RESET}")

def print_tool_call(tool_name, arguments):
    """Print tool call information"""
    timestamp = print_timestamp()
    print(f"\n{timestamp} {Colors.BRIGHT_MAGENTA}{Icons.TOOL} Tool:{Colors.RESET} {Colors.CYAN}{tool_name}{Colors.RESET}")
    if arguments:
        try:
            formatted_args = json.dumps(arguments, indent=2)
            print(f"{Colors.DIM}  Args:{Colors.RESET}")
            for line in formatted_args.split('\n'):
                print(f"{Colors.DIM}  {line}{Colors.RESET}")
        except:
            print(f"{Colors.DIM}  Args: {arguments}{Colors.RESET}")

def print_tool_result(result, success=True):
    """Print tool result with formatting"""
    timestamp = print_timestamp()
    icon = Icons.SUCCESS if success else Icons.ERROR
    color = Colors.BRIGHT_GREEN if success else Colors.BRIGHT_RED
    
    print(f"\n{timestamp} {color}{icon} Result:{Colors.RESET}")
    
    # Truncate long results for better readability
    result_str = str(result)
    max_length = UI_CONFIG["max_result_length"]
    
    if len(result_str) > max_length:
        truncated = result_str[:max_length] + "..."
        print(f"{Colors.DIM}  {truncated}{Colors.RESET}")
        print(f"{Colors.DIM}  ... ({len(result_str)} chars total){Colors.RESET}")
    else:
        print(f"{Colors.DIM}  {result_str}{Colors.RESET}")

def print_error(message):
    """Print error message"""
    timestamp = print_timestamp()
    print(f"\n{timestamp} {Colors.BRIGHT_RED}{Icons.ERROR} Error: {message}{Colors.RESET}")

def print_separator():
    """Print a visual separator"""
    print(f"\n{Colors.DIM}{"─" * 50}{Colors.RESET}")

def print_timing(start_time, end_time, tool_timings=None):
    """Print the time taken for processing"""
    elapsed = end_time - start_time
    elapsed_seconds = elapsed.total_seconds()
    
    # Calculate tool time
    total_tool_time = sum(timing['duration'] for timing in tool_timings) if tool_timings else 0.0
    
    # Print main timing info
    if total_tool_time > 0:
        print(f"\n{Colors.BRIGHT_GREEN}⏱ Tool time: {total_tool_time:.2f}s | Total: {elapsed_seconds:.2f}s{Colors.RESET}")
        print(f"{Colors.BRIGHT_GREEN}🔧 Tools used: {len(tool_timings)}{Colors.RESET}")
        
        for timing in tool_timings:
            print(f"{Colors.GREEN}   • {timing['name']}: {timing['duration']:.2f}s{Colors.RESET}")
    else:
        print(f"\n{Colors.BRIGHT_GREEN}⏱ Total: {elapsed_seconds:.2f}s{Colors.RESET}")

def print_goodbye():
    """Print clean goodbye message"""
    goodbye = f"""
{Colors.DIM}{"─" * 50}{Colors.RESET}
{Colors.BRIGHT_GREEN}Thanks for using MCP Chat Client!{Colors.RESET}
{Colors.DIM}Session ended at {datetime.now().strftime("%H:%M:%S")}{Colors.RESET}
"""
    print(goodbye)

def print_connection_success(tool_count):
    """Print successful connection message"""
    print(f"{Colors.BRIGHT_GREEN}{Icons.SUCCESS} Connected - {tool_count} tools available{Colors.RESET}")

def print_connection_info():
    """Print connection attempt message"""
    print(f"{Colors.CYAN}{Icons.PROCESSING} Connecting to MCP server...{Colors.RESET}")