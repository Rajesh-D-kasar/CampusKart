import { useEffect, useMemo, useState } from "react";
import { getProducts } from "../api/productApi";
import ProductCard from "../components/ProductCard";
import SearchBar from "../components/SearchBar";
import { useCart } from "../context/CartContext";

function Products() {
  const [products, setProducts] = useState([]);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("loading");
  const { addItem } = useCart();

  useEffect(() => {
    let active = true;

    getProducts()
      .then((data) => {
        if (active) {
          setProducts(data);
          setStatus("ready");
        }
      })
      .catch(() => {
        if (active) {
          setStatus("error");
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const filteredProducts = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) return products;

    return products.filter((product) =>
      `${product.name} ${product.category}`
        .toLowerCase()
        .includes(normalizedQuery)
    );
  }, [products, query]);

  return (
    <section className="container page-section">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Campus store</span>
          <h1>Products</h1>
        </div>
        <SearchBar value={query} onChange={setQuery} />
      </div>

      {status === "loading" && <p className="status-card">Loading products...</p>}
      {status === "error" && (
        <div className="status-card error-card">
          <h2>Products could not be loaded</h2>
          <p>Start the FastAPI backend on port 8000 and refresh this page.</p>
        </div>
      )}
      {status === "ready" && filteredProducts.length === 0 && (
        <p className="status-card">No products match "{query}".</p>
      )}
      {status === "ready" && filteredProducts.length > 0 && (
        <div className="product-grid">
          {filteredProducts.map((product) => (
            <ProductCard key={product.id} product={product} onAdd={addItem} />
          ))}
        </div>
      )}
    </section>
  );
}

export default Products;
