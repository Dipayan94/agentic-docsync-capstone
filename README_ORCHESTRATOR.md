# Orchestrator - Agentic SDLC Entry Point

## Overview

There is no orchestrator script. Orchestration is done **entirely through GitHub Copilot Custom Agents** (`.agent.md` files), invoked from Copilot Chat in Agent Mode. This matches the capstone objective: the SDLC pipeline must be driven through Copilot Agents/Prompts/Instructions/Skills/Hooks, not external scripts.

## The Agents

The orchestrator and seven stage agents live in [.github/agents/](.github/agents/) as `*.agent.md` files. **`sdlc_orchestrator` is the single entry point** (`user-invocable: true`) — it's the only one that shows up in the Copilot Chat **Agent picker**. The seven stage agents are `user-invocable: false`: hidden from the picker, and only ever run as subagents that the orchestrator delegates to. Stage 7 uses the `create-pull-request` skill in [.github/skills/](.github/skills/) instead of an agent.

| Agent | Stage | Approval Gate | Output |
|-------|-------|----------------|--------|
| `requirements-agent` | 1. Requirements | ❌ No | `docs/sdlc/requirements.md` (from Confluence) |
| `architecture-agent` | 2. Architecture | ✅ YES | `docs/sdlc/architecture.md` |
| `design-review-agent` | 3. Design Review | ✅ YES | `docs/sdlc/design-review.md` |
| `planning-agent` | 4. Implementation Planning | ❌ No | `docs/sdlc/impl-plan.md` |
| `implementation-agent` | 5. Implementation | ❌ No | `docsync/*` |
| `verification-agent` | 6. Verification | ❌ No (pass/fail) | `tests/*` + `docs/sdlc/verification-report.md` |
| `create-pull-request` skill | 7. Pull Request Creation | ❌ No | GitHub PR opened |
| `code-review-agent` | 8. Code Review (on the live PR) | ✅ YES (approve publishing findings) | Inline PR review comments + `docs/sdlc/code-review-report.md` |
| **`sdlc_orchestrator`** | Coordinates all of the above | — | **Entry point** — invokes stage agents as subagents and uses the PR skill |

## How to Run It

1. Open Copilot Chat, select the **Agent** picker, choose `sdlc_orchestrator`.
2. Give it a Confluence PRD page URL/ID/title (its argument hint) — e.g. `@sdlc_orchestrator https://kb.epam.com/spaces/.../pages/.../PRD-001...`. If you don't provide one, it asks for it before Stage 1.
3. It invokes each stage agent as a subagent in order, pausing at the 3 approval gates (Architecture, Design Review, Code Review) for your yes/no/feedback. Code review deliberately runs **after** the PR is opened so findings are posted as real inline comments on the PR — but it drafts its findings and asks you to approve **publishing** them before posting anything to GitHub. Merging the PR is always your separate, manual call.

To resume from a specific stage (e.g. after fixing something), tell `sdlc_orchestrator` which stage to start from — it's still the only agent you talk to.

## External Integrations (MCP)

Configured in [.vscode/mcp.json](.vscode/mcp.json):
- **`confluence`** (via `mcp-atlassian`, PAT auth against kb.epam.com) — `requirements-agent` reads the PRD/User Story page from Confluence. The page URL/ID/title is a dynamic input each run, not fixed — pass it when invoking the agent, or it will ask.
- **`github`** — the Stage 7 skill opens the Pull Request and `code-review-agent` posts inline review comments via the GitHub MCP server instead of `gh` CLI.

## Skill and Hook

- **PR skill:** `.github/skills/create-pull-request/SKILL.md` prepares the PR from the verified current branch. It does not create commits or rewrite local changes.
- **Secret guard hook:** `.github/hooks/pre-commit-secret-guard.json` registers a Copilot CLI `PreToolUse` hook for Bash. Before direct `git commit` commands, it checks added lines in staged changes, plus tracked unstaged changes for `git commit -a/--all`, against common credential patterns. It denies the call when likely secrets are found and reports only file/line and pattern category.
- The hook is a best-effort pattern scanner, not a replacement for a dedicated secret-scanning product. It does not install a native Git hook and will not intercept commits outside Copilot or indirect commit wrappers. Copilot documents command-hook timeouts as fail-open, so this is not an absolute commit barrier.

`github` is a remote HTTP server using OAuth (VS Code prompts you to sign in on first use). `confluence` runs locally via Docker (`ghcr.io/sooperset/mcp-atlassian`) and needs Docker installed; the first time it's used, VS Code will prompt you for your Confluence Personal Access Token (stored only for the session, never written to this file).

## Local Dev Tasks

Two plain VS Code tasks remain in [.vscode/tasks.json](.vscode/tasks.json) for running the app and test suite locally (Cmd+Shift+P → "Run Task"):
- **app: Run FastAPI (uvicorn)**
- **test: Run pytest with coverage**

## Stages Overview

| Stage | Name | Approval Gate | Output |
|-------|------|---------------|--------|
| 1 | Requirements Analysis | ❌ No | `docs/sdlc/requirements.md` (from Confluence) |
| 2 | Architecture Design | ✅ YES | `docs/sdlc/architecture.md` |
| 3 | Design Review | ✅ YES | `docs/sdlc/design-review.md` |
| 4 | Implementation Planning | ❌ No | `docs/sdlc/impl-plan.md` |
| 5 | Implementation | ❌ No | `docsync/*` files |
| 6 | Verification & Testing | ❌ No (pass/fail) | `tests/*` + `docs/sdlc/verification-report.md` |
| 7 | Pull Request Creation | ❌ No | GitHub PR opened via the `create-pull-request` skill and GitHub MCP |
| 8 | Code Review | ✅ YES (approve publishing findings) | Inline review comments posted on the PR + `docs/sdlc/code-review-report.md` |

**Approval Gates:** 3 total (Stages 2, 3, 8). Code review intentionally runs **after** the PR is opened so findings are posted as real GitHub PR review comments; Stage 8's approval is for *publishing those findings*, not for merging — merging the PR is always a separate manual step the human does on GitHub.

## Demo Tips

1. Start with the `requirements-agent` alone to show it pulling the PRD live from Confluence.
2. Run the full pipeline via `sdlc_orchestrator` through Stage 7, then show the opened PR on GitHub. The orchestrator uses the skill for PR creation.
3. Run `code-review-agent` and refresh the PR in the browser to show inline review comments appearing in real time.
4. Show `docs/sdlc/` and `git log --oneline` for traceability from PRD → reviewed PR (merge is a manual step you do afterwards).
