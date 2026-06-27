import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getCategories, getProducts } from "../api/productApi";
import CategoryCard from "../components/CategoryCard";
import ProductCard from "../components/ProductCard";
import SearchBar from "../components/SearchBar";
import { useCart } from "../context/CartContext";

function Products() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [query, setQuery] = useState(searchParams.get("search") || "");
  const [selectedCategory, setSelectedCategory] = useState(
    searchParams.get("category") || ""
  );
  const [sort, setSort] = useState(searchParams.get("sort") || "name");
  const [showInStockOnly, setShowInStockOnly] = useState(false);
  const [status, setStatus] = useState("loading");
  const { addItem } = useCart();
  const navigate = useNavigate();

  useEffect(() => {
    let active = true;

    getCategories()
      .then((data) => {
        if (active) {
          setCategories(data);
        }
      })
      .catch(() => {
        if (active) {
          setCategories([]);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    const params = {};

    if (query.trim()) {
      params.search = query.trim();
    }
    if (selectedCategory) {
      params.category = selectedCategory;
    }
    if (sort !== "name") {
      params.sort = sort;
    }

    setStatus("loading");

    getProducts(params)
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
  }, [query, selectedCategory, sort]);

  const updateUrl = ({
    queryValue = query,
    categoryValue = selectedCategory,
    sortValue = sort,
  } = {}) => {
    const nextParams = {};

    if (queryValue.trim()) {
      nextParams.search = queryValue.trim();
    }
    if (categoryValue) {
      nextParams.category = categoryValue;
    }
    if (sortValue !== "name") {
      nextParams.sort = sortValue;
    }

    setSearchParams(nextParams);
  };

  const handleQueryChange = (nextQuery) => {
    setQuery(nextQuery);
    updateUrl({ queryValue: nextQuery });
  };

  const handleCategorySelect = (category) => {
    setSelectedCategory(category.slug);
    updateUrl({ categoryValue: category.slug });
  };

  const handleSortChange = (event) => {
    const nextSort = event.target.value;
    setSort(nextSort);
    updateUrl({ sortValue: nextSort });
  };

  const applyQuickFilter = ({ search = "", category = "", nextSort = "name" }) => {
    setQuery(search);
    setSelectedCategory(category);
    setSort(nextSort);
    updateUrl({
      queryValue: search,
      categoryValue: category,
      sortValue: nextSort,
    });
  };

  const handleSuggestionSelect = (suggestion) => {
    if (suggestion.type === "product" && suggestion.product_id) {
      navigate(`/products/${suggestion.product_id}`);
      return;
    }
    setQuery("");
    setSelectedCategory(suggestion.category_slug || "");
    setSort("name");
    updateUrl({
      queryValue: "",
      categoryValue: suggestion.category_slug || "",
      sortValue: "name",
    });
  };

  const visibleProducts = useMemo(() => {
    if (!showInStockOnly) return products;
    return products.filter((product) => product.in_stock);
  }, [products, showInStockOnly]);

  const selectedCategoryName =
    categories.find((category) => category.slug === selectedCategory)?.name ||
    "All products";
  const categoryTotal = categories.reduce(
    (total, category) => total + category.product_count,
    0
  );

  return (
    <section className="container page-section">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Campus store</span>
          <h1>{selectedCategoryName}</h1>
        </div>
        <SearchBar
          value={query}
          onChange={handleQueryChange}
          onSelect={handleSuggestionSelect}
        />
      </div>

      {categories.length > 0 && (
        <div className="category-strip" aria-label="Product categories">
          <CategoryCard
            active={!selectedCategory}
            category={{
              name: "All products",
              slug: "",
              product_count: categoryTotal,
            }}
            compact
            onSelect={handleCategorySelect}
          />
          {categories.map((category) => (
            <CategoryCard
              key={category.slug}
              active={selectedCategory === category.slug}
              category={category}
              compact
              onSelect={handleCategorySelect}
            />
          ))}
        </div>
      )}

      <div className="product-toolbar">
        <p>
          Showing <strong>{visibleProducts.length}</strong> item
          {visibleProducts.length === 1 ? "" : "s"}
        </p>
        <div className="toolbar-actions">
          <label className="checkbox-filter">
            <input
              type="checkbox"
              checked={showInStockOnly}
              onChange={(event) => setShowInStockOnly(event.target.checked)}
            />
            In stock only
          </label>
          <label className="sort-control">
            <span>Sort</span>
            <select value={sort} onChange={handleSortChange}>
              <option value="name">Name</option>
              <option value="price_low">Price: low to high</option>
              <option value="price_high">Price: high to low</option>
              <option value="discount">Top discounts</option>
            </select>
          </label>
        </div>
      </div>

      <div className="quick-filter-row" aria-label="Quick product filters">
        <button
          type="button"
          onClick={() => applyQuickFilter({ nextSort: "discount" })}
        >
          Top discounts
        </button>
        <button
          type="button"
          onClick={() => applyQuickFilter({ search: "milk" })}
        >
          Breakfast
        </button>
        <button
          type="button"
          onClick={() => applyQuickFilter({ category: "beverages" })}
        >
          Drinks
        </button>
        <button
          type="button"
          onClick={() => applyQuickFilter({ category: "pantry" })}
        >
          Pantry staples
        </button>
      </div>

      {status === "loading" && <p className="status-card">Finding fresh picks...</p>}
      {status === "error" && (
        <div className="status-card error-card">
          <h2>Products could not be loaded</h2>
          <p>Start the FastAPI backend on port 8000 and refresh this page.</p>
        </div>
      )}
      {status === "ready" && visibleProducts.length === 0 && (
        <p className="status-card">
          No products match this filter. Try another category or search term.
        </p>
      )}
      {status === "ready" && visibleProducts.length > 0 && (
        <div className="product-grid">
          {visibleProducts.map((product) => (
            <ProductCard key={product.id} product={product} onAdd={addItem} />
          ))}
        </div>
      )}
    </section>
  );
}

export default Products;
