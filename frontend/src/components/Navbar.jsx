import { NavLink } from "react-router-dom";
import { useCart } from "../context/CartContext";

function Navbar() {
  const { itemCount } = useCart();
  const navClassName = ({ isActive }) => (isActive ? "active" : undefined);

  return (
    <header className="site-header">
      <nav className="navbar container" aria-label="Main navigation">
        <NavLink className="brand" to="/">
          Campus<span>Kart</span>
        </NavLink>

        <div className="nav-links">
          <NavLink className={navClassName} end to="/">
            Home
          </NavLink>
          <NavLink className={navClassName} to="/products">
            Products
          </NavLink>
          <NavLink className={navClassName} to="/login">
            Login
          </NavLink>
          <NavLink
            className={({ isActive }) =>
              `cart-link${isActive ? " active" : ""}`
            }
            to="/cart"
          >
            Cart <span className="cart-count">{itemCount}</span>
          </NavLink>
        </div>
      </nav>
    </header>
  );
}

export default Navbar;
