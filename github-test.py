import asyncio
import json
from github_client import GitHubClient

async def main():
    client = GitHubClient()
    print("--- Testing list_repos() ---")
    repos = await client.list_repos()
    print(json.dumps(repos, indent=2))
    
    # We use a repo name that was fetched or fallback
    repo_name = repos[0]["name"] if repos else "fastmcp" # just use a fallback if no direct match available, assuming we know format
    # Better yet, let test use an explicit test repo full name since user endpoint only gives the name, not owner/name
    # Since personal tokens are used, assuming owner is same 
    # Just hardcoding the test to use the provided one you had before
    repo_full_name = "ajaymaan13/fraudnet-ai"
    print(f"--- Testing against {repo_full_name} ---")

    print(f"--- Testing list_open_prs({repo_full_name}) ---")
    prs = await client.list_open_prs(repo_full_name)
    print(json.dumps(prs, indent=2))
    
    if not prs or isinstance(prs, str):
        print("No open PRs found to test the other PR methods.")
        # We can still test repository files
        test_pr_number = None
        base_branch = "main" # Fallback
    else:
        test_pr_number = prs[0]['number']
        
    if test_pr_number:
        print(f"\n--- Testing get_pull_request({repo_full_name}, {test_pr_number}) ---")
        pr_info = await client.get_pull_request(repo_full_name, test_pr_number)
        print(json.dumps(pr_info, indent=2))
        base_branch = pr_info['base_branch']
        
        print(f"\n--- Testing get_pr_files({repo_full_name}, {test_pr_number}) ---")
        pr_files = await client.get_pr_files(repo_full_name, test_pr_number)
        # Print only first file to avoid flooding
        if pr_files:
            print(f"Total files changed: {len(pr_files)}")
            print("First file preview:")
            print(json.dumps(pr_files[0], indent=2)[:500] + "\n...[truncated]")
        else:
            print("No files changed in this PR.")
            
        print(f"\n--- Testing get_pr_diff({repo_full_name}, {test_pr_number}) ---")
        pr_diff = await client.get_pr_diff(repo_full_name, test_pr_number)
        print(pr_diff[:500] + "\n...[truncated diff]")

    print(f"\n--- Testing list_files({repo_full_name}, '') ---")
    files = await client.list_files(repo_full_name, "")
    print(f"Found {len(files)} items in root:")
    print(json.dumps(files[:3], indent=2))
    
    print(f"\n--- Testing get_file_content({repo_full_name}, 'README.md', '{base_branch}') ---")
    try:
        content = await client.get_file_content(repo_full_name, "README.md", base_branch)
        print(content[:300] + "\n...[truncated content]")
    except Exception as e:
        print(f"Failed to fetch README.md: {e}")

if __name__ == "__main__":
    asyncio.run(main())