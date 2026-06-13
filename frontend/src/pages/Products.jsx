import Navbar from "../components/Navbar";
import ProductCard from "../components/ProductCard";
import Footer from "../components/Footer";

function Products() {
  return (
    <div>
      <Navbar />

      <h2>Products</h2>

      <ProductCard name="Maggi" price={15} image="https://via.placeholder.com/120" />
      <ProductCard name="Milk" price={60} image="https://via.placeholder.com/120" />
      <ProductCard name="Bread" price={40} image="https://via.placeholder.com/120" />

      <Footer />
    </div>
  );
}

export default Products;
