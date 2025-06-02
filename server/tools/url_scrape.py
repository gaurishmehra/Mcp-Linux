import subprocess
import json
import pyperclip
import time
import re
from urllib.parse import urlparse
from html.parser import HTMLParser
from html import unescape

def get_hyprland_clients():
    """Get all client windows from Hyprland"""
    try:
        result = subprocess.run(['hyprctl', 'clients', '-j'], 
                              capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error getting Hyprland clients: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return []

def find_zen_workspace():
    """Find workspace containing window with class 'zen'"""
    clients = get_hyprland_clients()
    
    zen_windows = []
    
    for client in clients:
        # Check if the window class contains 'zen' (case-insensitive)
        if 'zen' in client.get('class', '').lower():
            workspace_id = client.get('workspace', {}).get('id', 'Unknown')
            workspace_name = client.get('workspace', {}).get('name', 'Unknown')
            
            zen_windows.append({
                'title': client.get('title', 'Unknown'),
                'class': client.get('class', 'Unknown'),
                'workspace_id': workspace_id,
                'workspace_name': workspace_name
            })
    
    return zen_windows

def current_workspace():
    """Get the current workspace info (handles both regular and special workspaces)"""
    try:
        # Always get the regular active workspace first
        current_workspace = subprocess.run(['hyprctl', 'activeworkspace', '-j'],
                                         capture_output=True, text=True, check=True)
        workspace_data = json.loads(current_workspace.stdout)
        regular_workspace = {
            'id': workspace_data.get('id', 1),
            'name': workspace_data.get('name', '1'),
            'is_special': False
        }
        
        # Then check if we're in a special workspace by checking the monitor
        monitor_result = subprocess.run(['hyprctl', 'monitors', '-j'],
                                      capture_output=True, text=True, check=True)
        monitors_data = json.loads(monitor_result.stdout)
        
        # Check the first monitor's special workspace
        if monitors_data and len(monitors_data) > 0:
            special_workspace = monitors_data[0].get('specialWorkspace', {})
            if special_workspace.get('name') is not None and special_workspace.get('name') != "":
                return {
                    'id': special_workspace.get('id', -1),
                    'name': special_workspace.get('name', ''),
                    'is_special': True,
                    'underlying_workspace': regular_workspace  # Store the regular workspace underneath
                }
        
        # If not in special workspace, return regular workspace
        return regular_workspace
        
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Error getting current workspace: {e}")
        return {'id': 1, 'name': '1', 'is_special': False}

def switch_to_workspace(workspace_info):
    """Switch to workspace (handles both regular and special workspaces)"""
    if workspace_info.get('is_special', False):
        # For special workspaces, use the name
        workspace_name = workspace_info['name']
        subprocess.run(['hyprctl', 'dispatch', 'togglespecialworkspace', workspace_name.replace('special:', '')])
    else:
        # For regular workspaces, use the ID
        workspace_id = workspace_info['id']
        subprocess.run(['hyprctl', 'dispatch', 'workspace', str(workspace_id)])

def get_workspace_info(workspace_data):
    """Convert workspace data to consistent format"""
    if isinstance(workspace_data, dict):
        workspace_name = workspace_data.get('name', str(workspace_data.get('id', 1)))
        return {
            'id': workspace_data.get('id'),
            'name': workspace_name,
            'is_special': workspace_name.startswith('special:')
        }
    else:
        # Handle case where workspace_data might be just an ID
        return {
            'id': workspace_data,
            'name': str(workspace_data),
            'is_special': False
        }

def normalize_url(url):
    """Normalize URL for comparison by removing protocol and www"""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain + parsed.path

def get_all_tabs():
    """Get all tabs by pressing Ctrl+E and parsing the JSON response"""
    # Press Ctrl+E to get tab information
    subprocess.run(['wtype', '-M', 'ctrl', '-k', 'e'])
    time.sleep(0.3)  # Give the extension time to copy to clipboard
    
    # Get the clipboard content
    tab_data = pyperclip.paste()
    
    # Parse the JSON tab data
    try:
        tabs = json.loads(tab_data)
        return tabs
    except json.JSONDecodeError as e:
        print(f"Could not parse tab data as JSON: {tab_data}")
        print(f"Error: {e}")
        return {'current_tab': None, 'other_tabs': []}

def find_matching_tab(target_url, tabs):
    """Find a tab that matches the target URL (only check tabs with id <= 8)"""
    target_normalized = normalize_url(target_url)
    
    # Check current tab
    if tabs.get('current_tab') and tabs['current_tab'].get('url'):
        current_tab = tabs['current_tab']
        if current_tab.get('id', 1) <= 8 and normalize_url(current_tab['url']) == target_normalized:
            return {'type': 'current', 'id': current_tab['id']}
    
    # Check other tabs (only those with id <= 8)
    for tab in tabs.get('other_tabs', []):
        if tab.get('id', 9) <= 8 and tab.get('url') and normalize_url(tab['url']) == target_normalized:
            return {'type': 'other', 'id': tab['id']}
    
    return None

def switch_to_tab(tab_id):
    """Switch to a specific tab using Ctrl+number"""
    if 1 <= tab_id <= 8:
        # Use Ctrl+1 through Ctrl+8 to switch tabs
        subprocess.run(['wtype', '-M', 'ctrl', '-k', str(tab_id)])
        time.sleep(0.2)
        return True
    return False

def parse_page_data(json_data):
    """Parse the JSON data returned by Ctrl+G and extract relevant information"""
    try:
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
        
        # Extract the main fields
        tab_number = data.get('tab_number', 'Unknown')
        title = data.get('title', 'No title')
        url = data.get('url', 'No URL')
        content = data.get('content', 'No content')
        
        # Create a formatted output
        output_parts = []
        
        # Add title
        if title and title != 'No title':
            output_parts.append(f"TITLE: {title}")
            output_parts.append("=" * 80)
        
        # Add URL
        if url and url != 'No URL':
            output_parts.append(f"URL: {url}")
            output_parts.append("-" * 80)
        
        # Add main content
        if content and content != 'No content':
            # Clean up the content - remove excessive whitespace
            cleaned_content = re.sub(r'\s+', ' ', content.strip())
            output_parts.append(cleaned_content)
        
        # Add metadata at the end
        output_parts.append("")
        output_parts.append("=" * 80)
        output_parts.append(f"TAB: {tab_number}")
        
        return "\n".join(output_parts)
        
    except json.JSONDecodeError as e:
        print(f"Error parsing page data JSON: {e}")
        return f"Error parsing page data: {json_data[:500]}..."
    except Exception as e:
        print(f"Unexpected error parsing page data: {e}")
        return f"Error processing page data: {str(e)}"

def format_extracted_content(extracted_data):
    """Format the extracted content for display (legacy function for backward compatibility)"""
    # This function is kept for backward compatibility
    # The new parse_page_data function handles the JSON format
    if isinstance(extracted_data, str):
        try:
            # Try to parse as JSON first
            return parse_page_data(extracted_data)
        except:
            # Fall back to treating as plain text
            return extracted_data
    elif isinstance(extracted_data, dict):
        return parse_page_data(extracted_data)
    else:
        return str(extracted_data)

def scrape_url(url: str) -> str:
    """Main function to scrape URL content using Zen browser"""
    if not url:
        return "No URL provided"
    
    # Get workspace information
    zen_windows = find_zen_workspace()
    current_workspace_info = current_workspace()
    
    if not zen_windows:
        return "No Zen browser window found"
    
    zen_workspace_data = zen_windows[0]
    zen_workspace_info = get_workspace_info({
        'id': zen_workspace_data['workspace_id'],
        'name': zen_workspace_data['workspace_name']
    })
    
    print(f"Current workspace: {current_workspace_info}")
    print(f"Zen workspace: {zen_workspace_info}")
    
    # Store initial clipboard content to avoid conflicts
    initial_clipboard = pyperclip.paste()
    
    # If currently in a special workspace, toggle it off first
    current_special_name = None
    if current_workspace_info.get('is_special', False):
        current_special_name = current_workspace_info['name'].replace('special:', '')
        subprocess.run(['hyprctl', 'dispatch', 'togglespecialworkspace', current_special_name])
        time.sleep(0.1)
    
    # Switch to zen workspace
    switch_to_workspace(zen_workspace_info)
    time.sleep(0.2)
    
    try:
        # Clear clipboard before getting tab info
        pyperclip.copy("")
        time.sleep(0.1)
        
        # Get all tabs
        tabs = get_all_tabs()
        current_tab_count = 1 + len(tabs.get('other_tabs', []))
        print(f"Found current tab + {len(tabs.get('other_tabs', []))} other tabs")
        
        # Check if URL matches any existing tab (only tabs with id <= 8)
        matching_tab = find_matching_tab(url, tabs)
        opened_new_tab = False
        
        if matching_tab is not None:
            print(f"Found matching tab: {matching_tab}")
            # Switch to the matching tab using Ctrl+number
            if matching_tab['type'] == 'current':
                print("URL already in current tab")
                # Already on the correct tab, do nothing
            else:
                print(f"Switching to tab {matching_tab['id']}")
                if not switch_to_tab(matching_tab['id']):
                    print(f"Failed to switch to tab {matching_tab['id']}")
                    return "Failed to switch to matching tab"
                time.sleep(0.5)  # Increased wait time
        else:
            print(f"No matching tab found for {url} (or tab id > 8), opening new tab")
            # Open new tab with the URL
            subprocess.run(['wtype', '-M', 'ctrl', '-k', 't'])  # Ctrl+T for new tab
            time.sleep(0.5)  # Increased wait time
            
            # Type the URL
            subprocess.run(['wtype', url])
            time.sleep(0.3)
            
            # Press Enter to navigate
            subprocess.run(['wtype', '-k', 'Return'])
            time.sleep(4)  # Increased wait time for page to load
            opened_new_tab = True
        
        # Clear clipboard before copying page data
        pyperclip.copy("")
        time.sleep(0.2)
        
        # Press Ctrl+G to get the structured page data
        subprocess.run(['wtype', '-M', 'ctrl', '-k', 'g'])
        time.sleep(0.5)  # Wait for the extension to process and copy data
        
        # Get the copied JSON content
        page_json = pyperclip.paste()
        time.sleep(0.2)
        
        if opened_new_tab:
            print("Closing new tab...")
            subprocess.run(['wtype', '-M', 'ctrl', '-k', 'w'])  # Ctrl+W to close tab
            time.sleep(0.2)

        print(f"Extracted JSON data: {len(page_json)} characters")
        
        # Parse and format the JSON data
        formatted_content = parse_page_data(page_json)
        
        return formatted_content

    finally:
        # Switch back to original workspace properly
        if current_workspace_info.get('is_special', False):
            # If we were originally in a special workspace:
            # 1. First go back to the regular workspace that was underneath the special
            underlying_workspace = current_workspace_info.get('underlying_workspace')
            if underlying_workspace:
                subprocess.run(['hyprctl', 'dispatch', 'workspace', str(underlying_workspace['id'])])
            time.sleep(0.1)
            # 2. Then toggle the special workspace back on
            subprocess.run(['hyprctl', 'dispatch', 'togglespecialworkspace', current_special_name])
        else:
            # If we were in a regular workspace, just switch back normally
            switch_to_workspace(current_workspace_info)

# Description for the tool
scrape_url_description = "Scrape the readable content of a given URL. This tool returns the cleaned text content, title, and URL from the page in a structured JSON format."