# GitHub Code Review MCP Server

An MCP server that gives Claude direct access to your GitHub repositories for code review, security analysis, and developer onboarding.

## Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop) (recommended)
- Or: [Python >= 3.13](https://www.python.org/downloads/) + `uv`

## Installation

Clone the repository:

```bash
git clone <your-repo-link>
cd code-review-mcp
```

### Docker (recommended)

No Python setup needed. Docker handles the environment.

Build the image:

```bash
docker build -t code-review-mcp .
```

### Local Python

Install dependencies:

```bash
uv sync
```

Create a `.env` file:

```dotenv
GITHUB_TOKEN=your_personal_access_token
```

## Adding to Claude Desktop

Open the config file on macOS:

```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Claude Desktop — Docker

The token is passed as an environment variable at runtime — it never goes into the image.

```json
{
  "mcpServers": {
    "github-code-reviewer": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "-e", "GITHUB_TOKEN", "code-review-mcp"],
      "env": {
        "GITHUB_TOKEN": "your_github_personal_access_token"
      }
    }
  }
}
```

### Claude Desktop — Local Python

```json
{
  "mcpServers": {
    "github-code-reviewer": {
      "command": "/ABSOLUTE/PATH/TO/code-review-mcp/.venv/bin/python",
      "args": [
        "/ABSOLUTE/PATH/TO/code-review-mcp/server.py"
      ],
      "env": {
        "GITHUB_TOKEN": "your_github_personal_access_token"
      }
    }
  }
}
```

*Restart Claude Desktop entirely for changes to take effect.*

## MCP Primitives

> **Resources** = direct access to known data
> **Tools** = ways to discover, compute, or decide
> **Prompts** = pre-loaded instructions that tell Claude what to do and how to respond

## Resources

Resources are read via URI — Claude fetches them directly without needing a tool call.

| URI | What it returns |
| --- | --------------- |
| `github://{owner}/{repo}` | Repo metadata: description, default branch, language, stars, forks |
| `github://{owner}/{repo}/pulls/{pr_number}` | Full PR context: metadata + changed files + diff (bundled) |
| `github://{owner}/{repo}/blob/{branch}/{path}` | File content from a specific branch |
| `github://{owner}/{repo}/contents/{path}` | File content from the default branch (auto-resolved) |

## Tools

Tools are used when Claude needs to discover or compute something.

| Tool | What it does |
| ---- | ------------ |
| `list_public_repos` | List all public repos for the authenticated user |
| `list_open_prs` | List open PRs in a repo |
| `get_pull_request` | Get PR title, description, and branch info |
| `get_pr_files` | List files changed in a PR |
| `get_pr_diff` | Get the raw unified diff of a PR |
| `get_file_content` | Fetch raw file content from a specific branch |
| `list_files` | Browse the directory tree of a repo |

## Prompts

Prompts load structured instructions and PR/repo context in one shot.

| Prompt | Args | What it does |
| ------ | ---- | ------------ |
| `security_review` | `repo_name`, `pr_number` | Runs a security-focused review. Outputs a findings table with severity, file, line, issue, and fix — plus a verdict. |
| `explain_to_junior` | `repo_name`, `pr_number` | Explains the PR to a junior developer. No jargon, no line references — focuses on the *why*, not the *what*. |
| `onboard_me` | `repo_name` | Onboards a new developer. Claude reads the codebase and produces structured sections: what it does, structure, entry point, key modules, setup, and conventions. |

## Context Window Guards

Diffs larger than 30,000 characters are automatically truncated. The truncation notice tells Claude to use the `get_pr_diff` tool directly if the full diff is needed. Metadata and file listings are always preserved.
