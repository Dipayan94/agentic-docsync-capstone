# Agentic SDLC Workflow Guide

## Overview

This guide explains how to execute the **GitHub Copilot Agentic SDLC workflow** for the Documentation Sync capstone project.

## Architecture

### Agents

**Orchestrator Agent:**
- Coordinates all 8 stages
- Manages human approval gates
- Tracks workflow progress

**Specialized Agents (8 stages):**
1. **requirements-agent** - Extract requirements from PRD
2. **architecture-agent** - Design system architecture
3. **design-review-agent** - Review for risks and quality
4. **planning-agent** - Break down into tasks
5. **implementation-agent** - Write production code
6. **code-review-agent** - Review code quality
7. **verification-agent** - Generate and run tests
8. **pr-agent** - Create pull request

### Tools Each Agent Needs

| Agent | Tools |
|-------|-------|
| requirements-agent | File read (PRD), File write (requirements.md) |
| architecture-agent | File read (requirements, codebase), File write (architecture.md) |
| design-review-agent | File read (architecture), File write (design-review.md) |
| planning-agent | File read (architecture, review), File write (impl-plan.md) |
| implementation-agent | File read (plan), File write (code files) |
| code-review-agent | File read (code), File write (review report) |
| verification-agent | File read/write (tests), Test execution, Coverage |
| pr-agent | File read (all artifacts), Git ops, GitHub PR creation |
| orchestrator-agent | Agent invocation, File read, User prompts |

### GitHub Copilot Integration

#### Option 1: Use GitHub Copilot CLI
```bash
# Start orchestrator
gh copilot suggest "Execute orchestrator-agent from .github/agents/orchestrator-agent.md to run the full SDLC workflow"
```

#### Option 2: Use GitHub Copilot Chat in VS Code
1. Open VS Code
2. Open Copilot Chat (Cmd+Shift+I)
3. Type: `@workspace Execute the orchestrator-agent to start the SDLC workflow`
4. Copilot will read agent definitions and execute stages

#### Option 3: Manual Stage-by-Stage Execution
Execute each agent manually:

```bash
# Stage 1: Requirements
gh copilot suggest "Act as requirements-agent from .github/agents/requirements-agent.md. Read custom_PRD/PRD-001-Documentation-Sync.md and generate docs/sdlc/requirements.md"

# Stage 2: Architecture
gh copilot suggest "Act as architecture-agent. Read docs/sdlc/requirements.md and generate docs/sdlc/architecture.md"

# [Approval Gate 1] - Human reviews architecture.md

# Stage 3: Design Review
gh copilot suggest "Act as design-review-agent. Review docs/sdlc/architecture.md and generate docs/sdlc/design-review.md"

# [Approval Gate 2] - Human reviews design-review.md

# Stage 4: Planning
gh copilot suggest "Act as planning-agent. Read architecture and design review, generate docs/sdlc/impl-plan.md"

# Stage 5: Implementation
gh copilot suggest "Act as implementation-agent. Implement all tasks from docs/sdlc/impl-plan.md. Create docsync/ module."

# Stage 6: Code Review
gh copilot suggest "Act as code-review-agent. Review all code in docsync/ and generate docs/sdlc/code-review-report.md"

# [Approval Gate 3] - Human reviews code-review-report.md

# Stage 7: Verification
gh copilot suggest "Act as verification-agent. Generate tests, run them, generate docs/sdlc/verification-report.md"

# Stage 8: PR Creation
gh copilot suggest "Act as pr-agent. Create pull request with comprehensive description from all SDLC artifacts"

# [Approval Gate 4] - Human merges PR
```

## Execution Steps

### Prerequisites
1. ✅ Repository cloned and opened in VS Code
2. ✅ GitHub Copilot installed and authenticated
3. ✅ Python 3.9+ and venv set up
4. ✅ PRDs created in `custom_PRD/`
5. ✅ Agent definitions in `.github/agents/`

### Step-by-Step Execution

#### Start: Initialize
```bash
# Verify setup
ls -la .github/agents/
ls -la custom_PRD/

# Ensure git is clean
git status
```

