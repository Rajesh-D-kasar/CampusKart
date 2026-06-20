import { Link } from "react-router-dom";
import CartItem from "../components/CartItem";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";

function Price({ value }) {
  return (
    <>
      {"\u20B9"}
      {value}
    </>
  );
}

function Cart() {
  const { isAuthenticated } = useAuth();
  const {
    items,
    total,
    deliveryFee,
    grandTotal,
    loading,
    error,
    updateQuantity,
    removeItem,
    clearCart,
  } = useCart();

  if (items.length === 0) {
    return (
      <section className="container page-section empty-state">
        <span aria-hidden="true">{"\u{1F6D2}"}</span>
        <h1>Your cart is empty</h1>
        <p>Add a few campus essentials and they will appear here.</p>
        <Link className="button" to="/products">
          Browse products
        </Link>
      </section>
    );
  }

  return (
    <section className="container page-section">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Ready to order</span>
          <h1>Your cart</h1>
        </div>
        <button className="text-button" onClick={clearCart}>
          Clear cart
        </button>
      </div>

      {loading && <p className="status-card">Syncing cart...</p>}
      {error && <p className="form-error">{error}</p>}

      <div className="cart-layout">
        <div className="cart-list">
          {items.map((item) => (
            <CartItem
              key={item.id}
              item={item}
              onQuantityChange={updateQuantity}
              onRemove={removeItem}
            />
          ))}
        </div>
        <aside className="order-summary">
          <h2>Order summary</h2>
          <div>
            <span>Subtotal</span>
            <strong>
              <Price value={total} />
            </strong>
          </div>
          <div>
            <span>Delivery</span>
            <strong>
              {deliveryFee === 0 ? "Free" : <Price value={deliveryFee} />}
            </strong>
          </div>
          <div className="summary-total">
            <span>Total</span>
            <strong>
              <Price value={grandTotal} />
            </strong>
          </div>
          <Link
            className="button checkout-button"
            to={isAuthenticated ? "/checkout" : "/login"}
          >
            {isAuthenticated ? "Proceed to checkout" : "Login to checkout"}
          </Link>
        </aside>
      </div>
    </section>
  );
}

export default Cart;
