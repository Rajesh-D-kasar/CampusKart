import { useEffect, useState } from "react";
import { getProductSuggestions } from "../api/productApi";

function SearchBar({ value, onChange, onSelect }) {
  const [suggestions, setSuggestions] = useState([]);
  const [focused, setFocused] = useState(false);

  useEffect(() => {
    if (!focused) return undefined;

    const timeout = window.setTimeout(() => {
      getProductSuggestions(value.trim())
        .then(setSuggestions)
        .catch(() => setSuggestions([]));
    }, value.trim() ? 180 : 0);

    return () => window.clearTimeout(timeout);
  }, [focused, value]);

  const handleSelect = (suggestion) => {
    setFocused(false);
    setSuggestions([]);
    if (onSelect) {
      onSelect(suggestion);
      return;
    }
    onChange(suggestion.value);
  };

  return (
    <label className="search-bar">
      <span className="sr-only">Search products</span>
      <input
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => window.setTimeout(() => setFocused(false), 120)}
        placeholder="Search groceries and essentials"
      />
      {focused && suggestions.length > 0 && (
        <div className="search-suggestions">
          {suggestions.map((suggestion) => (
            <button
              key={`${suggestion.type}-${suggestion.href}`}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => handleSelect(suggestion)}
              type="button"
            >
              <span>{suggestion.type === "category" ? "Category" : "Product"}</span>
              <strong>{suggestion.label}</strong>
            </button>
          ))}
        </div>
      )}
    </label>
  );
}

export default SearchBar;
