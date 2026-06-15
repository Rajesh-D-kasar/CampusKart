import { createContext, useContext, useEffect, useMemo, useState } from "react";
import {
  addCartItem,
  calculateCartCount,
  calculateCartTotal,
  updateCartItemQuantity,
} from "../utils/cart";

const CART_STORAGE_KEY = "campuskart-cart";
const CartContext = createContext(null);

function loadCart() {
  try {
    const savedCart = localStorage.getItem(CART_STORAGE_KEY);
    const parsedCart = savedCart ? JSON.parse(savedCart) : [];
    return Array.isArray(parsedCart) ? parsedCart : [];
  } catch {
    return [];
  }
}

export function CartProvider({ children }) {
  const [items, setItems] = useState(loadCart);

  useEffect(() => {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
  }, [items]);

  const value = useMemo(
    () => ({
      items,
      itemCount: calculateCartCount(items),
      total: calculateCartTotal(items),
      addItem: (product) => setItems((current) => addCartItem(current, product)),
      updateQuantity: (productId, quantity) =>
        setItems((current) =>
          updateCartItemQuantity(current, productId, quantity)
        ),
      removeItem: (productId) =>
        setItems((current) =>
          current.filter((item) => item.id !== productId)
        ),
      clearCart: () => setItems([]),
    }),
    [items]
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const context = useContext(CartContext);

  if (!context) {
    throw new Error("useCart must be used inside CartProvider");
  }

  return context;
}
