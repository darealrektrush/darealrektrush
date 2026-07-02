#!/usr/bin/env bash

# Sets up the daily-log + memory + task-file workflow for Claude Code.

# Run this on your Linux machine (where Claude Code runs), e.g.:

#   chmod +x setup-claude-workflow.sh

#   ./setup-claude-workflow.sh

set -e

LOGS="$HOME/Google Drive/ClaudeLogs"

MEMDIR="$HOME/.claude/memory"

COMMANDS="$HOME/.claude/commands"

TZ="America/Vancouver"

GLOBAL_CLAUDE_MD="$HOME/.claude/CLAUDE.md"

echo "Setting up workflow..."

echo "  Logs:     $LOGS"

echo "  Memory:   $MEMDIR"

echo "  Commands: $COMMANDS"

echo "  Timezone: $TZ"

echo

mkdir -p "$LOGS"

mkdir -p "$MEMDIR"

mkdir -p "$COMMANDS"

# --- Task file (source of truth for open/done) ---

TASKFILE="$MEMDIR/thomas-open-tasks.md"

if [ ! -f "$TASKFILE" ]; then

  cat > "$TASKFILE" << 'EOF'

# Thomas — Open Tasks

Source of truth for what's open vs. done. Written by /wrap and /end-of-day, read by /good-morning and /catch-up.

## Open

## Done

EOF

  echo "Created $TASKFILE"

else

  echo "Task file already exists, leaving it alone: $TASKFILE"

fi

# --- MEMORY.md index ---

MEMORY_MD="$MEMDIR/MEMORY.md"

if [ ! -f "$MEMORY_MD" ]; then

  cat > "$MEMORY_MD" << 'EOF'

# MEMORY.md — Persistent Memory Index

This file and the other files in this folder hold deduplicated, durable facts

(project state, decisions, gotchas) — auto-loaded at the start of every session.

## Files in this folder

- thomas-open-tasks.md — SOURCE OF TRUTH for what's open vs. done. Logs are

  narrative and can go stale; this file is current status. /wrap and

  /end-of-day write it; /good-morning and /catch-up read it.

## System note

Daily-log + memory workflow, set up on 2026-07-02.

- Daily logs live in ~/Google Drive/ClaudeLogs, one markdown file per day,

  named [T] YYYY-MM-DD.md. Multiple sessions per day append blocks to the

  same dated file.

- Three layers: (1) daily log = chronological narrative, (2) this memory

  folder = deduplicated durable facts, (3) thomas-open-tasks.md = current

  status, the single source of truth for open vs. done.

- Timezone for timestamps: America/Vancouver (Pacific).

- Slash commands: /good-morning (start of day, full recap + recommendation),

  /catch-up (light orientation for a fresh mid-day chat), /wrap (any-time

  session handoff), /end-of-day (full day wrap-up).

EOF

  echo "Created $MEMORY_MD"

else

  echo "MEMORY.md already exists, leaving it alone: $MEMORY_MD"

fi

# --- Global CLAUDE.md pointer ---

mkdir -p "$(dirname "$GLOBAL_CLAUDE_MD")"

POINTER_LINE="At the start of every session, read $MEMORY_MD and the files it points to for persistent project memory."

if [ -f "$GLOBAL_CLAUDE_MD" ] && grep -qF "$MEMORY_MD" "$GLOBAL_CLAUDE_MD"; then

  echo "CLAUDE.md already points to memory folder, skipping."

else

  {

    echo ""

    echo "## Persistent memory"

    echo "$POINTER_LINE"

  } >> "$GLOBAL_CLAUDE_MD"

  echo "Added memory pointer to $GLOBAL_CLAUDE_MD"

fi

# --- Slash command: good-morning ---

cat > "$COMMANDS/good-morning.md" << EOF

---

description: Morning orientation — recaps recent daily logs and recommends what to work on

---

# Good Morning

Orient the new session.

## Steps

1. Read persistent memory — MEMORY.md and the memory files in $MEMDIR carry current project state; lean on them.

2. Read the task list — open thomas-open-tasks.md in $MEMDIR and treat it as the source of truth for what's open vs. done. The daily logs are a chronological narrative and can lag; the task file is the deduplicated, current status. Build the recap's open-items list from THIS file, not from the logs alone.

3. Read the last 3 daily logs from $LOGS (sort by date in the [T] YYYY-MM-DD.md filename, most recent first). Use these for recent-activity color, then reconcile against the task file (step 2): if a log and the task file disagree on whether something is done, say so and verify before asserting status — don't silently trust either one.

4. Brief recap — keep it tight:

   - 2-4 bullets of what was worked on recently (from the logs).

   - Open/mid-flight items, drawn from thomas-open-tasks.md.

   - Then ONE clear recommendation for the most important thing to work on. Make a real call.

