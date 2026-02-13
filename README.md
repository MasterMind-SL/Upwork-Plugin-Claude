# Upwork Scraper - Claude Code Plugin

A Claude Code plugin that scrapes Upwork jobs, analyzes market demand, and helps freelancers build winning portfolios.

Since Upwork has no public job search API (GraphQL API doesn't support it, RSS feeds were discontinued Aug 2024), this plugin uses browser automation to scrape listings and then fetches details in parallel via HTTP.

## Features

- **One-Command Setup** - `/upwork-scraper:install` installs everything automatically
- **Best Matches** - Fetch your personalized Upwork job recommendations
- **Job Search** - Search with keywords, filters, and boolean queries
- **Market Analysis** - Understand skill demand, budget ranges, and trends
- **Portfolio Suggestions** - Get data-driven project ideas to showcase your skills
- **5 Specialized Agents** - Proposal writing, job evaluation, rate optimization, profile review, and portfolio design

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) v1.0.33+
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) and Firefox are installed automatically by `/upwork-scraper:install`

## Installation

### Option 1: Install from marketplace (recommended)

This is the easiest way. Add the marketplace and install the plugin directly inside Claude Code:

```
/plugin marketplace add MasterMind-SL/Upwork-Plugin-Claude
/plugin install upwork-scraper@upwork-plugin-claude
```

Then restart Claude Code and run the install skill:

```
/upwork-scraper:install
```

This automatically installs Python dependencies and the browser. If you prefer to do it manually:

```bash
cd ~/.claude/plugins/cache/upwork-scraper/
uv sync
uv run playwright install firefox
```

### Option 2: Install from source (for development)

```bash
# Clone the repository
git clone https://github.com/MasterMind-SL/Upwork-Plugin-Claude
cd Upwork-Plugin-Claude

# Install dependencies
uv sync
uv run playwright install firefox

# Create local config (optional)
cp .env.example .env

# Launch Claude Code with the plugin loaded
claude --plugin-dir .
```

### Option 3: Add as a team marketplace

Add this to your project's `.claude/settings.json` so team members get prompted to install it:

```json
{
  "extraKnownMarketplaces": {
    "upwork-plugin-claude": {
      "source": {
        "source": "github",
        "repo": "MasterMind-SL/Upwork-Plugin-Claude"
      }
    }
  },
  "enabledPlugins": {
    "upwork-scraper@upwork-plugin-claude": true
  }
}
```

## Usage

Once loaded, you get 5 slash commands:

| Command | Description |
|---------|-------------|
| `/upwork-scraper:install` | Install dependencies (uv, packages, browser) |
| `/upwork-scraper:best-matches` | Fetch your personalized Best Matches |
| `/upwork-scraper:search <query>` | Search jobs (e.g., `/upwork-scraper:search python fastapi`) |
| `/upwork-scraper:analyze <skill>` | Analyze market demand for a skill |
| `/upwork-scraper:portfolio <skills>` | Get portfolio project ideas for your skills |

### First-time setup

After installing, run `/upwork-scraper:install` to set up dependencies automatically. Then the first time you run a scraping command, the plugin will:

1. Open a Camoufox browser window
2. Ask you to log in to Upwork and solve any CAPTCHAs
3. Save your session cookies for future use

After the initial login, the session persists across restarts.

### Example workflow

```
> /upwork-scraper:best-matches 30

Found 30 Best Matches:
1. **AI Agent Developer** - $50-80/hr | Expert | Python, LangChain...

> /upwork-scraper:analyze python

Top skills in demand: Python (85%), FastAPI (42%), Django (38%)...

> /upwork-scraper:portfolio python,fastapi,react

Project 1: AI-Powered API Gateway...
```

## Agents

The plugin includes 5 specialized agents that Claude invokes automatically:

| Agent | What it does |
|-------|-------------|
| `portfolio-designer` | Designs open-source portfolio projects from market data |
| `proposal-writer` | Crafts tailored proposals for specific job postings |
| `job-evaluator` | Evaluates jobs for red flags, fit, and ROI before applying |
| `rate-optimizer` | Analyzes market rates and recommends optimal pricing |
| `profile-reviewer` | Reviews your Upwork profile against market demand |

## Architecture

```
Claude Code <--STDIO/JSON-RPC--> MCP Server (src/server.py)
                                      |
                                 HTTP :8024
                                      |
                                 Session Manager
                                      |
                              +-------+-------+
                         Camoufox          httpx
                         (login)      (parallel scraping)
```

The MCP server auto-starts the Session Manager on `localhost:8024`. Camoufox handles authentication and CAPTCHA solving, then transfers cookies to httpx for fast parallel scraping.

## Configuration

Environment variables (in `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SESSION_MANAGER_HOST` | `127.0.0.1` | Session Manager bind address |
| `SESSION_MANAGER_PORT` | `8024` | Session Manager port |
| `DATA_DIR` | `./data` | SQLite DB and browser profile storage |
| `BROWSER_HEADLESS` | `false` | Must be `false` for CAPTCHA solving |
| `BROWSER_TIMEOUT` | `30000` | Browser navigation timeout (ms) |

## Development

```bash
# Run tests
uv run pytest

# Run Session Manager standalone
uv run python -m src.session_manager

# Run MCP Server standalone (STDIO)
uv run python -m src.server
```

## License

MIT
