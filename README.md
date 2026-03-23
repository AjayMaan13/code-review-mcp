# GitHub Code Review MCP Server

This is a Model Context Protocol (MCP) server that provides AI assistants (like Claude) with tools to interact with your GitHub repositories. Specifically, it enables retrieving Pull Requests, diffs, files, and navigating the codebase for intelligent code review and analysis.

## Prerequisites

- [Python >= 3.13](https://www.python.org/downloads/)
- `uv` (Recommended) or `pip`

## Installation

1. Clone the repository:
```bash
git clone <your-repo-link>
cd code-review-mcp
```

2. Create a `.venv` and install dependencies:
```bash
uv sync   # Or if using pip: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt/run from pyproject.toml
```

3. Create a `.env` file from the sample (or copy this):
```dotenv
GITHUB_TOKEN=your_personal_access_token
GITHUB_REPO=owner/repo_name
```

## Adding to Claude Desktop

To use this with Claude Desktop, you need to add it to your `claude_desktop_config.json` file. 

On macOS, open the config file:
```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Add the following inside `mcpServers` (Make sure to replace the paths and variables):

```json
{
  "mcpServers": {
    "github-code-reviewer": {
      "command": "/ABSOLUTE/PATH/TO/code-review-mcp/.venv/bin/python",
      "args": [
        "/ABSOLUTE/PATH/TO/code-review-mcp/server.py"
      ],
      "env": {
        "GITHUB_TOKEN": "your_github_personal_access_token",
        "GITHUB_REPO": "ajaymaan13/fraudnet-ai"
      }
    }
  }
}
```

*Restart Claude Desktop entirely for the changes to take effect.*

## Tools Provided

- `list_open_prs`: See all current PRs.
- `get_pull_request`: View title, description, and source/target branches for context.
- `get_pr_files`: See which files were modified.
- `get_pr_diff`: Parse the actual code line changes (additions/deletions).
- `list_files`: Navigate through your project's directory tree.
- `get_file_content`: Fetch raw file content on a branch to understand context.