#### Stage 1: Requirements (5 min)
**Prompt for GitHub Copilot:**
```
Read the agent definition in .github/agents/requirements-agent.md.
Act as the requirements-agent and execute the process described.
Read custom_PRD/PRD-001-Documentation-Sync.md and generate docs/sdlc/requirements.md.
```

**Expected Output:**
- `docs/sdlc/requirements.md` created
- Git commit: `[Requirements] Extract requirements from PRD-001`

**Validation:**
- File exists and is well-structured
- All functional and non-functional requirements listed

---

#### Stage 2: Architecture (10 min)
**Prompt for GitHub Copilot:**
```
Read the agent definition in .github/agents/architecture-agent.md.
Act as the architecture-agent and execute the process described.
Read docs/sdlc/requirements.md and existing codebase (main.py, models.py).
Generate docs/sdlc/architecture.md proposing the system architecture.
```

**Expected Output:**
- `docs/sdlc/architecture.md` created
- Git commit: `[Architecture] Propose docsync module structure`

**🔒 APPROVAL GATE 1:**
1. Human reads `docs/sdlc/architecture.md`
2. Reviews component design, data flow, tech choices
3. Decision: APPROVE / REQUEST CHANGES
4. If approved, proceed to Stage 3

---

#### Stage 3: Design Review (10 min)
**Prompt for GitHub Copilot:**
```
Read the agent definition in .github/agents/design-review-agent.md.
Act as the design-review-agent and execute the process described.
Review docs/sdlc/architecture.md for security, performance, quality.
Generate docs/sdlc/design-review.md with findings and recommendations.
```

**Expected Output:**
- `docs/sdlc/design-review.md` created
- Git commit: `[Design Review] Architecture review with findings`

**🔒 APPROVAL GATE 2:**
1. Human reads `docs/sdlc/design-review.md`
2. Reviews identified risks and recommendations
3. Decision: APPROVE / REQUEST CHANGES
4. If approved, proceed to Stage 4

---

#### Stage 4: Planning (10 min)
**Prompt for GitHub Copilot:**
```
Read the agent definition in .github/agents/planning-agent.md.
Act as the planning-agent and execute the process described.
Read docs/sdlc/architecture.md and docs/sdlc/design-review.md.
Generate docs/sdlc/impl-plan.md with task breakdown and dependencies.
```

**Expected Output:**
- `docs/sdlc/impl-plan.md` created
- Git commit: `[Planning] Task breakdown with dependencies`

**Validation:**
- 10-15 tasks defined
- Dependencies clearly specified
- Acceptance criteria for each task

---

#### Stage 5: Implementation (30 min)
**Prompt for GitHub Copilot:**
```
Read the agent definition in .github/agents/implementation-agent.md.
Act as the implementation-agent and execute the process described.
Read docs/sdlc/impl-plan.md and implement all tasks in order.
Create the docsync/ module with all components.
```

**Expected Output:**
- `docsync/` directory created with:
  - `__init__.py`
  - `models.py`
  - `openapi_parser.py`
  - `markdown_generator.py`
  - `diff_engine.py`
  - `cli.py`
  - `exceptions.py`
- `requirements.txt` updated
- Git commits: `[Implementation] Phase X - <description>`

**Validation:**
- All files created
- Code compiles without errors
- Type hints and docstrings present

---

#### Stage 6: Code Review (15 min)
**Prompt for GitHub Copilot:**
```
Read the agent definition in .github/agents/code-review-agent.md.
Act as the code-review-agent and execute the process described.
Review all code in docsync/ directory.
Check for correctness, security, error handling, quality, DRY principle.
Generate docs/sdlc/code-review-report.md with findings.
```

**Expected Output:**
- `docs/sdlc/code-review-report.md` created
- Git commit: `[Code Review] Review findings and recommendations`

**🔒 APPROVAL GATE 3:**
1. Human reads `docs/sdlc/code-review-report.md`
2. Reviews identified issues (critical, high, medium, low)
3. Decision: APPROVE / REQUEST FIXES
4. If critical issues, implementation-agent fixes them
5. If approved, proceed to Stage 7

---

