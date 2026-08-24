(function () {
  const PLACEHOLDER = "assets/placeholder.svg";

  const yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());

  const ctaBtn = document.querySelector(".cta-block__btn");
  if (ctaBtn && !document.querySelector(".whatsapp-float")) {
    const bubble = document.createElement("a");
    bubble.className = "whatsapp-float";
    bubble.href = ctaBtn.href;
    bubble.target = "_blank";
    bubble.rel = "noopener noreferrer";
    bubble.setAttribute("aria-label", "Écrire sur WhatsApp");
    bubble.innerHTML =
      '<img src="assets/whatsapp.svg" alt="" width="28" height="28" decoding="async" />';
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
          '<p class="grid-message">Aucun projet pour le moment.</p>';
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
        '<p class="grid-message">Impossible de charger les projets pour le moment.</p>';
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
    const descText = item.description || "Ouvrir le design";
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
