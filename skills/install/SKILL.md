---
name: install
description: Install all plugin dependencies automatically. Run this after installing the plugin from the marketplace or cloning the repo.
---

# Install Upwork Scraper — Full Setup

Fully automated installation of everything needed to run the plugin. Run all steps sequentially — do NOT skip any step and do NOT ask for confirmation between steps.

## Determine plugin root

Set `PLUGIN_ROOT` for all subsequent commands. Try these in order until one works:
1. If environment variable `CLAUDE_PLUGIN_ROOT` is set, use that.
2. If `./pyproject.toml` exists and contains `upwork-job-scraper`, use `$PWD`.
3. Use `~/.claude/plugins/cache/upwork-scraper/` as fallback.

Store the resolved path and use it for ALL subsequent commands.

## Step 1 — Install uv (package manager)

Run via Bash: `uv --version`

If uv is NOT found, install it automatically:
- Detect the OS. Run via Bash: `uname -s` (returns "Linux", "Darwin", or contains "MINGW"/"MSYS" for Windows).
- **Windows** (MINGW/MSYS): Run via Bash with timeout 60000:
  ```
  powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **Mac/Linux**: Run via Bash with timeout 60000:
  ```
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- After install, verify with: `~/.local/bin/uv --version || uv --version`
- If it still fails, tell the user to install uv manually from https://docs.astral.sh/uv/ and stop.

## Step 2 — Install Python dependencies

Run via Bash with timeout 120000:
```
uv sync --directory "$PLUGIN_ROOT"
```

If `uv` is at `~/.local/bin/uv` (wasn't in PATH), use the full path.

## Step 3 — Install Firefox browser for Camoufox

Run via Bash with timeout 300000:
```
uv run --directory "$PLUGIN_ROOT" playwright install firefox
```

This downloads ~80MB. Be patient and use the 5-minute timeout.

## Step 4 — Create .env config

Run via Bash:
```
test -f "$PLUGIN_ROOT/.env" || cp "$PLUGIN_ROOT/.env.example" "$PLUGIN_ROOT/.env"
```

## Step 5 — Verify installation

Run via Bash:
```
uv run --directory "$PLUGIN_ROOT" python -c "from src.server import mcp; print('OK: MCP server ready')"
```

## Report results

If all steps succeeded, print exactly this (filling in the actual values):

```
Installation complete!

  Plugin root: <resolved path>
  uv: <version>
  Python packages: installed
  Firefox browser: installed
  Config: .env ready

IMPORTANT: You must restart Claude Code for the MCP server to connect.
Close this session and reopen Claude Code, then run:
  /upwork-scraper:best-matches
```

If any step failed, show which step failed with the error output and suggest how to fix it. Do NOT print the success message if any step failed.
