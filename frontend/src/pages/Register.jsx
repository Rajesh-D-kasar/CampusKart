import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function getErrorMessage(error) {
  return error.response?.data?.detail || "Registration failed. Please try again.";
}

function Register() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    phone: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (event) => {
    setFormData((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await register({
        ...formData,
        phone: formData.phone || null,
      });
      navigate("/products");
    } catch (registerError) {
      setError(getErrorMessage(registerError));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="container auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h2>Register</h2>
        <p>Create an account to save carts, addresses, and future orders.</p>
        {error && <p className="form-error">{error}</p>}
        <label>
          Name
          <input
            name="full_name"
            type="text"
            value={formData.full_name}
            onChange={handleChange}
            placeholder="Your name"
            required
          />
        </label>
        <label>
          Email
          <input
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="you@example.com"
            required
          />
        </label>
        <label>
          Phone
          <input
            name="phone"
            type="tel"
            value={formData.phone}
            onChange={handleChange}
            placeholder="Optional phone number"
          />
        </label>
        <label>
          Password
          <input
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="At least 8 characters"
            minLength={8}
            required
          />
        </label>
        <button className="button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Creating account..." : "Create account"}
        </button>
        <p>
          Already registered? <Link to="/login">Login</Link>
        </p>
      </form>
    </section>
  );
}

export default Register;
