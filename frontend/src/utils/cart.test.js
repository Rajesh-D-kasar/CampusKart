import assert from "node:assert/strict";
import test from "node:test";
import {
  addCartItem,
  calculateCartCount,
  calculateCartTotal,
  updateCartItemQuantity,
} from "./cart.js";

const product = { id: 1, name: "Maggi", price: 15 };

test("adds a new product with quantity one", () => {
  assert.deepEqual(addCartItem([], product), [{ ...product, quantity: 1 }]);
});

test("increments an existing product", () => {
  const cart = addCartItem([{ ...product, quantity: 1 }], product);
  assert.equal(cart[0].quantity, 2);
});

test("removes an item when quantity reaches zero", () => {
  assert.deepEqual(
    updateCartItemQuantity([{ ...product, quantity: 1 }], product.id, 0),
    []
  );
});

test("calculates item count and total", () => {
  const cart = [
    { ...product, quantity: 2 },
    { id: 2, name: "Milk", price: 60, quantity: 1 },
  ];

  assert.equal(calculateCartCount(cart), 3);
  assert.equal(calculateCartTotal(cart), 90);
});
