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
      const item = normalizeItem(rawItem);
      if (!item.itemId || !item.name || item.unitPriceCents <= 0) return;
      if (catalog && !catalog.has(itemKey(item))) return;
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
        variant: null,
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
        const base = catalog.get(`${slot.dataset.itemId}::`);
        const second = slot.dataset.secondPriceCents
          ? catalog.get(`${slot.dataset.itemId}::${slot.dataset.secondPriceLabel || "Variante"}`)
          : null;
        slot.innerHTML = "";

        [base, second].filter(Boolean).forEach((menuItem) => {
          const selected = getSelected(menuItem.itemId, menuItem.variant);
          const row = document.createElement("div");
          row.className = "item-action-row";
          if (menuItem.variant) {
            const label = document.createElement("span");
            label.className = "variant-label";
            label.textContent = `${menuItem.variant} · ${formatMoney(menuItem.unitPriceCents, currency)}`;
            row.appendChild(label);
          }
          if (selected) {
            row.appendChild(createQuantityControls(selected));
          } else {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "remember-button";
            button.textContent = menuItem.variant ? `${menuItem.variant} merken` : "Merken";
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

    initNavArrows(document);
    persistAndRender();
  }

  function initNavArrows(document) {
    const nav = document.querySelector(".category-nav");
    const left = document.querySelector("[data-scroll-nav='left']");
    const right = document.querySelector("[data-scroll-nav='right']");
    if (!nav || !left || !right) return;
    const updateButtons = () => {
      const maxScroll = nav.scrollWidth - nav.clientWidth;
      left.disabled = nav.scrollLeft <= 4;
      right.disabled = nav.scrollLeft >= maxScroll - 4;
    };
    const scrollNav = (direction) => {
      nav.scrollBy({ left: direction * Math.max(180, nav.clientWidth * 0.72), behavior: "smooth" });
    };
    left.addEventListener("click", () => scrollNav(-1));
    right.addEventListener("click", () => scrollNav(1));
    nav.addEventListener("scroll", updateButtons, { passive: true });
    global.addEventListener("resize", updateButtons);
    updateButtons();
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
