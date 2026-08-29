# CLAUDE.md — Fixbyte Templates

This file defines how AI assistants should help with this repository.

## Project constraints

- Static-output site: the deployed site is plain HTML, CSS, and vanilla JS. Build steps
  are allowed, but only as dependency-free Python scripts in `scripts/`. No bundlers, no
  package managers, no framework runtimes.
- Data-driven templates: content lives in `data/*.json` and is rendered by `js/cards.js`. Shared header/footer live in `partials/` and are loaded by `js/partials.js`.
- Keep changes minimal and backwards-compatible unless explicitly asked to refactor.
- Do not add third-party scripts, CDNs, or analytics without explicit approval.

## Safe contribution rules

1. Always preserve the static-output architecture: whatever the build does, what ships
   must be plain HTML, CSS, and vanilla JS with no runtime dependencies.
2. When editing templates:
   - Update content via `data/*.json` where possible.
   - Keep HTML semantic and accessible (proper headings, labels, alt text).
3. When editing `js/cards.js`:
   - Do not introduce `eval`, `innerHTML` from untrusted sources, or arbitrary remote fetches.
   - Any new data fetch must be from same-origin `/data/*.json` or `/partials/*.html` paths.
4. CSS changes:
   - Stay within `css/style.css`; avoid inline styles in HTML.
   - Maintain mobile-first, responsive behavior.

## Vocabulary

- `docs/references/dictionary/` is the authoritative vocabulary for this repo — one
  term per file (`Hallucination.md`, `Sycophancy.md`, `Subagent.md`, …).
- When a term it defines is relevant, read that entry before using the term, and use
  it with the precision the entry demands. Do not substitute an external URL or
  recall from memory.
- Each entry has an "Avoid" note saying what the term excludes; respect it rather
  than using these words as loose synonyms.

## AI-assisted workflow

- Before proposing changes, summarize:
  - What files will change
  - How the data flow (JSON → JS → DOM) is affected
  - Any impact on deployment or custom domain
- Prefer small, focused edits over large rewrites.
- For any structural change (new template, new data shape, new deployment target), propose a plan first and wait for confirmation.

## Quality expectations

- No broken links or missing assets.
- All category templates must remain usable on mobile and desktop.
- Keep file size and complexity low; avoid unnecessary dependencies.
