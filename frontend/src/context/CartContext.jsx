import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import {
  addCartItem as addCartItemApi,
  clearServerCart,
  getCart,
  removeCartItem,
  updateCartItem,
} from "../api/cartApi";
import { useAuth } from "./AuthContext";
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

function mapServerCart(serverCart) {
  return serverCart.items.map((item) => ({
    id: item.product_id,
    name: item.name,
    price: item.price,
    mrp: item.mrp,
    unit: item.unit,
    icon: item.icon,
    image_url: item.image_url,
    quantity: item.quantity,
    stock_quantity: item.stock_quantity,
    in_stock: item.in_stock,
  }));
}

export function CartProvider({ children }) {
  const { isAuthenticated, loading: authLoading, token } = useAuth();
  const [items, setItems] = useState(loadCart);
  const [serverCart, setServerCart] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const syncedTokenRef = useRef(null);

  useEffect(() => {
    if (!isAuthenticated) {
      localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
    }
  }, [isAuthenticated, items]);

  useEffect(() => {
    if (authLoading) return;

    if (!isAuthenticated || !token) {
      syncedTokenRef.current = null;
      setServerCart(null);
      setLoading(false);
      return;
    }

    if (syncedTokenRef.current === token) return;
    syncedTokenRef.current = token;

    const syncCart = async () => {
      setLoading(true);
      setError("");

      try {
        let latestCart = await getCart();
        const localItems = loadCart();

        for (const item of localItems) {
          latestCart = await addCartItemApi(item.id, item.quantity);
        }

        setServerCart(latestCart);
        setItems(mapServerCart(latestCart));
        localStorage.removeItem(CART_STORAGE_KEY);
      } catch {
        setError("We could not sync your cart with this account.");
      } finally {
        setLoading(false);
      }
    };

    syncCart();
  }, [authLoading, isAuthenticated, token]);

  const applyServerCart = (nextCart) => {
    setServerCart(nextCart);
    setItems(mapServerCart(nextCart));
  };

  const runServerAction = async (action) => {
    setError("");
    try {
      const nextCart = await action();
      applyServerCart(nextCart);
    } catch (cartError) {
      setError(cartError.response?.data?.detail || "Cart update failed.");
    }
  };

  const refreshCart = async () => {
    if (!isAuthenticated) {
      return null;
    }

    setLoading(true);
    setError("");
    try {
      const nextCart = await getCart();
      applyServerCart(nextCart);
      return nextCart;
    } catch (cartError) {
      setError(cartError.response?.data?.detail || "Cart refresh failed.");
      return null;
    } finally {
      setLoading(false);
    }
  };

  const value = useMemo(
    () => ({
      items,
      itemCount: serverCart?.item_count ?? calculateCartCount(items),
      total: serverCart?.subtotal ?? calculateCartTotal(items),
      deliveryFee: serverCart?.delivery_fee ?? (calculateCartTotal(items) >= 199 ? 0 : 20),
      grandTotal:
        serverCart?.total ??
        calculateCartTotal(items) +
          (calculateCartTotal(items) >= 199 || calculateCartTotal(items) === 0 ? 0 : 20),
      loading,
      error,
      addItem: async (product) => {
        if (isAuthenticated) {
          await runServerAction(() => addCartItemApi(product.id, 1));
          return;
        }
        setItems((current) => addCartItem(current, product));
      },
      updateQuantity: async (productId, quantity) => {
        if (isAuthenticated) {
          if (quantity <= 0) {
            await runServerAction(() => removeCartItem(productId));
            return;
          }
          await runServerAction(() => updateCartItem(productId, quantity));
          return;
        }
        setItems((current) =>
          updateCartItemQuantity(current, productId, quantity)
        );
      },
      removeItem: async (productId) => {
        if (isAuthenticated) {
          await runServerAction(() => removeCartItem(productId));
          return;
        }
        setItems((current) => current.filter((item) => item.id !== productId));
      },
      clearCart: async () => {
        if (isAuthenticated) {
          await runServerAction(clearServerCart);
          return;
        }
        setItems([]);
      },
      refreshCart,
    }),
    [error, isAuthenticated, items, loading, serverCart]
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
