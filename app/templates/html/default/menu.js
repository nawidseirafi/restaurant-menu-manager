(function (global) {
  const STORAGE_KEY = "tacomex_menu_selection_v1";
  const STORAGE_VERSION = 1;

  function itemKey(item) {
    return `${item.itemId}::${item.variant || ""}`;
  }

  function createEmptySelection(menuVersion = "local") {
    return { version: STORAGE_VERSION, menuVersion, items: [] };
  }

  function normalizeQuantity(value) {
    const quantity = Number.parseInt(value, 10);
    return Number.isFinite(quantity) && quantity > 0 ? quantity : 1;
  }

  function normalizeCents(value) {
    const cents = Number.parseInt(value, 10);
    return Number.isFinite(cents) && cents >= 0 ? cents : 0;
  }

  function normalizeItem(item) {
    return {
      itemId: String(item.itemId),
      orderNumber: item.orderNumber ? String(item.orderNumber) : "",
      name: String(item.name || ""),
      variant: item.variant ? String(item.variant) : null,
      unitPriceCents: normalizeCents(item.unitPriceCents),
      quantity: normalizeQuantity(item.quantity),
      note: item.note ? String(item.note) : "",
    };
  }

  function sanitizeSelection(rawSelection, catalog) {
    if (!rawSelection || !Array.isArray(rawSelection.items)) {
      return createEmptySelection();
    }
    const next = createEmptySelection(rawSelection.menuVersion || "local");
    rawSelection.items.forEach((rawItem) => {
      let item = normalizeItem(rawItem);
      if (catalog) {
        // Older exports stored the first size without a label.
        const current = catalog.get(itemKey(item)) || (!item.variant
          ? Array.from(catalog.values()).find((entry) => String(entry.itemId) === item.itemId)
          : null);
        if (!current) return;
        item = normalizeItem({ ...item, ...current });
      }
      if (!item.itemId || !item.name || item.unitPriceCents <= 0) return;
      const existing = next.items.find((entry) => itemKey(entry) === itemKey(item));
      if (existing) {
        existing.quantity += item.quantity;
        if (item.note) existing.note = item.note;
      } else {
        next.items.push(item);
      }
    });
    return next;
  }

  function loadSelection(storage, catalog) {
    try {
      const raw = storage.getItem(STORAGE_KEY);
      return sanitizeSelection(raw ? JSON.parse(raw) : null, catalog);
    } catch (_error) {
      return createEmptySelection();
    }
  }

  function saveSelection(storage, selection) {
    storage.setItem(STORAGE_KEY, JSON.stringify(sanitizeSelection(selection)));
  }

  function addItem(selection, item) {
    const normalized = normalizeItem(item);
    const existing = selection.items.find((entry) => itemKey(entry) === itemKey(normalized));
    if (existing) {
      existing.quantity += 1;
    } else {
      selection.items.push(normalized);
    }
    return selection;
  }

  function updateQuantity(selection, itemId, variant, quantity) {
    const id = String(itemId);
    const normalizedVariant = variant ? String(variant) : null;
    const nextQuantity = Number.parseInt(quantity, 10);
    selection.items = selection.items.filter((item) => {
      if (item.itemId !== id || item.variant !== normalizedVariant) return true;
      if (!Number.isFinite(nextQuantity) || nextQuantity <= 0) return false;
      item.quantity = nextQuantity;
      return true;
    });
    return selection;
  }

  function removeItem(selection, itemId, variant) {
    const id = String(itemId);
    const normalizedVariant = variant ? String(variant) : null;
    selection.items = selection.items.filter((item) => item.itemId !== id || item.variant !== normalizedVariant);
    return selection;
  }

  function clearSelection(selection) {
    selection.items = [];
    return selection;
  }

  function updateNote(selection, itemId, variant, note) {
    const id = String(itemId);
    const normalizedVariant = variant ? String(variant) : null;
    const item = selection.items.find((entry) => entry.itemId === id && entry.variant === normalizedVariant);
    if (item) item.note = String(note || "");
    return selection;
  }

  function calculateTotal(selection) {
    return selection.items.reduce((sum, item) => sum + item.unitPriceCents * item.quantity, 0);
  }

  function calculateCount(selection) {
    return selection.items.reduce((sum, item) => sum + item.quantity, 0);
  }

  function formatMoney(cents, currency = "EUR") {
    return new Intl.NumberFormat("de-DE", {
      style: "currency",
      currency,
    }).format(cents / 100);
  }

  const core = {
    STORAGE_KEY,
    createEmptySelection,
    sanitizeSelection,
    loadSelection,
    saveSelection,
    addItem,
    updateQuantity,
    removeItem,
    clearSelection,
    updateNote,
    calculateTotal,
    calculateCount,
    formatMoney,
  };

  function initDom() {
    if (!global.document) return;

    const document = global.document;
    const storage = global.localStorage;
    const slots = Array.from(document.querySelectorAll(".menu-action-slot"));
    const currency = slots[0]?.dataset.currency || "EUR";
    const catalog = new Map();

    slots.forEach((slot) => {
      const baseItem = {
        itemId: slot.dataset.itemId,
        orderNumber: slot.dataset.orderNumber || "",
        name: slot.dataset.name,
        variant: slot.dataset.priceLabel || null,
        unitPriceCents: normalizeCents(slot.dataset.priceCents),
      };
      catalog.set(itemKey(baseItem), baseItem);
      if (slot.dataset.secondPriceCents) {
        const variantItem = {
          itemId: slot.dataset.itemId,
          orderNumber: slot.dataset.orderNumber || "",
          name: slot.dataset.name,
          variant: slot.dataset.secondPriceLabel || "Variante",
          unitPriceCents: normalizeCents(slot.dataset.secondPriceCents),
        };
        catalog.set(itemKey(variantItem), variantItem);
      }
    });

    let selection = loadSelection(storage, catalog);

    const bar = document.querySelector("[data-selection-bar]");
    const summary = document.querySelector("[data-selection-summary]");
    const total = document.querySelector("[data-selection-total]");
    const drawer = document.querySelector("[data-selection-drawer]");
    const itemsContainer = document.querySelector("[data-selection-items]");
    const emptyState = document.querySelector("[data-selection-empty]");
    const largeView = document.querySelector("[data-large-view]");
    const largeItems = document.querySelector("[data-large-items]");
    const largeTotal = document.querySelector("[data-large-total]");

    function persistAndRender() {
      saveSelection(storage, selection);
      renderMenuActions();
      renderSelection();
      updateStickyBar();
      renderLargeView();
    }

    function getSelected(itemId, variant) {
      const key = `${itemId}::${variant || ""}`;
      return selection.items.find((item) => itemKey(item) === key);
    }

    function renderMenuActions() {
      slots.forEach((slot) => {
        const base = catalog.get(`${slot.dataset.itemId}::${slot.dataset.priceLabel || ""}`);
        const second = slot.dataset.secondPriceCents
          ? catalog.get(`${slot.dataset.itemId}::${slot.dataset.secondPriceLabel || "Variante"}`)
          : null;
        slot.innerHTML = "";

        [base, second].filter(Boolean).forEach((menuItem) => {
          const selected = getSelected(menuItem.itemId, menuItem.variant);
          const row = document.createElement("div");
          row.className = "menu-price-row";
          const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
          icon.setAttribute("class", "price-icon");
          icon.setAttribute("aria-hidden", "true");
          const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
          use.setAttribute("href", ["drink-pitcher", "drink-glass", "menu-plate"].includes(slot.dataset.priceIcon) ? `#${slot.dataset.priceIcon}` : "#menu-plate");
          icon.appendChild(use);
          const size = document.createElement("span");
          size.className = "price-size";
          size.textContent = menuItem.variant || slot.dataset.defaultLabel || "Portion";
          const price = document.createElement("strong");
          price.className = "variant-price";
          price.textContent = formatMoney(menuItem.unitPriceCents, currency);
          row.append(icon, size, price);
          if (selected) {
            row.appendChild(createQuantityControls(selected));
          } else {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "menu-remember-button";
            button.innerHTML = '<svg aria-hidden="true" viewBox="0 0 24 24"><use href="#bookmark"/></svg>';
            button.title = "Merken";
            button.setAttribute("aria-label", `${menuItem.name}${menuItem.variant ? " " + menuItem.variant : ""} merken`);
            button.addEventListener("click", () => {
              selection = addItem(selection, menuItem);
              persistAndRender();
            });
            row.appendChild(button);
          }
          slot.appendChild(row);
        });
      });
    }

    function createQuantityControls(item) {
      const controls = document.createElement("div");
      controls.className = "quantity-controls";
      const minus = document.createElement("button");
      minus.type = "button";
      minus.textContent = "−";
      minus.setAttribute("aria-label", `${item.name} Menge reduzieren`);
      minus.addEventListener("click", () => {
        selection = updateQuantity(selection, item.itemId, item.variant, item.quantity - 1);
        persistAndRender();
      });
      const value = document.createElement("span");
      value.textContent = String(item.quantity);
      value.setAttribute("aria-live", "polite");
      const plus = document.createElement("button");
      plus.type = "button";
      plus.textContent = "+";
      plus.setAttribute("aria-label", `${item.name} Menge erhoehen`);
      plus.addEventListener("click", () => {
        selection = updateQuantity(selection, item.itemId, item.variant, item.quantity + 1);
        persistAndRender();
      });
      controls.append(minus, value, plus);
      return controls;
    }

    function renderSelection() {
      if (!itemsContainer || !emptyState || !total) return;
      itemsContainer.innerHTML = "";
      const hasItems = selection.items.length > 0;
      emptyState.hidden = hasItems;
      selection.items.forEach((item) => {
        const row = document.createElement("article");
        row.className = "selection-item";
        row.innerHTML = `
          <div class="selection-item-main">
            <div>
              <strong>${escapeHtml(item.quantity)} × ${escapeHtml(item.orderNumber ? item.orderNumber + ". " + item.name : item.name)}</strong>
              ${item.variant ? `<span>${escapeHtml(item.variant)}</span>` : ""}
              <small>${formatMoney(item.unitPriceCents, currency)} je Stück</small>
            </div>
            <strong>${formatMoney(item.unitPriceCents * item.quantity, currency)}</strong>
          </div>
          <label>
            Notiz
            <input type="text" value="${escapeAttribute(item.note)}" placeholder="z. B. ohne Zwiebeln" data-note-item="${escapeAttribute(item.itemId)}" data-note-variant="${escapeAttribute(item.variant || "")}">
          </label>
        `;
        const actionRow = document.createElement("div");
        actionRow.className = "selection-actions";
        actionRow.appendChild(createQuantityControls(item));
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "remove-button";
        remove.textContent = "Entfernen";
        remove.setAttribute("aria-label", `${item.name} entfernen`);
        remove.addEventListener("click", () => {
          selection = removeItem(selection, item.itemId, item.variant);
          persistAndRender();
        });
        actionRow.appendChild(remove);
        row.appendChild(actionRow);
        itemsContainer.appendChild(row);
      });
      itemsContainer.querySelectorAll("[data-note-item]").forEach((input) => {
        input.addEventListener("input", (event) => {
          selection = updateNote(selection, event.target.dataset.noteItem, event.target.dataset.noteVariant || null, event.target.value);
          saveSelection(storage, selection);
          renderLargeView();
        });
      });
      total.textContent = formatMoney(calculateTotal(selection), currency);
    }

    function updateStickyBar() {
      if (!bar || !summary) return;
      const count = calculateCount(selection);
      bar.hidden = count === 0;
      summary.textContent = `${count} ${count === 1 ? "Artikel" : "Artikel"} · ${formatMoney(calculateTotal(selection), currency)}`;
      document.body.classList.toggle("has-selection", count > 0);
    }

    function renderLargeView() {
      if (!largeItems || !largeTotal) return;
      largeItems.innerHTML = "";
      if (selection.items.length === 0) {
        largeItems.innerHTML = "<p>Noch nichts gemerkt.</p>";
      } else {
        selection.items.forEach((item) => {
          const row = document.createElement("article");
          row.className = "large-item";
          row.innerHTML = `
            <strong>${escapeHtml(item.quantity)} × ${escapeHtml(item.orderNumber ? item.orderNumber + ". " + item.name : item.name)}</strong>
            ${item.variant ? `<span>${escapeHtml(item.variant)}</span>` : ""}
            ${item.note ? `<p>${escapeHtml(item.note)}</p>` : ""}
          `;
          largeItems.appendChild(row);
        });
      }
      largeTotal.textContent = formatMoney(calculateTotal(selection), currency);
    }

    document.querySelector("[data-open-selection]")?.addEventListener("click", () => {
      drawer.hidden = false;
      drawer.querySelector(".drawer-panel")?.focus();
    });
    document.querySelectorAll("[data-close-selection]").forEach((button) => {
      button.addEventListener("click", () => {
        drawer.hidden = true;
      });
    });
    document.querySelector("[data-clear-selection]")?.addEventListener("click", () => {
      if (global.confirm("Möchtest du deine gesamte Auswahl wirklich löschen?")) {
        selection = clearSelection(selection);
        persistAndRender();
      }
    });
    document.querySelector("[data-show-large]")?.addEventListener("click", () => {
      largeView.hidden = false;
      renderLargeView();
    });
    document.querySelector("[data-close-large]")?.addEventListener("click", () => {
      largeView.hidden = true;
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        if (largeView) largeView.hidden = true;
        if (drawer) drawer.hidden = true;
      }
    });

    persistAndRender();
    initCategoryNavigation(document);
  }

  function initCategoryNavigation(document) {
    const nav = document.querySelector(".category-nav");
    // Both the brand header and navigation remain above the current category.
    const wrapper = document.querySelector(".site-top");
    if (!nav || !wrapper) return;
    const entries = Array.from(nav.querySelectorAll('a[href^="#"]'))
      .map((link) => ({ link, section: document.getElementById(link.hash.slice(1)) }))
      .filter((entry) => entry.section);
    if (!entries.length) return;

    let activeLink = null;
    let scheduled = false;
    function update() {
      scheduled = false;
      const height = wrapper.getBoundingClientRect().height;
      document.documentElement.style.setProperty("--category-nav-height", height + "px");
      let current = entries[0];
      for (const entry of entries) {
        if (entry.section.getBoundingClientRect().top <= height + 1) current = entry;
      }
      // A short final category may never reach the top of the viewport.
      if (global.scrollY > 0 && global.scrollY + global.innerHeight >= document.documentElement.scrollHeight - 2) {
        current = entries[entries.length - 1];
      }
      if (current.link === activeLink) return;
      activeLink?.removeAttribute("aria-current");
      activeLink = current.link;
      activeLink.setAttribute("aria-current", "location");
      const bounds = nav.getBoundingClientRect();
      const tab = activeLink.getBoundingClientRect();
      if (tab.left < bounds.left || tab.right > bounds.right) {
        // Only move the tab strip; keep the page's vertical scroll position.
        nav.scrollBy({ left: tab.left - bounds.left - (bounds.width - tab.width) / 2, behavior: "instant" });
      }
    }
    function scheduleUpdate() {
      if (scheduled) return;
      scheduled = true;
      global.requestAnimationFrame(update);
    }
    global.addEventListener("scroll", scheduleUpdate, { passive: true });
    global.addEventListener("resize", scheduleUpdate);
    global.addEventListener("load", scheduleUpdate);
    if (global.ResizeObserver) {
      const observer = new global.ResizeObserver(scheduleUpdate);
      observer.observe(wrapper);
      entries.forEach(({ section }) => observer.observe(section));
    }
    update();
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    }[char]));
  }

  function escapeAttribute(value) {
    return escapeHtml(value).replace(/`/g, "&#096;");
  }

  global.TacoMexMenuSelection = core;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = core;
  }
  if (global.document) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", initDom);
    } else {
      initDom();
    }
  }
})(typeof window !== "undefined" ? window : globalThis);
