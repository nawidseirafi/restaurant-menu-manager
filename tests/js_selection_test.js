const assert = require("node:assert/strict");
const selection = require("../app/templates/html/default/menu.js");

function memoryStorage(initialValue = null) {
  let value = initialValue;
  return {
    getItem() {
      return value;
    },
    setItem(_key, nextValue) {
      value = nextValue;
    },
    value() {
      return value;
    },
  };
}

function run() {
  let state = selection.createEmptySelection("2026-09-01");
  selection.addItem(state, {
    itemId: 123,
    name: "Burrito Happiness",
    variant: null,
    unitPriceCents: 1890,
  });
  assert.equal(state.items.length, 1);
  assert.equal(state.items[0].quantity, 1);

  selection.addItem(state, {
    itemId: 123,
    name: "Burrito Happiness",
    variant: null,
    unitPriceCents: 1890,
  });
  assert.equal(state.items[0].quantity, 2);
  assert.equal(selection.calculateCount(state), 2);
  assert.equal(selection.calculateTotal(state), 3780);

  selection.updateQuantity(state, 123, null, 1);
  assert.equal(state.items[0].quantity, 1);
  selection.updateQuantity(state, 123, null, 0);
  assert.equal(state.items.length, 0);

  selection.addItem(state, {
    itemId: 456,
    name: "Coca Cola",
    variant: "0,3 l",
    unitPriceCents: 390,
  });
  selection.addItem(state, {
    itemId: 456,
    name: "Coca Cola",
    variant: "0,2 l",
    unitPriceCents: 290,
  });
  assert.equal(state.items.length, 2);
  assert.equal(selection.calculateTotal(state), 680);

  selection.updateNote(state, 456, "0,3 l", "ohne Eis");
  assert.equal(state.items.find((item) => item.variant === "0,3 l").note, "ohne Eis");

  selection.removeItem(state, 456, "0,2 l");
  assert.equal(state.items.length, 1);

  const storage = memoryStorage();
  selection.saveSelection(storage, state);
  const restored = selection.loadSelection(storage);
  assert.equal(restored.items.length, 1);
  assert.equal(restored.items[0].variant, "0,3 l");

  const broken = selection.loadSelection(memoryStorage("{kaputt"));
  assert.equal(broken.items.length, 0);

  selection.clearSelection(restored);
  assert.equal(restored.items.length, 0);
  assert.equal(selection.calculateTotal(restored), 0);

  console.log("selection tests passed");
}

run();
