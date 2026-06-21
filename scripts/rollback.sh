#!/usr/bin/env bash
# taOS rollback -- restore the branch + commit the last update left, then
# restart. Pure git + service restart on purpose: it must work when an update
# has broken the Python app or the dashboard is unreachable.
#
#   bash scripts/rollback.sh            # undo the last update (branch + version)
#   bash scripts/rollback.sh <ref>      # roll back to a specific tag/branch/sha
#
# The updater records the pre-update state in <install>/.taos-rollback before it
# touches anything, so even a clean fast-forward has a restore point.
set -euo pipefail

# --- locate the install (this script lives in <install>/scripts) ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${TAOS_INSTALL_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
cd "$INSTALL_DIR"

if [[ ! -d .git ]]; then
  echo "taos rollback: $INSTALL_DIR is not a git checkout; cannot roll back" >&2
  exit 1
fi

log(){ echo "[rollback] $*"; }

target_ref="${1:-}"

if [[ -n "$target_ref" ]]; then
  # Explicit target: a tag, branch, or sha the user named.
  prev_branch=""
  prev_sha="$target_ref"
  log "explicit target: $target_ref"
elif [[ -f .taos-rollback ]]; then
  # shellcheck disable=SC1091
  source .taos-rollback
  prev_branch="${prev_branch:-}"
  prev_sha="${prev_sha:-}"
  log "recorded target: branch='${prev_branch}' commit='${prev_sha:0:12}'"
else
  # Fallback for installs predating the recorded file: newest recovery tag.
  prev_sha="$(git tag --list 'taos-pre-update-*' --sort=-creatordate | head -1)"
  prev_branch=""
  if [[ -z "$prev_sha" ]]; then
    echo "taos rollback: no recorded rollback target and no taos-pre-update-* tag found" >&2
    exit 1
  fi
  log "no record file; using newest recovery tag: $prev_sha"
fi

# Best-effort fetch so an explicit branch/tag that only exists on the remote
# can still be resolved; never fatal (offline recovery must still work).
git fetch origin --tags --quiet 2>/dev/null || log "fetch skipped (offline?)"

if ! git rev-parse --verify --quiet "${prev_sha}^{commit}" >/dev/null; then
  echo "taos rollback: cannot resolve '$prev_sha' to a commit" >&2
  exit 1
fi

# Restore BOTH branch and version: move/create the recorded branch onto the
# recorded commit and check it out. With no recorded branch (explicit ref or
# tag fallback) we land in detached HEAD at that commit, which is still a valid
# running state.
if [[ -n "$prev_branch" && "$prev_branch" != "HEAD" ]]; then
  log "restoring branch '$prev_branch' at ${prev_sha:0:12}"
  git checkout -B "$prev_branch" "$prev_sha"
else
  log "checking out $prev_sha (detached)"
  git checkout --quiet --detach "$prev_sha"
fi

# --- restart the service (first method that applies wins) ---
restarted=""
if command -v systemctl >/dev/null 2>&1; then
  if systemctl is-enabled tinyagentos >/dev/null 2>&1 || systemctl status tinyagentos >/dev/null 2>&1; then
    sudo systemctl restart tinyagentos 2>/dev/null && restarted="systemd" || true
  fi
  if [[ -z "$restarted" ]] && systemctl --user status tinyagentos >/dev/null 2>&1; then
    systemctl --user restart tinyagentos 2>/dev/null && restarted="systemd --user" || true
  fi
fi
if [[ -z "$restarted" ]] && command -v launchctl >/dev/null 2>&1; then
  plist="$HOME/Library/LaunchAgents/com.tinyagentos.controller.plist"
  if [[ -f "$plist" ]]; then
    launchctl unload "$plist" 2>/dev/null || true
    launchctl load "$plist" 2>/dev/null && restarted="launchd" || true
  fi
fi
if [[ -z "$restarted" && -x "$INSTALL_DIR/scripts/taos-run.sh" ]]; then
  pkill -f "tinyagentos" 2>/dev/null || true
  nohup "$INSTALL_DIR/scripts/taos-run.sh" >/dev/null 2>&1 &
  restarted="nohup"
fi

now_sha="$(git rev-parse --short HEAD)"
now_ref="$(git rev-parse --abbrev-ref HEAD)"
log "rolled back to ${now_ref} @ ${now_sha}"
if [[ -n "$restarted" ]]; then
  log "service restarted via ${restarted}. Give it a few seconds, then reload taOS."
else
  log "could not auto-restart the service; restart taOS manually to finish."
fi
log "note: if the web UI looks stale, the frontend bundle may need a rebuild (re-run the installer)."
