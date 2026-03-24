import asyncio
from mcp.server.fastmcp import FastMCP
from github_client import GitHubClient

mcp = FastMCP("code-reviewer")

github = GitHubClient()

# Max diff characters allowed in any single context payload.
# Priority on truncation: keep metadata + file list, trim the diff.
MAX_DIFF_CHARS = 30_000

def _guard_diff(diff: str) -> str:
    if len(diff) <= MAX_DIFF_CHARS:
        return diff
    dropped = len(diff) - MAX_DIFF_CHARS
    return (
        diff[:MAX_DIFF_CHARS]
        + f"\n\n[DIFF TRUNCATED — {dropped:,} characters omitted."
        + " Use the get_pr_diff tool directly to fetch the full diff.]"
    )


# --- RESOURCES ---

# Repo metadata resource — URI: github://{owner}/{repo}
# Returns name, description, default branch, language, and stats for a repo.
# Useful as a starting point before diving into PRs or files — gives Claude
# the default branch name and general context without requiring a tool call.
@mcp.resource("github://{owner}/{repo}")
async def get_repo_resource(owner: str, repo: str) -> str:
    """Read metadata for a GitHub repository."""
    repo_name = f"{owner}/{repo}"
    try:
        r = await github.get_repo(repo_name)
        return (
            f"Repo: {r['name']}\n"
            f"Description: {r['description']}\n"
            f"Default Branch: {r['default_branch']}\n"
            f"Language: {r['language']}\n"
            f"Stars: {r['stars']}  Forks: {r['forks']}  Open Issues: {r['open_issues']}\n"
            f"Private: {r['private']}\n"
            f"URL: {r['url']}"
        )
    except Exception as e:
        return f"Error getting repo metadata: {e}"


# Bundled PR resource — URI: github://{owner}/{repo}/pulls/{pr_number}
# Composes get_pull_request + get_pr_files + get_pr_diff into a single response.
# Useful because Claude gets everything it needs for a full code review in one
# resource read, instead of making three separate tool calls.
@mcp.resource("github://{owner}/{repo}/pulls/{pr_number}")
async def get_pr_resource(owner: str, repo: str, pr_number: int) -> str:
    """Read full PR context: metadata, changed files, and raw diff."""
    repo_name = f"{owner}/{repo}"
    try:
        pr, files, diff = await asyncio.gather(
            github.get_pull_request(repo_name, pr_number),
            github.get_pr_files(repo_name, pr_number),
            github.get_pr_diff(repo_name, pr_number),
        )

        files_list = "\n".join(f"  - {f['filename']} ({f['status']})" for f in files)

        return (
            f"Title: {pr['title']}\n"
            f"Description: {pr['description']}\n"
            f"Branch: {pr['head_branch']} → {pr['base_branch']}\n\n"
            f"Changed Files:\n{files_list}\n\n"
            f"Diff:\n{_guard_diff(diff)}"
        )
    except Exception as e:
        return f"Error getting PR: {e}"

# File resource (branch-aware) — URI: github://{owner}/{repo}/blob/{branch}/{path}
# Use this when the branch is already known (e.g. from PR head branch).
@mcp.resource("github://{owner}/{repo}/blob/{branch}/{path}")
async def get_file_content_resource(owner: str, repo: str, branch: str, path: str) -> str:
    """Read a specific file from a known branch."""
    repo_name = f"{owner}/{repo}"
    try:
        return await github.get_file_content(repo_name, path, branch)
    except Exception as e:
        return f"Error getting file content: {e}"


# File resource (default branch) — URI: github://{owner}/{repo}/contents/{path}
# Use this when the branch is unknown — auto-resolves the repo's default branch.
# Easier for Claude to use since it doesn't need branch context upfront.
@mcp.resource("github://{owner}/{repo}/contents/{path}")
async def get_file_content_default_resource(owner: str, repo: str, path: str) -> str:
    """Read a specific file from the repo's default branch."""
    repo_name = f"{owner}/{repo}"
    try:
        repo_meta = await github.get_repo(repo_name)
        branch = repo_meta["default_branch"]
        return await github.get_file_content(repo_name, path, branch)
    except Exception as e:
        return f"Error getting file content: {e}"


# --- PROMPTS ---

