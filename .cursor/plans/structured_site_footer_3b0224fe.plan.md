---
name: Structured site footer
overview: "Replace the one-line footer on all 7 templates with a charcoal four-block layout: brand (logo-light + slogan), Contact, Pages, and Legal — styled in css/style.css, no new legal pages or social URLs yet."
todos:
  - id: css-footer
    content: "Rewrite .site-footer / .footer-inner styles: charcoal bg, 4-zone grid, brand + social + meta; decouple from header-inner"
    status: completed
  - id: html-footer
    content: Replace footer markup on all 7 HTML pages with brand (logo-light + slogan), Contact, Pages, Legal, meta year row
    status: completed
isProject: false
---

# Structured site footer

## Slogan (chosen)

**Recommended (will ship):** `Votre enseigne live en 72 h.`

Short enough under the logo, concrete, matches the Essai / 72 h promise already on the site.

Alternatives considered (not used):
- `Essai 0 € · live en 72 h.` — more promo, slightly noisier
- `Le site qui dit oui avant l’appel.` — brandier, less operational
- `Photo WhatsApp. Site à jour.` — tactical, weaker as a brand line
- `Designs pour métiers de proximité.` — category, not offer

## Defaults for unresolved links

- **WhatsApp:** reuse `https://wa.me/32493622901` + existing [`assets/whatsapp.svg`](assets/whatsapp.svg), label `WhatsApp`
- **Instagram / Facebook:** text + simple inline SVG icons, `href="#"` for now (no URLs in repo)
- **Legal:** labels only — `Mentions légales`, `Politique de confidentialité` → `href="#"` (no new pages)

## Layout (desktop → mobile)

Four zones inside `.wrap.footer-inner`:

1. **Brand** — [`assets/logo-light.svg`](assets/logo-light.svg) + slogan under it
2. **Contact** — WhatsApp, Instagram, Facebook (icon + text each)
3. **Pages** — Accueil + same category links as the header nav
4. **Legal** — Mentions légales, Politique de confidentialité

Bottom row keeps copyright / year (`#year` + existing `cards.js` logic) + `studio.fixbyte.be`.

```text
[ logo-light ]     Contact          Pages              Legal
  slogan           WA + text        Accueil            Mentions légales
                   IG + text        Restaurants…       Politique…
                   FB + text

  Fixbyte · 2026 · studio.fixbyte.be
```

Mobile: brand full width, then 3 link columns stacked or 2+1 wrap; keep readable tap targets.

## Files to change

| File | Change |
|------|--------|
| [`css/style.css`](css/style.css) | Charcoal footer (`background: var(--charcoal)`), light text/links, grid for brand + 3 columns, social row styles; stop sharing `.footer-inner` flex rules with the header |
| [`index.html`](index.html) + 6 category templates | Same footer markup (restaurant, barbiers, agences, entreprises, cafes, ecommerce) |

**Data flow:** no JSON / `cards.js` change except keep `#year` population.

**Deploy:** static-only; no CNAME / architecture impact. Broken `#` legal/social links are intentional placeholders until URLs/pages exist.

## HTML shape (shared across pages)

```html
<footer class="site-footer">
  <div class="wrap footer-inner">
    <div class="footer-brand">
      <a href="index.html" class="footer-logo">
        <img src="assets/logo-light.svg" alt="Fixbyte" width="150" height="70" />
      </a>
      <p class="footer-slogan">Votre enseigne live en 72&nbsp;h.</p>
    </div>
    <nav class="footer-col" aria-label="Contact">…</nav>
    <nav class="footer-col" aria-label="Pages">…</nav>
    <nav class="footer-col" aria-label="Informations légales">…</nav>
    <p class="footer-meta">… year …</p>
  </div>
</footer>
```

## CSS notes

- Background: `var(--charcoal)` (`#2c2a28` from [`css/style.css`](css/style.css) L20)
- Text/links: parchment / soft white; hover underline or teal accent (`--teal`)
- Decouple `.header-inner` from `.footer-inner` (today they share one flex rule)
- Logo height ~48–56px so it doesn’t dominate the footer
- Contact links as flex rows: icon 20–24px + label

## Out of scope

- Creating legal page content
- Real Instagram/Facebook URLs
- Changing header logo or float WhatsApp bubble
