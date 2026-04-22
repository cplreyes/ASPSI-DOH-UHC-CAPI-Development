# Changelog

All notable changes to the F2 Healthcare Worker Survey PWA are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.0.0] — 2026-04-23

### Added
- **Section tree sidebar** — sticky desktop sidebar + responsive burger-menu drawer listing all 10 sections; badges show current (teal), completed (green checkmark), and upcoming (muted) states
- **Side arrow navigation** — fixed prev/next chevron buttons at vertical center of screen; on desktop the left arrow clears the sidebar; right arrow turns primary color on the last section to signal finish
- **Swipe gesture** — horizontal swipe >50 px (dominant axis) navigates between sections on mobile and tablet
- **Slide animation** — sections animate in from left or right depending on direction of navigation
- **Save Draft** — replaces the old bottom nav bar; a "Draft saved" confirmation appears for 2 seconds after saving
- **Question numbering** — question IDs (Q1, Q2, …) displayed as muted number prefixes so enumerators can reference items by number
- **Sticky section header** — section title and progress bar stay visible while scrolling through long sections
- **Version display** — `v1.0.0` shown as a subtle badge under the app title in the header; version is baked in at build time from `package.json`

### Fixed
- **Backend build** — `stripCjsExport` regex now correctly removes the entire `if (typeof module !== 'undefined')` block; a `m`-flag + non-greedy match bug was leaving the outer closing `}` behind, causing a syntax error in the generated `Code.gs`
- **Sync CORS** — POST requests now use `Content-Type: text/plain` to avoid the OPTIONS preflight that Apps Script cannot handle; the body is still readable via `e.postData.contents`
