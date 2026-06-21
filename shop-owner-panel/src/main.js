import "./styles.css";

const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(
  /\/$/,
  ""
);
const TOKEN_KEY = "campuskart-owner-token";
const USER_KEY = "campuskart-owner-user";

const state = {
  token: localStorage.getItem(TOKEN_KEY),
  user: loadStoredUser(),
  summary: null,
  orders: [],
  deliveryPartners: [],
  supportTickets: [],
  inventory: [],
  products: [],
  categories: [],
  orderTab: "open",
  orderQuery: "",
  inventoryQuery: "",
  saving: "",
};

const el = {
  loginView: document.querySelector("#login-view"),
  panelView: document.querySelector("#panel-view"),
  loginForm: document.querySelector("#login-form"),
  loginError: document.querySelector("#login-error"),
  email: document.querySelector("#email"),
  password: document.querySelector("#password"),
  ownerCopy: document.querySelector("#owner-copy"),
  refreshButton: document.querySelector("#refresh-button"),
  logoutButton: document.querySelector("#logout-button"),
  statsGrid: document.querySelector("#stats-grid"),
  orderTabs: document.querySelector("#order-tabs"),
  orderSearch: document.querySelector("#order-search"),
  ordersList: document.querySelector("#orders-list"),
  supportForm: document.querySelector("#support-form"),
  supportCategory: document.querySelector("#support-category"),
  supportSubject: document.querySelector("#support-subject"),
  supportMessage: document.querySelector("#support-message"),
  supportList: document.querySelector("#support-list"),
  lowStockList: document.querySelector("#low-stock-list"),
  inventorySearch: document.querySelector("#inventory-search"),
  inventoryList: document.querySelector("#inventory-list"),
  productManageList: document.querySelector("#product-manage-list"),
  productForm: document.querySelector("#product-form"),
  productCategory: document.querySelector("#product-category"),
  productName: document.querySelector("#product-name"),
  productUnit: document.querySelector("#product-unit"),
  productPrice: document.querySelector("#product-price"),
  productMrp: document.querySelector("#product-mrp"),
  productStock: document.querySelector("#product-stock"),
  categoryForm: document.querySelector("#category-form"),
  categoryName: document.querySelector("#category-name"),
  panelError: document.querySelector("#panel-error"),
};

