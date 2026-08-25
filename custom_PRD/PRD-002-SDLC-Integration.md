# PRD-002: Agentic SDLC Integration for Documentation Sync

## Product Requirement Document

**Status:** Draft
**Priority:** High
**Created:** 2026-08-25
**Owner:** Engineering Team

---

## Problem Statement

Building the Documentation Sync feature (PRD-001) requires following a complete SDLC process. We need an **AI-native, agent-driven workflow** using GitHub Copilot that automates and orchestrates each stage from requirements to PR, while keeping humans in the loop for approvals.

---

## Business Objective

Demonstrate a **GitHub Copilot Capstone-Ready SDLC Pipeline** that:
- Automates 8 SDLC stages using specialized AI agents
- Maintains human approval gates at critical decision points
- Produces traceable artifacts at each stage
- Showcases GitHub Copilot's Agents, Skills, Prompts, and Hooks

**Success Metrics:**
- All 8 SDLC stages executed by agents
- Human approval gates working at 4 checkpoints
- Full traceability from PRD to merged PR
- Git history reflects SDLC progression

---

## SDLC Stages & Agents

### Stage 1: Requirements Analysis
**Agent:** `requirements-agent`
**Input:** PRD-001 markdown file
**Process:**
1. Read PRD-001 from `custom_PRD/` directory
2. Extract functional and non-functional requirements
3. Identify ambiguities or missing details
4. Generate clarifying questions (if any)
5. Create `docs/sdlc/requirements.md` with structured requirements

**Output:** `docs/sdlc/requirements.md`
**Approval Gate:** ❌ No (requirements come from PRD)
**Tools Needed:** File read, markdown parsing

---

### Stage 2: Architecture Design
**Agent:** `architecture-agent`
**Input:** `docs/sdlc/requirements.md`
**Process:**
1. Read requirements document
2. Analyze current codebase structure (`main.py`, `models.py`)
3. Propose system architecture for docsync feature
4. Define components: OpenAPI Parser, Doc Generator, Diff Engine, CLI
5. Specify data flow and module interactions
6. Choose technology stack (libraries, frameworks)

**Output:** `docs/sdlc/architecture.md`
**Approval Gate:** ✅ YES - Human reviews architecture before proceeding
**Tools Needed:** File read, codebase analysis, GitHub Copilot workspace context

---

### Stage 3: Design Review
**Agent:** `design-review-agent`
**Input:** `docs/sdlc/architecture.md`
**Process:**
1. Read architecture document
2. Review for: Security risks, Performance bottlenecks, Scalability issues, Error handling gaps, Dependency risks
3. Check alignment with requirements
4. Identify edge cases not covered
5. Generate findings and recommendations

**Output:** `docs/sdlc/design-review.md`
**Approval Gate:** ✅ YES - Human reviews findings and decides GO/NO-GO
**Tools Needed:** File read, static analysis patterns

---

### Stage 4: Implementation Planning
**Agent:** `planning-agent`
**Input:** `docs/sdlc/architecture.md` + `docs/sdlc/design-review.md`
**Process:**
1. Break architecture into implementation tasks
2. Order tasks by dependency (what must happen first)
3. Estimate complexity for each task
4. Identify blocked tasks
5. Create dependency graph

**Output:** `docs/sdlc/impl-plan.md`
**Approval Gate:** ❌ No (planning is derived from approved architecture)
**Tools Needed:** File read, task breakdown logic

---

### Stage 5: Implementation
**Agent:** `implementation-agent`
**Input:** `docs/sdlc/impl-plan.md`
**Process:**
1. Read implementation plan
2. Create directory structure: `docsync/` module
3. Implement each component per plan:
   - `docsync/openapi_parser.py`
   - `docsync/markdown_generator.py`
   - `docsync/diff_engine.py`
   - `docsync/cli.py`
   - `docsync/__init__.py`
4. Update `requirements.txt` with new dependencies
5. Follow Python best practices and typing

**Output:** Implementation code in `docsync/` directory
**Approval Gate:** ❌ No (but code review comes next)
**Tools Needed:** File write, code generation, GitHub Copilot code completion

---

