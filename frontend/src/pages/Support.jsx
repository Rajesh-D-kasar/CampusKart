import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { createSupportTicket, getSupportTickets } from "../api/supportApi";
import { useAuth } from "../context/AuthContext";

function formatStatus(value) {
  return String(value || "").replaceAll("_", " ");
}

function Support() {
  const { isAuthenticated } = useAuth();
  const [searchParams] = useSearchParams();
  const orderId = searchParams.get("orderId");
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(isAuthenticated);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [form, setForm] = useState({
    category: "order",
    subject: orderId ? `Help with order #${orderId}` : "",
    message: "",
  });

  const canSubmit = useMemo(
    () => form.subject.trim().length >= 3 && form.message.trim().length >= 10,
    [form]
  );

  useEffect(() => {
    if (!isAuthenticated) return;
    setLoading(true);
    getSupportTickets()
      .then(setTickets)
      .catch((supportError) => {
        setError(
          supportError.response?.data?.detail || "Could not load support tickets."
        );
      })
      .finally(() => setLoading(false));
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <section className="container page-section">
        <div className="status-card">
          <h1>Login needed</h1>
          <p>Support ticket create karne ke liye pehle login karo.</p>
          <Link className="button" to="/login">
            Login
          </Link>
        </div>
      </section>
    );
  }

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    try {
      const ticket = await createSupportTicket({
        audience: "customer",
        category: form.category,
        subject: form.subject.trim(),
        message: form.message.trim(),
        order_id: orderId ? Number(orderId) : null,
      });
      setTickets((currentTickets) => [ticket, ...currentTickets]);
      setForm({ category: "order", subject: "", message: "" });
      setSuccess("Support ticket create ho gaya. Team jaldi update karegi.");
    } catch (supportError) {
      setError(
        supportError.response?.data?.detail || "Could not create support ticket."
      );
    }
  };

  return (
    <section className="container page-section">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Help center</span>
          <h1>Customer support</h1>
          <p>
            Order, payment, delivery OTP, refund ya account issue yahin raise
            karo.
          </p>
        </div>
      </div>

      <div className="support-layout">
        <form className="checkout-card support-form-card" onSubmit={handleSubmit}>
          <h2>Create ticket</h2>
          {error && <p className="form-error">{error}</p>}
          {success && <p className="form-success">{success}</p>}
          <label>
            Issue type
            <select
              value={form.category}
              onChange={(event) =>
                setForm((current) => ({ ...current, category: event.target.value }))
              }
            >
              <option value="order">Order</option>
              <option value="payment">Payment/refund</option>
              <option value="delivery">Delivery/OTP</option>
              <option value="account">Account</option>
              <option value="other">Other</option>
            </select>
          </label>
          <label>
            Subject
            <input
              value={form.subject}
              onChange={(event) =>
                setForm((current) => ({ ...current, subject: event.target.value }))
              }
              placeholder="Example: Delivery OTP issue"
              required
            />
          </label>
          <label>
            Message
            <textarea
              value={form.message}
              onChange={(event) =>
                setForm((current) => ({ ...current, message: event.target.value }))
              }
              placeholder="Problem detail me likho..."
              required
            />
          </label>
          <button className="button checkout-button" disabled={!canSubmit}>
            Submit ticket
          </button>
        </form>

        <section className="checkout-card support-ticket-list">
          <h2>Your tickets</h2>
          {loading ? (
            <p>Loading support tickets...</p>
          ) : tickets.length === 0 ? (
            <p>Abhi koi ticket nahi hai.</p>
          ) : (
            tickets.map((ticket) => (
              <article className="support-ticket-row" key={ticket.id}>
                <div>
                  <span className="eyebrow">
                    #{ticket.id} - {ticket.category}
                  </span>
                  <strong>{ticket.subject}</strong>
                  <p>{ticket.message}</p>
                  {ticket.resolution && <small>{ticket.resolution}</small>}
                </div>
                <span className={`status-chip status-${ticket.status}`}>
                  {formatStatus(ticket.status)}
                </span>
              </article>
            ))
          )}
        </section>
      </div>
    </section>
  );
}

export default Support;
