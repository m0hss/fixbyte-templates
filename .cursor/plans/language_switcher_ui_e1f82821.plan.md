---
name: Language switcher UI
overview: Add a styled flag + full-name language dropdown in the header and footer on all 7 pages. Français is the only active choice; English and Nederlands (Belgium flag) appear disabled for phase 2 wiring.
todos:
  - id: flag-assets
    content: Add fr.svg, gb.svg, be.svg under assets/flags/
    status: completed
  - id: css-lang-switcher
    content: Style .lang-switcher for header + footer-brand (under slogan)
    status: completed
  - id: js-toggle
    content: Minimal open/close/Escape/outside-click for [data-lang-switcher]
    status: completed
  - id: html-all-pages
    content: Header after nav; footer under .footer-slogan in .footer-brand on all 7 pages
    status: completed
isProject: false
---

# Language switcher (UI only)

## Scope

- **Pages:** all 7 templates ([`index.html`](index.html), [`restaurant.html`](restaurant.html), [`barbiers.html`](barbiers.html), [`agences.html`](agences.html), [`entreprises.html`](entreprises.html), [`cafes.html`](cafes.html), [`ecommerce.html`](ecommerce.html)) — same shared header/footer markup pattern as the recent footer work.
- **Phase 1:** visual + accessible dropdown only. No locale routing, no content translation, no `html lang` switching, no JSON/i18n.
- **Languages shown:**
  - **Français** — French flag — selected / only interactive choice
  - **English** — UK flag — visible, disabled (`aria-disabled`), no action
  - **Nederlands** — Belgium flag — visible, disabled, no action

## Placement

**Header** — inside `.header-inner`, after `.site-nav`:

```text
[ FixByte Studio ]     [ nav pills … ]     [ 🇫🇷 Français ▾ ]
```

**Footer** — inside `.footer-brand`, directly under `.footer-slogan` (same column as logo + slogan):

```text
[ logo ]
  slogan
  [ 🇫🇷 Français ▾ ]   ← under blockquote.footer-slogan
```

HTML order in `.footer-brand`: logo link → `blockquote.footer-slogan` → `.lang-switcher`. Leave `.footer-meta` unchanged (copyright only).

## Markup pattern (shared)

Use a compact custom dropdown (not `<select>`) so flag + full label style cleanly. Prefer a button + listbox pattern with a few lines of vanilla JS for open/close, Escape, and outside click.

```html
<div class="lang-switcher" data-lang-switcher>
  <button
    type="button"
    class="lang-switcher__btn"
    aria-expanded="false"
    aria-haspopup="listbox"
    aria-label="Choisir la langue"
  >
    <img class="lang-switcher__flag" src="assets/flags/fr.svg" alt="" width="20" height="14" />
    <span class="lang-switcher__label">Français</span>
    <span class="lang-switcher__chevron" aria-hidden="true"></span>
  </button>
  <ul class="lang-switcher__menu" role="listbox" hidden>
    <li role="option" aria-selected="true" data-lang="fr">…Français</li>
    <li role="option" aria-disabled="true" data-lang="en">…English</li>
    <li role="option" aria-disabled="true" data-lang="nl">…Nederlands</li>
  </ul>
</div>
```

- Selecting Français when already selected just closes the menu.
- EN/NL: not focusable as actions (or focusable but inert); `tabindex="-1"` on disabled options; no `href` navigation.
- Optional subtle hint on disabled rows: `Bientôt` (small muted text) so phase 2 is clear without clutter.

Duplicate the same block in header and footer (two instances per page). Both stay on Français until phase 2.

## Assets

Add three small local SVGs (no CDN, no emoji):

- [`assets/flags/fr.svg`](assets/flags/fr.svg) — France
- [`assets/flags/gb.svg`](assets/flags/gb.svg) — English
- [`assets/flags/be.svg`](assets/flags/be.svg) — Nederlands (Belgium)

Keep them tiny (~20×14 viewBox), decorative (`alt=""`); language name is the accessible text.

## CSS ([`css/style.css`](css/style.css))

New block `.lang-switcher` (+ modifiers if needed):

- **Header variant** (default): pill trigger aligned with `.site-nav__link` (white bg, charcoal border, Figtree) so it feels part of the chrome, not a second nav system.
- **Footer variant** (`.footer-brand .lang-switcher` or `.lang-switcher--footer`): light text / translucent border on charcoal; sits in the brand column stack under the slogan (existing `.footer-brand` flex column + gap already spaces it).
- Flag + label + chevron in a row; menu as absolute dropdown with shadow/border matching existing cards (no purple glow / overbuilt pills). Open upward or downward as needed so it isn’t clipped by footer edges (`overflow` check on `.site-footer` / `.footer-inner`).
- Disabled options: reduced opacity, `cursor: not-allowed`, no hover accent.
- Mobile: header keeps switcher on the right of the brand row or under nav with wrap; footer switcher stays in the brand column under the slogan (no meta-row change).

## JS ([`js/cards.js`](js/cards.js) or tiny shared snippet)

Minimal behavior only (no locale logic):

- Toggle `aria-expanded` + menu `hidden`
- Close on outside click / Escape
- Ignore clicks on `aria-disabled` options
- Init all `[data-lang-switcher]` on the page (header + footer)

No fetch, no `eval`, no remote assets. Keep under ~40–60 lines.

## Data / deploy impact

- **Data flow:** none — static HTML + CSS + tiny JS; JSON / card rendering unchanged.
- **Deploy:** static-only; no CNAME or workflow changes.

## Out of scope (phase 2)

- Wiring EN/NL to real locales / alternate pages
- Syncing selection across header/footer beyond static Français
- Translating copy or `html lang` / `og:locale`
- Persisting choice in `localStorage`

## Implementation order

1. Add flag SVGs under `assets/flags/`
2. Add `.lang-switcher` styles (header + under-slogan in `.footer-brand`) in [`css/style.css`](css/style.css)
3. Add toggle script (extend [`js/cards.js`](js/cards.js) or a small `js/lang-switcher.js` linked from all pages)
4. Paste identical header + footer markup into all 7 HTML files
5. Spot-check desktop/mobile: open/close, disabled EN/NL, sticky header z-index over content
