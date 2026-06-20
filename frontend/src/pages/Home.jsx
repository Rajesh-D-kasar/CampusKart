import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getOffers } from "../api/offerApi";
import { getCategories } from "../api/productApi";
import CategoryCard from "../components/CategoryCard";
import ProductCard from "../components/ProductCard";
import { useCart } from "../context/CartContext";

function Home() {
  const [categories, setCategories] = useState([]);
  const [offers, setOffers] = useState(null);
  const { addItem } = useCart();

  useEffect(() => {
    let active = true;

    Promise.all([getCategories(), getOffers()])
      .then(([categoryData, offerData]) => {
        if (active) {
          setCategories(categoryData.slice(0, 8));
          setOffers(offerData);
        }
      })
      .catch(() => {
        if (active) {
          setCategories([]);
          setOffers(null);
        }
      });

    return () => {
      active = false;
    };
  }, []);

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

      {offers?.banners?.length > 0 && (
        <section className="container promo-grid" aria-label="Promotions">
          {offers.banners.map((banner) => (
            <article className={`promo-card promo-${banner.tone}`} key={banner.id}>
              <div>
                <span className="eyebrow">Limited offer</span>
                <h2>{banner.title}</h2>
                <p>{banner.subtitle}</p>
              </div>
              <Link className="button button-secondary" to={banner.cta_href}>
                {banner.cta_label}
              </Link>
            </article>
          ))}
        </section>
      )}

      <section className="container feature-grid" aria-label="Store benefits">
        <article>
          <span aria-hidden="true">{"\u26A1"}</span>
          <h2>Quick delivery</h2>
          <p>Built for busy campus schedules.</p>
        </article>
        <article>
          <span aria-hidden="true">{"\u{1F6D2}"}</span>
          <h2>Daily essentials</h2>
          <p>Useful products without the long search.</p>
        </article>
        <article>
          <span aria-hidden="true">{"\u{1F49A}"}</span>
          <h2>Simple checkout</h2>
          <p>A clear cart with instant totals.</p>
        </article>
      </section>

      {offers?.coupons?.length > 0 && (
        <section className="container home-section">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Coupons</span>
              <h2>Apply savings at checkout</h2>
            </div>
            <Link to="/cart" className="text-link">
              Use coupons
            </Link>
          </div>
          <div className="coupon-grid">
            {offers.coupons.map((coupon) => (
              <article className="coupon-card" key={coupon.code}>
                <span>{coupon.code}</span>
                <strong>{coupon.title}</strong>
                <p>{coupon.description}</p>
              </article>
            ))}
          </div>
        </section>
      )}

      {categories.length > 0 && (
        <section className="container home-section">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Shop by aisle</span>
              <h2>Fresh categories for quick orders</h2>
            </div>
            <Link to="/products" className="text-link">
              View all products
            </Link>
          </div>
          <div className="category-grid">
            {categories.map((category) => (
              <CategoryCard key={category.slug} category={category} />
            ))}
          </div>
        </section>
      )}

      {offers?.collections?.map((collection) => (
        <section className="container home-section" key={collection.key}>
          <div className="section-heading">
            <div>
              <span className="eyebrow">Smart basket</span>
              <h2>{collection.title}</h2>
              <p>{collection.description}</p>
            </div>
            <Link
              to={
                collection.key === "top-discounts"
                  ? "/products?sort=discount"
                  : "/products"
              }
              className="text-link"
            >
              See more
            </Link>
          </div>
          <div className="product-grid">
            {collection.products.map((product) => (
              <ProductCard key={product.id} product={product} onAdd={addItem} />
            ))}
          </div>
        </section>
      ))}
    </>
  );
}

export default Home;
