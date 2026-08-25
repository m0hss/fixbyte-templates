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
      mount("site-header", header);
      mount("site-footer", footer);

      document.dispatchEvent(new CustomEvent("fixbyte:partials-ready"));
    } catch (error) {
      console.error("Failed to load shared chrome:", error);
    }
  }

  init();
})();
