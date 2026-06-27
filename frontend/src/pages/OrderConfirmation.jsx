import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import {
  cancelOrder,
  getOrder,
  getOrderInvoice,
  submitOrderReview,
} from "../api/orderApi";
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
  return `${order.eta_minutes} min`;
}

const REVIEW_TAGS = [
  ["fresh", "Fresh items"],
  ["fast_delivery", "Fast delivery"],
  ["polite_partner", "Polite partner"],
  ["good_packing", "Good packing"],
  ["missing_item", "Missing item"],
  ["late_delivery", "Late delivery"],
];

const DEFAULT_REVIEW_FORM = {
  overall_rating: 5,
  product_rating: 5,
  delivery_rating: 5,
  seller_rating: 5,
  comment: "",
  issue_tags: [],
};

function OrderConfirmation() {
  const { orderId } = useParams();
  const location = useLocation();
  const [order, setOrder] = useState(location.state?.order || null);
  const [loading, setLoading] = useState(!location.state?.order);
  const [error, setError] = useState("");
  const [invoice, setInvoice] = useState(null);
  const [actionError, setActionError] = useState("");
  const [reviewForm, setReviewForm] = useState(DEFAULT_REVIEW_FORM);
  const [reviewSaving, setReviewSaving] = useState(false);
  const [reviewMessage, setReviewMessage] = useState("");

  useEffect(() => {
    if (order) return;

    const loadOrder = async () => {
      setLoading(true);
      setError("");
      try {
        setOrder(await getOrder(orderId));
      } catch (orderError) {
        setError(orderError.response?.data?.detail || "We could not load this order.");
      } finally {
        setLoading(false);
      }
    };

    loadOrder();
  }, [order, orderId]);

  useEffect(() => {
    if (!order?.review) return;
    setReviewForm({
      overall_rating: order.review.overall_rating,
      product_rating: order.review.product_rating,
      delivery_rating: order.review.delivery_rating,
      seller_rating: order.review.seller_rating,
      comment: order.review.comment || "",
      issue_tags: order.review.issue_tags || [],
    });
  }, [order?.review]);

  if (loading) {
    return (
      <section className="container page-section">
        <p className="status-card">Getting your order ready...</p>
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
  const lifecycleEvents = order.lifecycle_events || [];
  const partner = order.delivery_partner;
  const canCancel = ["placed", "confirmed", "packing"].includes(order.status);
  const canReview = order.status === "delivered";

  const handleCancel = async () => {
    const reason = window.prompt("Cancel reason likho:", "Ordered by mistake");
    if (reason === null) return;
    setActionError("");
    try {
      setOrder(await cancelOrder(order.id, reason.trim()));
    } catch (cancelError) {
      setActionError(
        cancelError.response?.data?.detail || "We could not cancel this order."
      );
    }
  };

  const handleInvoice = async () => {
    setActionError("");
    try {
      setInvoice(await getOrderInvoice(order.id));
    } catch (invoiceError) {
      setActionError(
        invoiceError.response?.data?.detail || "We could not load this invoice."
      );
    }
  };

  const handleRatingChange = (field, value) => {
    setReviewForm((current) => ({
      ...current,
      [field]: Number(value),
    }));
  };

  const toggleReviewTag = (tag) => {
    setReviewForm((current) => ({
      ...current,
      issue_tags: current.issue_tags.includes(tag)
        ? current.issue_tags.filter((item) => item !== tag)
        : [...current.issue_tags, tag],
    }));
  };

  const handleReviewSubmit = async (event) => {
    event.preventDefault();
    setActionError("");
    setReviewMessage("");
    setReviewSaving(true);
    try {
      const review = await submitOrderReview(order.id, reviewForm);
      setOrder((current) => ({ ...current, review }));
      setReviewMessage("Thanks! Review save ho gaya.");
    } catch (reviewError) {
      setActionError(
        reviewError.response?.data?.detail || "We could not save your review."
      );
    } finally {
      setReviewSaving(false);
    }
  };

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
            <strong>{formatLabel(order.status)}</strong>
            <small>{formatDateTime(order.updated_at)}</small>
          </article>
          {order.delivery_location && (
            <article>
              <span>Last rider location</span>
              <strong>{formatDateTime(order.delivery_location.created_at)}</strong>
              <a
                href={`https://www.google.com/maps/search/?api=1&query=${order.delivery_location.latitude},${order.delivery_location.longitude}`}
                rel="noreferrer"
                target="_blank"
              >
                Open map
              </a>
            </article>
          )}
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
                  {item.fulfillment_status !== "pending" && (
                    <small>
                      {formatLabel(item.fulfillment_status)}
                      {item.substitution_note ? ` - ${item.substitution_note}` : ""}
                    </small>
                  )}
                </div>
                <strong>
                  {formatCurrency(item.line_total)}
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
            <strong>{formatLabel(order.status)}</strong>
          </div>
          <div>
            <span>Payment</span>
            <strong>{formatPaymentMethod(order.payment_method)}</strong>
          </div>
          <div>
            <span>Payment status</span>
            <strong>{formatLabel(order.payment_status)}</strong>
          </div>
          <div>
            <span>Subtotal</span>
            <strong>
              {formatCurrency(order.subtotal)}
            </strong>
          </div>
          <div>
            <span>Delivery</span>
            <strong>
              {order.delivery_fee === 0 ? "Free" : formatCurrency(order.delivery_fee)}
            </strong>
          </div>
          <div className="summary-total">
            <span>Total</span>
            <strong>
              {formatCurrency(order.total)}
            </strong>
          </div>
          <Link className="button checkout-button" to="/products">
            Continue shopping
          </Link>
          <Link className="button button-secondary checkout-button" to="/orders">
            View all orders
          </Link>
          <Link
            className="button button-secondary checkout-button"
            to={`/support?orderId=${order.id}`}
          >
            Need help?
          </Link>
          <button
            className="button button-secondary checkout-button"
            type="button"
            onClick={handleInvoice}
          >
            View invoice
          </button>
          {canCancel && (
            <button
              className="button button-secondary checkout-button"
              type="button"
              onClick={handleCancel}
            >
              Cancel order
            </button>
          )}
          {actionError && <p className="form-error">{actionError}</p>}
        </aside>
      </div>

      {invoice && (
        <section className="checkout-card invoice-card">
          <h2>Invoice {invoice.invoice_number}</h2>
          <p>
            {invoice.customer_name} - {formatPaymentMethod(invoice.payment_method)}
          </p>
          <div className="invoice-grid">
            <span>Subtotal</span>
            <strong>
              {formatCurrency(invoice.subtotal)}
            </strong>
            <span>Delivery</span>
            <strong>
              {formatCurrency(invoice.delivery_fee)}
            </strong>
            <span>Total</span>
            <strong>
              {formatCurrency(invoice.total)}
            </strong>
          </div>
        </section>
      )}

      {canReview && (
        <section className="checkout-card review-card">
          <div className="section-heading review-heading">
            <div>
              <span className="eyebrow">Order feedback</span>
              <h2>{order.review ? "Update your review" : "Rate your order"}</h2>
              <p>Delivery ke baad quick feedback do, taaki service better ho.</p>
            </div>
            {order.review && (
              <span className="status-chip">
                Rated {order.review.overall_rating}/5
              </span>
            )}
          </div>
          <form className="review-form" onSubmit={handleReviewSubmit}>
            {[
              ["overall_rating", "Overall"],
              ["product_rating", "Products"],
              ["delivery_rating", "Delivery"],
              ["seller_rating", "Seller"],
            ].map(([field, label]) => (
              <label key={field}>
                {label}
                <select
                  value={reviewForm[field]}
                  onChange={(event) => handleRatingChange(field, event.target.value)}
                >
                  {[5, 4, 3, 2, 1].map((rating) => (
                    <option key={rating} value={rating}>
                      {rating} star{rating === 1 ? "" : "s"}
                    </option>
                  ))}
                </select>
              </label>
            ))}
            <label className="review-comment">
              Comment
              <textarea
                maxLength={500}
                placeholder="Freshness, packing, delivery experience..."
                value={reviewForm.comment}
                onChange={(event) =>
                  setReviewForm((current) => ({
                    ...current,
                    comment: event.target.value,
                  }))
                }
              />
            </label>
            <div className="review-tags">
              {REVIEW_TAGS.map(([tag, label]) => (
                <button
                  className={reviewForm.issue_tags.includes(tag) ? "is-active" : ""}
                  key={tag}
                  onClick={() => toggleReviewTag(tag)}
                  type="button"
                >
                  {label}
                </button>
              ))}
            </div>
            <button className="button" disabled={reviewSaving} type="submit">
              {reviewSaving ? "Saving..." : order.review ? "Update review" : "Submit review"}
            </button>
            {reviewMessage && <p className="form-success">{reviewMessage}</p>}
          </form>
        </section>
      )}

      <section className="checkout-card tracking-card">
        <h2>Order tracking</h2>
        {lifecycleEvents.length > 0 && (
          <div className="lifecycle-grid">
            {lifecycleEvents.map((event) => (
              <article
                className={event.completed ? "is-complete" : ""}
                key={event.key}
              >
                <span>{event.completed ? "\u2713" : ""}</span>
                <strong>{event.label}</strong>
                <p>{event.description}</p>
                <small>{formatDateTime(event.timestamp)}</small>
              </article>
            ))}
          </div>
        )}
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
