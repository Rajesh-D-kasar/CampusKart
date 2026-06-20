import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  getDeliveryOrders,
  updateDeliveryOrderStatus,
} from "../api/deliveryApi";
import { useAuth } from "../context/AuthContext";

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

function formatDateTime(dateValue) {
  if (!dateValue) return "Updating soon";
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(dateValue));
}

function formatAddress(address) {
  return [
    address.line1,
    address.line2,
    `${address.city}, ${address.state} - ${address.postal_code}`,
  ]
    .filter(Boolean)
    .join(", ");
}

function nextAction(order) {
  if (order.status === "confirmed" || order.status === "packing") {
    return { label: "Start delivery", status: "out_for_delivery" };
  }
  if (order.status === "out_for_delivery") {
    return { label: "Mark delivered", status: "delivered" };
  }
  return null;
}

function DeliveryDashboard() {
  const { isAuthenticated, loading: authLoading, user } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState("");
  const [error, setError] = useState("");

  const canUseDelivery =
    user?.role === "delivery_partner" || user?.role === "admin";

  const summary = useMemo(
    () => ({
      active: orders.filter((order) => order.status !== "delivered").length,
      delivered: orders.filter((order) => order.status === "delivered").length,
    }),
    [orders]
  );

  const loadOrders = async () => {
    setLoading(true);
    setError("");
    try {
      setOrders(await getDeliveryOrders());
    } catch (deliveryError) {
      setError(
        deliveryError.response?.data?.detail || "Could not load delivery orders."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isAuthenticated || !canUseDelivery) return;
    loadOrders();
  }, [isAuthenticated, canUseDelivery]);

  const handleStatusUpdate = async (orderId, status) => {
    setSaving(`order-${orderId}`);
    setError("");
    try {
      const updatedOrder = await updateDeliveryOrderStatus(orderId, status);
      setOrders((current) =>
        current.map((order) => (order.id === orderId ? updatedOrder : order))
      );
    } catch (deliveryError) {
      setError(
        deliveryError.response?.data?.detail || "Could not update delivery status."
      );
    } finally {
      setSaving("");
    }
  };

  if (authLoading) {
    return (
      <section className="container page-section">
        <p className="status-card">Checking your session...</p>
      </section>
    );
  }

  if (!isAuthenticated) {
    return (
      <section className="container auth-page">
        <div className="auth-card">
          <h2>Login required</h2>
          <p>Please login with a delivery partner account.</p>
          <Link className="button" to="/login">
            Login to continue
          </Link>
        </div>
      </section>
    );
  }

  if (!canUseDelivery) {
    return (
      <section className="container page-section">
        <div className="status-card error-card">
          <h2>Delivery access required</h2>
          <p>This dashboard is only for delivery partners and admins.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="container page-section">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Partner operations</span>
          <h1>Delivery dashboard</h1>
          <p>Track assigned orders and update doorstep delivery progress.</p>
        </div>
        <button className="button button-secondary" onClick={loadOrders}>
          Refresh
        </button>
      </div>

      <div className="delivery-stats-grid">
        <article>
          <span>Active deliveries</span>
          <strong>{summary.active}</strong>
        </article>
        <article>
          <span>Delivered today</span>
          <strong>{summary.delivered}</strong>
        </article>
      </div>

      {loading && <p className="status-card">Loading delivery orders...</p>}
      {error && <p className="form-error">{error}</p>}

      {!loading && !error && orders.length === 0 && (
        <div className="empty-state orders-empty-state">
          <h1>No assigned deliveries</h1>
          <p>Confirmed and packing orders assigned to you will appear here.</p>
        </div>
      )}

      <div className="delivery-board-grid">
        {orders.map((order) => {
          const address = order.delivery_address_snapshot;
          const action = nextAction(order);
          return (
            <article className="checkout-card delivery-order-card" key={order.id}>
              <div className="delivery-order-header">
                <div>
                  <span className="order-card-label">#{order.order_number}</span>
                  <h2>{order.customer_name}</h2>
                  <p>{order.item_count} items - {formatDateTime(order.created_at)}</p>
                </div>
                <span className={`status-pill status-${order.status}`}>
                  {formatStatus(order.status)}
                </span>
              </div>

              <div className="delivery-meta-grid">
                <article>
                  <span>ETA</span>
                  <strong>
                    {order.status === "delivered"
                      ? "Delivered"
                      : `${order.eta_minutes ?? "-"} min`}
                  </strong>
                  <small>{order.tracking_message}</small>
                </article>
                <article>
                  <span>Payment</span>
                  <strong>{formatStatus(order.payment_status)}</strong>
                  <small>
                    <Price value={order.total} /> via {formatStatus(order.payment_method)}
                  </small>
                </article>
              </div>

              <div className="delivery-address-card">
                <span>Drop address</span>
                <strong>{address.receiver_name}</strong>
                <p>{formatAddress(address)}</p>
                <small>Phone: {address.phone}</small>
                {order.delivery_instruction && (
                  <small>Note: {order.delivery_instruction}</small>
                )}
              </div>

              <div className="delivery-items-list">
                {order.items.map((item) => (
                  <div key={item.id}>
                    <span>{item.product_name}</span>
                    <strong>
                      {item.quantity} x {item.unit}
                    </strong>
                  </div>
                ))}
              </div>

              <div className="delivery-actions">
                {action ? (
                  <button
                    className="button"
                    disabled={saving === `order-${order.id}`}
                    onClick={() => handleStatusUpdate(order.id, action.status)}
                  >
                    {saving === `order-${order.id}` ? "Saving..." : action.label}
                  </button>
                ) : (
                  <span className="status-card compact-status-card">
                    Delivery complete
                  </span>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

export default DeliveryDashboard;
