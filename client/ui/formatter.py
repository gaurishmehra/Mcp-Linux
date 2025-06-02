"""
Text formatting utilities for streaming responses
"""

from .colors import Colors

class StreamingFormatter:
    """Handles streaming text formatting with proper color management"""
    
    def __init__(self):
        self.buffer = ""
        self.in_think_tag = False
        self.think_depth = 0
        self.think_end_times = []
        
    def process_chunk(self, chunk):
        """Process a streaming chunk and return formatted output"""
        from datetime import datetime
        
        self.buffer += chunk
        output = ""
        
        # Process character by character to handle streaming think tags
        i = 0
        while i < len(self.buffer):
            # Check for opening think tag
            if self.buffer[i:i+7] == '<think>':
                if not self.in_think_tag:
                    # Start think tag - switch to dark color
                    output += f"{Colors.DARK_GRAY}<think>"
                    self.in_think_tag = True
                    self.think_depth += 1
                    i += 7
                    continue
                else:
                    # Already in think tag, just add the text
                    output += '<think>'
                    self.think_depth += 1
                    i += 7
                    continue
            
            # Check for closing think tag
            elif self.buffer[i:i+8] == '</think>':
                if self.in_think_tag:
                    self.think_depth -= 1
                    if self.think_depth <= 0:
                        # End think tag - reset to normal color
                        output += f"</think>{Colors.WHITE}"
                        self.in_think_tag = False
                        self.think_depth = 0
                        self.think_end_times.append(datetime.now())
                    else:
                        output += '</think>'
                    i += 8
                    continue
                else:
                    # Not in think tag, just add the text
                    output += '</think>'
                    i += 8
                    continue
            
            # Regular character
            else:
                output += self.buffer[i]
                i += 1
        
        # Clear the buffer since we've processed everything
        self.buffer = ""
        return output
    
    def get_total_thinking_time(self, start_time):
        """Get the total time spent thinking from start to last think tag end"""
        if not self.think_end_times:
            # No think tags found, so no thinking time
            return None
        
        # Return time from start to the last think tag end
        last_think_end = max(self.think_end_times)
        return last_think_end - start_time

def print_streaming_response(content, formatter):
    """Print streaming content with proper formatting and think tag styling"""
    formatted_content = formatter.process_chunk(content)
    print(formatted_content, end='', flush=True)