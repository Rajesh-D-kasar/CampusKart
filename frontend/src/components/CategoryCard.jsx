
import { Link } from "react-router-dom";

const CATEGORY_ICONS = {
  fruits: "\u{1F34E}",
  vegetables: "\u{1F955}",
  "dairy-eggs": "\u{1F95B}",
  beverages: "\u{1F964}",
  pantry: "\u{1F35A}",
  "meat-seafood": "\u{1F357}",
  "frozen-desserts": "\u{1F368}",
  "pet-care": "\u{1F43E}",
  household: "\u{1F9FB}",
  "health-nutrition": "\u{1F4AA}",
};

function CategoryCard({ category, active = false, compact = false, onSelect }) {
  const className = [
    "category-card",
    active ? "is-active" : "",
    compact ? "is-compact" : "",
  ]
    .filter(Boolean)
    .join(" ");
  const icon = CATEGORY_ICONS[category.slug] || "\u{1F6D2}";
  const content = (
    <>
      <span className="category-card-icon" aria-hidden="true">
        {category.image_url ? <img src={category.image_url} alt="" /> : icon}
      </span>
      <span>
        <strong>{category.name}</strong>
        <small>{category.product_count} items</small>
      </span>
    </>
  );

  if (onSelect) {
    return (
      <button className={className} type="button" onClick={() => onSelect(category)}>
        {content}
      </button>
    );
  }

  return (
    <Link className={className} to={`/products?category=${category.slug}`}>
      {content}
    </Link>
  );
}

export default CategoryCard;
