---
name: create-pull-request
description: Prepare and open a pull request after implementation and verification are complete. Use for Stage 7 of the DocSync SDLC workflow or when asked to create a PR.
---

# Create Pull Request

Create a clear, reviewable pull request for the current, verified branch.

## Preconditions

- Read the SDLC artifacts, especially `docs/sdlc/requirements.md`, the implementation plan, and `docs/sdlc/verification-report.md` when present.
- Inspect the current branch, `git status`, recent commits, and configured remotes.
- Confirm the working tree has no uncommitted changes. Do not stage, commit, discard, or rewrite changes as part of PR creation.
- Use the current branch as the PR head. Do not switch branches, force-push, or assume a fixed feature branch name.
- If the branch is not pushed, push the current branch only when the user or orchestrated Stage 7 has authorized publishing it. Otherwise, explain what is missing and stop.
- If the base branch is unclear, explain what is missing and stop rather than guessing.
- Check whether a PR already exists for the current branch before attempting to create another.

## Prepare the PR

1. Summarize the actual changes using the diff and SDLC artifacts.
2. Report test results and coverage only when supported by current command output or a verification report. Never invent counts, benchmarks, files, or requirement status.
3. Draft a title in the format `[Feature] <concise description>`.
4. Include these sections in the PR body:
   - **Summary** — what the change delivers and why.
   - **Changes Made** — the important implementation and documentation changes.
   - **Test Evidence** — verified test command/results and coverage, if available.
   - **Known Limitations** — only confirmed limitations.
   - **Reviewer Checklist** — concrete checks for reviewers.
   - **Traceability** — links or paths to the PRD and relevant SDLC artifacts, when available.
5. Keep the body concise and consistent with the actual branch contents.

## Publish

- Use the configured GitHub MCP pull-request tools to create the PR in `Dipayan94/agentic-docsync-capstone`; do not use the `gh` CLI.
- Use the repository's default branch as the base unless the workflow or human explicitly specifies another base.
- Do not create commits or push uncommitted work. Pushing the already-committed current branch is allowed only when the user/workflow has authorized publishing it.
- Request reviewers only when explicitly specified.
- Return the PR number and URL, title, and a concise summary of the verified test evidence. If creation fails, report the actual error and do not claim success.
