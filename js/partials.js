(function () {
  const SLOT = "<!-- partial:lang-switcher -->";

  const config = {
    activeNav: (document.body.getAttribute("data-active-nav") || "").trim(),
    headerSep: (document.body.getAttribute("data-header-sep") || "").trim(),
    copyright: (document.body.getAttribute("data-copyright") || "").trim(),
  };

  function parseRoot(html) {
    const doc = new DOMParser().parseFromString(html, "text/html");
    return doc.body.firstElementChild;
  }

  async function loadPartial(name) {
    const response = await fetch("partials/" + name + ".html");
    if (!response.ok) {
      throw new Error("partials/" + name + ".html (" + response.status + ")");
    }
    return response.text();
  }

  function applyHeader(header) {
    if (config.headerSep) {
      const sep = header.querySelector(".brand-wordmark__sep");
      if (sep) {
        sep.setAttribute("width", config.headerSep);
        sep.setAttribute("height", config.headerSep);
      }
    }

    if (!config.activeNav) return;
    const href = config.activeNav + ".html";
    const link = header.querySelector('.site-nav__link[href="' + href + '"]');
    if (!link) return;
    link.classList.add("is-active");
    link.setAttribute("aria-current", "page");
  }

  function applyFooter(footer) {
    const yearEl = footer.querySelector("#year");
    if (yearEl) yearEl.textContent = String(new Date().getFullYear());

    if (!config.copyright) return;
    const copyEl = footer.querySelector("[data-copyright]");
    if (copyEl) copyEl.textContent = config.copyright;
  }

  function mount(id, node) {
    const slot = document.getElementById(id);
    if (!slot || !node) return;
    slot.replaceWith(node);
  }

  // The switcher partial is shared by every page, so its links can only point
  // at each locale's home page. The <link rel="alternate" hreflang> cluster in
  // the head knows the equivalent URL for *this* page, so use it to upgrade
  // each option. Reading the targets from the same tags search engines use
  // keeps the switcher and the hreflang metadata from ever disagreeing.
  function applyLangSwitcher(root) {
    const alternates = {};
    document
      .querySelectorAll('link[rel="alternate"][hreflang]')
      .forEach((link) => {
        alternates[link.getAttribute("hreflang")] = link.getAttribute("href");
      });

    root.querySelectorAll("[data-lang][hreflang]").forEach((option) => {
      const href = alternates[option.getAttribute("hreflang")];
      if (href) option.setAttribute("href", href);
    });
  }

  function initLangSwitchers() {
    const switchers = Array.from(
      document.querySelectorAll("[data-lang-switcher]")
    );
    if (!switchers.length) return;

    function setOpen(root, open) {
      const btn = root.querySelector(".lang-switcher__btn");
      const menu = root.querySelector(".lang-switcher__menu");
      if (!btn || !menu) return;
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      menu.hidden = !open;
    }

    function closeAll() {
      switchers.forEach((root) => setOpen(root, false));
    }

    switchers.forEach((root) => {
      const btn = root.querySelector(".lang-switcher__btn");
      const menu = root.querySelector(".lang-switcher__menu");
      if (!btn || !menu) return;

      btn.addEventListener("click", (event) => {
        event.stopPropagation();
        const willOpen = btn.getAttribute("aria-expanded") !== "true";
        closeAll();
        setOpen(root, willOpen);
      });

      menu.addEventListener("click", (event) => {
        event.stopPropagation();
      });
    });

    document.addEventListener("click", closeAll);
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeAll();
    });
  }

  async function init() {
    try {
      const [langHtml, headerHtml, footerHtml] = await Promise.all([
        loadPartial("lang-switcher"),
        loadPartial("header"),
        loadPartial("footer"),
      ]);

      const header = parseRoot(headerHtml.replace(SLOT, langHtml));
      const footer = parseRoot(footerHtml.replace(SLOT, langHtml));

      applyHeader(header);
      applyFooter(footer);
      applyLangSwitcher(header);
      applyLangSwitcher(footer);
      mount("site-header", header);
      mount("site-footer", footer);

      initLangSwitchers();
      document.dispatchEvent(new CustomEvent("fixbyte:partials-ready"));
    } catch (error) {
      console.error("Failed to load shared chrome:", error);
    }
  }

  init();
})();
