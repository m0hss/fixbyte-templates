# Fixbyte Templates

A minimal, static HTML/CSS/JS template set for small-business landing pages, powered by local JSON data and a simple card-based layout.

## Templates

- **Home** — `/index.html`  
  Main landing with template cards and overview sections.
- **Barbiers** — `/barbiers.html`  
  Barber-shop style template with services, pricing, and contact.
- **Restaurant** — `/restaurant.html`  
  Restaurant/café template with menu highlights, gallery, and reservation CTA.
- **Agences** — `/agences.html`  
  Agency / institution template with offer, proofs, and contact.
- **Entreprises** — `/entreprises.html`  
  Construction / renovation business template with savoir-faire, works, and quote CTA.
- **Cafés & boulangeries** — `/cafes.html`  
  Café/bakery template with daily menu, hours, address, and click & collect.
- **E-commerce** — `/ecommerce.html`  
  Online shop / product-launch template with catalog, pricing, and purchase CTA.

Preview locally using `./serve.sh` (see below) and open:

- http://localhost:8080/
- http://localhost:8080/barbiers.html
- http://localhost:8080/restaurant.html
- http://localhost:8080/agences.html
- http://localhost:8080/entreprises.html
- http://localhost:8080/cafes.html
- http://localhost:8080/ecommerce.html

## Local development with `serve.sh`

`serve.sh` is a tiny shell script that starts a local HTTP server in the project root.

```bash
# From the repository root
chmod +x serve.sh        # only once, if needed
./serve.sh
```

Then open your browser at `http://localhost:8080` (or the URL printed by the script).  
Edit HTML, CSS, JS, or JSON files and refresh the browser to see changes.

## How JSON data feeds the pages

Template data lives in `/data`:

- `data/barbiers.json` — data for the barber template
- `data/restaurants.json` — data for the restaurant template
- `data/agences.json` — data for the agencies template
- `data/entreprises.json` — data for the entreprises (travaux / rénovation) template
- `data/cafes.json` — data for the café & bakery template
- `data/ecommerce.json` — data for the e-commerce template

`js/cards.js` loads these JSON files in the browser and renders cards/sections on each page. The general pattern:

1. HTML includes `<script src="js/partials.js"></script>` then `<script src="js/cards.js"></script>`.
2. `partials.js` fetches `partials/header.html` and `partials/footer.html` (shared chrome) and mounts them.
3. `cards.js` fetches the relevant JSON (e.g. `data/barbiers.json`).
4. It builds DOM elements (cards, sections, lists) from the JSON and injects them into the page.

Shared header/footer live in `partials/`. Edit those files to change chrome on every page.

To customize a template:

1. Edit the corresponding JSON file under `data/`.
2. Adjust fields in `cards.js` if you change the data shape.
3. Refresh the page to verify the updated content.

## Deployment target

This repository is intended to be deployed as a **static site**:

- All pages are plain HTML/CSS/JS with no build step.
- The site can be hosted on any static host (GitHub Pages, Netlify, Vercel, Cloudflare Pages, or a simple nginx/Apache server).

The presence of a `CNAME` file indicates the project is configured for a **custom domain** on a platform that supports it (e.g. GitHub Pages).

## Custom-domain procedure (GitHub Pages example)

1. Enable GitHub Pages for the repository (Settings → Pages):
   - Source: `Deploy from a branch`
   - Branch: `master` (or `main`), folder: `/ (root)`
2. In the same Pages settings, set your custom domain (e.g. `templates.fixbyte.io`).
3. Ensure `CNAME` contains exactly that domain (no `https://`, no trailing slash).
4. Configure DNS at your registrar:
   - For a root domain: `A` records to GitHub Pages IPs.
   - For a subdomain: `CNAME` to `<username>.github.io`.
5. Wait for DNS propagation and GitHub's HTTPS certificate issuance.

## Rollback steps

If a deployment breaks or introduces bad changes:

1. Identify the last good commit:
   - Use `git log` or GitHub's commit history.
2. Revert or reset:
   - For a single bad commit: `git revert <bad-commit-sha>` and push.
   - For multiple recent commits on a feature branch: reset that branch to the good commit and force-push the branch.
3. If using GitHub Pages or another host with deploy previews:
   - Re-deploy from the known-good commit/branch.
4. Verify:
   - Open all five templates locally and on the live domain.
   - Check that JSON-driven sections render correctly.

Keep the default branch stable and use feature branches for experiments so you always have a safe commit to roll back to.