@mcp.prompt()
async def security_review(repo_name: str, pr_number: int) -> str:
    """
    Run a security-focused review on a pull request.
    Fetches the full PR and instructs Claude on what to look for.
    """
    try:
        pr, files, diff = await asyncio.gather(
            github.get_pull_request(repo_name, pr_number),
            github.get_pr_files(repo_name, pr_number),
            github.get_pr_diff(repo_name, pr_number),
        )

        files_list = "\n".join(f"  - {f['filename']} ({f['status']})" for f in files)

        pr_context = (
            f"Title: {pr['title']}\n"
            f"Description: {pr['description']}\n"
            f"Branch: {pr['head_branch']} → {pr['base_branch']}\n\n"
            f"Changed Files:\n{files_list}\n\n"
            f"Diff:\n{_guard_diff(diff)}"
        )
    except Exception as e:
        return f"Error loading PR for security review: {e}"

    return f"""You are a security-focused code reviewer. Analyze the pull request below.

Check for:
- Injection vulnerabilities (SQL, command, LDAP, XPath)
- Broken authentication or session management
- Sensitive data exposure (secrets, tokens, PII in logs or responses)
- Insecure direct object references
- Missing or incorrect input validation
- Insecure dependencies or version pinning issues
- Hardcoded credentials or API keys
- Unsafe deserialization
- Missing authorization checks (can user A access user B's data?)
- Use of deprecated or known-unsafe functions

Output format — use exactly this structure:

## Summary
One sentence on the overall security posture of this PR.

## Findings

| Severity | File | Line | Issue | Fix |
|----------|------|------|-------|-----|
| Critical/High/Medium/Low | filename | line # | what the vulnerability is | concrete fix |

Add one row per finding. If no issues found, write "No findings." in the table body.

## Verdict
APPROVED / APPROVED WITH COMMENTS / CHANGES REQUIRED — one sentence justifying it.

---

{pr_context}"""


@mcp.prompt()
async def explain_to_junior(repo_name: str, pr_number: int) -> str:
    """
    Explain a pull request to a junior developer.
    Focuses on the why, not the what. No jargon, no line references.
    """
    try:
        pr, files, diff = await asyncio.gather(
            github.get_pull_request(repo_name, pr_number),
            github.get_pr_files(repo_name, pr_number),
            github.get_pr_diff(repo_name, pr_number),
        )

        files_list = "\n".join(f"  - {f['filename']} ({f['status']})" for f in files)

        pr_context = (
            f"Title: {pr['title']}\n"
            f"Description: {pr['description']}\n"
            f"Branch: {pr['head_branch']} → {pr['base_branch']}\n\n"
            f"Changed Files:\n{files_list}\n\n"
            f"Diff:\n{_guard_diff(diff)}"
        )
    except Exception as e:
        return f"Error loading PR: {e}"

    return f"""You are explaining a code change to a junior developer who is still learning.

Rules you must follow — no exceptions:
- No technical jargon. If you must use a technical term, define it immediately in plain English.
- Never reference specific line numbers or file paths.
- Focus on WHY the change was made, not WHAT was changed. The diff shows what — your job is the why.
- Explain the problem that existed before this change and why it mattered.
- Explain what is better now and what that means for the user or system.
- Use analogies if they help. Keep sentences short.
- End with one sentence the junior can use to explain this change to someone else.

---

{pr_context}"""


@mcp.prompt()
async def onboard_me(repo_name: str) -> str:
    """
    Onboard a new developer to a repository.
    Tells Claude to explore the codebase using list_files and get_file_content
    to build a picture of how the project is structured and how it works.
    """
    try:
        repo_meta = await github.get_repo(repo_name)
        root_files = await github.list_files(repo_name, "")
        root_listing = "\n".join(f"  {item['type']}: {item['path']}" for item in root_files)
    except Exception as e:
        return f"Error loading repo: {e}"

    return f"""You are onboarding a new developer to this repository. Your goal is to give them a complete mental model of the project so they can start contributing confidently.

You have access to these tools — use them actively:
- `list_files` to explore directories you want to understand
- `get_file_content` to read key files (entry points, config, core modules)

Here is what to cover, in this order:
1. What does this project do and who is it for? (use the description and README if present)
2. How is the codebase structured? Walk through the top-level directories and explain the role of each.
3. Where is the entry point? Trace how a request or job starts and flows through the system.
4. What are the key abstractions or modules a new developer will touch most often?
5. What does the dev need to set up locally to run this? (look for config files, .env examples, requirements)
6. Are there any non-obvious conventions or patterns in the code worth flagging?

Be concrete. Read the actual files — don't guess. If something is unclear after reading, say so.

Output format — use exactly these sections in this order:

## What It Does
## Project Structure
## Entry Point
## Key Modules
## Local Setup
## Conventions & Gotchas

---

Repo: {repo_meta['name']}
Description: {repo_meta['description']}
Language: {repo_meta['language']}
Default Branch: {repo_meta['default_branch']}

Root file listing:
{root_listing}"""


