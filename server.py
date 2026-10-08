import uuid
from datetime import datetime
from typing import Optional

from mcp.server.mcpserver import MCPServer

from main import Memory, VectorStore, format_memory

mcp = MCPServer(
    "memorystack",
    instructions=(
        "Long-term memory about the user. Call search_memory at the start of a task "
        "or whenever the user's preferences, background, or past context could matter. "
        "Call add_memory whenever you learn a lasting fact about the user. "
        "To correct a memory, delete the old one and add the new version."
    ),
)

_store = None


def get_store():
    # Load lazily so the server starts fast; the embedding model takes a few seconds.
    global _store
    if _store is None:
        _store = VectorStore()
    return _store


@mcp.tool()
def add_memory(content: str, category: str, importance: float) -> str:
    """Save a lasting fact about the user.

    Write content as a standalone sentence that makes sense without the conversation,
    e.g. "User prefers fish shell over zsh". Don't save one-off task details or secrets.

    category: one short lowercase word. Prefer: preference, personal, project, skill,
    work, goal, health, relationship. Use a new word only if none fit.

    importance (0.0-1.0):
      0.9-1.0  core identity or hard rules ("never do X", name, job)
      0.6-0.8  strong preferences, ongoing projects, key skills
      0.3-0.5  useful context, mild preferences
      0.0-0.2  minor trivia
    """
    if not 0.0 <= importance <= 1.0:
        return "Error: importance must be between 0.0 and 1.0"
    if not content.strip():
        return "Error: content is empty"

    memory = Memory(
        id=str(uuid.uuid4()),
        content=content.strip(),
        category=(category or "general").strip().lower(),
        importance=importance,
        timestamp=datetime.now().isoformat(),
    )
    get_store().add_memory(memory)
    return f"Saved {memory.id}"


@mcp.tool()
def search_memory(query: str, k: int = 5) -> str:
    """Find memories about the user that are semantically similar to the query.

    Returns lines of: [score] id | category | importance | content.
    Higher score means more relevant; below ~0.3 is usually unrelated.
    """
    results = get_store().search_similar(query, k=k)
    if not results:
        return "No memories found."
    return "\n".join(format_memory(r["memory"], r["score"]) for r in results)


@mcp.tool()
def list_memories(category: Optional[str] = None) -> str:
    """List all stored memories, optionally only those in one category."""
    memories = get_store().memories
    if category:
        memories = [m for m in memories if m.category == category.strip().lower()]
    if not memories:
        return "No memories stored."
    return "\n".join(format_memory(m) for m in memories)


@mcp.tool()
def delete_memory(memory_id: str) -> str:
    """Delete a memory by its id (get ids from search_memory or list_memories)."""
    if get_store().delete_memory(memory_id):
        return f"Deleted {memory_id}"
    return f"No memory found with id {memory_id}"


if __name__ == "__main__":
    mcp.run()
