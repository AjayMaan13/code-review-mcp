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

    async def list_open_prs(self):
        """Return a list of open pull requests (number, title, author)."""
        url = f"{BASE_URL}/repos/{GITHUB_REPO}/pulls"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            prs = response.json()

        result = []
        for pr in prs:
            result.append({
                "number": pr["number"],
                "title": pr["title"],
                "author": pr["user"]["login"]
            })
        return result

    async def get_pull_request(self, pr_number: int):
        """Return PR title, description, and branch info."""
        url = f"{BASE_URL}/repos/{GITHUB_REPO}/pulls/{pr_number}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            pr = response.json()
            
        return {
            "title": pr["title"],
            "description": pr["body"],
            "head_branch": pr["head"]["ref"],
            "base_branch": pr["base"]["ref"]
        }
    
    async def get_pr_diff(self, pr_number: int) -> str:
        """Return the raw unified diff of a specific pull request."""
        url = f"{BASE_URL}/repos/{GITHUB_REPO}/pulls/{pr_number}"
        headers = self.headers.copy()
        headers["Accept"] = "application/vnd.github.v3.diff"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text

    async def get_pr_files(self, pr_number: int):
        """Return a list of changed files and their patches."""
        url = f"{BASE_URL}/repos/{GITHUB_REPO}/pulls/{pr_number}/files"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            files = response.json()
            
        result = []
        for f in files:
            result.append({
                "filename": f["filename"],
                "status": f["status"],
                "patch": f.get("patch", "")
            })
        return result

    async def get_file_content(self, path: str, branch: str) -> str:
        """Return the raw content of any file."""
        url = f"{BASE_URL}/repos/{GITHUB_REPO}/contents/{path}"
        headers = self.headers.copy()
        headers["Accept"] = "application/vnd.github.v3.raw"
        params = {"ref": branch}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.text

    async def list_files(self, path: str = ""):
        """Return a directory listing at a path."""
        url = f"{BASE_URL}/repos/{GITHUB_REPO}/contents/{path}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            contents = response.json()
            
        if not isinstance(contents, list):
            contents = [contents]
            
        return [{"name": item["name"], "type": item["type"], "path": item["path"]} for item in contents]