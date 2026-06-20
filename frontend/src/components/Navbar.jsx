import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";

function Navbar() {
  const { itemCount } = useCart();
  const { isAuthenticated, logout, user } = useAuth();
  const deliveryPanelUrl =
    import.meta.env.VITE_DELIVERY_PANEL_URL || "http://127.0.0.1:5174";
  const shopOwnerPanelUrl =
    import.meta.env.VITE_SHOP_OWNER_PANEL_URL || "http://127.0.0.1:5175";
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
          {isAuthenticated ? (
            <>
              <NavLink className={navClassName} to="/orders">
                Orders
              </NavLink>
              {user.role === "admin" && (
                <a href={shopOwnerPanelUrl}>Shop Panel</a>
              )}
              {(user.role === "delivery_partner" || user.role === "admin") && (
                <a href={deliveryPanelUrl}>
                  Delivery
                </a>
              )}
              <span className="nav-user">Hi, {user.full_name.split(" ")[0]}</span>
              <button className="nav-button" onClick={logout}>
                Logout
              </button>
            </>
          ) : (
            <>
              <NavLink className={navClassName} to="/login">
                Login
              </NavLink>
              <NavLink className={navClassName} to="/register">
                Register
              </NavLink>
            </>
          )}
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
