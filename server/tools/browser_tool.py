#!/usr/bin/env python3

import subprocess
import json
import pyperclip
import time

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

def browser_tool(execute: str) -> str:
    if execute != "y":
        return "This tool is not meant to be executed directly. It is designed to be used within the MCP framework."
    
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
    
    # If currently in a special workspace, toggle it off first
    current_special_name = None
    if current_workspace_info.get('is_special', False):
        current_special_name = current_workspace_info['name'].replace('special:', '')
        subprocess.run(['hyprctl', 'dispatch', 'togglespecialworkspace', current_special_name])
        time.sleep(0.1)
    
    # Switch to zen workspace
    switch_to_workspace(zen_workspace_info)
    time.sleep(0.2)
    
    # Press Ctrl+E to trigger the Firefox extension
    subprocess.run(['wtype', '-M', 'ctrl', '-k', 'e'])
    time.sleep(0.3)  # Give the extension time to copy to clipboard
    
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
    
    return pyperclip.paste()


browser_tool_description = """
Use execute=y to run the tool.
This tool gets current tab URL and title and all other tabs' URLs and titles.
"""