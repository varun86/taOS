<!--
  SINGLE SOURCE OF TRUTH for cross-agent handoff. Committed so any agent on any
  platform sees it. Update on merge / task-start / rate-limit / handoff. The Pi
  :00/:30 cron also refreshes it. Keep it SHORT, link issues for detail.
  See docs/AGENT_HANDOFF.md (local-only) for the on-arrival checklist + rules.
-->

# taOS: Live Status

**Last updated:** 2026-06-10 ~19:30 BST, by @taOS (Mac session). SESSION ENDING, Jay restarting Claude in the correct folder.
**Repo:** github.com/jaylfc/taOS, branches `master` (stable) <- `dev` (integration).

## GOTCHA for the next agent
- **FOLDER:** all taOS work is `jaylfc/taOS` at `~/Development/tinyagentos`. The prior session was launched from `~/Development/taosmd` by mistake (Claude then labels the session taOSmd, cosmetic). RESTART Claude in `~/Development/tinyagentos`, then say "read docs/AGENT_HANDOFF.md".
- **#752 (safe cleanups) is OPEN, CI green-pending, NOT yet merged.** The auto-merge watcher died with the prior session. Merge it to dev when CI is green (approve-lock leak eviction + auth_requests indexes + shared httpx client #660; 45 tests passed on the Pi). Use the GitHub UI or a PAT.
- **Merges/protected writes 401 on the gh OAuth token** intermittently (read calls are fine). Use the **GitHub UI merge button**, or a `ghp_` PAT via `GH_TOKEN=<pat> gh pr merge ...`. This is a token limitation, not a CI failure.
- A background merge-watcher was auto-merging #746/#748/#749 via PAT, but **it dies when this session ends**, so finish them manually (below).
- Never `--delete-branch` on a dev->master PR (auto-closes PRs targeting dev).
- **Promote with `--merge`, NOT squash.** Repeated squash-promotions diverge dev/master and conflict on shared files (hit this on #750). Fixed by reconciling with `git merge -s ours origin/master` on dev then a real `--merge` promotion, so dev is an ancestor of master again.

## Immediate next actions
- M1 security CLEARED to master (93f395e2): SSRF #745, CSRF #746, CI-fix #748, docs #749 all merged + promoted.
- FIRST: merge #752 (safe cleanups) once CI green. Then NEXT BUILD: **#737** cluster-worker pairing-code auth (designed in the #737 comment, 4 phases, mechanical -> sonnet with a full spec). Then **#751** beads-inspired native task-graph (joint rec, awaiting Jay greenlight).

## In flight
- **M1 security (audit milestone 1):** SSRF #738 DONE (#745 merged). CSRF #648 -> #746 (Strict session cookie + token wiring + fixed a latent silent-403 lock bug; per-route rollout tracked in #747). Remaining M1: **#737 cluster-worker auth** = a device-pairing-code flow, fully designed in the #737 comment (worker prints a code, admin pairs in taOS, mints the signing_key; 4 build phases). Not started.
- **beads evaluation (handoff tooling):** design thread OPEN with @taOSmd on the A2A integration channel (msg #289). beads = github.com/gastownhall/beads, a Go CLI+MCP, Dolt-backed, AI-agent-native dependency-graph issue tracker (hash IDs for concurrent multi-agent writes, `bd ready` offline unblocked-work queue, `bd prime` session context). 4 open questions posed (boundary: taosmd component vs peer; overlap with our A2A+memory; SBC/Dolt weight; adopt-as-is vs concepts-only). CONVERGED with taOSmd: BUILD thin-native (Dolt too heavy for SBC; native task events feed the v2 memory engine, which beads cannot). Joint rec filed as **#751**, AWAITING Jay greenlight (buy vs build). taOSmd drafts the taosmd-side schema/endpoints; taOS wires the Tasks-app + handoff-bootstrap consumption side.
- **#744 external coding-agent onboarding:** spec committed (`docs/design/external-agent-onboarding.md`), token->project-memory contract v1 locked with taOSmd. 7 taOS build tasks queued behind M1.
- **Repo audit:** done, grade B-, report at `docs/audit/2026-06-10-repo-audit.md` (LOCAL-ONLY, gitignored, unpatched security detail). Findings tracked in issues #737-740 #743 + existing.

## Open issues filed this session
#735 feedback/bug tracker, #736 websites (taos.my + redirect), #737 cluster-worker pairing auth, #738 SSRF (fixed #745), #739 CI ruff+vitest+npm-audit, #740 Python lockfile, #741 resilience workflow, #742 memory-migrate cutover, #743 docs drift, #744 external-agent onboarding, #747 CSRF per-route rollout, #751 native task-graph (beads-inspired, joint rec).

## Cross-project (taosmd / A2A)
- #25 memory unification DONE both sides + live + verified. Trust enforcement live-but-dormant (needs TAOSMD_REGISTRY_URL).
- Progress channels live: `taos-progress` (mine), `taosmd-progress` (theirs); both feed project memory.
- Workflow rules adopted both sides; durable 30-min freshness crons (taOS :00/:30, taosmd :15/:45). Pi Claude session is CLOSED (Mac session is sole @taOS driver this stretch). taOSmd confirmed clean-handoff protocol LIVE + battle-tested (msg 294, recovered with zero lost work at 17:05).

## Blocked / waiting on human (Jay)
- `#15` exo fork deletion: needs `gh auth refresh -s delete_repo`.
- `TAOSMD_REGISTRY_URL` cutover: gated on the consent UI shipping (deliberate).
- Decide buy-vs-build on beads once taOSmd + I bring the joint rec.

## Where to look
1. GitHub issues = task list. 2. This file = snapshot. 3. docs/AGENT_HANDOFF.md (local) = rules + bootstrap. 4. A2A bus :7900 (taos-progress / general / integration). 5. @taOS Pi memory (Claude Code only).
