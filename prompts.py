import asyncio
from mcp.server.fastmcp import FastMCP
from github_client import GitHubClient
from config import guard_diff


def register(mcp: FastMCP, github: GitHubClient) -> None:

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
                f"Diff:\n{guard_diff(diff)}"
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
                f"Diff:\n{guard_diff(diff)}"
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
