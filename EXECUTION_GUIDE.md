# Execution Guide - How to Actually Run the Agentic SDLC

## Understanding the Architecture

### What We Built
- **Agent Definitions** (.md files) - Instructions for AIs, not executable code
- **PRD Files** - Input requirements
- **Directory Structure** - Where outputs go

### What Executes the Agents?
The agents are executed by **an AI assistant reading the agent definition and following it**. Three options:

1. **GitHub Copilot** (if available) - Reads agent definitions in VS Code/CLI
2. **Claude Code** (me! - what we're using right now)
3. **Manual** (you, following the instructions)

---

## Option 1: Execute with Claude Code (Current Tool - RECOMMENDED)

**This is what we're using right now!** I (Claude) can act as each agent.

### Entry Point: Use Me (Claude)

I can read the agent definitions and execute each stage for you. Here's how:

#### Start the Workflow

**Prompt me with:**
```
Execute Stage 1: Act as requirements-agent from .github/agents/requirements-agent.md.
Read custom_PRD/PRD-001-Documentation-Sync.md and generate docs/sdlc/requirements.md following the process exactly.
```

**I will:**
1. Read the agent definition file
2. Read the PRD
3. Extract requirements
4. Generate docs/sdlc/requirements.md
5. Commit it
6. Tell you it's done

**Then you:**
- Review the output
- Approve or give feedback
- Ask me to proceed to Stage 2

#### Continue Through Stages

**For each stage, prompt me:**
```
Execute Stage 2: Act as architecture-agent from .github/agents/architecture-agent.md.
Read docs/sdlc/requirements.md and generate docs/sdlc/architecture.md.
```

```
Execute Stage 3: Act as design-review-agent...
```

And so on through all 8 stages.

#### Orchestrator Role

Instead of executing each stage manually, you can ask me to act as the orchestrator:

**Prompt:**
```
Act as orchestrator-agent from .github/agents/orchestrator-agent.md.
Execute all 8 SDLC stages in order, pausing at approval gates for my review.
Start with Stage 1 (requirements-agent).
```

**I will:**
1. Execute Stage 1 (requirements)
2. Execute Stage 2 (architecture)
3. PAUSE and show you architecture.md
4. Ask: "Review architecture.md. Approve? (yes/no)"
5. Wait for your response
6. Continue based on your approval
7. Repeat for all stages

**This is the easiest way to execute the workflow!**

---

## Option 2: Execute with GitHub Copilot (If You Have It)

### Prerequisites
- GitHub Copilot subscription
- VS Code with GitHub Copilot extension
- OR GitHub Copilot CLI installed

### Entry Point: VS Code Copilot Chat

1. **Open VS Code** with your repository
2. **Open Copilot Chat** (Cmd+Shift+I or Ctrl+Shift+I)
3. **Type a prompt referencing the agent:**

```
@workspace Act as requirements-agent from .github/agents/requirements-agent.md.
Read custom_PRD/PRD-001-Documentation-Sync.md and generate docs/sdlc/requirements.md.
Follow the process steps exactly as defined in the agent file.
```

4. **Copilot will:**
   - Read the agent definition
   - Read the PRD
   - Generate the requirements.md file
   - Show you the result

5. **You review and approve, then continue to next stage**

### Entry Point: GitHub Copilot CLI

If you have `gh copilot` CLI:

```bash
gh copilot suggest "Act as requirements-agent from .github/agents/requirements-agent.md. Read custom_PRD/PRD-001-Documentation-Sync.md and generate docs/sdlc/requirements.md"
```

### Orchestrator with Copilot

```
@workspace Act as orchestrator-agent from .github/agents/orchestrator-agent.md.
Execute the full SDLC workflow (8 stages) with approval gates.
Start with Stage 1.
```

Copilot will attempt to coordinate the workflow, pausing for your approval.

---

## Option 3: Manual Execution (You Follow the Instructions)

You can execute the workflow yourself by:

1. **Read the agent definition** (e.g., requirements-agent.md)
2. **Follow the process steps manually**
3. **Generate the output files yourself**
4. **Commit with proper message**

This is educational but time-consuming.

---

## MCP (Model Context Protocol) Setup

### What MCPs Are
MCPs are integrations that give AI assistants access to external tools:
- **JIRA MCP** - Read/write JIRA issues
- **GitHub MCP** - Advanced GitHub operations
- **Filesystem MCP** - File operations (built-in for Claude)
- **Web MCP** - Fetch web content (built-in)

### What MCPs We're Actually Using

**For this workflow: NONE required!**

We designed this to be **MCP-free** and simple:

#### Instead of JIRA MCP → We use PRD files
- **Why:** Simpler, no authentication needed
- **How:** PRD-001-Documentation-Sync.md contains all requirements
- **Benefit:** Works offline, no external dependencies

#### Instead of GitHub MCP → We use `gh` CLI
- **Why:** Simple, standard, widely available
- **How:** `gh pr create`, `gh repo view`, etc.
- **Benefit:** No complex MCP setup

#### Built-in Tools (Already Available)
- **File operations** - Claude/Copilot can read/write files natively
- **Git operations** - Using bash commands
- **Python execution** - For running tests

### If You Want JIRA Integration (Optional)

If you want to use real JIRA instead of PRD files:

#### Setup JIRA MCP (for Claude Code)

1. **Check if JIRA MCP is available:**
```
/mcp
```

2. **If not available, you'd need to configure it in Claude settings** (but this is overkill for the demo)

3. **Modify requirements-agent to read from JIRA:**
```
Instead of: Read custom_PRD/PRD-001-Documentation-Sync.md
Use: Read JIRA issue PROJECT-123 via MCP
```

**Recommendation:** Stick with PRD files for simplicity!

---

## Why is Orchestrator an Agent?

Great question! Here's the thinking:

### The Orchestrator IS an Agent Because:

1. **It has a specific role** - Coordinate other agents
2. **It has inputs** - Agent definitions, workflow state
3. **It has a process** - Execute stages in order, manage approvals
4. **It has outputs** - Workflow status, summary report

### But It's Special:

The orchestrator is a **meta-agent**:
- **Regular agents** (requirements, architecture, etc.) → Perform specific tasks
- **Orchestrator agent** → Invokes and coordinates regular agents

Think of it like:
- **Workers** (agents) → Build parts of a house
- **Foreman** (orchestrator) → Coordinates workers, checks quality

### Alternatives to Orchestrator as Agent

We could have made orchestrator:
1. **A script** - Python/Bash script that calls other agents
2. **A GitHub Action** - Automated workflow
3. **A human** - You, manually coordinating

But making it an agent provides:
- ✅ Consistency - Same pattern as other agents
- ✅ Flexibility - AI can adapt to issues
- ✅ Simplicity - One execution model for everything

---

## Execution Flow Diagram

```
You (Human)
    ↓
    [Prompts AI: "Act as orchestrator-agent"]
    ↓
AI (Claude/Copilot) reads orchestrator-agent.md
    ↓
    [Stage 1] AI reads requirements-agent.md → Executes → Creates requirements.md
    ↓
    [Stage 2] AI reads architecture-agent.md → Executes → Creates architecture.md
    ↓
    [PAUSE] AI shows you architecture.md → "Approve?"
    ↓
You → "Yes, approve"
    ↓
    [Stage 3] AI reads design-review-agent.md → Executes → Creates design-review.md
    ↓
    ... continues through all 8 stages ...
    ↓
    [Stage 8] AI creates PR
    ↓
You → Review and merge PR
    ↓
✅ COMPLETE
```

---

## Practical Example: Let's Start Stage 1

### If Using Claude Code (Me):

**You say:**
```
Execute Stage 1: Act as requirements-agent.
Read .github/agents/requirements-agent.md for instructions.
Read custom_PRD/PRD-001-Documentation-Sync.md for input.
Generate docs/sdlc/requirements.md following the agent's process.
```

**I do:**
1. Read requirements-agent.md (I understand my role)
2. Read PRD-001 (I understand the requirements)
3. Extract and structure requirements
4. Write docs/sdlc/requirements.md
5. Commit the file
6. Tell you: "✅ Stage 1 complete. Review docs/sdlc/requirements.md. Ready for Stage 2?"

**You review and approve, then we continue.**

---

## Comparison: GitHub Copilot vs Claude Code

| Feature | GitHub Copilot | Claude Code (Me) |
|---------|----------------|------------------|
| **Availability** | Requires subscription | You're using me now! |
| **Setup** | VS Code extension | Already set up |
| **Agent Execution** | Via @workspace prompts | Via direct prompts |
| **File Operations** | Native | Native |
| **Git Operations** | Via commands | Via bash/git |
| **Approval Gates** | Manual prompts | Manual prompts |
| **Orchestration** | Can coordinate | Can coordinate |

**Bottom Line:** Both work! Claude Code (what you're using now) is perfect for this.

---

## Recommended Approach for Your Demo

### Use Claude Code (Me) as the Executor

**Advantages:**
- ✅ Already set up (you're talking to me)
- ✅ No additional tools needed
- ✅ I can execute all 8 stages
- ✅ I can act as orchestrator
- ✅ Clear, transparent process

**Process:**
1. You prompt me to execute each stage (or act as orchestrator)
2. I read agent definitions and execute
3. I create artifacts and commit
4. You review and approve
5. We proceed to next stage

**Time Required:** ~90 minutes for full workflow

---

## Next Step: Would You Like Me to Start?

I can execute the workflow right now! Just say:

**Option A (Orchestrated):**
```
"Execute the orchestrator-agent workflow. Start with Stage 1 and proceed through all stages with approval gates."
```

**Option B (Stage by Stage):**
```
"Execute Stage 1: requirements-agent. Read the PRD and generate requirements.md"
```

Which would you prefer?

---

## FAQ

### Q: Are the agent .md files executable code?
**A:** No, they're instructions for an AI to follow.

### Q: Do I need to install any MCPs?
**A:** No! The workflow uses PRD files and standard tools only.

### Q: Can this run automatically without human input?
**A:** No (by design). Approval gates require human decisions.

### Q: Why not use a Python script instead of agents?
**A:** Agent-based = flexible, AI-driven, adapts to issues. Script = rigid, predefined logic.

### Q: What if GitHub Copilot doesn't understand the agent definitions?
**A:** Use Claude Code (me) instead, or execute manually following the instructions.

### Q: How do I know if it's working?
**A:** Check `docs/sdlc/` - files appear after each stage. Check `git log` - commits show progress.

---

**Ready to execute? Let me know!**
