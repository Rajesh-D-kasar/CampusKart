import "./styles.css";

const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(
  /\/$/,
  ""
);
const TOKEN_KEY = "campuskart-delivery-token";
const USER_KEY = "campuskart-delivery-user";

const state = {
  token: localStorage.getItem(TOKEN_KEY),
  user: loadStoredUser(),
  orders: [],
  summary: null,
  supportTickets: [],
  tab: "active",
  query: "",
  savingOrderId: null,
};

const elements = {
  loginView: document.querySelector("#login-view"),
  panelView: document.querySelector("#panel-view"),
  loginForm: document.querySelector("#login-form"),
  loginError: document.querySelector("#login-error"),
  email: document.querySelector("#email"),
  password: document.querySelector("#password"),
  partnerCopy: document.querySelector("#partner-copy"),
  shiftTitle: document.querySelector("#shift-title"),
  lastRefresh: document.querySelector("#last-refresh"),
  codDue: document.querySelector("#cod-due"),
  statsGrid: document.querySelector("#stats-grid"),
  tabs: document.querySelector("#tabs"),
  searchInput: document.querySelector("#search-input"),
  panelError: document.querySelector("#panel-error"),
  ordersGrid: document.querySelector("#orders-grid"),
  supportForm: document.querySelector("#support-form"),
  supportCategory: document.querySelector("#support-category"),
  supportSubject: document.querySelector("#support-subject"),
  supportMessage: document.querySelector("#support-message"),
  supportList: document.querySelector("#support-list"),
  refreshButton: document.querySelector("#refresh-button"),
  logoutButton: document.querySelector("#logout-button"),
};

function loadStoredUser() {
  try {
    const savedUser = localStorage.getItem(USER_KEY);
    return savedUser ? JSON.parse(savedUser) : null;
  } catch {
    return null;
  }
}

function setError(element, message) {
  element.textContent = message || "";
  element.hidden = !message;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatMoney(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: Number.isInteger(value) ? 0 : 2,
  }).format(value || 0);
}