#### Stage 7: Verification (20 min)
**Prompt for GitHub Copilot:**
```
Read the agent definition in .github/agents/verification-agent.md.
Act as the verification-agent and execute the process described.
Generate comprehensive unit and integration tests for docsync/ module.
Create tests/ directory with test files.
Run pytest and measure coverage.
Generate docs/sdlc/verification-report.md with results.
```

**Expected Output:**
- `tests/` directory created with:
  - `test_models.py`
  - `test_openapi_parser.py`
  - `test_markdown_generator.py`
  - `test_diff_engine.py`
  - `test_cli.py`
  - `test_integration.py`
  - `fixtures/` (test data)
- `docs/sdlc/verification-report.md` created
- Git commits:
  - `[Verification] Add comprehensive unit tests`
  - `[Verification] Verification report with results`

**Validation:**
- All tests pass
- Coverage > 80%
- Verification report shows PASS status

---

#### Stage 8: PR Creation (10 min)
**Prompt for GitHub Copilot:**
```
Read the agent definition in .github/agents/pr-agent.md.
Act as the pr-agent and execute the process described.
Read all SDLC artifacts from docs/sdlc/.
Create a comprehensive pull request with description, test evidence, and reviewer checklist.
Use GitHub CLI to create the PR.
```

**Expected Output:**
- Feature branch created: `feature/automated-doc-sync`
- All changes committed
- PR created on GitHub
- Git commit: `[PR] Create pull request for documentation sync feature`

**🔒 APPROVAL GATE 4:**
1. Human reviews PR on GitHub
2. Reviews all changes, test evidence, SDLC artifacts
3. Decision: MERGE / REQUEST CHANGES
4. If approved, merge PR

---

### Completion

After all stages:
- ✅ 8 SDLC stages completed
- ✅ 4 approval gates passed
- ✅ Full traceability in git history
- ✅ PR merged
- ✅ Feature ready for use

**Verify:**
```bash
# Check git log
git log --oneline

# Should show commits for each stage:
# [PR] Create pull request...
# [Verification] Verification report...
# [Verification] Add comprehensive unit tests
# [Code Review] Review findings...
# [Implementation] Phase 3...
# [Implementation] Phase 2...
# [Implementation] Phase 1...
# [Planning] Task breakdown...
# [Design Review] Architecture review...
# [Architecture] Propose docsync...
# [Requirements] Extract requirements...
# [Setup] Create PRDs and agents...
```

## Tips for Success

### For GitHub Copilot Users
1. **Be specific in prompts:** Reference agent files by path
2. **Wait for completion:** Let each stage finish before approving
3. **Review artifacts:** Always read generated docs at approval gates
4. **Commit per stage:** Keep git history clean
5. **Use agent definitions:** Copilot will follow them if you reference them

### Common Issues

**Issue: Copilot doesn't follow agent definition**
- Solution: Explicitly say "Read and follow the agent definition in .github/agents/<name>.md"

**Issue: Files not created in correct location**
- Solution: Specify absolute paths or verify current directory

**Issue: Tests fail**
- Solution: verification-agent should debug and fix, or loop back to implementation-agent

**Issue: Approval gates skipped**
- Solution: orchestrator-agent must explicitly wait for human input

## Alternative: Manual Execution

If GitHub Copilot integration is limited, you can execute agents manually:

1. Read agent definition file
2. Follow the process steps manually
3. Generate outputs as specified
4. Commit with proper message format
5. Human reviews at approval gates

## Measuring Success

The capstone is successful when:
- ✅ All 8 SDLC stages executed
- ✅ All artifacts in `docs/sdlc/` are present
- ✅ Git history shows clear progression
- ✅ All tests pass (45 tests, >80% coverage)
- ✅ PR created and merged
- ✅ Feature works (can run docsync CLI successfully)

**Deliverables:**
- Functional docsync feature
- 8 SDLC artifacts
- 45+ tests
- Merged PR
- Git history showing AI-driven workflow

## Next Steps After Completion

1. Demo the feature to judges
2. Show SDLC artifacts as evidence of process
3. Explain approval gates and human-in-the-loop
4. Highlight traceability from PRD to merged code
5. Discuss benefits of Agentic SDLC

---

**Ready to start?** Execute the orchestrator-agent or run stages manually following this guide!
