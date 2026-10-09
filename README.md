# MemoryStack

Local long-term memory for AI agents. Memories are embedded with
`all-mpnet-base-v2` and stored in a FAISS index, so agents can search them by
meaning. Everything stays on your machine. Works on macOS, Linux, and Windows.

Use it two ways:
- **MCP server** (`server.py`): gives Claude Code, Cursor, Codex, Claude Desktop, etc.
  `add_memory`, `search_memory`, `list_memories`, and `delete_memory` tools.
- **CLI** (`main.py`): manage memories from the terminal.

## Setup

Requires Python 3.10+ and git.

**macOS / Linux**
```bash
git clone https://github.com/TravisSaper/MemoryStack.git
cd MemoryStack
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

**Windows** (PowerShell or Command Prompt)
```powershell
git clone https://github.com/TravisSaper/MemoryStack.git
cd MemoryStack
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```
If `py` isn't found, use `python` instead. You don't need to activate the venv;
every command here calls its Python directly.

**Linux notes**
- On Debian/Ubuntu, if `python3 -m venv` fails, install it first:
  `sudo apt install python3-venv`.
- By default pip installs the GPU (CUDA) build of PyTorch on Linux, which is
  several GB. MemoryStack runs fine on CPU, so unless you want GPU support,
  install the CPU build first, then the requirements:
  ```bash
  .venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
  .venv/bin/pip install -r requirements.txt
  ```

The embedding model (~440 MB) downloads on first use, so the first command or
tool call takes a while. Run a CLI command once after setup (see [CLI](#cli))
to download it before connecting an agent.

## Connect an agent

Use absolute paths to the venv's Python and `server.py`. Your Python path is:

| OS | Python in the venv |
|---|---|
| macOS / Linux | `/abs/path/MemoryStack/.venv/bin/python` |
| Windows | `C:\abs\path\MemoryStack\.venv\Scripts\python.exe` |

**Claude Code** (available in every project):
```bash
# macOS / Linux
claude mcp add memorystack --scope user -- /abs/path/MemoryStack/.venv/bin/python /abs/path/MemoryStack/server.py
```
```powershell
# Windows
claude mcp add memorystack --scope user -- C:\abs\path\MemoryStack\.venv\Scripts\python.exe C:\abs\path\MemoryStack\server.py
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
On Windows, JSON needs every backslash doubled:
```json
{
  "mcpServers": {
    "memorystack": {
      "command": "C:\\abs\\path\\MemoryStack\\.venv\\Scripts\\python.exe",
      "args": ["C:\\abs\\path\\MemoryStack\\server.py"]
    }
  }
}
```

**Codex** (`~/.codex/config.toml`, or `%USERPROFILE%\.codex\config.toml` on Windows):
```toml
[mcp_servers.memorystack]
command = "/abs/path/MemoryStack/.venv/bin/python"
args = ["/abs/path/MemoryStack/server.py"]
```
On Windows, use single quotes so backslashes are taken literally:
```toml
[mcp_servers.memorystack]
command = 'C:\abs\path\MemoryStack\.venv\Scripts\python.exe'
args = ['C:\abs\path\MemoryStack\server.py']
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

Run these from the `MemoryStack` folder.

**macOS / Linux**
```bash
.venv/bin/python main.py --mode add --text "Prefers fish shell" --category preference --importance 0.7
.venv/bin/python main.py --mode search --text "shell" -k 3
.venv/bin/python main.py --mode list [--category preference]
.venv/bin/python main.py --mode delete --id <id>
```

**Windows**
```powershell
.venv\Scripts\python.exe main.py --mode add --text "Prefers fish shell" --category preference --importance 0.7
.venv\Scripts\python.exe main.py --mode search --text "shell" -k 3
.venv\Scripts\python.exe main.py --mode list [--category preference]
.venv\Scripts\python.exe main.py --mode delete --id <id>
```

## Data

Memories are stored next to the code in `memories.json` (the search index is
rebuilt from it on load). It is gitignored because it contains personal
information. Back it up yourself if you care about it.

Several agents and the CLI can use the same store at once: writes are locked
and each process reloads changes made by the others.
