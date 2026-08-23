# CLAUDE.md — Fixbyte Templates

This file defines how AI assistants should help with this repository.

## Project constraints

- Static-only site: plain HTML, CSS, and vanilla JS. No build step, no bundlers.
- Data-driven templates: content lives in `data/*.json` and is rendered by `js/cards.js`.
- Keep changes minimal and backwards-compatible unless explicitly asked to refactor.
- Do not add third-party scripts, CDNs, or analytics without explicit approval.

## Safe contribution rules

1. Always preserve the no-build, static architecture.
2. When editing templates:
   - Update content via `data/*.json` where possible.
   - Keep HTML semantic and accessible (proper headings, labels, alt text).
3. When editing `js/cards.js`:
   - Do not introduce `eval`, `innerHTML` from untrusted sources, or arbitrary remote fetches.
   - Any new data fetch must be from same-origin `/data/*.json` paths.
4. CSS changes:
   - Stay within `css/style.css`; avoid inline styles in HTML.
   - Maintain mobile-first, responsive behavior.

## AI-assisted workflow

- Before proposing changes, summarize:
  - What files will change
  - How the data flow (JSON → JS → DOM) is affected
  - Any impact on deployment or custom domain
- Prefer small, focused edits over large rewrites.
- For any structural change (new template, new data shape, new deployment target), propose a plan first and wait for confirmation.

## Quality expectations

- No broken links or missing assets.
- All three templates must remain usable on mobile and desktop.
- Keep file size and complexity low; avoid unnecessary dependencies.