5. Ask whether I want to jump into a project or start something new, listing the live open problems (from thomas-open-tasks.md) one line each.

Tone: punchy, conversational, no wall of text.

EOF

echo "Created $COMMANDS/good-morning.md"

# --- Slash command: catch-up ---

cat > "$COMMANDS/catch-up.md" << EOF

---

description: Light orientation for a fresh chat — quick context from memory and today's log, no full morning recap

---

# Catch Up

Lightweight orientation for picking up in a fresh chat mid-stream. Lighter than /good-morning — no broad multi-day recap, no "what do you want to work on" interview. Just enough to keep moving.

## Steps

1. Lean on memory — MEMORY.md and the files in $MEMDIR carry current project state.

2. Read today's log only (and yesterday's if today's doesn't exist yet) from $LOGS — [T] YYYY-MM-DD.md. Pay attention to the latest ## Session block's "Still open" / "Pick up here".

3. Give a 2-3 line catch-up: where things stand right now and the single most likely next action. Then ask "Pick up here, or something else?" — short, no ceremony.

For a full start-of-day recap with recommendations, use /good-morning instead.

EOF

echo "Created $COMMANDS/catch-up.md"

# --- Slash command: wrap ---

cat > "$COMMANDS/wrap.md" << EOF

---

description: Wrap up and hand off the current session (any time of day) — saves a timestamped log block and updates memory

---

# Wrap / Session Handoff

Save the state of THIS chat session so a new chat can pick up cleanly. Same machinery as /end-of-day, but framed for any-time-of-day session handoffs.

## Steps

1. Determine today's date and the current time (my timezone: $TZ).

2. Recap THIS session — focus on what a fresh chat would need to continue: decisions made, files changed, what's done, and especially anything left mid-flight or unfinished.

3. Write to today's log file $LOGS/[T] YYYY-MM-DD.md:

   - If the file exists, APPEND a new block headed ## Session — <HH:MM $TZ>. Do not overwrite earlier blocks. Multiple sessions per day live in one dated file.

   - If it doesn't exist yet, create it with frontmatter (author: claude / type: daily / date: YYYY-MM-DD), a # Session Log — <Weekday, Month D YYYY> heading, then the first session block.

   - In each session block capture: Worked on, Built/Changed, Still open, Pick up here (one clear next action).

4. Reconcile the task list — update thomas-open-tasks.md in $MEMDIR so it matches reality after this session: tick off anything completed (with a dated checkmark), add any new tasks that surfaced, and re-prioritize if things changed. This file is what /good-morning reads back, so keeping it current is what prevents log-task drift.

5. Update the rest of persistent memory for any other durable facts (update existing files rather than duplicating, keep MEMORY.md in sync). Log = narrative; memory = deduplicated facts.

6. Report the log file path and the session-block time you appended, plus any memory files touched (call out the task-list update explicitly).

EOF

echo "Created $COMMANDS/wrap.md"

# --- Slash command: end-of-day ---

cat > "$COMMANDS/end-of-day.md" << EOF

---

description: End-of-day wrap-up — writes a dated session log and updates persistent memory

---

# End of Day Wrap-Up

Run the end-of-day process.

## Steps

1. Determine today's date (my timezone: $TZ). Use it for the filename and heading.

2. Recap the session. Look back over what was actually worked on in this conversation — decisions made, files changed, things discovered, things left unfinished. Don't pad; capture what a future session would need to pick up cleanly.

3. Write the log to $LOGS/[T] YYYY-MM-DD.md. If a file for today already exists, APPEND a new ## Session — <time> block rather than overwriting. Structure:

```markdown
---
author: claude
type: daily
date: YYYY-MM-DD
---

# Session Log — <Weekday, Month D YYYY>

## What We Worked On

- ...

## What Was Built or Changed

- ...

## Still Open

- ...

## Start Here Tomorrow

<one clear paragraph: the single most important next action>
```

4. Reconcile the task list. Update thomas-open-tasks.md in $MEMDIR to match reality after today: tick off completed items (with a dated checkmark), add new tasks that surfaced, re-prioritize as needed.

5. Update the rest of persistent memory for any other durable facts that emerged today. Update existing files rather than duplicating; keep the MEMORY.md index in sync.

6. Report which log file you wrote (full path) and which memory files you touched (call out the task-list update explicitly).

EOF

echo "Created $COMMANDS/end-of-day.md"

echo

echo "Done. Next steps:"

echo "  1. cd into a Claude Code session anywhere and run /good-morning as a smoke test."

echo "  2. It should read the empty task file + empty logs folder without errors and tell you the system is ready."
