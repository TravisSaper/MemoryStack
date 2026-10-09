import uuid
from datetime import datetime
from mcp.server.mcpserver import MCPServer
from main import Memory, VectorStore, format_memory

mcp = MCPServer("memorystack", instructions="Long-term memory about the user. Call search_memory at the start of a task or when the user's preferences, background or past context could matter. Call add_memory when you learn a lasting fact about the user. To correct a memory delete the old one and add the new version.")
store = None

def get_store():
    global store
    if store is None:
        store = VectorStore()
    return store

@mcp.tool()
def add_memory(content: str, category: str, importance: float) -> str:
    """Save a lasting fact about the user as a standalone sentence, e.g. "User prefers fish shell over zsh". No one-off task details or secrets.
    category: one lowercase word, prefer preference, personal, project, skill, work, goal, health, relationship.
    importance 0.0-1.0: 0.9-1.0 core identity or hard rules, 0.6-0.8 strong preferences/projects/skills, 0.3-0.5 useful context, 0.0-0.2 trivia."""
    if not 0.0 <= importance <= 1.0:
        return "Error: importance must be between 0.0 and 1.0"
    if not content.strip():
        return "Error: content is empty"

    memory = Memory(
        id=str(uuid.uuid4()),
        content=content.strip(),
        category=(category or "general").strip().lower(),
        importance=importance,
        timestamp=datetime.now().isoformat()
    )
    get_store().add_memory(memory)
    return f"Saved {memory.id}"

@mcp.tool()
def search_memory(query: str, k: int = 5) -> str:
    """Semantic search over user memories. Returns [score] id | category | importance | content. Below ~0.3 is usually unrelated."""
    results = get_store().search_similar(query, k=k)
    if not results:
        return "No memories found."
    return "\n".join(format_memory(r["memory"], r["score"]) for r in results)

@mcp.tool()
def list_memories(category: str = "") -> str:
    """List all memories, or only one category."""
    mems = get_store().list_memories()
    if category:
        mems = [m for m in mems if m.category == category.strip().lower()]
    if not mems:
        return "No memories stored."
    return "\n".join(format_memory(m) for m in mems)

@mcp.tool()
def delete_memory(memory_id: str) -> str:
    """Delete a memory by id (ids come from search_memory or list_memories)."""
    if get_store().delete_memory(memory_id):
        return f"Deleted {memory_id}"
    return f"No memory found with id {memory_id}"

if __name__ == "__main__":
    mcp.run()