function formatDateTime(value) {
  if (!value) return "Updating soon";
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatStatus(value) {
  return String(value || "").replaceAll("_", " ");
}

function addressText(address = {}) {
  return [address.line1, address.line2, `${address.city}, ${address.state} ${address.postal_code}`]
    .filter(Boolean)
    .join(", ");
}

function phoneHref(phone) {
  return `tel:${String(phone || "").replace(/[^\d+]/g, "")}`;
}

function mapHref(address) {
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
    addressText(address)
  )}`;
}

function nextAction(order) {
  if (order.status === "confirmed" || order.status === "packing") {
    if (!order.store_ready) {
      return {
        label: "Waiting for shop ready",
        status: "",
        otpLabel: "Pickup not ready",
        otpHelp: "Shop owner packed / ready mark karega tab pickup OTP milega.",
        disabled: true,
      };
    }
    return {
      label: "Verify shop OTP & start route",
      status: "out_for_delivery",
      otpLabel: "Shop pickup OTP",
      otpHelp: "Packed bag lete waqt shop owner se OTP lo.",
    };
  }
  if (order.status === "out_for_delivery") {
    return {
      label: "Verify customer OTP & deliver",
      status: "delivered",
      otpLabel: "Customer delivery OTP",
      otpHelp: "Order handover karte waqt customer se OTP lo.",
    };
  }
  return null;
}

async function apiFetch(path, options = {}) {
  const headers = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(state.token ? { Authorization: `Bearer ${state.token}` } : {}),
    ...options.headers,
  };
  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    if (response.status === 401) logout();
    throw new Error(data?.detail || "Request failed. Please try again.");
  }
  return data;
}

function saveSession(session) {
  state.token = session.access_token;
  state.user = session.user;
  localStorage.setItem(TOKEN_KEY, session.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(session.user));
}

function logout() {
  state.token = null;
  state.user = null;
  state.orders = [];
  state.summary = null;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  renderShell();
}

async function login(email, password) {
  const session = await apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

  if (!["delivery_partner", "admin"].includes(session.user.role)) {
    throw new Error("Only delivery partners and admins can use this panel.");
  }

  saveSession(session);
  renderShell();
  await loadDashboard();
}

async function loadDashboard() {
  if (!state.token) return;
  setError(elements.panelError, "");
  elements.refreshButton.disabled = true;

  try {
    const [summary, orders, supportTickets] = await Promise.all([
      apiFetch("/delivery/summary"),
      apiFetch("/delivery/orders"),
      apiFetch("/support/tickets"),
    ]);
    state.summary = summary;
    state.orders = orders;
    state.supportTickets = supportTickets;
    elements.lastRefresh.textContent = `Last synced ${formatDateTime(
      new Date().toISOString()
    )}`;
    renderDashboard();
  } catch (error) {
    setError(elements.panelError, error.message);
  } finally {
    elements.refreshButton.disabled = false;
  }
}

async function createSupportTicket() {
  const ticket = await apiFetch("/support/tickets", {
    method: "POST",
    body: JSON.stringify({
      audience: "delivery",
      category: elements.supportCategory.value,
      subject: elements.supportSubject.value.trim(),
      message: elements.supportMessage.value.trim(),
    }),
  });
  state.supportTickets = [ticket, ...state.supportTickets];
  elements.supportForm.reset();
  renderSupportTickets();
}

async function updateOrderStatus(orderId, status, otp) {
  const order = state.orders.find((item) => item.id === orderId);
  const cleanOtp = String(otp || "").trim();
  if (!/^\d{6}$/.test(cleanOtp)) {
    setError(elements.panelError, "6 digit OTP enter karo, phir status update hoga.");
    document.querySelector(`[data-handoff-otp="${orderId}"]`)?.focus();
    return;
  }

  if (
    status === "delivered" &&
    order?.payment_method === "cash_on_delivery" &&
    order?.payment_status === "pending" &&
    !window.confirm(`COD ${formatMoney(order.total)} collect ho gaya?`)
  ) {
    return;
  }

  state.savingOrderId = orderId;
  renderOrders();
  setError(elements.panelError, "");

  try {
    const updatedOrder = await apiFetch(`/delivery/orders/${orderId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status, otp: cleanOtp }),
    });
    state.orders = state.orders.map((item) =>
      item.id === orderId ? updatedOrder : item
    );
    await loadDashboard();
  } catch (error) {
    setError(elements.panelError, error.message);
  } finally {
    state.savingOrderId = null;
    renderOrders();
  }
}

function renderShell() {
  const isLoggedIn = Boolean(state.token && state.user);
  elements.loginView.hidden = isLoggedIn;
  elements.panelView.hidden = !isLoggedIn;

  if (!isLoggedIn) return;

  const firstName = state.user.full_name.split(" ")[0];
  elements.partnerCopy.textContent = `${firstName}, assigned deliveries yahin manage hongi.`;
  elements.shiftTitle.textContent =
    state.summary?.active_orders > 0 ? "Active shift running" : "No active drops";
}

function renderStats() {
  const summary = state.summary || {
    active_orders: 0,
    packing_orders: 0,
    out_for_delivery_orders: 0,
    delivered_orders: 0,
    cod_collection_due: 0,
    delivered_value: 0,
  };

  elements.codDue.textContent = formatMoney(summary.cod_collection_due);
  elements.statsGrid.innerHTML = [
    ["Active", summary.active_orders],
    ["Pickup queue", summary.packing_orders],
    ["On road", summary.out_for_delivery_orders],
    ["Delivered", summary.delivered_orders],
    ["Delivered value", formatMoney(summary.delivered_value)],
  ]
    .map(
      ([label, value]) => `
        <article class="stat-card">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
        </article>
      `
    )
    .join("");
}

