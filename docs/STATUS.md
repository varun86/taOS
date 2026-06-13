SINGLE SOURCE OF TRUTH for cross-agent handoff.
Last updated: 2026-06-13 ~22:22 BST, @taOS (active, 5h usage 48%).

▶ WAKE QUEUE (Jay's active queue):
1. THEME #865 MERGED to dev: #867 (Safari backdrop-filter repaint) + #868 (macOS graphite #1d1d1f/#171717 + LIVE adaptive neural wallpaper, generic slogan overlay, any aspect incl 3840x1200 ultrawide). Verified in a local vite build+preview (graphite + neural canvas render, Agents cols aligned). JAY TESTING ON PI (pull dev). Animation + Safari dark<->light need a live look.
2. PROMO HERO PROGRAM (active, see memory [[promo-hero-initiative]]): build the REAL app seeded w/ mock data for a multi-window hero screenshot (chat + project canvas + store). Mocks approved. Public features to MERGE: App Store FULL redesign (popularity backend = real GitHub stars + Community section), project canvas/mind-map view (net-new), agent desktop window-mgmt API (#18). Mock DATA stays PRIVATE on the local `marketing` branch (never push/merge; MARKETING.md). STANDING: every promo render needs a 5:2 X-article cut. Tasks #13-18.
3. BRAINSTORM live-wallpaper PACKAGE format + agent authoring guidelines + store sharing (see [[live-wallpapers]]).
3. MOBILE AUDIT: check the Agents app + chat/Messages + composer look right on mobile (Jay flagged); verify the new neural wallpaper + graphite chrome on mobile too.
4. WALLPAPER picker Phase 1 (#864): reorg into Theme-default / Built-in / Your-wallpapers(+upload) sections + a Settings entry point; Phase 2 = Wallhaven KEYLESS browse + optional API-key entry. Mock approved. NOTE: #868 already added a wallpaper "kind" + wordmark toggle to the picker; build on that.
5. DYNAMIC ISLAND v2 (#854): design+mocks approved (island holds agent+search, agent chat bubble replaces side panel + poppable window, search bubble, Mac animations). Build plan then build.
6. GITHUB (#858): Phase 1 connect flow MERGED (#862). Next: Phase 2 time-scoped sharing + consent picker; Phase 3 agent access-request + runtime token injection; Phase 4 fork->PR ops. OAuth app registered (Client ID Ov23licVGSIqagQLXAqb public/in-source; secret stays host-side, NOT in repo; device flow needs no secret).

Branch tips: master=6394a3ed. dev=865f278d (#867 + #868 merged). Local-only `marketing` branch (private, no upstream; promo mock data; NEVER push/merge).

Session state: ACTIVE (5h 48%). #867+#868 merged to dev for Jay's Pi test. taos-website stats secured + merged to main (#5; set STATS_USER/STATS_PASS in Coolify). Next: build the promo/store program (tasks #13-18).

WEBSITE: taos.my live. All 4 taos-website PRs merged (stats/changelog/nav/accessibility).

CI: test suite parallelized via #839 (xdist -n auto). CodeRabbit may be out of credits -- do not merge on a fake rate-limit pass. Use @coderabbitai full review to retrigger; manual review OK for tiny already-reviewed PRs.

OPEN PRs:
- #846 dependabot esbuild bump -- SUPERSEDED by #849 (already on dev); close it
- #476 DRAFT feat(userspace): App Runtime v1 -- stays DRAFT, not ready to merge
(merged to dev since last update: #867 Safari repaint, #868 macOS-dark + neural wallpaper. taos-website #5 stats-auth merged to main.)

Notable open issues (bugs first):
- #844 rkllama store-UI install chain broken (wrong script + non-interactive false-success) -- unresolved
- #841 update check shows no updates when local branch diverged from origin -- unresolved
- #825 taOS agent model swap breaks routing (stale per-agent key preferred over master key)
- #840 chat: per-agent framework slash commands (Telegram-style) in DMs and via @agent /
- #836 deep-navigation API for taOS agent to drive desktop (hook shipped; agent tool side pending)

Done (since last STATUS.md update):
- ALL 26 agent jobs COMPLETE and on master (via #845 batch).
- Messages-polish (#838), agent manual templates (#842), CI parallelization (#839) all merged to dev then master.
- Light theme (#848), esbuild RCE patch (#849), brand rename (#847), chat composer unified (#850), Agents redesign (#851), update flow fix (#852), Chat Slack-polish (#853), agent kill switch (#857) all on dev.
- This sweep: docs/STATUS.md (dev tip + #860), docs/agent-qmd-serve-setup.md + docs/mirror-policy.md (brand rename TinyAgentOS->taOS).

Next queue:
1. Land #859 and #860 after CI + review.
2. Close #846 (superseded by #849).
3. Fix #844 and #841 (bugs, high user impact).
4. #825 key-scope fix.
5. Desktop overhaul (#824) and widget epic: needs Jay design session first.

Decisions (carried from prior sessions):
- PR for all code changes (no direct-to-dev commits for features).
- Never --delete-branch on a dev->master PR (deletes dev, closes all dev-targeting PRs).
- Jay updates Pi manually -- do not SSH-deploy after merges.
- gh pr merge 401s -- use GitHub UI or gh api PUT for merges.

Security queue: #747 #737 #672 #658 #655 #654 #653 #651 #650 #647

GOTCHA: docs/AGENT_HANDOFF.md is intentionally untracked (exposed Pi LAN IP in a prior commit; restored from memory but kept out of git). The RESTART CHECK at its top is stale (referenced #752, long-closed); ignore it.
