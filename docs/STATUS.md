<!--
  SINGLE SOURCE OF TRUTH for cross-agent handoff. Committed to the repo so it is
  visible to ANY agent on ANY platform (Claude Code, Cursor, Codex, web, etc.) —
  not just sessions that share the Pi memory store.

  CONTRACT: update this file whenever you (a) merge work, (b) start a sizeable task,
  (c) get rate-limited mid-task, or (d) hand off. The hourly freshness cron also
  refreshes the "Branch state" + "Recently merged" blocks. Keep it SHORT — link to
  GitHub issues for detail; this is the dashboard, not the archive.

  See docs/AGENT_HANDOFF.md for the on-arrival checklist and the hop protocol.
-->

# taOS — Live Status

**Last updated:** 2026-06-10 ~14:30 BST · by @taOS (Mac session, claude-fable-5)
**Repo:** github.com/jaylfc/taOS · **Branches:** `master` (stable, installs track) ← `dev` (integration)

## Branch state
- `master` tip: `a13692de` — promotion #727 (install fixes + registry governance PR2)
- `dev` tip: `dfee2b0f` — consent scope validation (#733), ahead of master by 7 commits
- **Open PR `#734`** (dev→master promotion): CI GREEN + mergeable. The CLI admin-merge over API persistently 401s against the protected `master` branch (a token/branch-protection limitation, not a CI failure). **ACTION (Jay): click "Merge" on PR #734 in the GitHub UI** — one click, the browser session bypasses the CLI-token limitation. Squash. Do NOT `--delete-branch` (deleting `dev` auto-closes every PR that targets it — burned once on 2026-06-10).

## In flight
- **Repo audit** (principal-level, 4-phase): Phases 1–2 done (8 dimensions; testing got lighter review after a rate limit). NEW findings folded into issues #737 #738 #739 #740 #743; many findings corroborate existing issues (#672 #648 #646 #653 #642 #639 #660 #657 #655). Synthesized report doc → `docs/audit/2026-06-10-repo-audit.md` still **pending** (exec summary + themes + milestone plan).
- **Multi-agent resilience workflow** — DONE (this file + `AGENT_HANDOFF.md`, commit 29172153) + tracked in #741.
- **Bug/feedback tracker feature** — filed as #735 (+ websites #736).

## Open feature / improvement issues (filed 2026-06-10)
- `#735` feedback & bug tracker (in-taOS form → curated DB → issue triage)
- `#736` websites: taos.my + tinyagentos.com redirect
- `#741` cross-agent resilience workflow (STATUS/HANDOFF/cron)
- `#742` memory-unification migrate cutover (deferred until real data)
- `#737` security: unauthenticated cluster worker register/heartbeat (High)
- `#738` security: SSRF in knowledge ingest (Medium-High)
- `#739` CI: enforce ruff + run vitest + npm audit (quick win)
- `#740` deps: no Python lockfile / non-reproducible installs
- `#743` docs drift (getting-started /opt path = High, design docs, CONTRIBUTING htmx)

## Recently merged (dev, last batch)
`#733` consent scope allowlist + granted⊆requested · `c1fb3f98` live taosmd hit-shape fix · `#732` taosmd→PyPI pin · `#731` consent notification UI · `#730` governance audit panel · `#728` user-memory proxy hardening · `#729` registry approval UI.

## Cross-project (taosmd / A2A)
- **#25 memory unification: DONE both sides.** taosmd `feat/user-memory-unification` merged to taosmd master (PR #149, `71e913a`); `/ingest/batch` + `?mode=bm25` live on the Pi serve (:7900), verified end-to-end. taOS proxy (`routes/user_memory.py`) points at it. **Next:** run `POST /api/user-memory/migrate` cutover when there's real user data (none yet).
- **Trust & Comms enforcement: live** on taosmd (GrantsVerifier), dormant until `TAOSMD_REGISTRY_URL` is configured — held behind the consent flow by design.
- A2A bus: `http://<pi>:7900`, channels general/observability/integration. @taOSmd (memory/bench), @hermes (framework agent), @taOS (this/controller).

## Blocked / waiting on human (Jay)
- `#734` manual merge (token write-endpoint hiccup — see Branch state).
- `#15` exo fork deletion — needs `gh auth refresh -s delete_repo` run by Jay.
- `TAOSMD_REGISTRY_URL` cutover — deliberate, gated on consent UI shipping.

## Where to look (durable stores, in priority order)
1. **GitHub issues** = the task list. `gh issue list --state open`. Cross-platform, the canonical backlog.
2. **This file** = current snapshot.
3. **`docs/AGENT_HANDOFF.md`** = how to get oriented + the rules + the hop protocol.
4. **A2A bus** (`:7900`) = live inter-agent coordination (transient).
5. **@taOS memory** on the Pi (`~/.claude/projects/-home-jay-Development-tinyagentos/memory/`) = durable context for Claude Code sessions (NOT visible to other platforms — that's why this file exists).
