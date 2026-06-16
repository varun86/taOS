# Changelog

All notable changes to taOS are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow semver beta: `1.0.0-beta.N`, bumped on each dev->master promotion.

## [Unreleased]

## [1.0.0-beta.3] - 2026-06-16

### Added
- Mobile Store redesigned into an Apple App Store-style layout: bottom tab bar (Discover/Apps/Agents/Search/Updates), a featured hero, horizontal app carousels with Get pills and star counts, full-screen search, and a device filter.
- Real cover banners and icons across the Store: OpenClaw, Hermes, Ollama, ComfyUI, n8n, and the self-hosted apps, plus a shared Stable Diffusion banner (the AUTOMATIC1111 build shown in grayscale to distinguish it). A shared AppIcon component falls back to a branded monogram when no logo exists, so no tile renders blank.

### Fixed
- Installed apps in the mobile Store no longer show a non-interactive "Open" control; they show an honest installed status.
- Failed Store installs now surface a Retry action instead of failing silently.
- Store icons and cover images reset correctly when a reused tile switches to a different app.

## [1.0.0-beta.2] - 2026-06-16

### Added
- Mail app with IMAP/SMTP account setup, message list, read, and send.
- Reddit, YouTube, GitHub, and X apps available as optional Store installs.
- Agent-callable screenshot endpoint for desktop-control workflows.

### Changed
- Browser app redesigned with the Store/Images design bar and taos.my set as the default homepage, with automatic dark/light scheme applied to proxied sites.
- Projects app shell redesigned with a Workspace hero tab.
- Notification bell wired to the backend feed with actionable click routing to the originating app or agent.
- Updates panel now shows version numbers (e.g. 1.0.0-beta.2) as the primary display, with commit SHAs as a secondary detail.

### Fixed
- Controller restart time reduced from ~46 s to ~7 s by eliminating the graceful-stop hang.
- Projects canvas crash caused by malformed element payloads written by agents.
- Window move and resize jitter under rapid pointer events.

## [1.0.0-beta.1] - 2026-06-09

Initial source-available public beta release under the taOS Sustainable Use License v0.1.
