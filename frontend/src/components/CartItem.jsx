function CartItem({ item, onQuantityChange, onRemove }) {
  return (
    <article className="cart-item">
      <div className="cart-item-icon" aria-hidden="true">
        {item.image_url ? <img src={item.image_url} alt="" /> : item.icon}
      </div>
      <div className="cart-item-details">
        <h3>{item.name}</h3>
        <p>{item.unit}</p>
        <strong>
          {"\u20B9"}
          {item.price}
        </strong>
      </div>
      <div className="quantity-control" aria-label={`Quantity for ${item.name}`}>
        <button
          aria-label={`Remove one ${item.name}`}
          onClick={() => onQuantityChange(item.id, item.quantity - 1)}
        >
          -
        </button>
        <span>{item.quantity}</span>
        <button
          aria-label={`Add one ${item.name}`}
          onClick={() => onQuantityChange(item.id, item.quantity + 1)}
        >
          +
        </button>
      </div>
      <strong className="line-total">
        {"\u20B9"}
        {item.price * item.quantity}
      </strong>
      <button className="remove-button" onClick={() => onRemove(item.id)}>
        Remove
      </button>
    </article>
  );
}

export default CartItem;
