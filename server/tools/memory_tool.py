import json
import os

def memoryaccesstool(operation: str, memory: str = "", memory_id: int = None, filename: str = "memory.json"):
    """
    Memory access tool for reading, writing, and editing operations with ID management.
    
    Args:
        operation (str): "read", "write", or "edit"
        memory (str): Content to write (only used in write mode)
        memory_id (int): ID of memory to remove (only used in edit mode)
        filename (str): Name of the memory file (default: "memory.json")
    
    Returns:
        str or dict: Memory content with IDs for read, status message for write/edit
    """
    
    def load_memories():
        """Load memories from file, return empty list if file doesn't exist."""
        if not os.path.exists(filename):
            return []
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                return json.load(file)
        except (json.JSONDecodeError, Exception):
            return []
    
    def save_memories(memories):
        """Save memories to file."""
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(memories, file, indent=2, ensure_ascii=False)
    
    def reassign_ids(memories):
        """Reassign IDs to be sequential starting from 1."""
        for i, memory_entry in enumerate(memories):
            memory_entry['id'] = i + 1
        return memories
    
    if operation.lower() == "read":
        try:
            memories = load_memories()
            if not memories:
                return "Memory is empty"
            
            # Format output with IDs
            result = "Memory Contents:\n" + "="*50 + "\n"
            for entry in memories:
                result += f"ID: {entry['id']}\n"
                result += f"Content: {entry['content']}\n"
                result += f"Timestamp: {entry['timestamp']}\n"
                result += "-" * 30 + "\n"
            
            return result
        except Exception as e:
            return f"Error reading memory: {str(e)}"
    
    elif operation.lower() == "write":
        try:
            memories = load_memories()
            
            # Create new memory entry with ID
            new_id = len(memories) + 1
            new_entry = {
                'id': new_id,
                'content': memory,
                'timestamp': __import__('datetime').datetime.now().isoformat()
            }
            
            # Append to memories
            memories.append(new_entry)
            save_memories(memories)
            
            return f"Memory successfully written with ID: {new_id}. Content: '{memory}'"
        except Exception as e:
            return f"Error writing to memory: {str(e)}"
    
    elif operation.lower() == "edit":
        if memory_id is None:
            return "Error: memory_id is required for edit operation"
        
        try:
            memories = load_memories()
            if not memories:
                return "No memories to edit"
            
            # Find and remove memory with specified ID
            original_count = len(memories)
            memories = [m for m in memories if m['id'] != memory_id]
            
            if len(memories) == original_count:
                return f"Memory with ID {memory_id} not found"
            
            # Reassign IDs to be sequential
            memories = reassign_ids(memories)
            save_memories(memories)
            
            return f"Memory with ID {memory_id} successfully removed. Remaining memories have been renumbered."
        except Exception as e:
            return f"Error editing memory: {str(e)}"
    
    else:
        return "Invalid operation. Use 'read', 'write', or 'edit'."


memory_tool_description = """A tool used to access external memory for saving, reading information about the user.
Use only operation = read, to read, operation = write & memory = <content> to write, and operation = edit & memory_id = <id> to remove a memory.
You must save any and all information you deem even slightly useful about the user, for smoother future interactions.
"""