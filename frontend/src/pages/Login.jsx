import { Link } from "react-router-dom";

function Login() {
  return (
    <section className="container auth-page">
      <form className="auth-card" onSubmit={(event) => event.preventDefault()}>
        <h2>Login</h2>
        <p>Authentication will be connected in the next backend milestone.</p>
        <label>
          Email
          <input type="email" placeholder="you@example.com" required />
        </label>
        <label>
          Password
          <input type="password" placeholder="Enter password" required />
        </label>
        <button className="button" type="submit" disabled>
          Login coming next
        </button>
        <p>
          New here? <Link to="/register">Create an account</Link>
        </p>
      </form>
    </section>
  );
}

export default Login;
