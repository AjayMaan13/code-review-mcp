from mcp.server.fastmcp import FastMCP
from github_client import GitHubClient

mcp = FastMCP("code-reviewer")

github = GitHubClient()


# --- RESOURCES ---

@mcp.resource("github://{owner}/{repo}/pulls/{pr_number}/diff")
async def get_pr_diff_resource(owner: str, repo: str, pr_number: int) -> str:
    """Read the raw diff of a pull request as a resource."""
    repo_name = f"{owner}/{repo}"
    try:
        return await github.get_pr_diff(repo_name, pr_number)
    except Exception as e:
        return f"Error getting PR diff: {e}"

@mcp.resource("github://{owner}/{repo}/blob/{branch}/{path}")
async def get_file_content_resource(owner: str, repo: str, branch: str, path: str) -> str:
    """Read a specific file from the repository as a resource."""
    repo_name = f"{owner}/{repo}"
    try:
        return await github.get_file_content(repo_name, path, branch)
    except Exception as e:
        return f"Error getting file content: {e}"


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