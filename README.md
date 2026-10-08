# MemoryStack

Local long-term memory for AI agents. Memories are embedded with
`all-MiniLM-L6-v2` and stored in a FAISS index, so agents can search them by
meaning. Everything stays on your machine.

Use it two ways:
- **MCP server** (`server.py`): gives Claude Code, Cursor, Codex, Claude Desktop, etc.
  `add_memory`, `search_memory`, `list_memories`, and `delete_memory` tools.
- **CLI** (`main.py`): manage memories from the terminal.

## Setup

Requires Python 3.10+.

```bash
git clone https://github.com/<you>/MemoryStack.git
cd MemoryStack
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

The embedding model (~90 MB) downloads on first use.

## Connect an agent

Use absolute paths to the venv's Python and `server.py`.

**Claude Code** (available in every project):
```bash
claude mcp add memorystack --scope user -- /abs/path/MemoryStack/.venv/bin/python /abs/path/MemoryStack/server.py
```

**Claude Desktop, Cursor, and other JSON-configured clients**:
```json
{
  "mcpServers": {
    "memorystack": {
      "command": "/abs/path/MemoryStack/.venv/bin/python",
      "args": ["/abs/path/MemoryStack/server.py"]
    }
  }
}
```

**Codex** (`~/.codex/config.toml`):
```toml
[mcp_servers.memorystack]
command = "/abs/path/MemoryStack/.venv/bin/python"
args = ["/abs/path/MemoryStack/server.py"]
```

### Optional: tell the agent to use it

The server already ships usage instructions, but agents follow them more
reliably with a line in `CLAUDE.md` / `AGENTS.md`:

```md
## Memory
Use the memorystack tools for long-term memory about me. Search it at the start
of tasks where my preferences or background matter, and save lasting facts you
learn about me with a fitting category and importance.
```

## Tools

| Tool | Purpose |
|---|---|
| `add_memory(content, category, importance)` | Save a fact. The agent picks the category (`preference`, `personal`, `project`, `skill`, `work`, `goal`, ...) and importance (0.0–1.0). |
| `search_memory(query, k=5)` | Semantic search; returns score, id, category, importance, content. |
| `list_memories(category=None)` | List all memories, or one category. |
| `delete_memory(memory_id)` | Delete by id. To edit a memory, delete it and add the new version. |

## CLI

```bash
.venv/bin/python main.py --mode add --text "Prefers fish shell" --category preference --importance 0.7
.venv/bin/python main.py --mode search --text "shell" -k 3
.venv/bin/python main.py --mode list [--category preference]
.venv/bin/python main.py --mode delete --id <id>
```

## Data

Memories are stored next to the code in `memories.json` and
`memory_index.faiss`. Both are gitignored because they contain personal
information. Back them up yourself if you care about them.
