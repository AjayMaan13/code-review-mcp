import os
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
                f"#{pr['number']} - {pr['title']} (by {pr['user']['login']})"
            )

        return "\n".join(result)