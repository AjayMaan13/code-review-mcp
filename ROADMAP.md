# Roadmap

Features and improvements planned for future iterations.

---

## Error Handling Polish

Right now most errors return a plain string like `"Error getting PR: ..."`. The upgrade is structured errors that tell Claude *why* it failed so it can recover gracefully instead of giving up.

- `404` → resource not found (wrong repo name, PR doesn't exist)
- `401` → bad or expired token
- `403` → token lacks required permissions
- `422` → bad input (malformed repo name, invalid PR number)

Claude can do something useful with a 404 (suggest checking the repo name). It can't do anything useful with an opaque string.

---

## Post Review Comments to GitHub

The server is currently read-only. The highest-impact upgrade: use `POST /repos/{owner}/{repo}/pulls/{pr_number}/reviews` to post Claude's review directly as a GitHub PR review.

This turns the server from a reading tool into a full review bot — the review shows up in the GitHub UI like any human reviewer's comment.

---

## Inline Comments

GitHub's review API supports attaching comments to specific lines via the `position` field in the diff. The `security_review` prompt already outputs file + line number — wire that output to `POST /repos/{owner}/{repo}/pulls/{pr_number}/comments` to post inline comments directly on the offending lines.

Depends on: **Post review comments** being implemented first.

---

## Webhook Trigger

Right now reviews are triggered manually. The jump from tool to bot: set up a GitHub webhook that fires on `pull_request.opened`, hits a FastAPI endpoint, and triggers the review automatically — no human invocation needed.

High-level flow:
1. PR opened on GitHub
2. GitHub sends `pull_request.opened` webhook to your endpoint
3. FastAPI handler calls the MCP server
4. Claude runs `security_review` (or a configurable prompt)
5. Review is posted back to the PR

Depends on: **Post review comments** being implemented first.