function loadStoredUser() {
  try {
    const value = localStorage.getItem(USER_KEY);
    return value ? JSON.parse(value) : null;
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

function formatDate(value) {
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatStatus(value) {
  return String(value || "").replaceAll("_", " ");
}

function addressText(address = {}) {
  return [
    address.line1,
    address.line2,
    `${address.city || ""}, ${address.state || ""} ${address.postal_code || ""}`.trim(),
  ]
    .filter(Boolean)
    .join(", ");
}

function slugify(value) {
  return String(value || "")
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
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
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  renderShell();
}

async function login(email, password) {
  const session = await apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

  if (session.user.role !== "admin") {
    throw new Error("Shop owner panel ke liye admin account chahiye.");
  }

  saveSession(session);
  renderShell();
  await loadDashboard();
}

async function loadDashboard() {
  if (!state.token) return;
  el.refreshButton.disabled = true;
  setError(el.panelError, "");

  try {
    const [
      summary,
      orders,
      deliveryPartners,
      supportTickets,
      inventory,
      categories,
      products,
    ] =
      await Promise.all([
      apiFetch("/admin/summary"),
      apiFetch("/admin/orders"),
      apiFetch("/admin/delivery-partners"),
      apiFetch("/admin/support/tickets"),
      apiFetch("/admin/inventory"),
      apiFetch("/admin/categories"),
      apiFetch("/admin/products"),
    ]);
    state.summary = summary;
    state.orders = orders;
    state.deliveryPartners = deliveryPartners;
    state.supportTickets = supportTickets;
    state.inventory = inventory;
    state.categories = categories;
    state.products = products;
    renderDashboard();
  } catch (error) {
    setError(el.panelError, error.message);
  } finally {
    el.refreshButton.disabled = false;
  }
}

function nextOrderActions(order) {
  const actions = [];
  if (order.status === "placed") actions.push(["Confirm", "confirmed"]);
  if (order.status === "confirmed") actions.push(["Start packing", "packing"]);
  if (!["out_for_delivery", "delivered", "cancelled"].includes(order.status)) {
    actions.push(["Cancel", "cancelled"]);
  }
  return actions;
}

async function updateOrderStatus(orderId, status) {
  state.saving = `order-${orderId}`;
  renderOrders();
  try {
    const order = await apiFetch(`/admin/orders/${orderId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
    state.orders = state.orders.map((item) => (item.id === orderId ? order : item));
    await loadDashboard();
  } catch (error) {
    setError(el.panelError, error.message);
  } finally {
    state.saving = "";
    renderOrders();
  }
}

async function updateOrderAssignment(orderId, deliveryPartnerId) {
  state.saving = `assign-${orderId}`;
  renderOrders();
  try {
    const order = await apiFetch(`/admin/orders/${orderId}/assignment`, {
      method: "PATCH",
      body: JSON.stringify({
        delivery_partner_id: deliveryPartnerId ? Number(deliveryPartnerId) : null,
      }),
    });
    state.orders = state.orders.map((item) => (item.id === orderId ? order : item));
  } catch (error) {
    setError(el.panelError, error.message);
  } finally {
    state.saving = "";
    renderOrders();
  }
}

async function markOrderReady(orderId) {
  state.saving = `ready-${orderId}`;
  renderOrders();
  try {
    const order = await apiFetch(`/admin/orders/${orderId}/ready`, {
      method: "PATCH",
    });
    state.orders = state.orders.map((item) => (item.id === orderId ? order : item));
    await loadDashboard();
  } catch (error) {
    setError(el.panelError, error.message);
  } finally {
    state.saving = "";
    renderOrders();
  }
}

async function createSupportTicket() {
  const ticket = await apiFetch("/support/tickets", {
    method: "POST",
    body: JSON.stringify({
      audience: "seller",
      category: el.supportCategory.value,
      subject: el.supportSubject.value.trim(),
      message: el.supportMessage.value.trim(),
    }),
  });
  state.supportTickets = [ticket, ...state.supportTickets];
  el.supportForm.reset();
  renderSupportTickets();
}

async function updateSupportTicket(ticketId, status) {
  const ticket = await apiFetch(`/admin/support/tickets/${ticketId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
  state.supportTickets = state.supportTickets.map((item) =>
    item.id === ticketId ? ticket : item
  );
  renderSupportTickets();
}

async function replySupportTicket(ticketId, message) {
  const ticket = await apiFetch(`/support/tickets/${ticketId}/messages`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
  state.supportTickets = state.supportTickets.map((item) =>
    item.id === ticketId ? ticket : item
  );
  renderSupportTickets();
}

async function updateStock(productId, stockQuantity, reorderLevel, isActive = true) {
  state.saving = `stock-${productId}`;
  renderInventory();
  try {
    const updated = await apiFetch(`/admin/inventory/${productId}`, {
      method: "PATCH",
      body: JSON.stringify({
        stock_quantity: stockQuantity,
        reorder_level: reorderLevel,
        is_active: isActive,
      }),
    });
    state.inventory = state.inventory.map((item) =>
      item.product_id === productId ? updated : item
    );
    renderDashboard();
  } catch (error) {
    setError(el.panelError, error.message);
  } finally {
    state.saving = "";
    renderInventory();
  }
}

async function updateProduct(productId) {
  const priceInput = document.querySelector(`[data-product-price="${productId}"]`);
  const mrpInput = document.querySelector(`[data-product-mrp="${productId}"]`);
  const imageInput = document.querySelector(`[data-product-image="${productId}"]`);
  const activeInput = document.querySelector(`[data-product-active="${productId}"]`);
  state.saving = `product-${productId}`;
  renderProducts();
  try {
    const updated = await apiFetch(`/admin/products/${productId}`, {
      method: "PATCH",
      body: JSON.stringify({
        price: Number(priceInput.value),
        mrp: Number(mrpInput.value),
        image_url: imageInput.value.trim(),
        is_active: Boolean(activeInput.checked),
      }),
    });
    state.products = state.products.map((item) =>
      item.id === productId ? updated : item
    );
    await loadDashboard();
  } catch (error) {
    setError(el.panelError, error.message);
  } finally {
    state.saving = "";
    renderProducts();
  }
}

async function createProduct() {
  const name = el.productName.value.trim();
  const price = Number(el.productPrice.value);
  const mrp = Number(el.productMrp.value);
  const payload = {
    category_id: Number(el.productCategory.value),
    name,
    slug: slugify(name),
    unit: el.productUnit.value.trim(),
    price,
    mrp: Math.max(mrp, price),
    stock_quantity: Number(el.productStock.value || 0),
    reorder_level: 5,
    is_active: true,
  };
  await apiFetch("/admin/products", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  el.productForm.reset();
  el.productStock.value = "10";
  await loadDashboard();
}

async function createCategory() {
  const name = el.categoryName.value.trim();
  await apiFetch("/admin/categories", {
    method: "POST",
    body: JSON.stringify({ name, slug: slugify(name), display_order: 50 }),
  });
  el.categoryForm.reset();
  await loadDashboard();
}

function renderShell() {
  const loggedIn = Boolean(state.token && state.user);
  el.loginView.hidden = loggedIn;
  el.panelView.hidden = !loggedIn;

  if (loggedIn) {
    el.ownerCopy.textContent = `${state.user.full_name}, orders aur dukaan ka stock yahin control hoga.`;
  }
}

function renderStats() {
  const summary = state.summary || {};
  const cards = [
    ["Total orders", summary.total_orders || 0],
    ["Open orders", summary.open_orders || 0],
    ["Active products", summary.active_products || 0],
    ["Low stock", summary.low_stock_items || 0],
    ["Revenue", formatMoney(summary.total_revenue || 0)],
  ];
  el.statsGrid.innerHTML = cards
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
  const query = state.orderQuery.toLowerCase().trim();
  return state.orders.filter((order) => {
    const matchesTab =
      state.orderTab === "all"
        ? true
        : state.orderTab === "open"
          ? !["delivered", "cancelled"].includes(order.status)
          : state.orderTab === "done"
            ? ["delivered", "cancelled"].includes(order.status)
            : state.orderTab === "packing"
              ? ["confirmed", "packing", "out_for_delivery"].includes(order.status)
              : order.status === state.orderTab;
    if (!matchesTab) return false;
    if (!query) return true;
    return [
      order.order_number,
      order.customer_name,
      order.customer_email,
      order.delivery_city,
      order.status,
    ]
      .join(" ")
      .toLowerCase()
      .includes(query);
  });
}

function renderOrderTabs() {
  el.orderTabs.querySelectorAll("button").forEach((button) => {
    button.classList.toggle("active", button.dataset.orderTab === state.orderTab);
  });
}

function renderOrders() {
  const orders = filteredOrders();
  if (orders.length === 0) {
    el.ordersList.innerHTML = `
      <div class="empty-card">
        <h3>No orders found</h3>
        <p>Search ya tab change karke dekho.</p>
      </div>
    `;
    return;
  }

  el.ordersList.innerHTML = orders.map(renderOrderCard).join("");
}

function renderOrderCard(order) {
  const actions = nextOrderActions(order);
  const address = order.delivery_address_snapshot || {};
  const partner = order.delivery_partner;
  const items = order.items || [];
  const partnerOptions = state.deliveryPartners
    .map((deliveryPartner) => {
      const selected = partner?.name === deliveryPartner.name ? "selected" : "";
      return `<option value="${deliveryPartner.id}" ${selected}>${escapeHtml(
        deliveryPartner.name
      )} (${escapeHtml(deliveryPartner.active_order_count)} active)</option>`;
    })
    .join("");
  const canManageAssignment = !["out_for_delivery", "delivered", "cancelled"].includes(
    order.status
  );
  const canMarkReady =
    ["confirmed", "packing"].includes(order.status) && !order.store_ready;
  return `
    <article class="order-card">
      <div class="order-main">
        <div>
          <span class="item-code">#${escapeHtml(order.order_number)}</span>
          <h3>${escapeHtml(order.customer_name)}</h3>
          <p>${escapeHtml(order.item_count)} items - ${escapeHtml(order.delivery_city || "City updating")}</p>
          <small>${formatDate(order.created_at)}</small>
        </div>
        <div class="order-money">
          <strong>${formatMoney(order.total)}</strong>
          <span class="status-pill status-${escapeHtml(order.status)}">${escapeHtml(formatStatus(order.status))}</span>
        </div>
      </div>
      <p class="order-note">${escapeHtml(order.tracking_message || "Order update pending")}</p>
      <div class="fulfillment-grid">
        <section class="pack-card">
          <div>
            <span class="eyebrow">Pack this order</span>
            <strong>${escapeHtml(items.length)} item lines</strong>
          </div>
          <div class="pack-list">
            ${items
              .map(
                (item) => `
                  <label>
                    <input type="checkbox" data-pack-item="${order.id}-${item.id}" />
                    <span>${escapeHtml(item.product_name)}</span>
                    <strong>${escapeHtml(item.quantity)} x ${escapeHtml(item.unit)}</strong>
                  </label>
                `
              )
              .join("")}
          </div>
        </section>

        <section class="handoff-card">
          <span class="eyebrow">Delivery handoff</span>
          <label class="partner-select">
            Delivery boy
            <select
              data-assign-order="${order.id}"
              ${canManageAssignment && state.saving !== `assign-${order.id}` ? "" : "disabled"}
            >
              <option value="">Choose delivery boy</option>
              ${partnerOptions}
            </select>
          </label>
          ${
            partner
              ? `
                <strong>${escapeHtml(partner.name)}</strong>
                <small>Phone: ${escapeHtml(partner.phone)}</small>
                <small>Vehicle: ${escapeHtml(partner.vehicle_number)}</small>
              `
              : `
                <strong>Assigning after confirmation</strong>
                <small>Order confirm karte hi delivery partner show hoga.</small>
              `
          }
          ${
            order.pickup_otp
              ? `
                <div class="otp-box">
                  <span>Pickup OTP</span>
                  <strong>${escapeHtml(order.pickup_otp)}</strong>
                  <small>Sirf assigned delivery boy ko dena jab packed bag handover ho.</small>
                </div>
              `
              : `
                <div class="handoff-status ${order.pickup_verified ? "verified" : ""}">
                  ${
                    order.pickup_verified
                      ? "Pickup verified"
                      : order.store_ready
                        ? "Pickup OTP loading"
                        : "Mark ready to show pickup OTP"
                  }
                </div>
              `
          }
        </section>
      </div>

      <section class="customer-card">
        <span class="eyebrow">Customer & address</span>
        <strong>${escapeHtml(address.receiver_name || order.customer_name)}</strong>
        <p>${escapeHtml(addressText(address) || "Address updating")}</p>
        <small>Phone: ${escapeHtml(address.phone || order.customer_phone || "Not available")}</small>
        ${
          order.delivery_instruction
            ? `<small>Note: ${escapeHtml(order.delivery_instruction)}</small>`
            : ""
        }
      </section>
      <div class="action-row">
        ${
          canMarkReady
            ? `
              <button
                class="primary-button small-button"
                data-ready-order="${order.id}"
                ${state.saving === `ready-${order.id}` ? "disabled" : ""}
                type="button"
              >
                ${state.saving === `ready-${order.id}` ? "Saving..." : "Packed / Ready pickup"}
              </button>
            `
            : ""
        }
        ${actions
          .map(
            ([label, status]) => `
              <button
                class="${status === "cancelled" ? "ghost-button danger-button" : "primary-button small-button"}"
                data-order-id="${order.id}"
                data-order-status="${status}"
                ${state.saving === `order-${order.id}` ? "disabled" : ""}
                type="button"
              >
                ${state.saving === `order-${order.id}` ? "Saving..." : label}
              </button>
            `
          )
          .join("")}
      </div>
    </article>
  `;
}

function renderSupportTickets() {
  if (state.supportTickets.length === 0) {
    el.supportList.innerHTML = `<div class="quiet-card">Abhi koi support ticket nahi hai.</div>`;
    return;
  }
  el.supportList.innerHTML = state.supportTickets
    .slice(0, 8)
    .map(
      (ticket) => `
        <article class="support-ticket">
          <div>
            <span class="item-code">#${ticket.id} - ${escapeHtml(ticket.category)}</span>
            <strong>${escapeHtml(ticket.subject)}</strong>
            <p>${escapeHtml(ticket.message)}</p>
            ${ticket.order_number ? `<small>Order: ${escapeHtml(ticket.order_number)}</small>` : ""}
            ${
              ticket.messages?.length
                ? `<div class="ticket-thread">
                    ${ticket.messages
                      .map(
                        (message) => `
                          <div>
                            <strong>${escapeHtml(message.author_name)} - ${escapeHtml(formatStatus(message.author_role))}</strong>
                            <p>${escapeHtml(message.message)}</p>
                          </div>
                        `
                      )
                      .join("")}
                  </div>`
                : ""
            }
          </div>
          <div class="ticket-actions">
            <span class="status-pill status-${escapeHtml(ticket.status)}">${escapeHtml(formatStatus(ticket.status))}</span>
            <button class="ghost-button small-button" data-ticket-reply="${ticket.id}" type="button">Reply</button>
            ${
              ticket.status !== "resolved"
                ? `<button class="ghost-button small-button" data-ticket-status="resolved" data-ticket-id="${ticket.id}" type="button">Resolve</button>`
                : ""
            }
          </div>
        </article>
      `
    )
    .join("");
}

function filteredInventory() {
  const query = state.inventoryQuery.toLowerCase().trim();
  return state.inventory
    .filter((item) => {
      if (!query) return true;
      return [item.name, item.category, item.slug].join(" ").toLowerCase().includes(query);
    })
    .sort((a, b) => Number(b.low_stock) - Number(a.low_stock) || a.name.localeCompare(b.name));
}

function renderLowStock() {
  const lowStock = state.inventory.filter((item) => item.low_stock).slice(0, 8);
  if (lowStock.length === 0) {
    el.lowStockList.innerHTML = `<div class="quiet-card">Sab stock theek hai.</div>`;
    return;
  }
  el.lowStockList.innerHTML = lowStock
    .map(
      (item) => `
        <article>
          <strong>${escapeHtml(item.name)}</strong>
          <span>${escapeHtml(item.available_quantity)} left</span>
        </article>
      `
    )
    .join("");
}

function renderInventory() {
  const items = filteredInventory();
  if (items.length === 0) {
    el.inventoryList.innerHTML = `<div class="empty-card"><h3>No item found</h3></div>`;
    return;
  }
  el.inventoryList.innerHTML = items.map(renderInventoryRow).join("");
}

function renderInventoryRow(item) {
  return `
    <article class="inventory-row">
      <div class="item-name">
        <span>${escapeHtml(item.category)}</span>
        <strong>${escapeHtml(item.name)}</strong>
        ${item.low_stock ? `<em>Low stock</em>` : ""}
      </div>
      <div class="stock-read">
        <span>Available</span>
        <strong>${escapeHtml(item.available_quantity)}</strong>
      </div>
      <label>
        Stock
        <input
          type="number"
          min="${item.reserved_quantity}"
          value="${item.stock_quantity}"
          data-stock-input="${item.product_id}"
        />
      </label>
      <label>
        Alert at
        <input
          type="number"
          min="0"
          value="${item.reorder_level}"
          data-reorder-input="${item.product_id}"
        />
      </label>
      <div class="stock-actions">
        <button class="ghost-button" data-stock-delta="-1" data-product-id="${item.product_id}" type="button">-1</button>
        <button class="ghost-button" data-stock-delta="5" data-product-id="${item.product_id}" type="button">+5</button>
        <button class="primary-button small-button" data-save-stock="${item.product_id}" ${state.saving === `stock-${item.product_id}` ? "disabled" : ""} type="button">
          ${state.saving === `stock-${item.product_id}` ? "Saving..." : "Save"}
        </button>
      </div>
    </article>
  `;
}

function renderCategories() {
  el.productCategory.innerHTML = state.categories
    .filter((category) => category.is_active)
    .map(
      (category) =>
        `<option value="${category.id}">${escapeHtml(category.name)}</option>`
    )
    .join("");
}

function renderProducts() {
  if (state.products.length === 0) {
    el.productManageList.innerHTML = `<div class="empty-card"><h3>No products found</h3></div>`;
    return;
  }
  el.productManageList.innerHTML = state.products
    .slice()
    .sort((a, b) => a.name.localeCompare(b.name))
    .map(
      (product) => `
        <article class="product-manage-row">
          <div class="item-name">
            <span>${escapeHtml(product.category)}</span>
            <strong>${escapeHtml(product.name)}</strong>
            <small>${escapeHtml(product.unit)}</small>
          </div>
          <label>
            Price
            <input data-product-price="${product.id}" type="number" min="0" step="1" value="${product.price}" />
          </label>
          <label>
            MRP
            <input data-product-mrp="${product.id}" type="number" min="0" step="1" value="${product.mrp}" />
          </label>
          <label class="image-field">
            Image URL
            <input data-product-image="${product.id}" value="${escapeHtml(product.image_url || "")}" placeholder="https://..." />
          </label>
          <label class="active-toggle">
            <input data-product-active="${product.id}" type="checkbox" ${product.is_active ? "checked" : ""} />
            Active
          </label>
          <button class="primary-button small-button" data-save-product="${product.id}" ${state.saving === `product-${product.id}` ? "disabled" : ""} type="button">
            ${state.saving === `product-${product.id}` ? "Saving..." : "Save"}
          </button>
        </article>
      `
    )
    .join("");
}

function renderDashboard() {
  renderShell();
  renderStats();
  renderOrderTabs();
  renderOrders();
  renderSupportTickets();
  renderLowStock();
  renderInventory();
  renderProducts();
  renderCategories();
}

el.loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setError(el.loginError, "");
  try {
    await login(el.email.value.trim(), el.password.value);
  } catch (error) {
    setError(el.loginError, error.message);
  }
});

el.refreshButton.addEventListener("click", loadDashboard);
el.logoutButton.addEventListener("click", logout);

el.orderTabs.addEventListener("click", (event) => {
  const button = event.target.closest("[data-order-tab]");
  if (!button) return;
  state.orderTab = button.dataset.orderTab;
  renderOrderTabs();
  renderOrders();
});

el.orderSearch.addEventListener("input", (event) => {
  state.orderQuery = event.target.value;
  renderOrders();
});

el.inventorySearch.addEventListener("input", (event) => {
  state.inventoryQuery = event.target.value;
  renderInventory();
});

el.ordersList.addEventListener("click", async (event) => {
  const readyButton = event.target.closest("[data-ready-order]");
  if (readyButton) {
    await markOrderReady(Number(readyButton.dataset.readyOrder));
    return;
  }

  const button = event.target.closest("[data-order-id]");
  if (!button) return;
  await updateOrderStatus(Number(button.dataset.orderId), button.dataset.orderStatus);
});

el.ordersList.addEventListener("change", async (event) => {
  const select = event.target.closest("[data-assign-order]");
  if (!select) return;
  await updateOrderAssignment(Number(select.dataset.assignOrder), select.value);
});

el.supportForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setError(el.panelError, "");
  try {
    await createSupportTicket();
  } catch (error) {
    setError(el.panelError, error.message);
  }
});

el.supportList.addEventListener("click", async (event) => {
  const replyButton = event.target.closest("[data-ticket-reply]");
  if (replyButton) {
    const message = window.prompt("Support reply likho:");
    if (!message?.trim()) return;
    try {
      await replySupportTicket(Number(replyButton.dataset.ticketReply), message.trim());
    } catch (error) {
      setError(el.panelError, error.message);
    }
    return;
  }

  const button = event.target.closest("[data-ticket-id]");
  if (!button) return;
  try {
    await updateSupportTicket(Number(button.dataset.ticketId), button.dataset.ticketStatus);
  } catch (error) {
    setError(el.panelError, error.message);
  }
});

el.inventoryList.addEventListener("click", async (event) => {
  const deltaButton = event.target.closest("[data-stock-delta]");
  if (deltaButton) {
    const input = document.querySelector(
      `[data-stock-input="${deltaButton.dataset.productId}"]`
    );
    input.value = Math.max(0, Number(input.value) + Number(deltaButton.dataset.stockDelta));
    return;
  }

  const saveButton = event.target.closest("[data-save-stock]");
  if (!saveButton) return;

  const productId = Number(saveButton.dataset.saveStock);
  const stockInput = document.querySelector(`[data-stock-input="${productId}"]`);
  const reorderInput = document.querySelector(`[data-reorder-input="${productId}"]`);
  await updateStock(productId, Number(stockInput.value), Number(reorderInput.value));
});

el.productManageList.addEventListener("click", async (event) => {
  const saveButton = event.target.closest("[data-save-product]");
  if (!saveButton) return;
  await updateProduct(Number(saveButton.dataset.saveProduct));
});

el.productForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setError(el.panelError, "");
  try {
    await createProduct();
  } catch (error) {
    setError(el.panelError, error.message);
  }
});

el.categoryForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setError(el.panelError, "");
  try {
    await createCategory();
  } catch (error) {
    setError(el.panelError, error.message);
  }
});

renderShell();
if (state.token) {
  loadDashboard();
}
