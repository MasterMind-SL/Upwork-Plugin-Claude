---
name: install
description: Install plugin dependencies (uv, Python packages, browser). Run this after installing the plugin from the marketplace or cloning the repo.
---

# Install Upwork Scraper Dependencies

Automate the setup of all dependencies needed for the Upwork Scraper plugin.

## Steps

1. **Check uv**: Run `uv --version` via Bash.
   - If it fails (not found), tell the user: "uv is required but not installed. Install it with: `curl -LsSf https://astral.sh/uv/install.sh | sh` (Mac/Linux) or `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` (Windows), then restart Claude Code and run this skill again."
   - If it succeeds, proceed.

2. **Install Python dependencies**: Run via Bash:
   ```
   uv sync --directory "${CLAUDE_PLUGIN_ROOT:-$PWD}"
   ```
   - If `CLAUDE_PLUGIN_ROOT` is not set, try the current working directory.
   - If that also fails, check `~/.claude/plugins/cache/upwork-scraper/` and use that path.

3. **Install browser**: Run via Bash:
   ```
   uv run --directory "${CLAUDE_PLUGIN_ROOT:-$PWD}" playwright install firefox
   ```

4. **Create .env** (optional): Check if `.env` exists in the plugin root.
   - If not, copy `.env.example` to `.env`:
     ```
     cp "${CLAUDE_PLUGIN_ROOT:-$PWD}/.env.example" "${CLAUDE_PLUGIN_ROOT:-$PWD}/.env"
     ```

5. **Verify**: Run via Bash:
   ```
   uv run --directory "${CLAUDE_PLUGIN_ROOT:-$PWD}" python -c "from src.server import mcp; print('MCP server OK')"
   ```
   - If it prints "MCP server OK", tell the user: "Installation complete! Restart Claude Code to activate the plugin, then use `/upwork-scraper:best-matches` to get started."
   - If it fails, show the error and suggest troubleshooting steps.
