function formatPrice(value) {
  return Number(value).toLocaleString("en-IN", {
    maximumFractionDigits: 0,
  });
}

function ProductCard({ product, onAdd }) {
  const hasDiscount = product.discount_percent > 0;
  const stockCopy =
    product.stock_quantity <= 0
      ? "Out of stock"
      : product.stock_quantity <= 8
        ? `Only ${product.stock_quantity} left`
        : "In stock";

  return (
    <article className="product-card">
      {hasDiscount && (
        <span className="discount-badge">{product.discount_percent}% off</span>
      )}
      <div className="product-icon" aria-hidden="true">
        {product.image_url ? (
          <img src={product.image_url} alt="" loading="lazy" />
        ) : (
          product.icon
        )}
      </div>
      <span className="product-category">{product.category}</span>
      <h3>{product.name}</h3>
      <p className="product-unit">{product.unit}</p>
      <p className={product.in_stock ? "stock-copy" : "stock-copy is-empty"}>
        {stockCopy}
      </p>
      <div className="product-card-footer">
        <div className="price-stack">
          <strong>
            {"\u20B9"}
            {formatPrice(product.price)}
          </strong>
          {hasDiscount && (
            <span>
              {"\u20B9"}
              {formatPrice(product.mrp)}
            </span>
          )}
        </div>
        <button
          className="button button-small"
          disabled={!product.in_stock}
          onClick={() => onAdd(product)}
        >
          {product.in_stock ? "Add" : "Out"}
        </button>
      </div>
    </article>
  );
}

export default ProductCard;
