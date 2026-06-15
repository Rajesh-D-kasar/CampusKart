import { Link } from "react-router-dom";

function Register() {
  return (
    <section className="container auth-page">
      <form className="auth-card" onSubmit={(event) => event.preventDefault()}>
        <h2>Register</h2>
        <p>Account creation will be connected in the next backend milestone.</p>
        <label>
          Name
          <input type="text" placeholder="Your name" required />
        </label>
        <label>
          Email
          <input type="email" placeholder="you@example.com" required />
        </label>
        <label>
          Password
          <input type="password" placeholder="Create a password" required />
        </label>
        <button className="button" type="submit" disabled>
          Registration coming next
        </button>
        <p>
          Already registered? <Link to="/login">Login</Link>
        </p>
      </form>
    </section>
  );
}

export default Register;