### Stage 6: Code Review
**Agent:** `code-review-agent`
**Input:** All implementation code
**Process:**
1. Review code for:
   - **Correctness:** Logic errors, edge cases
   - **Security:** Input validation, injection risks
   - **Error Handling:** Try-catch blocks, error messages
   - **Test Coverage:** Are tests needed?
   - **Code Quality:** DRY principle, clarity, typing
   - **Dependencies:** Safe, up-to-date libraries
2. Generate review report with findings
3. Suggest improvements

**Output:** `docs/sdlc/code-review-report.md`
**Approval Gate:** ✅ YES - Human reviews findings and approves/requests changes
**Tools Needed:** Static code analysis, GitHub Copilot review mode

---

### Stage 7: Verification & Testing
**Agent:** `verification-agent`
**Input:** Implementation code
**Process:**
1. Generate unit tests for each module:
   - `tests/test_openapi_parser.py`
   - `tests/test_markdown_generator.py`
   - `tests/test_diff_engine.py`
   - `tests/test_cli.py`
2. Run pytest suite
3. Verify test coverage > 80%
4. Test CLI with sample data
5. Validate output quality

**Output:**
- Test files in `tests/` directory
- `docs/sdlc/verification-report.md` with results

**Approval Gate:** ❌ No (verification is pass/fail)
**Tools Needed:** Test generation, pytest execution, coverage analysis

---

### Stage 8: Pull Request Creation
**Agent:** `pr-agent`
**Input:** All SDLC artifacts + implementation
**Process:**
1. Generate PR title and description
2. Summarize changes made
3. Include test evidence (pytest output)
4. Reference PRD and requirements
5. Add reviewer checklist
6. List known limitations
7. Create PR on GitHub

**Output:** GitHub Pull Request
**Approval Gate:** ✅ YES - Human reviews and merges PR
**Tools Needed:** GitHub API/CLI, PR template generation

---

## Orchestrator Agent

**Agent:** `orchestrator-agent`
**Purpose:** Coordinate all 8 stages with human-in-the-loop gates

**Workflow:**
```
START
  ↓
1. Run requirements-agent → requirements.md
  ↓
2. Run architecture-agent → architecture.md
  ↓
[GATE 1] Human reviews architecture → APPROVE/REJECT
  ↓ (if APPROVE)
3. Run design-review-agent → design-review.md
  ↓
[GATE 2] Human reviews findings → APPROVE/REJECT
  ↓ (if APPROVE)
4. Run planning-agent → impl-plan.md
  ↓
5. Run implementation-agent → code files
  ↓
6. Run code-review-agent → code-review-report.md
  ↓
[GATE 3] Human reviews code → APPROVE/REJECT
  ↓ (if APPROVE)
7. Run verification-agent → tests + verification-report.md
  ↓
8. Run pr-agent → GitHub PR
  ↓
[GATE 4] Human merges PR → DONE
```

**Tools Needed:** Agent orchestration, state management, approval prompts

---

## Agent Tool Requirements

### Tools Available to Agents:

1. **File Operations**
   - Read files (PRD, code, docs)
   - Write files (docs, code, tests)
   - Create directories

2. **GitHub Integration**
   - Create PRs
   - Read repository structure
   - Access commit history

3. **Code Analysis**
   - Parse Python code
   - Analyze dependencies
   - Check code quality

4. **Testing**
   - Generate pytest tests
   - Run pytest
   - Measure coverage

5. **Markdown/Document Processing**
   - Parse markdown
   - Generate structured docs

6. **OpenAPI/JSON**
   - Parse JSON schemas
   - Validate OpenAPI specs

### Optional Tools (Nice to Have):
- JIRA integration (if we want to create/update tickets)
- GitHub Issues (for tracking findings)
- Linting tools (pylint, black, mypy)

---

## Human Approval Gates

### Gate 1: Architecture Approval
**When:** After architecture.md is generated
**Decision:** Is the proposed architecture sound?
**If REJECT:** Provide feedback, architecture-agent revises

### Gate 2: Design Review Approval
**When:** After design-review.md is generated
**Decision:** Are identified risks acceptable?
**If REJECT:** Revise architecture to address risks

