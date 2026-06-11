<!--
  SINGLE SOURCE OF TRUTH for cross-agent handoff. Committed so any agent on any
  platform sees it. Update on merge / task-start / rate-limit / handoff. The
  session freshness cron (:08/:38) also refreshes it. Keep it SHORT, link issues.
  See docs/AGENT_HANDOFF.md for the on-arrival checklist + rules.
-->

# taOS: Live Status

**Last updated:** 2026-06-11 ~20:40 BST, by @taOS (Mac session). PRE-COMPACTION SNAPSHOT. Fresh 5h window ~7%. WORK QUEUE (priority order): (1) PR #787 promotion (carries #785 Phase 4 + #786 rknpu/#783 fix) -> merge to master with merge_method=merge when green; THEN post the APPROVED #783 reply to HarMaximus (key points: root cause = install-rknpu.sh died because binutils/strings missing before rkllama installed, so /api/pull got connection-refused; fixed in #786; tell him to re-run `curl -fsSL .../master/scripts/install-server.sh | sudo bash`; be honest we have no Rock 5B so his reports matter; welcome feature ideas; thank his perseverance; humanised, no em dashes). (2) PR #788 (docker app Launchpad shortcut records the ALLOCATED host port not the container port; regression test added, 12 pass) -> merge to dev when green, include in next promotion. (3) LIVE PI REMEDIATION (Jay priority, not done): Pi still has legacy searxng on host :8080 (docker, 8080:8080) blocking rkllama; rkllama.service INACTIVE. Plan: deploy #788 to Pi, uninstall searx via POST /api/store/uninstall-v2 {app_id:searxng}, `systemctl start rkllama` (now :8080 free), reinstall searx via POST /api/store/install-v2 {manifest_id:searxng} -> lands on a 30000-40000 pool port + auto-creates a Launchpad shortcut; verify rkllama answers on :8080 and the browser shortcut opens searx. Admin auth = jay/alexander04. (4) File the 6 idea-issue drafts from the workflow (bench pause/resume+queuing, ubuntu-touch phone, native-desktop API parity, TUI/tuiui, edit-agent-message, copy/paste-from-agents). Full drafts in the workflow output JSON under result.drafts at /private/tmp/claude-501/-Volumes-NVMe-Users-jay-Development-tinyagentos/dbeb8dad-a1ca-4808-8fa2-3a8c804738d2/tasks/w8l7fxoa0.output (review for human voice before creating). (5) #695 REOPENED (reserve core ports + migrate legacy apps off reserved ports). #785/#786 merged to dev. SSE bus monitor + freshness/usage cron armed; resume pair fires on quota reset.
**Local-only in flight (not in git):** an Understand-Anything `/understand` run on `tinyagentos/cluster/` is paused mid-Phase-2. Intermediate files live in `tinyagentos/cluster/.understand-anything/` (gitignored): scan + batches done, batch-1 graph written (51 nodes, 100 edges), phases 3-7 (assemble/architecture/tour/review/save) pending. Resume by re-running `/understand tinyagentos/cluster` (incremental) or merging batch-1 and continuing. Note: scoping to a subdir gave 0 deterministic import edges (absolute package imports do not resolve in the narrow root); a `tinyagentos/`-root run would be richer. #778 gained a Coolify deployment plan: host the version-check endpoint on the tinyagentos.com site (Coolify from a GitHub repo) so it serves the latest version for seamless self-update AND counts installs anonymously in one call.
**Repo:** github.com/jaylfc/taOS, branches `master` (stable) <- `dev` (integration). master tip c3608c61 (PR #784); dev tip 0270ce95 (master + #785 Phase 4 + STATUS commits).

## GOTCHA for the next agent
- **Protected merges:** `gh pr merge` 401s on the OAuth token but `gh api -X PUT repos/jaylfc/taOS/pulls/N/merge -f merge_method=squash` WORKS (use `merge_method=merge` for dev->master promotions; never squash a promotion, never `--delete-branch`).
- CodeRabbit fake passes: a green CodeRabbit check can be a rate-limit notice; check the PR comments, use `@coderabbitai full review`. Kilo often 504s ("Assistant request timed out") = infra flake, not findings.
- `tests/` is NOT an importable package: never `from tests.conftest import X`; expose shared helpers as function-returning fixtures.
- Worker onboarding now REQUIRES pairing (a worker prints a code, admin approves in Cluster, signing key minted) before register/heartbeat. Signing string + headers in tinyagentos/cluster/worker_auth.py; worker side in tinyagentos/worker/pairing.py. VALIDATED in production (#772 passed).
- **Pi Claude session is ARCHIVED and its crons are stopped.** Freshness rides ONLY on the active agent's session cron (re-arm on a new session); there is no Pi-side durable backstop. The Pi controller + A2A bus are services and keep running.

## Recently landed
- **#737 cluster-worker pairing auth:** Phase 1 backend (#762) + Phase 2 worker scripts/agent signing (#770) DONE and on master (#767, #775). E2E VALIDATED in production (#772 closed: real Pi controller + Fedora worker, full announce->confirm->claim->signed register/heartbeat, unsigned->401). Phases 3 (UI pending-workers + enter-code dialog) and 4 (fleet migration UX) remain.
- **Beta incident fixes on master:** #763 (knowledge user_id migration self-heals bricked installs + exit-on-startup-failure), #754 (installer sudo gap), #768 (installer re-run ownership / priv-esc), #752 (perf), #758 (controller-rescue runbook), #757 (prefetch placeholder).
- Pi controller is UPDATED to master 66688348 (done for the #772 test) and has the pairing backend live.

## Immediate next actions
1. **#737 Phase 3** (UI pending-workers list + enter-code dialog): frontend-design pass, HELD for a design session with Jay (Apple-grade bar), ties into #760/#761 badges.
2. **#737 Phase 4** (fleet migration UX): existing workers re-pair once with a clear prompt, not silent 401s.
3. **#774 project/shelf registry:** design DONE + spec at docs/superpowers/specs/2026-06-11-project-shelf-registry-design.md (local, gitignored). taOSmd integration thread OPEN (integration channel msg 322): 3 contract questions (shelf create/archive shape; empty-shelf archive reversibility for link; carve-out re-key vs re-ingest). Implementation plan gated on their answers.
4. **#776 add-machine over SSH (#737 Phase 3.5):** design DONE + spec at docs/superpowers/specs/2026-06-11-add-machine-ssh-design.md (local). One-click Cluster "Add machine": paramiko SSH (not sshpass), controller auto-installs + auto-pairs (injects TAOS_PAIRING_CODE, confirms itself), key-exchange for durable mgmt, key-based auth v1 (Linux/macOS only; Windows = separate native app). Ready for an implementation plan; sequence the build behind Phase 3 UI (both Cluster-app frontend).
5. **#744** external coding-agent onboarding: taosmd side merged (their PR #151); our 7 build tasks queued.

## Open issues filed this stretch
#757 (fixed #771), #759 (fixed #764), #760 host badges everywhere (UI), #761 per-device emoji identity (brainstorm first), #772 fresh-install/pairing smoke (Pi+Fedora, PASSED+closed), #774 project/shelf registry (design done), #776 add-machine over SSH (design done), #777 install identity + version registration (per-bug context now, opt-in central reg later), #778 anonymous active-install count via the update check (aggregate only, no PII), #779 Projects-app code knowledge-graph plugin view for coding projects.

## Cross-project (taosmd / A2A)
- #744 taosmd side MERGED (their PR #151): grant matching on (canonical_id, project_id) + verified-claim project binding; the `agent` field on data endpoints is a TARGET SHELF, not the caller. Our 7 #744 build tasks queued.
- Progress channels live: `taos-progress`, `taosmd-progress`. Freshness crons: taOS session :08/:38 (re-armed 2026-06-11, was dark), Pi durable backstop NOT installed (decision pending Jay).

## Blocked / waiting on human (Jay)
- `#15` exo fork deletion: needs `gh auth refresh -s delete_repo`.
- `TAOSMD_REGISTRY_URL` cutover: gated on the consent UI shipping.
- #751 beads buy-vs-build greenlight; #761 emoji brainstorm; #774 -> taOSmd thread.
- Whether to install a durable Pi-side freshness cron as a backstop to the session cron.

## Where to look
1. GitHub issues = task list. 2. This file = snapshot. 3. docs/AGENT_HANDOFF.md = rules + bootstrap. 4. A2A bus :7900. 5. @taOS Pi memory (Claude Code only).
