import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getWallet } from "../api/walletApi";
import { useAuth } from "../context/AuthContext";
import {
  formatCurrency,
  formatDateTime,
  formatLabel,
} from "../utils/formatters";

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
            "We couldn't load your wallet. Please try again."
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
          <p>Login to see refund credits and wallet history.</p>
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
          <strong>{formatCurrency(wallet.balance)}</strong>
          <p>
            Refunds and paid-order cancellations are recorded here, so your
            credit history stays easy to follow.
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

          {loading && <p className="status-card">Opening your wallet...</p>}

          {!loading && wallet.transactions.length === 0 && (
            <div className="wallet-empty-state">
              <h3>Wallet is quiet for now</h3>
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
                    {formatLabel(transaction.transaction_type)}
                  </span>
                  <h3>{transaction.description}</h3>
                  <p>
                    {formatDateTime(transaction.created_at)}
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
                    +{formatCurrency(transaction.amount)}
                  </strong>
                  <small>
                    Balance {formatCurrency(transaction.balance_after)}
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