### Gate 3: Code Review Approval
**When:** After code-review-report.md is generated
**Decision:** Is implementation quality acceptable?
**If REJECT:** Implementation-agent fixes issues

### Gate 4: PR Merge
**When:** After PR is created
**Decision:** Ready to merge to main?
**If REJECT:** Address feedback, re-verify

---

## Artifacts & Traceability

Each stage produces an artifact stored in `docs/sdlc/`:

```
docs/sdlc/
├── requirements.md           [Stage 1 output]
├── architecture.md           [Stage 2 output]
├── design-review.md          [Stage 3 output]
├── impl-plan.md              [Stage 4 output]
├── code-review-report.md     [Stage 6 output]
└── verification-report.md    [Stage 7 output]
```

**Git Commits:**
- Each stage commits its artifact(s)
- Commit messages reference stage and agent
- Full audit trail in git history

---

## Directory Structure

```
agentic-docsync-capstone/
├── .github/
│   ├── copilot-instructions.md       # Project-wide instructions
│   └── agents/                        # Agent definitions
│       ├── orchestrator-agent.md
│       ├── requirements-agent.md
│       ├── architecture-agent.md
│       ├── design-review-agent.md
│       ├── planning-agent.md
│       ├── implementation-agent.md
│       ├── code-review-agent.md
│       ├── verification-agent.md
│       └── pr-agent.md
│
├── custom_PRD/                        # Input requirements
│   ├── PRD-001-Documentation-Sync.md
│   └── PRD-002-SDLC-Integration.md
│
├── docs/
│   ├── sdlc/                          # SDLC artifacts
│   │   ├── requirements.md
│   │   ├── architecture.md
│   │   ├── design-review.md
│   │   ├── impl-plan.md
│   │   ├── code-review-report.md
│   │   └── verification-report.md
│   └── api/                           # Generated API docs
│       └── api.md
│
├── docsync/                           # Feature implementation
│   ├── __init__.py
│   ├── openapi_parser.py
│   ├── markdown_generator.py
│   ├── diff_engine.py
│   └── cli.py
│
├── tests/                             # Test suite
│   ├── test_openapi_parser.py
│   ├── test_markdown_generator.py
│   ├── test_diff_engine.py
│   └── test_cli.py
│
└── (existing files)
```

---

## Success Criteria

**Demo is Ready When:**
- ✅ All 8 agents are defined and functional
- ✅ Orchestrator coordinates the workflow
- ✅ 4 human approval gates work correctly
- ✅ Full SDLC completes: PRD → merged PR
- ✅ Git history shows clear stage progression
- ✅ Documentation is complete and clear
- ✅ Feature works (docsync successfully syncs docs)

---

## Technical Notes

### Agent Definition Format
Each agent is a markdown file with:
- Purpose statement
- Input requirements
- Process steps
- Output specification
- Tools/capabilities needed
- Success criteria

### Orchestrator Implementation
- Can be a Python script or shell script
- Uses GitHub Copilot CLI/API
- Manages state between stages
- Prompts human for approvals
- Handles reject/retry loops

### GitHub Copilot Features to Showcase
1. **Agents:** 8 specialized agents + orchestrator
2. **Prompts:** Reusable prompts for each stage (optional)
3. **Instructions:** Project-wide `.github/copilot-instructions.md`
4. **Skills:** OpenAPI analysis capability (optional)
5. **Hooks:** Pre-commit validation (optional, bonus points)

---

## Timeline

**Estimated Duration:** 1 capstone session

**Breakdown:**
- Setup (PRDs, agents): Already done
- Stage 1-2: ~15 min
- Stage 3-4: ~15 min
- Stage 5-6: ~30 min
- Stage 7-8: ~20 min
- **Total:** ~90 min end-to-end

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Agent generates incorrect code | Code review agent + human approval gate |
| SDLC too complex to demo | Keep each stage focused and simple |
| GitHub Copilot limitations | Fall back to manual prompting if needed |
| Tests don't pass first time | Verification agent iterates until passing |

---

## Out of Scope

- Real JIRA integration (using PRD files instead)
- Continuous integration automation
- Multi-branch workflows
- Advanced git operations (rebase, squash)
- Deployment/release stages
- Performance benchmarking