function filteredOrders() {
  const query = state.query.trim().toLowerCase();
  return state.orders.filter((order) => {
    const matchesTab =
      state.tab === "active"
        ? order.status !== "delivered"
        : state.tab === "pickup"
          ? ["confirmed", "packing"].includes(order.status)
          : state.tab === "road"
            ? order.status === "out_for_delivery"
            : order.status === "delivered";

    if (!matchesTab) return false;
    if (!query) return true;

    const haystack = [
      order.order_number,
      order.customer_name,
      order.customer_phone,
      order.delivery_city,
      addressText(order.delivery_address_snapshot),
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(query);
  });
}

function renderTabs() {
  elements.tabs.querySelectorAll("button").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === state.tab);
  });
}

function renderOrders() {
  const orders = filteredOrders();

  if (orders.length === 0) {
    elements.ordersGrid.innerHTML = `
      <div class="empty-card">
        <h2>No orders here</h2>
        <p>Tab ya search change karke dekho. Assigned orders backend se sync hote hain.</p>
      </div>
    `;
    return;
  }

  elements.ordersGrid.innerHTML = orders.map(renderOrderCard).join("");
}

function renderSupportTickets() {
  if (!elements.supportList) return;
  if (state.supportTickets.length === 0) {
    elements.supportList.innerHTML = `<div class="quiet-card">No support tickets yet.</div>`;
    return;
  }
  elements.supportList.innerHTML = state.supportTickets
    .slice(0, 5)
    .map(
      (ticket) => `
        <article class="support-ticket">
          <div>
            <span>#${ticket.id} - ${escapeHtml(ticket.category)}</span>
            <strong>${escapeHtml(ticket.subject)}</strong>
            <p>${escapeHtml(ticket.message)}</p>
          </div>
          <span class="status-pill status-${escapeHtml(ticket.status)}">${escapeHtml(formatStatus(ticket.status))}</span>
        </article>
      `
    )
    .join("");
}

function renderOrderCard(order) {
  const address = order.delivery_address_snapshot || {};
  const action = nextAction(order);
  const isCodDue =
    order.payment_method === "cash_on_delivery" && order.payment_status === "pending";
  const saving = state.savingOrderId === order.id;
  const progress = order.delivery_progress_percent || 0;
  const phone = address.phone || order.customer_phone;

  return `
    <article class="order-card">
      <div class="order-head">
        <div>
          <span class="order-number">#${escapeHtml(order.order_number)}</span>
          <h2>${escapeHtml(order.customer_name)}</h2>
          <p>${escapeHtml(order.item_count)} items - ${formatDateTime(order.created_at)}</p>
        </div>
        <span class="status-pill status-${escapeHtml(order.status)}">
          ${escapeHtml(formatStatus(order.status))}
        </span>
      </div>

      <div class="progress-track" aria-label="Delivery progress">
        <span style="width: ${progress}%"></span>
      </div>

      <div class="info-grid">
        <article>
          <span>ETA</span>
          <strong>${order.status === "delivered" ? "Delivered" : `${order.eta_minutes ?? "-"} min`}</strong>
          <small>${escapeHtml(order.tracking_message)}</small>
        </article>
        <article>
          <span>Payment</span>
          <strong>${isCodDue ? "Collect COD" : escapeHtml(formatStatus(order.payment_status))}</strong>
          <small>${formatMoney(order.total)} - ${escapeHtml(formatStatus(order.payment_method))}</small>
        </article>
      </div>

      ${
        isCodDue
          ? `<div class="cod-alert">Collect ${formatMoney(order.total)} before marking delivered.</div>`
          : ""
      }

      <section class="address-card">
        <span>Drop address</span>
        <strong>${escapeHtml(address.receiver_name || order.customer_name)}</strong>
        <p>${escapeHtml(addressText(address))}</p>
        <small>Phone: ${escapeHtml(phone || "Not available")}</small>
        ${
          order.delivery_instruction
            ? `<small>Note: ${escapeHtml(order.delivery_instruction)}</small>`
            : ""
        }
      </section>

      <div class="quick-actions">
        <a class="ghost-button" href="${phoneHref(phone)}">Call customer</a>
        <a class="ghost-button" href="${mapHref(address)}" target="_blank" rel="noreferrer">
          Open map
        </a>
        <button class="ghost-button" data-copy-order="${escapeHtml(order.order_number)}" type="button">
          Copy order
        </button>
      </div>

      <details class="items-card" open>
        <summary>Item checklist</summary>
        ${order.items
          .map(
            (item) => `
              <label>
                <input type="checkbox" />
                <span>${escapeHtml(item.product_name)}</span>
                <strong>${escapeHtml(item.quantity)} x ${escapeHtml(item.unit)}</strong>
              </label>
            `
          )
          .join("")}
      </details>

      <section class="handoff-card">
        <div>
          <span>${action ? escapeHtml(action.otpLabel) : "Handoff complete"}</span>
          <strong>
            ${
              order.status === "delivered"
                ? "Order delivered"
                : order.status === "out_for_delivery"
                  ? "Customer OTP needed"
                  : "Shop OTP needed"
            }
          </strong>
          <small>${action ? escapeHtml(action.otpHelp) : "Pickup aur delivery dono verify ho chuke hain."}</small>
        </div>
        <div class="handoff-flags">
          <span class="${order.pickup_verified ? "done" : ""}">Pickup ${order.pickup_verified ? "verified" : "pending"}</span>
          <span class="${order.dropoff_verified ? "done" : ""}">Drop ${order.dropoff_verified ? "verified" : "pending"}</span>
        </div>
        ${
          action && !action.disabled
            ? `<label class="otp-input-card">
                <span>Enter 6 digit OTP</span>
                <input
                  inputmode="numeric"
                  maxlength="6"
                  pattern="[0-9]{6}"
                  placeholder="000000"
                  data-handoff-otp="${order.id}"
                />
              </label>`
            : ""
        }
      </section>

      <div class="order-actions">
        ${
          action?.status
            ? `<button class="primary-button" data-status-order="${order.id}" data-next-status="${action.status}" ${saving ? "disabled" : ""}>
                ${saving ? "Saving..." : action.label}
              </button>`
            : action?.disabled
              ? `<button class="ghost-button" disabled>${action.label}</button>`
              : `<span class="done-pill">Delivery completed</span>`
        }
      </div>
    </article>
  `;
}

