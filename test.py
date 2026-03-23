import asyncio
from github_client import GitHubClient

async def main():
    client = GitHubClient()
    prs = await client.list_open_prs()
    print(prs)

asyncio.run(main())