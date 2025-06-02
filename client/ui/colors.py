"""
Color definitions and styling for terminal output
"""

class Colors:
    """ANSI color codes for terminal output"""
    
    # Basic colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Bright colors
    BRIGHT_RED = '\033[1;31m'
    BRIGHT_GREEN = '\033[1;32m'
    BRIGHT_YELLOW = '\033[1;33m'
    BRIGHT_BLUE = '\033[1;34m'
    BRIGHT_MAGENTA = '\033[1;35m'
    BRIGHT_CYAN = '\033[1;36m'
    BRIGHT_WHITE = '\033[1;37m'
    
    # Dark/dim colors
    DARK_GRAY = '\033[90m'
    DARK_RED = '\033[31m'
    DARK_GREEN = '\033[32m'
    DARK_YELLOW = '\033[33m'
    DARK_BLUE = '\033[34m'
    DARK_MAGENTA = '\033[35m'
    DARK_CYAN = '\033[36m'
    
    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    
    # Reset
    RESET = '\033[0m'
    END = '\033[0m'

class Icons:
    """ASCII icons for different message types"""
    
    USER = ">"
    ASSISTANT = ">>"
    TOOL = "+"
    RESULT = "="
    ERROR = "!"
    SUCCESS = "✓"
    PROCESSING = "~"
    THINKING = "?"
    TIME = "@"
    SEPARATOR = "-"
    ARROW = "->"
    BULLET = "*"
    LOADING = "~"