function renderDashboard() {
  renderShell();
  renderStats();
  renderTabs();
  renderOrders();
  renderSupportTickets();
}

elements.loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setError(elements.loginError, "");

  try {
    await login(elements.email.value.trim(), elements.password.value);
  } catch (error) {
    setError(elements.loginError, error.message);
  }
});

document.querySelectorAll("[data-demo-email]").forEach((button) => {
  button.addEventListener("click", () => {
    elements.email.value = button.dataset.demoEmail;
    elements.password.value = "DeliveryPass123";
  });
});

elements.refreshButton.addEventListener("click", loadDashboard);
elements.logoutButton.addEventListener("click", logout);

elements.tabs.addEventListener("click", (event) => {
  const button = event.target.closest("[data-tab]");
  if (!button) return;
  state.tab = button.dataset.tab;
  renderTabs();
  renderOrders();
});

elements.searchInput.addEventListener("input", (event) => {
  state.query = event.target.value;
  renderOrders();
});

elements.supportForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setError(elements.panelError, "");
  try {
    await createSupportTicket();
  } catch (error) {
    setError(elements.panelError, error.message);
  }
});

elements.ordersGrid.addEventListener("click", async (event) => {
  const statusButton = event.target.closest("[data-status-order]");
  if (statusButton) {
    const orderId = Number(statusButton.dataset.statusOrder);
    const otpInput = document.querySelector(`[data-handoff-otp="${orderId}"]`);
    await updateOrderStatus(
      orderId,
      statusButton.dataset.nextStatus,
      otpInput?.value
    );
    return;
  }

  const copyButton = event.target.closest("[data-copy-order]");
  if (copyButton && navigator.clipboard) {
    await navigator.clipboard.writeText(copyButton.dataset.copyOrder);
    copyButton.textContent = "Copied";
    setTimeout(() => {
      copyButton.textContent = "Copy order";
    }, 900);
  }
});

renderShell();
if (state.token) {
  loadDashboard();
}
