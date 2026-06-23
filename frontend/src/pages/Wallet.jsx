import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getWallet } from "../api/walletApi";
import { useAuth } from "../context/AuthContext";

const currencyFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});

function formatDate(dateValue) {
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(dateValue));
}

function formatTransactionType(type) {
  return type.replaceAll("_", " ");
}

function Wallet() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [wallet, setWallet] = useState({ balance: 0, transactions: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated) return;

    const loadWallet = async () => {
      setLoading(true);
      setError("");
      try {
        const walletData = await getWallet();
        setWallet(walletData);
      } catch (walletError) {
        setError(
          walletError.response?.data?.detail ||
            "Could not load your wallet right now."
        );
      } finally {
        setLoading(false);
      }
    };

    loadWallet();
  }, [isAuthenticated]);

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
          <p>Please login to view refund credits and wallet history.</p>
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
          <span className="eyebrow">Refund credits</span>
          <h1>Wallet</h1>
        </div>
        <Link className="button button-secondary" to="/orders">
          View orders
        </Link>
      </div>

      {error && <p className="form-error">{error}</p>}

      <div className="wallet-layout">
        <aside className="wallet-balance-card">
          <span>Available balance</span>
          <strong>{currencyFormatter.format(wallet.balance)}</strong>
          <p>
            Paid order cancellations and Razorpay refunds are recorded here as
            customer wallet credits for clear tracking.
          </p>
          <Link className="button" to="/products">
            Shop with CampusKart
          </Link>
        </aside>

        <section className="wallet-history-card">
          <div className="admin-section-heading">
            <div>
              <span className="eyebrow">Latest activity</span>
              <h2>Wallet history</h2>
            </div>
            <small>Last 50 transactions</small>
          </div>

          {loading && <p className="status-card">Loading wallet...</p>}

          {!loading && wallet.transactions.length === 0 && (
            <div className="wallet-empty-state">
              <h3>No wallet activity yet</h3>
              <p>
                Refund credits will appear here after a paid order is cancelled
                or refunded.
              </p>
            </div>
          )}

          <div className="wallet-transaction-list">
            {wallet.transactions.map((transaction) => (
              <article className="wallet-transaction-card" key={transaction.id}>
                <div>
                  <span className="status-chip">
                    {formatTransactionType(transaction.transaction_type)}
                  </span>
                  <h3>{transaction.description}</h3>
                  <p>
                    {formatDate(transaction.created_at)}
                    {transaction.order_number && (
                      <>
                        {" "}
                        - Order{" "}
                        <Link to={`/orders/${transaction.order_id}`}>
                          #{transaction.order_number}
                        </Link>
                      </>
                    )}
                  </p>
                </div>
                <div className="wallet-transaction-meta">
                  <strong>
                    +{currencyFormatter.format(transaction.amount)}
                  </strong>
                  <small>
                    Balance {currencyFormatter.format(transaction.balance_after)}
                  </small>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </section>
  );
}

export default Wallet;
