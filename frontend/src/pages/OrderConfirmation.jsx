import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { getOrder } from "../api/orderApi";

function Price({ value }) {
  return (
    <>
      {"\u20B9"}
      {value}
    </>
  );
}

function formatStatus(status) {
  return status.replaceAll("_", " ");
}

function formatPaymentMethod(method) {
  if (method === "upi") return "Mock UPI";
  if (method === "card") return "Mock card";
  return "Cash on delivery";
}

function formatDateTime(dateValue) {
  if (!dateValue) return "Updating soon";
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(dateValue));
}

function formatEta(order) {
  if (order.status === "cancelled") return "Cancelled";
  if (order.status === "delivered") return "Delivered";
  if (order.eta_minutes == null) return "Updating";
  return `${order.eta_minutes} min`;
}

function OrderConfirmation() {
  const { orderId } = useParams();
  const location = useLocation();
  const [order, setOrder] = useState(location.state?.order || null);
  const [loading, setLoading] = useState(!location.state?.order);
  const [error, setError] = useState("");

  useEffect(() => {
    if (order) return;

    const loadOrder = async () => {
      setLoading(true);
      setError("");
      try {
        setOrder(await getOrder(orderId));
      } catch (orderError) {
        setError(orderError.response?.data?.detail || "Could not load order.");
      } finally {
        setLoading(false);
      }
    };

    loadOrder();
  }, [order, orderId]);

  if (loading) {
    return (
      <section className="container page-section">
        <p className="status-card">Loading order...</p>
      </section>
    );
  }

  if (error || !order) {
    return (
      <section className="container page-section">
        <div className="status-card error-card">
          <h2>Order not found</h2>
          <p>{error || "This order could not be loaded."}</p>
        </div>
      </section>
    );
  }

  const address = order.delivery_address_snapshot;
  const trackingSteps = order.tracking_steps || [];
  const partner = order.delivery_partner;

  return (
    <section className="container page-section">
      <div className="order-success">
        <span aria-hidden="true">{"\u2713"}</span>
        <div>
          <span className="eyebrow">Order placed</span>
          <h1>Thanks, your order is confirmed.</h1>
          <p>Order #{order.order_number}</p>
        </div>
      </div>

      <section className="checkout-card delivery-panel">
        <div className="delivery-panel-header">
          <div>
            <span className="eyebrow">Live tracking</span>
            <h2>{formatEta(order)}</h2>
            <p>{order.tracking_message}</p>
          </div>
          <div className="delivery-eta-card">
            <span>Estimated delivery</span>
            <strong>{formatDateTime(order.estimated_delivery_at)}</strong>
          </div>
        </div>
        <div className="delivery-progress">
          <span style={{ width: `${order.delivery_progress_percent || 0}%` }} />
        </div>
        <div className="delivery-meta-grid">
          <article>
            <span>Delivery partner</span>
            {partner ? (
              <>
                <strong>{partner.name}</strong>
                <small>
                  {partner.phone} - {partner.vehicle_number}
                </small>
              </>
            ) : (
              <>
                <strong>Assigning soon</strong>
                <small>Partner details appear after store confirmation.</small>
              </>
            )}
          </article>
          <article>
            <span>Current status</span>
            <strong>{formatStatus(order.status)}</strong>
            <small>{formatDateTime(order.updated_at)}</small>
          </article>
        </div>
      </section>

      {order.customer_delivery_otp && (
        <section className="checkout-card customer-otp-card">
          <div>
            <span className="eyebrow">Delivery OTP</span>
            <h2>{order.customer_delivery_otp}</h2>
            <p>
              Ye OTP delivery boy ko tabhi batana jab aap order receive kar rahe
              ho. Isse galat parcel handover avoid hota hai.
            </p>
          </div>
          <span>{order.dropoff_verified ? "Verified" : "Keep private"}</span>
        </section>
      )}

      <div className="checkout-layout">
        <div className="checkout-card">
          <h2>Items</h2>
          <div className="order-items">
            {order.items.map((item) => (
              <div className="order-item-row" key={item.id}>
                <div>
                  <strong>{item.product_name}</strong>
                  <small>
                    {item.unit} x {item.quantity}
                  </small>
                </div>
                <strong>
                  <Price value={item.line_total} />
                </strong>
              </div>
            ))}
          </div>

          <h2>Delivery address</h2>
          <p className="address-text">
            <strong>{address.receiver_name}</strong>
            <br />
            {address.line1}
            {address.line2 ? `, ${address.line2}` : ""}
            <br />
            {address.city}, {address.state} - {address.postal_code}
            <br />
            Phone: {address.phone}
          </p>
        </div>

        <aside className="order-summary">
          <h2>Bill details</h2>
          <div>
            <span>Status</span>
            <strong>{formatStatus(order.status)}</strong>
          </div>
          <div>
            <span>Payment</span>
            <strong>{formatPaymentMethod(order.payment_method)}</strong>
          </div>
          <div>
            <span>Payment status</span>
            <strong>{formatStatus(order.payment_status)}</strong>
          </div>
          <div>
            <span>Subtotal</span>
            <strong>
              <Price value={order.subtotal} />
            </strong>
          </div>
          <div>
            <span>Delivery</span>
            <strong>
              {order.delivery_fee === 0 ? (
                "Free"
              ) : (
                <Price value={order.delivery_fee} />
              )}
            </strong>
          </div>
          <div className="summary-total">
            <span>Total</span>
            <strong>
              <Price value={order.total} />
            </strong>
          </div>
          <Link className="button checkout-button" to="/products">
            Continue shopping
          </Link>
          <Link className="button button-secondary checkout-button" to="/orders">
            View all orders
          </Link>
        </aside>
      </div>

      <section className="checkout-card tracking-card">
        <h2>Order tracking</h2>
        <div className="tracking-timeline">
          {trackingSteps.map((step, index) => (
            <div
              className={`tracking-step${
                step.completed ? " is-active" : ""
              }${step.current ? " is-current" : ""}`}
              key={step.key}
            >
              <span>{step.completed ? "\u2713" : index + 1}</span>
              <div>
                <strong>{step.label}</strong>
                <p>{step.description}</p>
                <small>{formatDateTime(step.timestamp)}</small>
              </div>
            </div>
          ))}
        </div>
      </section>
    </section>
  );
}

export default OrderConfirmation;
