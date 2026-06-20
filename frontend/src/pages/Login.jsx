import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function getErrorMessage(error) {
  return error.response?.data?.detail || "Login failed. Please try again.";
}

function Login() {
  const navigate = useNavigate();
  const { login, requestLoginOtp, verifyLoginOtp } = useAuth();
  const [mode, setMode] = useState("otp");
  const [passwordForm, setPasswordForm] = useState({ email: "", password: "" });
  const [otpForm, setOtpForm] = useState({
    email: "",
    full_name: "",
    phone: "",
    otp: "",
  });
  const [otpRequested, setOtpRequested] = useState(false);
  const [otpMessage, setOtpMessage] = useState("");
  const [devOtp, setDevOtp] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handlePasswordChange = (event) => {
    setPasswordForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  };

  const handleOtpChange = (event) => {
    setOtpForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  };

  const handlePasswordSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await login(passwordForm);
      navigate("/products");
    } catch (loginError) {
      setError(getErrorMessage(loginError));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOtpRequest = async (event) => {
    event.preventDefault();
    setError("");
    setOtpMessage("");
    setDevOtp("");
    setIsSubmitting(true);

    try {
      const response = await requestLoginOtp({
        email: otpForm.email,
        full_name: otpForm.full_name || null,
        phone: otpForm.phone || null,
      });
      setOtpRequested(true);
      setOtpMessage(response.message);
      if (response.development_otp) {
        setDevOtp(response.development_otp);
        setOtpForm((current) => ({ ...current, otp: response.development_otp }));
      }
    } catch (otpError) {
      setError(getErrorMessage(otpError));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOtpVerify = async (event) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await verifyLoginOtp({
        email: otpForm.email,
        otp: otpForm.otp,
        full_name: otpForm.full_name || null,
        phone: otpForm.phone || null,
      });
      navigate("/products");
    } catch (otpError) {
      setError(getErrorMessage(otpError));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="container auth-page">
      <div className="auth-card">
        <div>
          <h2>Login</h2>
          <p>OTP se fast login karo, ya password use karo.</p>
        </div>

        <div className="auth-tabs" role="tablist" aria-label="Login options">
          <button
            className={mode === "otp" ? "active" : ""}
            onClick={() => {
              setMode("otp");
              setError("");
            }}
            type="button"
          >
            OTP login
          </button>
          <button
            className={mode === "password" ? "active" : ""}
            onClick={() => {
              setMode("password");
              setError("");
            }}
            type="button"
          >
            Password
          </button>
        </div>

        {error && <p className="form-error">{error}</p>}

        {mode === "otp" ? (
          <form className="auth-form-stack" onSubmit={otpRequested ? handleOtpVerify : handleOtpRequest}>
            <label>
              Email
              <input
                name="email"
                type="email"
                value={otpForm.email}
                onChange={handleOtpChange}
                placeholder="you@example.com"
                disabled={otpRequested}
                required
              />
            </label>
            {!otpRequested && (
              <>
                <label>
                  Name
                  <input
                    name="full_name"
                    type="text"
                    value={otpForm.full_name}
                    onChange={handleOtpChange}
                    placeholder="Your name"
                  />
                </label>
                <label>
                  Phone
                  <input
                    name="phone"
                    type="tel"
                    value={otpForm.phone}
                    onChange={handleOtpChange}
                    placeholder="Optional phone number"
                  />
                </label>
              </>
            )}
            {otpRequested && (
              <>
                {otpMessage && <p className="form-success">{otpMessage}</p>}
                {devOtp && (
                  <p className="otp-dev-note">
                    Dev OTP: <strong>{devOtp}</strong>
                  </p>
                )}
                <label>
                  6 digit OTP
                  <input
                    name="otp"
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]{6}"
                    maxLength={6}
                    value={otpForm.otp}
                    onChange={handleOtpChange}
                    placeholder="123456"
                    required
                  />
                </label>
              </>
            )}
            <button className="button" type="submit" disabled={isSubmitting}>
              {isSubmitting
                ? "Please wait..."
                : otpRequested
                  ? "Verify OTP"
                  : "Send OTP"}
            </button>
            {otpRequested && (
              <button
                className="button button-secondary"
                type="button"
                onClick={() => {
                  setOtpRequested(false);
                  setOtpMessage("");
                  setDevOtp("");
                  setOtpForm((current) => ({ ...current, otp: "" }));
                }}
              >
                Change email
              </button>
            )}
          </form>
        ) : (
          <form className="auth-form-stack" onSubmit={handlePasswordSubmit}>
            <label>
              Email
              <input
                name="email"
                type="email"
                value={passwordForm.email}
                onChange={handlePasswordChange}
                placeholder="you@example.com"
                required
              />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                value={passwordForm.password}
                onChange={handlePasswordChange}
                placeholder="Enter password"
                required
              />
            </label>
            <button className="button" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Logging in..." : "Login"}
            </button>
          </form>
        )}

        <p>
          New here? OTP login se account auto-create ho jayega, or{" "}
          <Link to="/register">password account banao</Link>.
        </p>
      </div>
    </section>
  );
}

export default Login;
