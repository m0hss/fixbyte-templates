# AGENTS.md — Fixbyte Templates

Guidelines for any AI agent working on this repository.

## Architecture overview

- **Templates**: `index.html`, `barbiers.html`, `restaurant.html`, `agences.html`, `entreprises.html`, `cafes.html`, `ecommerce.html`, `mentions-legales.html`, `politique-confidentialite.html`
- **Styles**: `css/style.css`
- **Logic**: `js/cards.js` (loads JSON and renders cards/sections); `js/partials.js` (loads shared header/footer from `partials/`)
- **Chrome**: `partials/header.html`, `partials/footer.html`, `partials/lang-switcher.html`
- **Data**: `data/barbiers.json`, `data/restaurants.json`, `data/agences.json`, `data/entreprises.json`, `data/cafes.json`, `data/ecommerce.json`
- **Local server**: `serve.sh`
- **Deployment**: static host (e.g. GitHub Pages) with custom domain via `CNAME`

## Allowed operations

Agents may:

- Edit HTML, CSS, JS, and JSON files to:
  - Fix bugs
  - Improve accessibility, responsiveness, or performance
  - Add small features within the existing architecture
- Update documentation (`README.md`, `CLAUDE.md`, `AGENTS.md`, `DEPLOY.md`)
- Add new templates that follow the same patterns (static HTML + JSON data + cards.js usage)

## Prohibited operations (without explicit human approval)

- Introducing build tools, bundlers, or frameworks.
- Adding remote scripts, CDNs, analytics, or tracking.
- Changing the deployment model (e.g. moving to a server-side framework).
- Rewriting `cards.js` in a different language or paradigm.
- Removing or altering existing templates in a breaking way.

## Contribution checklist

Before committing, ensure:

1. All templates still load and render their JSON data correctly.
2. No console errors in modern browsers.
3. Mobile and desktop layouts remain usable.
4. No new external network calls except same-origin `/data/*.json` and `/partials/*.html`.
5. Commit messages are clear and specific.

## Deployment and rollback

- Default branch (`master`) should always be deployable.
- Use feature branches for experiments.
- If a change breaks the site:
  - Revert the offending commit(s) or reset the branch to the last good commit.
  - Re-deploy from the stable commit.
  - Verify all five templates locally and on the live domain.
