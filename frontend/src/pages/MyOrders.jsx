import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getNotifications, markNotificationRead } from "../api/notificationApi";
import { getOrders } from "../api/orderApi";
import { useAuth } from "../context/AuthContext";
import {
  formatCurrency,
  formatDateTime,
  formatLabel,
  formatPaymentMethod,
} from "../utils/formatters";

function formatEta(order) {
  if (order.status === "cancelled") return "Cancelled";
  if (order.status === "delivered") return "Delivered";
  if (order.eta_minutes == null) return "Updating";
  return `${order.eta_minutes} min ETA`;
}

function MyOrders() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [orders, setOrders] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated) return;

    const loadOrders = async () => {
      setLoading(true);
      setError("");
      try {
        const [orderList, notificationList] = await Promise.all([
          getOrders(),
          getNotifications(),
        ]);
        setOrders(orderList);
        setNotifications(notificationList);
      } catch (orderError) {
        setError(
          orderError.response?.data?.detail ||
            "We couldn't load your orders. Please try again."
        );
      } finally {
        setLoading(false);
      }
    };

    loadOrders();
  }, [isAuthenticated]);

  const handleReadNotification = async (notificationId) => {
    try {
      const notification = await markNotificationRead(notificationId);
      setNotifications((current) =>
        current.map((item) => (item.id === notificationId ? notification : item))
      );
    } catch {
      // A missed read receipt should not block the orders page.
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
          <p>Login to see your orders, invoices, and delivery updates.</p>
          <Link className="button" to="/login">
            Login to continue
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="container page-section">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Track your orders</span>
          <h1>My orders</h1>
        </div>
        <Link className="button button-secondary" to="/products">
          Shop more
        </Link>
      </div>

      {loading && <p className="status-card">Bringing up your orders...</p>}
      {error && <p className="form-error">{error}</p>}

      {notifications.length > 0 && (
        <section className="notification-strip">
          {notifications.slice(0, 3).map((notification) => (
            <article
              className={notification.is_read ? "is-read" : ""}
              key={notification.id}
            >
              <div>
                <strong>{notification.title}</strong>
                <p>{notification.message}</p>
              </div>
              {!notification.is_read && (
                <button
                  className="button button-small"
                  type="button"
                  onClick={() => handleReadNotification(notification.id)}
                >
                  Mark read
                </button>
              )}
            </article>
          ))}
        </section>
      )}

      {!loading && !error && orders.length === 0 && (
        <div className="empty-state orders-empty-state">
          <span aria-hidden="true">{"\u{1F9FE}"}</span>
          <h1>Your first order is waiting</h1>
          <p>Once you place an order, tracking and invoices will show up here.</p>
          <Link className="button" to="/products">
            Browse products
          </Link>
        </div>
      )}

      <div className="orders-list">
        {orders.map((order) => (
          <article className="order-card" key={order.id}>
            <div>
              <span className="order-card-label">Order #{order.order_number}</span>
              <h2>{formatCurrency(order.total)}</h2>
              <p>
                {order.item_count} item{order.item_count === 1 ? "" : "s"} -
                placed {formatDateTime(order.created_at)}
              </p>
              <p className="order-tracking-copy">{order.tracking_message}</p>
            </div>
            <div className="order-card-meta">
              <span className={`status-pill status-${order.status}`}>
                {formatLabel(order.status)}
              </span>
              <small>{formatEta(order)}</small>
              {order.delivery_partner && (
                <small>{order.delivery_partner.name}</small>
              )}
              {order.status === "delivered" && (
                <small>
                  {order.review
                    ? `Rated ${order.review.overall_rating}/5`
                    : "Ready for your review"}
                </small>
              )}
              <small>{formatPaymentMethod(order.payment_method)}</small>
              <Link className="button button-small" to={`/orders/${order.id}`}>
                View details
              </Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export default MyOrders;
