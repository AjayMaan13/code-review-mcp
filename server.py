from mcp.server.fastmcp import FastMCP
from github_client import GitHubClient
import resources
import tools
import prompts

mcp = FastMCP("code-reviewer")
github = GitHubClient()

resources.register(mcp, github)
tools.register(mcp, github)
prompts.register(mcp, github)

if __name__ == "__main__":
    mcp.run()
