#!/usr/bin/env python3
"""
Agentic SDLC Orchestrator

Entry point for executing the complete SDLC workflow.
This script coordinates all 8 agents and manages approval gates.

Usage:
    python orchestrator.py                    # Full workflow
    python orchestrator.py --stage 1          # Execute specific stage
    python orchestrator.py --dry-run          # Preview without execution
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# ANSI colors for output
class Color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class StageStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class Stage:
    """Represents an SDLC stage"""
    id: int
    name: str
    agent_file: str
    input_files: List[str]
    output_file: str
    requires_approval: bool
    description: str

class AgenticOrchestrator:
    """Orchestrates the Agentic SDLC workflow"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.root_dir = Path(__file__).parent
        self.agents_dir = self.root_dir / ".github" / "agents"
        self.sdlc_dir = self.root_dir / "docs" / "sdlc"
        self.stages: List[Stage] = self._define_stages()
        self.stage_status: Dict[int, StageStatus] = {}

        # Ensure directories exist
        self.sdlc_dir.mkdir(parents=True, exist_ok=True)

    def _define_stages(self) -> List[Stage]:
        """Define all 8 SDLC stages"""
        return [
            Stage(
                id=1,
                name="Requirements Analysis",
                agent_file="requirements-agent.md",
                input_files=["custom_PRD/PRD-001-Documentation-Sync.md"],
                output_file="docs/sdlc/requirements.md",
                requires_approval=False,
                description="Extract and structure requirements from PRD"
            ),
            Stage(
                id=2,
                name="Architecture Design",
                agent_file="architecture-agent.md",
                input_files=["docs/sdlc/requirements.md"],
                output_file="docs/sdlc/architecture.md",
                requires_approval=True,
                description="Design system architecture and components"
            ),
            Stage(
                id=3,
                name="Design Review",
                agent_file="design-review-agent.md",
                input_files=["docs/sdlc/architecture.md"],
                output_file="docs/sdlc/design-review.md",
                requires_approval=True,
                description="Review architecture for risks and quality"
            ),
            Stage(
                id=4,
                name="Implementation Planning",
                agent_file="planning-agent.md",
                input_files=["docs/sdlc/architecture.md", "docs/sdlc/design-review.md"],
                output_file="docs/sdlc/impl-plan.md",
                requires_approval=False,
                description="Break down into implementation tasks"
            ),
            Stage(
                id=5,
                name="Implementation",
                agent_file="implementation-agent.md",
                input_files=["docs/sdlc/impl-plan.md"],
                output_file="docsync/",
                requires_approval=False,
                description="Write production code for docsync module"
            ),
            Stage(
                id=6,
                name="Code Review",
                agent_file="code-review-agent.md",
                input_files=["docsync/"],
                output_file="docs/sdlc/code-review-report.md",
                requires_approval=True,
                description="Review code quality and security"
            ),
            Stage(
                id=7,
                name="Verification & Testing",
                agent_file="verification-agent.md",
                input_files=["docsync/"],
                output_file="docs/sdlc/verification-report.md",
                requires_approval=False,
                description="Generate and run comprehensive tests"
            ),
            Stage(
                id=8,
                name="Pull Request Creation",
                agent_file="pr-agent.md",
                input_files=["docs/sdlc/"],
                output_file="GitHub PR",
                requires_approval=True,
                description="Create comprehensive pull request"
            ),
        ]

    def print_header(self):
        """Print orchestrator header"""
        print(f"\n{Color.HEADER}{Color.BOLD}{'=' * 70}{Color.ENDC}")
        print(f"{Color.HEADER}{Color.BOLD}   Agentic SDLC Orchestrator{Color.ENDC}")
        print(f"{Color.HEADER}{Color.BOLD}   Automated Documentation Sync - Capstone Project{Color.ENDC}")
        print(f"{Color.HEADER}{Color.BOLD}{'=' * 70}{Color.ENDC}\n")

    def print_stage_header(self, stage: Stage):
        """Print stage header"""
        print(f"\n{Color.OKCYAN}{Color.BOLD}Stage {stage.id}: {stage.name}{Color.ENDC}")
        print(f"{Color.OKCYAN}{'─' * 70}{Color.ENDC}")
        print(f"Agent: {stage.agent_file}")
        print(f"Description: {stage.description}")
        print(f"Output: {stage.output_file}")
        print(f"Approval Required: {'Yes' if stage.requires_approval else 'No'}")
        print()

    def check_prerequisites(self, stage: Stage) -> bool:
        """Check if stage prerequisites are met"""
        for input_file in stage.input_files:
            input_path = self.root_dir / input_file
            if not input_path.exists():
                print(f"{Color.FAIL}✗ Missing prerequisite: {input_file}{Color.ENDC}")
                return False

        agent_path = self.agents_dir / stage.agent_file
        if not agent_path.exists():
            print(f"{Color.FAIL}✗ Missing agent definition: {stage.agent_file}{Color.ENDC}")
            return False

        print(f"{Color.OKGREEN}✓ All prerequisites met{Color.ENDC}")
        return True

    def execute_stage_with_copilot(self, stage: Stage) -> bool:
        """Execute stage using GitHub Copilot"""
        print(f"{Color.OKBLUE}Invoking GitHub Copilot to execute {stage.name}...{Color.ENDC}\n")

        # Read agent definition
        agent_path = self.agents_dir / stage.agent_file
        with open(agent_path, 'r') as f:
            agent_definition = f.read()

        # Create prompt for Copilot
        prompt = self._create_copilot_prompt(stage, agent_definition)

        # Show prompt
        print(f"{Color.WARNING}Copilot Prompt:{Color.ENDC}")
        print(f"{Color.BOLD}{'─' * 70}{Color.ENDC}")
        print(prompt)
        print(f"{Color.BOLD}{'─' * 70}{Color.ENDC}\n")

        if self.dry_run:
            print(f"{Color.WARNING}[DRY RUN] Would execute with GitHub Copilot{Color.ENDC}")
            return True

        # Instructions for user
        print(f"{Color.HEADER}ACTION REQUIRED:{Color.ENDC}")
        print("1. Copy the prompt above")
        print("2. Open VS Code Copilot Chat (Cmd+Shift+I or Ctrl+Shift+I)")
        print("3. Paste the prompt and send it")
        print("4. Wait for Copilot to complete the task")
        print("5. Come back here and confirm completion\n")

        # Wait for user confirmation
        while True:
            response = input(f"{Color.BOLD}Has Copilot completed this stage? (yes/no/skip): {Color.ENDC}").strip().lower()
            if response == 'yes':
                return True
            elif response == 'skip':
                print(f"{Color.WARNING}Stage skipped by user{Color.ENDC}")
                self.stage_status[stage.id] = StageStatus.SKIPPED
                return False
            elif response == 'no':
                print(f"{Color.FAIL}Stage execution cancelled{Color.ENDC}")
                return False
            else:
                print("Please enter 'yes', 'no', or 'skip'")

    def _create_copilot_prompt(self, stage: Stage, agent_definition: str) -> str:
        """Create a prompt for GitHub Copilot"""
        input_files_str = ", ".join(stage.input_files)

        prompt = f"""@workspace Execute SDLC Stage {stage.id}: {stage.name}

Agent Definition: .github/agents/{stage.agent_file}

Task: Act as the {stage.name.lower()} agent and execute the process defined in the agent file.

Inputs: {input_files_str}
Output: {stage.output_file}

Instructions:
1. Read the agent definition from .github/agents/{stage.agent_file}
2. Read the input files: {input_files_str}
3. Follow the process steps exactly as defined in the agent file
4. Generate the output file: {stage.output_file}
5. Commit the changes with message format:
   [{stage.name}] <description>

   Generated by: {stage.agent_file.replace('.md', '')}
   Input: {input_files_str}
   Output: {stage.output_file}

Please execute this task following the agent definition precisely."""

        return prompt

    def request_approval(self, stage: Stage) -> bool:
        """Request human approval for stage"""
        output_path = self.root_dir / stage.output_file

        print(f"\n{Color.WARNING}{Color.BOLD}APPROVAL GATE {stage.id}{Color.ENDC}")
        print(f"{Color.WARNING}{'=' * 70}{Color.ENDC}")
        print(f"Stage: {stage.name}")
        print(f"Output: {stage.output_file}")
        print()

        if output_path.exists() and output_path.is_file():
            print(f"{Color.OKBLUE}Generated Output Preview:{Color.ENDC}")
            print(f"{Color.BOLD}{'─' * 70}{Color.ENDC}")
            with open(output_path, 'r') as f:
                content = f.read()
                # Show first 50 lines
                all_lines = content.split('\n')
                lines = all_lines[:50]
                print('\n'.join(lines))
                if len(all_lines) > 50:
                    remaining = len(all_lines) - 50
                    print(f"\n... ({remaining} more lines)")
            print(f"{Color.BOLD}{'─' * 70}{Color.ENDC}\n")

        print(f"Please review: {stage.output_file}")
        print()

        while True:
            response = input(f"{Color.BOLD}Approve this stage? (yes/no/feedback): {Color.ENDC}").strip().lower()
            if response == 'yes':
                print(f"{Color.OKGREEN}✓ Stage approved{Color.ENDC}")
                return True
            elif response == 'no':
                print(f"{Color.FAIL}✗ Stage rejected{Color.ENDC}")
                return False
            elif response == 'feedback':
                feedback = input(f"{Color.BOLD}Enter your feedback: {Color.ENDC}")
                print(f"\n{Color.WARNING}Feedback recorded: {feedback}{Color.ENDC}")
                print("Agent should revise based on feedback.")
                return False
            else:
                print("Please enter 'yes', 'no', or 'feedback'")

    def execute_workflow(self, start_stage: int = 1, end_stage: int = 8):
        """Execute the complete workflow"""
        self.print_header()

        if self.dry_run:
            print(f"{Color.WARNING}DRY RUN MODE - No actual execution{Color.ENDC}\n")

        print(f"Executing stages {start_stage} to {end_stage}")
        print(f"Approval gates: {sum(1 for s in self.stages if s.requires_approval)} total\n")

        for stage in self.stages:
            if stage.id < start_stage or stage.id > end_stage:
                continue

            self.print_stage_header(stage)
            self.stage_status[stage.id] = StageStatus.IN_PROGRESS

            # Check prerequisites
            if not self.check_prerequisites(stage):
                print(f"{Color.FAIL}Cannot proceed - prerequisites not met{Color.ENDC}")
                self.stage_status[stage.id] = StageStatus.FAILED
                break

            # Execute stage
            success = self.execute_stage_with_copilot(stage)

            if not success:
                if self.stage_status.get(stage.id) != StageStatus.SKIPPED:
                    self.stage_status[stage.id] = StageStatus.FAILED
                    print(f"{Color.FAIL}Workflow stopped at stage {stage.id}{Color.ENDC}")
                break

            self.stage_status[stage.id] = StageStatus.COMPLETED
            print(f"{Color.OKGREEN}✓ Stage {stage.id} completed{Color.ENDC}")

            # Approval gate
            if stage.requires_approval:
                approved = self.request_approval(stage)
                if not approved:
                    print(f"{Color.FAIL}Workflow stopped - approval denied{Color.ENDC}")
                    self.stage_status[stage.id] = StageStatus.FAILED
                    break

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print workflow summary"""
        print(f"\n{Color.HEADER}{Color.BOLD}Workflow Summary{Color.ENDC}")
        print(f"{Color.HEADER}{'=' * 70}{Color.ENDC}\n")

        for stage in self.stages:
            status = self.stage_status.get(stage.id, StageStatus.PENDING)
            status_color = {
                StageStatus.COMPLETED: Color.OKGREEN,
                StageStatus.FAILED: Color.FAIL,
                StageStatus.IN_PROGRESS: Color.WARNING,
                StageStatus.SKIPPED: Color.WARNING,
                StageStatus.PENDING: Color.ENDC,
            }.get(status, Color.ENDC)

            status_symbol = {
                StageStatus.COMPLETED: "✓",
                StageStatus.FAILED: "✗",
                StageStatus.IN_PROGRESS: "⏳",
                StageStatus.SKIPPED: "⊘",
                StageStatus.PENDING: "○",
            }.get(status, "?")

            print(f"{status_color}{status_symbol} Stage {stage.id}: {stage.name} - {status.value}{Color.ENDC}")

        completed = sum(1 for s in self.stage_status.values() if s == StageStatus.COMPLETED)
        total = len(self.stages)

        print(f"\n{Color.BOLD}Progress: {completed}/{total} stages completed{Color.ENDC}")

        if completed == total:
            print(f"\n{Color.OKGREEN}{Color.BOLD}🎉 WORKFLOW COMPLETE! 🎉{Color.ENDC}")
            print(f"{Color.OKGREEN}All stages executed successfully{Color.ENDC}")
            print(f"\nNext step: Review and merge the PR created in Stage 8\n")
        else:
            print(f"\n{Color.WARNING}Workflow incomplete. Review issues and continue.{Color.ENDC}\n")

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Agentic SDLC Orchestrator - Execute GitHub Copilot workflow"
    )
    parser.add_argument(
        '--stage',
        type=int,
        help='Execute a specific stage (1-8)'
    )
    parser.add_argument(
        '--start',
        type=int,
        default=1,
        help='Start from stage N (default: 1)'
    )
    parser.add_argument(
        '--end',
        type=int,
        default=8,
        help='End at stage N (default: 8)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview workflow without execution'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all stages and exit'
    )

    args = parser.parse_args()

    orchestrator = AgenticOrchestrator(dry_run=args.dry_run)

    if args.list:
        print("\nSDLC Stages:")
        print("=" * 70)
        for stage in orchestrator.stages:
            approval = "🔒 Approval Required" if stage.requires_approval else ""
            print(f"\nStage {stage.id}: {stage.name} {approval}")
            print(f"  Agent: {stage.agent_file}")
            print(f"  Output: {stage.output_file}")
            print(f"  Description: {stage.description}")
        print()
        return

    if args.stage:
        orchestrator.execute_workflow(start_stage=args.stage, end_stage=args.stage)
    else:
        orchestrator.execute_workflow(start_stage=args.start, end_stage=args.end)

if __name__ == "__main__":
    main()
