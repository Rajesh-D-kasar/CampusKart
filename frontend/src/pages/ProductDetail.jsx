import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  getProduct,
  getProductRecommendations,
} from "../api/productApi";
import ProductCard from "../components/ProductCard";
import { useCart } from "../context/CartContext";

function formatPrice(value) {
  return Number(value).toLocaleString("en-IN", {
    maximumFractionDigits: 0,
  });
}

function ProductDetail() {
  const { productId } = useParams();
  const [product, setProduct] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [status, setStatus] = useState("loading");
  const [added, setAdded] = useState(false);
  const { addItem } = useCart();

  useEffect(() => {
    let active = true;
    setStatus("loading");
    setAdded(false);

    Promise.all([
      getProduct(productId),
      getProductRecommendations(productId).catch(() => []),
    ])
      .then(([productData, recommendationData]) => {
        if (!active) return;
        setProduct(productData);
        setRecommendations(recommendationData);
        setStatus("ready");
      })
      .catch(() => {
        if (active) {
          setStatus("error");
        }
      });

    return () => {
      active = false;
    };
  }, [productId]);

  const savings = useMemo(() => {
    if (!product || product.mrp <= product.price) return 0;
    return product.mrp - product.price;
  }, [product]);

  const stockCopy =
    product?.stock_quantity <= 0
      ? "Currently out of stock"
      : product?.stock_quantity <= 8
        ? `Only ${product.stock_quantity} left`
        : "In stock and ready";

  const handleAdd = async () => {
    if (!product?.in_stock) return;
    await addItem(product);
    setAdded(true);
    window.setTimeout(() => setAdded(false), 1600);
  };

  if (status === "loading") {
    return (
      <section className="container page-section">
        <p className="status-card">Fetching product details...</p>
      </section>
    );
  }

  if (status === "error" || !product) {
    return (
      <section className="container page-section">
        <div className="status-card error-card">
          <h1>Product nahi mila</h1>
          <p>This item may be unavailable at the moment.</p>
          <Link className="button" to="/products">
            Back to products
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="container page-section">
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link to="/products">Products</Link>
        <span>/</span>
        <Link to={`/products?category=${product.category_slug}`}>
          {product.category}
        </Link>
        <span>/</span>
        <strong>{product.name}</strong>
      </nav>

      <article className="product-detail-hero">
        <div className="product-detail-media" aria-hidden="true">
          {product.discount_percent > 0 && (
            <span className="discount-badge">
              {product.discount_percent}% off
            </span>
          )}
          {product.image_url ? (
            <img src={product.image_url} alt="" />
          ) : (
            <span>{product.icon}</span>
          )}
        </div>

        <div className="product-detail-copy">
          <span className="eyebrow">{product.category}</span>
          <h1>{product.name}</h1>
          <p>{product.description || "Fresh daily essential for quick orders."}</p>

          <div className="product-detail-price-row">
            <strong>
              {"\u20B9"}
              {formatPrice(product.price)}
            </strong>
            {product.discount_percent > 0 && (
              <>
                <span>
                  {"\u20B9"}
                  {formatPrice(product.mrp)}
                </span>
                <em>
                  Save {"\u20B9"}
                  {formatPrice(savings)}
                </em>
              </>
            )}
          </div>

          <div className="product-detail-actions">
            <button
              className="button"
              disabled={!product.in_stock}
              onClick={handleAdd}
              type="button"
            >
              {added ? "Added to cart" : product.in_stock ? "Add to cart" : "Out of stock"}
            </button>
            <Link className="button button-secondary" to="/cart">
              View cart
            </Link>
          </div>

          <div className="product-detail-facts">
            <article>
              <span>Pack size</span>
              <strong>{product.unit}</strong>
            </article>
            <article>
              <span>Availability</span>
              <strong>{stockCopy}</strong>
            </article>
            <article>
              <span>Delivery</span>
              <strong>10-20 min estimate</strong>
            </article>
          </div>
        </div>
      </article>

      {recommendations.length > 0 && (
        <section className="home-section product-recommendations">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Recommended</span>
              <h2>Customers also add</h2>
              <p>Related products and smart basket fillers for this item.</p>
            </div>
            <Link
              className="text-link"
              to={`/products?category=${product.category_slug}`}
            >
              More in {product.category}
            </Link>
          </div>
          <div className="product-grid">
            {recommendations.map((item) => (
              <ProductCard key={item.id} product={item} onAdd={addItem} />
            ))}
          </div>
        </section>
      )}
    </section>
  );
}

export default ProductDetail;
