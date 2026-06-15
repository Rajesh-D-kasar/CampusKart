import { Link } from "react-router-dom";
import CartItem from "../components/CartItem";
import { useCart } from "../context/CartContext";

function Cart() {
  const { items, total, updateQuantity, removeItem, clearCart } = useCart();

  if (items.length === 0) {
    return (
      <section className="container page-section empty-state">
        <span aria-hidden="true">🛒</span>
        <h1>Your cart is empty</h1>
        <p>Add a few campus essentials and they will appear here.</p>
        <Link className="button" to="/products">
          Browse products
        </Link>
      </section>
    );
  }

  const deliveryFee = total >= 199 ? 0 : 20;

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
            <strong>₹{total}</strong>
          </div>
          <div>
            <span>Delivery</span>
            <strong>{deliveryFee === 0 ? "Free" : `₹${deliveryFee}`}</strong>
          </div>
          <div className="summary-total">
            <span>Total</span>
            <strong>₹{total + deliveryFee}</strong>
          </div>
          <button className="button checkout-button" disabled>
            Checkout coming next
          </button>
        </aside>
      </div>
    </section>
  );
}

export default Cart;
