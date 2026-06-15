
function SearchBar({ value, onChange }) {
  return (
    <label className="search-bar">
      <span className="sr-only">Search products</span>
      <input
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Search groceries and essentials"
      />
    </label>
  );
}

export default SearchBar;
