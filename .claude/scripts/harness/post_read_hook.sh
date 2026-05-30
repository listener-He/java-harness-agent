#!/usr/bin/env bash
# PostToolUse hook for Read — bash early-filter wrapper (T4.1 + G1 optimization).
#
# Reads fire MANY times per turn (file reads, exploration). Previous pure-Python
# hook paid ~98ms per invocation (Python startup) regardless of whether the file
# was a wiki/skill path. This wrapper does the path filter in bash (~10ms) and
# only forks python3 when the path actually qualifies for tracking.
#
# Hook contract: JSON payload on stdin with tool_input.file_path. Failure is
# silent — never abort tool execution.

set -u

# Buffer stdin (cat is faster than the python equivalent for short payloads).
payload=$(cat)

# Extract file_path with sed. Permissive regex: allows any whitespace around
# the colon and tolerates the field appearing anywhere in the JSON. We only
# need the FIRST hit; head -1 caps that.
fp=$(printf '%s' "$payload" | sed -nE 's/.*"file_path"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/p' | head -1)

# Bail fast on non-tracking paths (~99% of Reads). Match both absolute and
# repo-relative forms.
case "$fp" in
    */.claude/wiki/*|.claude/wiki/*|*/.claude/skills/*|.claude/skills/*)
        # Match — invoke tracker. exec replaces shell so we don't pay an extra
        # process for the bash exit.
        exec python3 .claude/scripts/local_intel/usage_tracker.py track "$fp"
        ;;
esac

exit 0
