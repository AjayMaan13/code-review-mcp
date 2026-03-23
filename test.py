import asyncio
from github_client import GitHubClient

async def main():
    client = GitHubClient()
    prs = await client.list_open_prs()
    pr = await client.get_pr_diff()
    print(prs)
    print(pr)

asyncio.run(main())