import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

BASE_URL = "https://api.github.com"


class GitHubClient:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
        }

    async def list_open_prs(self) -> str:
        """Return a formatted list of open pull requests."""
        url = f"{BASE_URL}/repos/{GITHUB_REPO}/pulls"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            prs = response.json()

        if not prs:
            return "No open pull requests."

        result = []
        for pr in prs:
            result.append(
                f"#{pr['number']} - {pr['title']} - Description: {pr['body']} (by {pr['user']['login']})"
            )

        return "\n".join(result)
    
    async def get_pr_diff(self) -> str:
        """Return the diff of a specific pull request."""
        pull_number = input("Enter Pull Request Number: ")
        url = f"{BASE_URL}/repos/{GITHUB_REPO}/pulls/{pull_number}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            pr = response.json()

        if not pr:
            print(f"Error finding PR", file=sys.stderr)
            return f"PR{pr_number} not found"
    
        return f"PR: {pr["node_id"]} made by {pr["user"]["login"]} description is: {pr["body"]}"