# --- TOOLS ---

@mcp.tool()
async def list_public_repos() -> str:
    """
    Get a list of all public repos created by the user and return them
    """

    try:
        repos = await github.list_repos()
        
        output = []
        for repo in repos:
            output.append(f"{repo['name']}")
        
        return "\n".join(output) if output else "No Repos found."
    except Exception as e:
        return f"Error getting repos: {e}"

@mcp.tool()
async def list_open_prs(repo_name: str) -> str:
    """
    Get a list of all open pull requests in the repository.
    Use this when the user asks about open PRs or wants to review one.
    Provide the repo_name like 'owner/repo' or 'ajaymaan13/fraudnet-ai'.
    """
    try:
        prs = await github.list_open_prs(repo_name)

        # convert to simple readable text
        if isinstance(prs, str):
            return f"Error: {prs}"

        output = []
        for pr in prs:
            output.append(f"#{pr['number']} - {pr['title']} (by {pr['author']})")

        return "\n".join(output) if output else "No open pull requests found."
    except Exception as e:
        return f"Error getting PRs: {e}"

@mcp.tool()
async def get_pull_request(repo_name: str, pr_number: int) -> str:
    """
    Get the details of a pull request.
    Use this when the user asks about the PR or wants to review one.
    """
    try:
        pr = await github.get_pull_request(repo_name, pr_number)
        
        if not pr:
            return "Error finding PR."
        
        return f"Title: {pr['title']}\nDescription: {pr['description']}\nHead Branch: {pr['head_branch']}\nBase Branch: {pr['base_branch']}"
    except Exception as e:
        return f"Error getting PR details: {e}"

@mcp.tool()
async def get_pr_diff(repo_name: str, pr_number: int) -> str:
    """
    Get the raw unified diff of a specific pull request.
    Use this to see the line-by-line changes made in a pull request.
    """
    try:
        diff = await github.get_pr_diff(repo_name, pr_number)
        return diff
    except Exception as e:
        return f"Error getting PR diff: {e}"

@mcp.tool()
async def get_pr_files(repo_name: str, pr_number: int) -> str:
    """
    Get a list of changed files and their patches in a pull request.
    Use this to get an overview of which files were modified.
    """
    try:
        files = await github.get_pr_files(repo_name, pr_number)
        if not files:
            return "No files changed."
        
        output = []
        for f in files:
            output.append(f"File: {f['filename']} (Status: {f['status']})")
        return "\n".join(output)
    except Exception as e:
        return f"Error getting PR files: {e}"

@mcp.tool()
async def get_file_content(repo_name: str, path: str, branch: str) -> str:
    """
    Get the raw content of any file from a specific branch.
    Use this to retrieve the full content of a file for context or review.
    """
    try:
        content = await github.get_file_content(repo_name, path, branch)
        return content
    except Exception as e:
        return f"Error getting file content: {e}"

@mcp.tool()
async def list_files(repo_name: str, path: str = "") -> str:
    """
    Get a directory listing at a specific path in the repository.
    Use this to explore the project structure. Leave path empty for the root directory.
    """
    try:
        files = await github.list_files(repo_name, path)
        if not files:
            return "No files found."
        
        output = []
        for item in files:
            output.append(f"{item['type']}: {item['path']} ({item['name']})")
        return "\n".join(output)
    except Exception as e:
        return f"Error listing files: {e}"

if __name__ == "__main__":
    mcp.run()