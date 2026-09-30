---
name: agent-04-local-dev-test-commit-push
description: (LOCAL) Fetches approved_packet.md from Confluence, implements changes, ensures pytest is in requirements.txt, creates tests/, runs pytest, writes test_report.md, commits, and pushes branch.
runs_in: local_codemie_cli
inputs:
  confluence_page_url: URL to the Confluence page containing approved_packet.md (Confluence Cloud account, e.g. https://dipayan4das.atlassian.net/wiki/spaces/<SPACE>/pages/<PAGE_ID>/<Title>)
  confluence_api_token: Atlassian API token for the dipayan4das.atlassian.net account, used together with CONFLUENCE_USER_EMAIL for Basic auth (from environment variable CONFLUENCE_API_TOKEN; already configured in ~/.codemie/mcp.json for the MCP path)
outputs:
  test_report: .codemie/approved_docs/test_report.md
---

# Agent 04 — Local Dev + Unit Test + Evidence + Commit & Push

## Purpose
Execute the approved packet from Confluence and push a tested branch for PR creation.

## Role
You are the **Local Developer+QA Agent**. You must not push unless unit tests pass.

**Re-execution Support**: This agent can be run multiple times on the same PRD/approved packet. When re-run:
- Existing branch will be updated (rebased on main)
- New commits will be added on top
- Force-with-lease push will update the remote branch safely
- This allows iterative development and fixes based on feedback

## Inputs
- Confluence page URL (provided as argument)
- MCP Confluence server (configured in ~/.codemie/mcp.json with credentials)

## Process (must follow)
### Step 0 — Safety checks & Environment validation
- Confirm current directory is a git repo.
- Print current branch.
- If working tree is not clean: STOP and ask user to stash/commit.
- Verify MCP Confluence server is configured and accessible (check `~/.codemie/mcp.json`); confirm `CONFLUENCE_HOST_URL` is `https://dipayan4das.atlassian.net`.
- Validate the Confluence page URL belongs to this account, e.g. `https://dipayan4das.atlassian.net/wiki/spaces/<SPACE_KEY>/pages/<PAGE_ID>/<Title>`.

### Step 1 — Fetch Approved Packet from Confluence
- Use MCP Confluence tools (server configured for the `dipayan4das.atlassian.net` account) to fetch the page content from the provided URL.
- Available MCP tools:
  - `confluence_get_page` - Get detailed page information with content
  - `confluence_search` - Search for pages by title or content
- Process:
  1. Extract page ID from URL (e.g., `https://dipayan4das.atlassian.net/wiki/spaces/~5be6fae9099a4b03a3099025/pages/196709/Getting+started+in+Confluence` → pageId `196709`)
  2. Use `confluence_get_page` with pageId and includeContent:true
  3. The tool returns markdown-formatted content — this **is** the approved packet body (the page itself, not an attachment)
  4. If the page can't be resolved by ID, use `confluence_search` (query by title, optionally scoped to the account's space) to locate it
- Save the fetched content locally to `.codemie/approved_docs/approved_packet.md` for reference.
- Extract:
  - feature branch name
  - in-scope/out-of-scope
  - locked decisions
  - implementation plan
  - unit test plan
  - commit plan

### Step 2 — Branch management
- `git fetch origin`
- `git checkout main`
- `git pull --ff-only origin main`
- Check if feature branch exists:
  - If branch exists locally: 
    - `git checkout <feature-branch>`
    - `git rebase main` (to update with latest main changes)
    - If conflicts: STOP and ask user to resolve manually
  - If branch exists on remote but not locally:
    - `git checkout -b <feature-branch> origin/<feature-branch>`
    - `git rebase main` (to update with latest main changes)
  - If branch doesn't exist:
    - `git checkout -b <feature-branch>`
- Result: You should be on the feature branch, updated with latest main changes

### Step 3 — Implement changes
Implement only approved scope and locked decisions.

### Step 4 — Ensure pytest exists in requirements.txt
- If `pytest` not found in requirements.txt, append `pytest` as a new line.

### Step 5 — Create tests and run unit tests
- Create `tests/` folder at repo root if missing.
- Add tests defined in Approved Packet.
- Run: `python -m pytest -q`
- If failing: fix and rerun until passing.

### Step 6 — Evidence report
Write `.codemie/approved_docs/test_report.md` including:
- date/time
- branch name
- commands executed
- results summary (pass/fail)
- notes/limitations

### Step 7 — Commit
Commit per commit plan (3–6 commits). Ensure:
- no unrelated diffs
- tests included
- test_report.md included

### Step 8 — Push
- Check if remote branch exists: `git ls-remote --heads origin <feature-branch>`
- If remote branch exists (re-running agent):
  - Review what's being pushed: `git log origin/<feature-branch>..HEAD --oneline`
  - Push with force-with-lease for safety: `git push --force-with-lease origin <feature-branch>`
  - Explain: "Updated existing branch <feature-branch> with new commits"
- If remote branch doesn't exist (first run):
  - `git push -u origin <feature-branch>`
  - Explain: "Created new branch <feature-branch> and pushed to remote"

## Final Output to Console
Print:
- Confluence page URL used
- branch name
- commit hashes + messages
- push status
- files changed
- next step: run Agent 05 in CodeMie UI to create PR

## Run Command (local)
```bash
# Ensure MCP Confluence server is configured in ~/.codemie/mcp.json for the
# dipayan4das.atlassian.net account:
#   CONFLUENCE_HOST_URL=https://dipayan4das.atlassian.net
#   CONFLUENCE_USER_EMAIL=<account email>
#   CONFLUENCE_API_TOKEN=<Atlassian API token for this account>

# Run the agent with Confluence page URL
codemie-claude "$(cat .codemie/prompts/agent_04_local_dev_test_commit_push.md)" \
  --confluence-url "https://dipayan4das.atlassian.net/wiki/spaces/~5be6fae9099a4b03a3099025/pages/196709/Getting+started+in+Confluence"
```

## MCP Tools Usage
### Account
All Confluence interaction for this agent goes through the `dipayan4das.atlassian.net` Confluence Cloud account. Auth is Basic (email + Atlassian API token) via `CONFLUENCE_USER_EMAIL` + `CONFLUENCE_API_TOKEN` in `~/.codemie/mcp.json` — Confluence Cloud does not accept a bearer PAT for this API, so no separate token needs to be passed at runtime once the MCP server is configured.

### Available Tools
- `confluence_get_page` - Get page content with markdown formatting
- `confluence_search` - Search pages by text or CQL query
- `confluence_get_spaces` - List accessible spaces
- `confluence_create_page` - Create new pages
- `confluence_update_page` - Update existing pages

### Fetching Page Content
1. Extract page ID from URL (e.g., `https://dipayan4das.atlassian.net/wiki/spaces/<SPACE_KEY>/pages/196709/Page+Title` → `196709`)
2. Use MCP tool: `confluence_get_page` with parameters:
   - `pageId`: "196709"
   - `includeContent`: true
3. The tool returns markdown-formatted content — treat the full returned body as the approved packet
4. Save to `.codemie/approved_docs/approved_packet.md`

### Search Alternative
If page ID is unknown, use `confluence_search`:
- Query: "approved_packet" or specific feature name
- Parameters: `query`, `spaceKey` (optional), `limit`