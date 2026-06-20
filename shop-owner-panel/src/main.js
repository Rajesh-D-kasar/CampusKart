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
  inventory: [],
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
  lowStockList: document.querySelector("#low-stock-list"),
  inventorySearch: document.querySelector("#inventory-search"),
  inventoryList: document.querySelector("#inventory-list"),
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
    const [summary, orders, inventory, categories] = await Promise.all([
      apiFetch("/admin/summary"),
      apiFetch("/admin/orders"),
      apiFetch("/admin/inventory"),
      apiFetch("/admin/categories"),
    ]);
    state.summary = summary;
    state.orders = orders;
    state.inventory = inventory;
    state.categories = categories;
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
  if (order.status === "packing") actions.push(["Send for delivery", "out_for_delivery"]);
  if (order.status === "out_for_delivery") actions.push(["Mark delivered", "delivered"]);
  if (!["delivered", "cancelled"].includes(order.status)) {
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
      <div class="action-row">
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

function renderDashboard() {
  renderShell();
  renderStats();
  renderOrderTabs();
  renderOrders();
  renderLowStock();
  renderInventory();
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
  const button = event.target.closest("[data-order-id]");
  if (!button) return;
  await updateOrderStatus(Number(button.dataset.orderId), button.dataset.orderStatus);
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
