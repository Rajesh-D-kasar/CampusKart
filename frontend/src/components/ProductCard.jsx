function ProductCard({ product, onAdd }) {
  return (
    <article className="product-card">
      <div className="product-icon" aria-hidden="true">
        {product.icon}
      </div>
      <span className="product-category">{product.category}</span>
      <h3>{product.name}</h3>
      <p className="product-unit">{product.unit}</p>
      <div className="product-card-footer">
        <strong>₹{product.price}</strong>
        <button className="button button-small" onClick={() => onAdd(product)}>
          Add
        </button>
      </div>
    </article>
  );
}

export default ProductCard;
