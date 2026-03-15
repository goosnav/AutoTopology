# CLAUDE.md – Permanent Rules & Checklist
# (Superpowers + pro-workflow enforce this on EVERY session)

## Core Workflow (NEVER break)
- ALWAYS use full Superpowers flow: brainstorm → write Plan.md → manual/automated review → git worktree → subagent strategy (prefer parallel when possible) → TDD implementation → code review → wrap-up ritual
- pro-workflow MUST run: scout agent (require >80% confidence), self-correction loop on any issue, 12 quality hooks
- Break EVERY plan into 2–5 minute tasks ONLY
- NEVER write or edit code until a failing test exists

## Quality Marching Orders (auto-applied in every review)
- Remove ALL dead/outdated code before adding anything new
- Run full test suite + basic security scan (no secrets, no obvious vulns)
- Follow project conventions + industry standards (ESLint/Prettier, PEP8, etc.)
- After ANY mistake or bad output: immediately append a new rule here + trigger pro-workflow wrap-up

## Agent & Subagent Rules
- Use small specialized sub-agents (tester, reviewer, debugger, scout) via skills
- Prefer parallel worktrees for independent tasks
- Keep context fresh — no giant monolith edits

## Learning & Memory
- Every correction becomes a permanent rule
- Review this file at the start of every new feature

# Project-specific rules (add yours below):
# - Example: Always use TypeScript strict mode
# - Example: All components must have tests + Storybook

## Persistent Handover & Memory Rules (SOTA March 2026 – Recall + wrap-up)
- At the END of EVERY major task, before /compact, or when closing a session: ALWAYS trigger pro-workflow wrap-up ritual + burn tokens to:
  1. Update .claude/recall-context.md (via Recall — keeps verbatim decisions, failed paths, architecture)
  2. Update ProjectState.md (structured summary for instant pickup)
- ProjectState.md format (Claude auto-maintains this):
  - Current architecture & key decisions
  - Open tasks + priorities (with confidence scores)
  - Test status & coverage
  - Known bugs + fixes applied
  - Patterns learned + rules added to CLAUDE.md
  - Next 2-5 minute micro-tasks
- Next session or sub-agent MUST read ProjectState.md + recall-context.md first (Superpowers/pro-workflow + Recall enforce this)
- Use /recall:session <session-id> only if you need the full raw transcript
- Every correction → append rule here + trigger self-correction loop

## ProjectState.md (create this empty file in repo root — Claude will populate it)

## README.md
- Add to the README.md file to ensure a comprehensive and proper explaination of the project along with the explaination of how to navigate the architecture and actually use the program. This should be optimized for public facing github projects along with solid formatting. 