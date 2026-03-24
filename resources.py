import asyncio
from mcp.server.fastmcp import FastMCP
from github_client import GitHubClient
from config import guard_diff


def register(mcp: FastMCP, github: GitHubClient) -> None:

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
                f"Diff:\n{guard_diff(diff)}"
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
