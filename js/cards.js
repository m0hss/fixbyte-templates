(function () {
  const CACHE_TTL_MS = 24 * 60 * 60 * 1000;
  const PLACEHOLDER = "assets/placeholder.svg";
  const MICROLINK = "https://api.microlink.io/";

  const yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());

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

      await Promise.all(
        items.map((item, index) => hydrateCard(grid.children[index], item.url))
      );
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

  function cacheKey(url) {
    return "fixbyte-og:" + url;
  }

  function getCached(url) {
    try {
      const raw = localStorage.getItem(cacheKey(url));
      if (!raw) return null;
      const entry = JSON.parse(raw);
      if (!entry || Date.now() - entry.ts > CACHE_TTL_MS) {
        localStorage.removeItem(cacheKey(url));
        return null;
      }
      return entry.data;
    } catch {
      return null;
    }
  }

  function setCached(url, data) {
    try {
      localStorage.setItem(
        cacheKey(url),
        JSON.stringify({ ts: Date.now(), data })
      );
    } catch {
      /* quota */
    }
  }

  function hostnameOf(url) {
    try {
      return new URL(url).hostname.replace(/^www\./, "");
    } catch {
      return url;
    }
  }

  function microlinkEmbed(url, extra) {
    const endpoint = new URL(MICROLINK);
    endpoint.searchParams.set("url", url);
    Object.entries(extra || {}).forEach(([key, value]) => {
      endpoint.searchParams.set(key, value);
    });
    return endpoint.toString();
  }

  async function fetchMeta(url) {
    const cached = getCached(url);
    if (cached) return cached;

    const endpoint = microlinkEmbed(url);
    const response = await fetch(endpoint);
    if (!response.ok) throw new Error("microlink");
    const json = await response.json();
    if (json.status !== "success" || !json.data) throw new Error("microlink");

    const data = {
      title: json.data.title || hostnameOf(url),
      description: json.data.description || "",
      image: json.data.image && json.data.image.url ? json.data.image.url : "",
    };
    setCached(url, data);
    return data;
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

  function bindImageFallback(img, url) {
    const screenshot = microlinkEmbed(url, {
      screenshot: "true",
      meta: "false",
      embed: "screenshot.url",
    });
    const ogEmbed = microlinkEmbed(url, { embed: "image.url" });

    img.addEventListener("error", function onError() {
      if (img.dataset.step === "og") {
        img.dataset.step = "shot";
        img.src = screenshot;
        return;
      }
      if (img.dataset.step === "shot") {
        img.removeEventListener("error", onError);
        img.dataset.step = "ph";
        img.src = PLACEHOLDER;
        img.style.objectFit = "contain";
      }
    });

    return ogEmbed;
  }

  async function hydrateCard(card, url) {
    let meta = {
      title: hostnameOf(url),
      description: "Ouvrir le design",
      image: "",
    };

    try {
      meta = { ...meta, ...(await fetchMeta(url)) };
    } catch {
      /* keep fallbacks */
    }

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

    title.textContent = meta.title;
    desc.textContent = meta.description || "Ouvrir le design";
    host.textContent = hostnameOf(url) + " ↗";

    img.alt = meta.title;
    const ogEmbed = bindImageFallback(img, url);
    img.dataset.step = "og";
    img.src = meta.image || ogEmbed;
  }
})();
