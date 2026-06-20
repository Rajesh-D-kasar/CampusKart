import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";

function Navbar() {
  const { itemCount } = useCart();
  const { isAuthenticated, logout, user } = useAuth();
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
                <NavLink className={navClassName} to="/admin">
                  Admin
                </NavLink>
              )}
              {(user.role === "delivery_partner" || user.role === "admin") && (
                <NavLink className={navClassName} to="/delivery">
                  Delivery
                </NavLink>
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
