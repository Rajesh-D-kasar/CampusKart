export function addCartItem(items, product) {
  const existingItem = items.find((item) => item.id === product.id);

  if (!existingItem) {
    return [...items, { ...product, quantity: 1 }];
  }

  return items.map((item) =>
    item.id === product.id
      ? { ...item, quantity: item.quantity + 1 }
      : item
  );
}

export function updateCartItemQuantity(items, productId, quantity) {
  if (quantity <= 0) {
    return items.filter((item) => item.id !== productId);
  }

  return items.map((item) =>
    item.id === productId ? { ...item, quantity } : item
  );
}

export function calculateCartCount(items) {
  return items.reduce((count, item) => count + item.quantity, 0);
}

export function calculateCartTotal(items) {
  return items.reduce(
    (total, item) => total + item.price * item.quantity,
    0
  );
}
