import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createAddress, getAddresses } from "../api/addressApi";
import { getOffers, previewCoupon } from "../api/offerApi";
import { placeOrder } from "../api/orderApi";
import { createRazorpayOrder, verifyRazorpayPayment } from "../api/paymentApi";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import { formatCurrency } from "../utils/formatters";

const emptyAddressForm = {
  label: "Home",
  receiver_name: "",
  phone: "",
  line1: "",
  line2: "",
  city: "",
  state: "",
  postal_code: "",
  is_default: true,
};

const paymentMethods = [
  {
    id: "cash_on_delivery",
    title: "Cash on delivery",
    description: "Pay when the order reaches your address.",
  },
  {
    id: "upi",
    title: "UPI (demo)",
    description: "Instant demo payment, marked paid after order placement.",
  },
  {
    id: "card",
    title: "Card (demo)",
    description: "Use the demo flow to simulate card success or failure.",
  },
  {
    id: "razorpay",
    title: "Razorpay checkout",
    description: "Use real Razorpay checkout when backend keys are configured.",
  },
];


function loadRazorpayScript() {
  if (window.Razorpay) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = resolve;
    script.onerror = () => reject(new Error("Razorpay checkout did not load."));
    document.body.appendChild(script);
  });
}

function Checkout() {
  const navigate = useNavigate();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const { items, total, deliveryFee, grandTotal, refreshCart } = useCart();
  const [addresses, setAddresses] = useState([]);
  const [selectedAddressId, setSelectedAddressId] = useState("");
  const [useNewAddress, setUseNewAddress] = useState(false);
  const [addressForm, setAddressForm] = useState(emptyAddressForm);
  const [deliveryInstruction, setDeliveryInstruction] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("cash_on_delivery");
  const [simulatePaymentFailure, setSimulatePaymentFailure] = useState(false);
  const [coupons, setCoupons] = useState([]);
  const [promoCode, setPromoCode] = useState("");
  const [appliedCoupon, setAppliedCoupon] = useState(null);
  const [couponError, setCouponError] = useState("");
  const [loadingAddresses, setLoadingAddresses] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated) return;

    const loadAddresses = async () => {
      setLoadingAddresses(true);
      setError("");
      try {
        const savedAddresses = await getAddresses();
        setAddresses(savedAddresses);
        if (savedAddresses.length > 0) {
          setSelectedAddressId(String(savedAddresses[0].id));
        } else {
          setUseNewAddress(true);
        }
      } catch (addressError) {
        setError(
          addressError.response?.data?.detail || "We could not load your saved addresses."
        );
      } finally {
        setLoadingAddresses(false);
      }
    };

    loadAddresses();
  }, [isAuthenticated]);

  useEffect(() => {
    let active = true;

    getOffers()
      .then((offerData) => {
        if (active) {
          setCoupons(offerData.coupons || []);
        }
      })
      .catch(() => {
        if (active) {
          setCoupons([]);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    setAppliedCoupon(null);
    setCouponError("");
  }, [total, deliveryFee]);

  const handleAddressChange = (event) => {
    const { name, type, checked, value } = event.target;
    setAddressForm((current) => ({
      ...current,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleCouponApply = async (event) => {
    event.preventDefault();
    setCouponError("");
    setAppliedCoupon(null);

    if (!promoCode.trim()) {
      setCouponError("Enter a coupon code.");
      return;
    }

    try {
      const preview = await previewCoupon({
        code: promoCode,
        subtotal: total,
        deliveryFee,
      });
      setPromoCode(preview.code);
      setAppliedCoupon(preview);
    } catch (couponApplyError) {
      setCouponError(
        couponApplyError.response?.data?.detail || "Coupon could not be applied."
      );
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      let addressId = selectedAddressId;
      let razorpayPayment = null;
      if (useNewAddress || addresses.length === 0) {
        const createdAddress = await createAddress(addressForm);
        addressId = String(createdAddress.id);
      }

      if (!addressId) {
        throw new Error("Select or add a delivery address.");
      }

      if (paymentMethod === "razorpay") {
        await loadRazorpayScript();
        const checkoutTotal = appliedCoupon?.total ?? grandTotal;
        const razorpayOrder = await createRazorpayOrder({
          amount: checkoutTotal,
          currency: "INR",
          receipt: `CK-${Date.now()}`,
          notes: {
            address_id: String(addressId),
            promo_code: appliedCoupon?.code || "",
          },
        });

        razorpayPayment = await new Promise((resolve, reject) => {
          const checkout = new window.Razorpay({
            key: razorpayOrder.key_id,
            amount: Math.round(razorpayOrder.amount * 100),
            currency: razorpayOrder.currency,
            name: "CampusKart",
            description: "Grocery order payment",
            order_id: razorpayOrder.order_id,
            handler: resolve,
            modal: {
              ondismiss: () => reject(new Error("Payment was cancelled.")),
            },
            prefill: {
              contact: addresses.find((item) => String(item.id) === String(addressId))
                ?.phone,
            },
            theme: { color: "#1f8f3a" },
          });
          checkout.open();
        });

        const verification = await verifyRazorpayPayment({
          razorpay_order_id: razorpayPayment.razorpay_order_id,
          razorpay_payment_id: razorpayPayment.razorpay_payment_id,
          razorpay_signature: razorpayPayment.razorpay_signature,
        });
        if (!verification.verified) {
          throw new Error("Payment verification failed. Contact support if money was debited.");
        }
      }

      const order = await placeOrder({
        address_id: Number(addressId),
        payment_method: paymentMethod,
        mock_payment_result:
          paymentMethod !== "cash_on_delivery" &&
          paymentMethod !== "razorpay" &&
          simulatePaymentFailure
            ? "failed"
            : "success",
        razorpay_order_id: razorpayPayment?.razorpay_order_id || null,
        razorpay_payment_id: razorpayPayment?.razorpay_payment_id || null,
        razorpay_signature: razorpayPayment?.razorpay_signature || null,
        promo_code: appliedCoupon?.code || null,
        delivery_instruction: deliveryInstruction || null,
      });
      await refreshCart();
      navigate(`/orders/${order.id}`, { state: { order } });
    } catch (checkoutError) {
      setError(
        checkoutError.response?.data?.detail ||
          checkoutError.message ||
          "We could not place your order."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (authLoading) {
    return (
      <section className="container page-section">
        <p className="status-card">Checking your session...</p>
      </section>
    );
  }

  if (!isAuthenticated) {
    return (
      <section className="container auth-page">
        <div className="auth-card">
          <h2>Login required</h2>
          <p>Login before checkout so we can save and track your order.</p>
          <Link className="button" to="/login">
            Login to continue
          </Link>
        </div>
      </section>
    );
  }

  if (items.length === 0) {
    return (
      <section className="container page-section empty-state">
        <span aria-hidden="true">{"\u2713"}</span>
        <h1>Your cart is empty</h1>
        <p>Add products before starting checkout.</p>
        <Link className="button" to="/products">
          Browse products
        </Link>
      </section>
    );
  }

  const payableDeliveryFee = appliedCoupon?.delivery_fee ?? deliveryFee;
  const payableDiscount = appliedCoupon?.discount ?? 0;
  const payableTotal = appliedCoupon?.total ?? grandTotal;

  return (
    <section className="container page-section">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Almost there</span>
          <h1>Checkout</h1>
        </div>
      </div>

      {error && <p className="form-error">{error}</p>}

      <form className="checkout-layout" onSubmit={handleSubmit}>
        <div className="checkout-card">
          <h2>Delivery address</h2>
          {loadingAddresses && <p>Getting your saved addresses...</p>}

          {addresses.length > 0 && (
            <div className="address-list">
              {addresses.map((address) => (
                <label className="address-option" key={address.id}>
                  <input
                    checked={!useNewAddress && selectedAddressId === String(address.id)}
                    name="address"
                    onChange={() => {
                      setUseNewAddress(false);
                      setSelectedAddressId(String(address.id));
                    }}
                    type="radio"
                  />
                  <span>
                    <strong>
                      {address.label} - {address.receiver_name}
                    </strong>
                    <small>
                      {address.line1}, {address.city}, {address.postal_code}
                    </small>
                  </span>
                </label>
              ))}
            </div>
          )}

          <label className="address-option">
            <input
              checked={useNewAddress}
              name="address"
              onChange={() => setUseNewAddress(true)}
              type="radio"
            />
            <span>
              <strong>Add a new address</strong>
              <small>Use this for hostel, home, or office delivery.</small>
            </span>
          </label>

          {useNewAddress && (
            <div className="address-form-grid">
              <label>
                Label
                <input
                  name="label"
                  onChange={handleAddressChange}
                  required
                  value={addressForm.label}
                />
              </label>
              <label>
                Receiver name
                <input
                  name="receiver_name"
                  onChange={handleAddressChange}
                  required
                  value={addressForm.receiver_name}
                />
              </label>
              <label>
                Phone
                <input
                  name="phone"
                  onChange={handleAddressChange}
                  required
                  value={addressForm.phone}
                />
              </label>
              <label>
                Address line 1
                <input
                  name="line1"
                  onChange={handleAddressChange}
                  required
                  value={addressForm.line1}
                />
              </label>
              <label>
                Address line 2
                <input
                  name="line2"
                  onChange={handleAddressChange}
                  value={addressForm.line2}
                />
              </label>
              <label>
                City
                <input
                  name="city"
                  onChange={handleAddressChange}
                  required
                  value={addressForm.city}
                />
              </label>
              <label>
                State
                <input
                  name="state"
                  onChange={handleAddressChange}
                  required
                  value={addressForm.state}
                />
              </label>
              <label>
                Postal code
                <input
                  name="postal_code"
                  onChange={handleAddressChange}
                  required
                  value={addressForm.postal_code}
                />
              </label>
              <label className="checkbox-label">
                <input
                  checked={addressForm.is_default}
                  name="is_default"
                  onChange={handleAddressChange}
                  type="checkbox"
                />
                Save as default address
              </label>
            </div>
          )}
        </div>

        <aside className="order-summary">
          <h2>Payment</h2>
          <div className="payment-options">
            {paymentMethods.map((method) => (
              <label className="payment-option" key={method.id}>
                <input
                  checked={paymentMethod === method.id}
                  name="payment_method"
                  onChange={() => {
                    setPaymentMethod(method.id);
                    if (method.id === "cash_on_delivery") {
                      setSimulatePaymentFailure(false);
                    }
                  }}
                  type="radio"
                />
                <span>
                  <strong>{method.title}</strong>
                  <small>{method.description}</small>
                </span>
              </label>
            ))}
          </div>
          {paymentMethod !== "cash_on_delivery" && paymentMethod !== "razorpay" && (
            <label className="payment-failure-toggle">
              <input
                checked={simulatePaymentFailure}
                onChange={(event) =>
                  setSimulatePaymentFailure(event.target.checked)
                }
                type="checkbox"
              />
              Simulate failed payment
            </label>
          )}
          <p className="payment-note">
            Razorpay uses the real checkout when backend keys are configured.
            Demo UPI/card stay available for local testing.
          </p>
          {coupons.length > 0 && (
            <section className="coupon-box">
              <h3>Offers</h3>
              <div className="coupon-chip-row">
                {coupons.map((coupon) => (
                  <button
                    key={coupon.code}
                    type="button"
                    onClick={() => {
                      setPromoCode(coupon.code);
                      setAppliedCoupon(null);
                      setCouponError("");
                    }}
                  >
                    {coupon.code}
                  </button>
                ))}
              </div>
              <div className="coupon-apply">
                <input
                  onChange={(event) => {
                    setPromoCode(event.target.value.toUpperCase());
                    setAppliedCoupon(null);
                    setCouponError("");
                  }}
                  placeholder="Enter coupon"
                  value={promoCode}
                />
                <button
                  className="button button-small"
                  onClick={handleCouponApply}
                  type="button"
                >
                  Apply
                </button>
              </div>
              {appliedCoupon && (
                <p className="coupon-success">
                  {appliedCoupon.code} applied. You save{" "}
                  {formatCurrency(appliedCoupon.savings)}.
                </p>
              )}
              {couponError && <p className="coupon-error">{couponError}</p>}
            </section>
          )}
          <label className="instruction-label">
            Delivery instruction
            <textarea
              maxLength="300"
              onChange={(event) => setDeliveryInstruction(event.target.value)}
              placeholder="Optional: call before delivery, gate number..."
              value={deliveryInstruction}
            />
          </label>
          <div>
            <span>Subtotal</span>
            <strong>
              {formatCurrency(total)}
            </strong>
          </div>
          <div>
            <span>Delivery</span>
            <strong>
              {payableDeliveryFee === 0 ? "Free" : formatCurrency(payableDeliveryFee)}
            </strong>
          </div>
          {payableDiscount > 0 && (
            <div>
              <span>Coupon discount</span>
              <strong>
                -{formatCurrency(payableDiscount)}
              </strong>
            </div>
          )}
          <div className="summary-total">
            <span>Total</span>
            <strong>
              {formatCurrency(payableTotal)}
            </strong>
          </div>
          <button className="button checkout-button" disabled={isSubmitting}>
            {isSubmitting
              ? "Processing..."
              : paymentMethod === "cash_on_delivery"
                ? "Place order"
                : paymentMethod === "razorpay"
                  ? "Pay with Razorpay"
                : "Pay and place order"}
          </button>
        </aside>
      </form>
    </section>
  );
}

export default Checkout;
