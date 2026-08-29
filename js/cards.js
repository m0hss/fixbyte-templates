(function () {
  // Asset paths are resolved against this script's own URL, so they stay
  // correct from /nl/ and friends without assuming the site sits at a domain
  // root.
  const scriptSrc = document.currentScript.src;
  const asset = (name) => new URL("../assets/" + name, scriptSrc).pathname;
  const PLACEHOLDER = asset("placeholder.svg");

  // Strings the builder translates via <body data-i18n-*> attributes. The
  // French text stays inline as the fallback, so behaviour is unchanged if an
  // attribute is missing.
  const t = (key, fallback) =>
    document.body.getAttribute("data-i18n-" + key) || fallback;

  const ctaBtn = document.querySelector(".cta-block__btn");
  if (ctaBtn && !document.querySelector(".whatsapp-float")) {
    const bubble = document.createElement("a");
    bubble.className = "whatsapp-float";
    bubble.href = ctaBtn.href;
    bubble.target = "_blank";
    bubble.rel = "noopener noreferrer";
    bubble.setAttribute("aria-label", t("wa-label", "Écrire sur WhatsApp"));

    const disc = document.createElement("span");
    disc.className = "whatsapp-float__disc";
    disc.setAttribute("aria-hidden", "true");
    const icon = document.createElement("img");
    icon.src = asset("whatsapp.svg");
    icon.alt = "";
    icon.width = 28;
    icon.height = 28;
    icon.decoding = "async";
    disc.appendChild(icon);

    const tip = document.createElement("span");
    tip.className = "whatsapp-float__tip";
    tip.setAttribute("role", "tooltip");
    tip.setAttribute("aria-hidden", "true");
    tip.textContent = t("wa-tip", "Écrivez-nous sur WhatsApp");

    bubble.append(disc, tip);
    document.body.appendChild(bubble);
  }

  const grid = document.getElementById("works");
  if (!grid) return;

  const source = grid.getAttribute("data-source");
  if (!source) return;

  init();

  async function init() {
    try {
      const items = await loadItems(source);
      if (!items.length) {
        grid.innerHTML =
          '<p class="grid-message">' + t("grid-empty", "Aucun projet pour le moment.") + "</p>";
        grid.setAttribute("aria-busy", "false");
        return;
      }

      grid.innerHTML = "";
      items.forEach((item) => {
        grid.appendChild(renderSkeleton(item.url));
      });

      items.forEach((item, index) => {
        hydrateCard(grid.children[index], item);
      });
    } catch (error) {
      console.error(error);
      grid.innerHTML =
        '<p class="grid-message">' +
        t("grid-error", "Impossible de charger les projets pour le moment.") +
        "</p>";
    } finally {
      grid.setAttribute("aria-busy", "false");
    }
  }

  async function loadItems(path) {
    const response = await fetch(path);
    if (!response.ok) throw new Error("json");
    const data = await response.json();
    if (!Array.isArray(data)) return [];
    return data.filter((item) => item && typeof item.url === "string");
  }

  function hostnameOf(url) {
    try {
      return new URL(url).hostname.replace(/^www\./, "");
    } catch {
      return url;
    }
  }

  function renderSkeleton(url) {
    const card = document.createElement("a");
    card.className = "mention-card is-skeleton";
    card.href = url;
    card.target = "_blank";
    card.rel = "noopener noreferrer";
    card.innerHTML =
      '<div class="mention-card__media"></div>' +
      '<div class="mention-card__body">' +
      '<div class="sk" style="width:70%"></div>' +
      '<div class="sk" style="width:92%"></div>' +
      '<div class="sk" style="width:40%"></div>' +
      "</div>";
    return card;
  }

  function hydrateCard(card, item) {
    const url = item.url;
    const titleText = item.title || hostnameOf(url);
    const descText = item.description || t("card-fallback", "Ouvrir le design");
    const imageSrc =
      typeof item.image === "string" && item.image
        ? item.image
        : PLACEHOLDER;

    card.classList.remove("is-skeleton");
    card.innerHTML =
      '<div class="mention-card__media"><img alt="" /></div>' +
      '<div class="mention-card__body">' +
      '<h2 class="mention-card__title"></h2>' +
      '<p class="mention-card__desc"></p>' +
      '<span class="mention-card__host"></span>' +
      "</div>";

    const img = card.querySelector("img");
    const title = card.querySelector(".mention-card__title");
    const desc = card.querySelector(".mention-card__desc");
    const host = card.querySelector(".mention-card__host");

    title.textContent = titleText;
    desc.textContent = descText;
    host.textContent = hostnameOf(url) + " ↗";
    img.alt = titleText;
    img.addEventListener("error", function onError() {
      img.removeEventListener("error", onError);
      img.src = PLACEHOLDER;
      img.style.objectFit = "contain";
    });
    if (imageSrc === PLACEHOLDER) {
      img.style.objectFit = "contain";
    }
    img.src = imageSrc;
  }

})();
