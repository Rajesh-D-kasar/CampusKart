import { Link } from "react-router-dom";

function Home() {
  return (
    <>
      <section className="hero">
        <div className="container hero-content">
          <span className="eyebrow">Fast campus delivery</span>
          <h1>Groceries at your door, before your next class.</h1>
          <p>
            Shop snacks, breakfast staples, beverages, and daily essentials
            from one simple store.
          </p>
          <div className="hero-actions">
            <Link className="button" to="/products">
              Start shopping
            </Link>
            <Link className="button button-secondary" to="/cart">
              View cart
            </Link>
          </div>
        </div>
      </section>

      <section className="container feature-grid" aria-label="Store benefits">
        <article>
          <span aria-hidden="true">⚡</span>
          <h2>Quick delivery</h2>
          <p>Built for busy campus schedules.</p>
        </article>
        <article>
          <span aria-hidden="true">🛒</span>
          <h2>Daily essentials</h2>
          <p>Useful products without the long search.</p>
        </article>
        <article>
          <span aria-hidden="true">💚</span>
          <h2>Simple checkout</h2>
          <p>A clear cart with instant totals.</p>
        </article>
      </section>
    </>
  );
}

export default Home;
