import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  createAdminCategory,
  createAdminProduct,
  getAdminCategories,
  getAdminInventory,
  getAdminOrders,
  getAdminProducts,
  getAdminSummary,
  updateAdminCategory,
  updateAdminInventory,
  updateAdminOrderStatus,
  updateAdminProduct,
} from "../api/adminApi";
import { useAuth } from "../context/AuthContext";
import {
  formatCurrency,
  formatDateTime,
  formatLabel,
  formatPaymentMethod,
} from "../utils/formatters";

const orderStatuses = [
  "placed",
  "confirmed",
  "packing",
  "out_for_delivery",
  "delivered",
  "cancelled",
];

const emptyCategoryForm = {
  name: "",
  slug: "",
  display_order: 0,
  is_active: true,
};

const emptyProductForm = {
  category_id: "",
  name: "",
  slug: "",
  description: "",
  unit: "",
  icon: "",
  image_url: "",
  price: "",
  mrp: "",
  stock_quantity: 0,
  reorder_level: 10,
  is_active: true,
};

function categoryEdit(category) {
  return {
    name: category.name,
    slug: category.slug,
    display_order: category.display_order,
    is_active: category.is_active,
  };
}

function productEdit(product) {
  return {
    category_id: product.category_id,
    name: product.name,
    slug: product.slug,
    description: product.description || "",
    unit: product.unit,
    icon: product.icon || "",
    image_url: product.image_url || "",
    price: product.price,
    mrp: product.mrp,
    stock_quantity: product.stock_quantity,
    reorder_level: product.reorder_level,
    is_active: product.is_active,
  };
}


function formatEta(order) {
  if (order.status === "cancelled") return "Cancelled";
  if (order.status === "delivered") return "Delivered";
  if (order.eta_minutes == null) return "Updating";
  return `${order.eta_minutes} min ETA`;
}

function AdminDashboard() {
  const { isAuthenticated, loading: authLoading, user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [orders, setOrders] = useState([]);
  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [categoryForm, setCategoryForm] = useState(emptyCategoryForm);
  const [productForm, setProductForm] = useState(emptyProductForm);
  const [categoryEdits, setCategoryEdits] = useState({});
  const [productEdits, setProductEdits] = useState({});
  const [inventoryEdits, setInventoryEdits] = useState({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState("");
  const [error, setError] = useState("");

  const isAdmin = user?.role === "admin";

  const loadAdminData = async () => {
    setLoading(true);
    setError("");
    try {
      const [
        nextSummary,
        nextOrders,
        nextCategories,
        nextProducts,
        nextInventory,
      ] = await Promise.all([
        getAdminSummary(),
        getAdminOrders(),
        getAdminCategories(),
        getAdminProducts(),
        getAdminInventory(),
      ]);
      setSummary(nextSummary);
      setOrders(nextOrders);
      setCategories(nextCategories);
      setProducts(nextProducts);
      setCategoryEdits(
        Object.fromEntries(
          nextCategories.map((category) => [category.id, categoryEdit(category)])
        )
      );
      setProductEdits(
        Object.fromEntries(
          nextProducts.map((product) => [product.id, productEdit(product)])
        )
      );
      setInventory(nextInventory);
      setInventoryEdits(
        Object.fromEntries(
          nextInventory.map((item) => [
            item.product_id,
            {
              stock_quantity: item.stock_quantity,
              reorder_level: item.reorder_level,
              is_active: item.is_active,
            },
          ])
        )
      );
    } catch (adminError) {
      setError(adminError.response?.data?.detail || "We could not load the dashboard.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isAuthenticated || !isAdmin) return;
    loadAdminData();
  }, [isAuthenticated, isAdmin]);

  useEffect(() => {
    if (categories.length === 0) return;
    setProductForm((current) =>
      current.category_id ? current : { ...current, category_id: categories[0].id }
    );
  }, [categories]);

  const handleStatusChange = async (orderId, status) => {
    setSaving(`order-${orderId}`);
    setError("");
    try {
      const updatedOrder = await updateAdminOrderStatus(orderId, status);
      setOrders((current) =>
        current.map((order) => (order.id === orderId ? updatedOrder : order))
      );
      setSummary(await getAdminSummary());
    } catch (adminError) {
      setError(adminError.response?.data?.detail || "We could not update this order.");
    } finally {
      setSaving("");
    }
  };

  const updateCategoryForm = (field, value) => {
    setCategoryForm((current) => ({ ...current, [field]: value }));
  };

  const updateCategoryEdit = (categoryId, field, value) => {
    setCategoryEdits((current) => ({
      ...current,
      [categoryId]: {
        ...current[categoryId],
        [field]: value,
      },
    }));
  };

  const handleCategoryCreate = async (event) => {
    event.preventDefault();
    setSaving("category-new");
    setError("");
    try {
      const createdCategory = await createAdminCategory({
        ...categoryForm,
        display_order: Number(categoryForm.display_order),
      });
      setCategories((current) => [...current, createdCategory]);
      setCategoryEdits((current) => ({
        ...current,
        [createdCategory.id]: categoryEdit(createdCategory),
      }));
      setCategoryForm(emptyCategoryForm);
    } catch (adminError) {
      setError(adminError.response?.data?.detail || "We could not create this category.");
    } finally {
      setSaving("");
    }
  };

  const handleCategorySave = async (categoryId) => {
    setSaving(`category-${categoryId}`);
    setError("");
    try {
      const edit = categoryEdits[categoryId];
      const updatedCategory = await updateAdminCategory(categoryId, {
        ...edit,
        display_order: Number(edit.display_order),
      });
      setCategories((current) =>
        current.map((category) =>
          category.id === categoryId ? updatedCategory : category
        )
      );
      setCategoryEdits((current) => ({
        ...current,
        [categoryId]: categoryEdit(updatedCategory),
      }));
    } catch (adminError) {
      setError(adminError.response?.data?.detail || "We could not update this category.");
    } finally {
      setSaving("");
    }
  };

  const updateProductForm = (field, value) => {
    setProductForm((current) => ({ ...current, [field]: value }));
  };

  const updateProductEdit = (productId, field, value) => {
    setProductEdits((current) => ({
      ...current,
      [productId]: {
        ...current[productId],
        [field]: value,
      },
    }));
  };

  const productPayload = (data) => ({
    ...data,
    category_id: Number(data.category_id),
    price: Number(data.price),
    mrp: Number(data.mrp),
    stock_quantity: Number(data.stock_quantity),
    reorder_level: Number(data.reorder_level),
  });

  const refreshCatalogAfterProductChange = async () => {
    const [nextSummary, nextProducts, nextInventory] = await Promise.all([
      getAdminSummary(),
      getAdminProducts(),
      getAdminInventory(),
    ]);
    setSummary(nextSummary);
    setProducts(nextProducts);
    setProductEdits(
      Object.fromEntries(
        nextProducts.map((product) => [product.id, productEdit(product)])
      )
    );
    setInventory(nextInventory);
  };

  const handleProductCreate = async (event) => {
    event.preventDefault();
    setSaving("product-new");
    setError("");
    try {
      await createAdminProduct(productPayload(productForm));
      await refreshCatalogAfterProductChange();
      setProductForm({
        ...emptyProductForm,
        category_id: categories[0]?.id || "",
      });
    } catch (adminError) {
      setError(adminError.response?.data?.detail || "We could not create this product.");
    } finally {
      setSaving("");
    }
  };

  const handleProductSave = async (productId) => {
    setSaving(`product-${productId}`);
    setError("");
    try {
      await updateAdminProduct(productId, productPayload(productEdits[productId]));
      await refreshCatalogAfterProductChange();
    } catch (adminError) {
      setError(adminError.response?.data?.detail || "We could not update this product.");
    } finally {
      setSaving("");
    }
  };

  const updateInventoryEdit = (productId, field, value) => {
    setInventoryEdits((current) => ({
      ...current,
      [productId]: {
        ...current[productId],
        [field]: value,
      },
    }));
  };

  const handleInventorySave = async (productId) => {
    setSaving(`inventory-${productId}`);
    setError("");
    try {
      const edit = inventoryEdits[productId];
      const updatedItem = await updateAdminInventory(productId, {
        stock_quantity: Number(edit.stock_quantity),
        reorder_level: Number(edit.reorder_level),
        is_active: Boolean(edit.is_active),
      });
      setInventory((current) =>
        current.map((item) => (item.product_id === productId ? updatedItem : item))
      );
      setSummary(await getAdminSummary());
    } catch (adminError) {
      setError(adminError.response?.data?.detail || "We could not update inventory.");
    } finally {
      setSaving("");
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
          <h2>Admin login required</h2>
          <p>Login with the development admin account to manage the store.</p>
          <Link className="button" to="/login">
            Login to continue
          </Link>
        </div>
      </section>
    );
  }

  if (!isAdmin) {
    return (
      <section className="container page-section">
        <div className="status-card error-card">
          <h2>Admin access required</h2>
          <p>This dashboard is only available to admin users.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="container page-section">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Store control room</span>
          <h1>Admin dashboard</h1>
        </div>
        <button className="button button-secondary" onClick={loadAdminData}>
          Refresh
        </button>
      </div>

      {loading && <p className="status-card">Opening the store dashboard...</p>}
      {error && <p className="form-error">{error}</p>}

      {summary && (
        <div className="admin-summary-grid">
          <article>
            <span>Total orders</span>
            <strong>{summary.total_orders}</strong>
          </article>
          <article>
            <span>Open orders</span>
            <strong>{summary.open_orders}</strong>
          </article>
          <article>
            <span>Active products</span>
            <strong>{summary.active_products}</strong>
          </article>
          <article>
            <span>Low stock</span>
            <strong>{summary.low_stock_items}</strong>
          </article>
          <article>
            <span>Revenue</span>
            <strong>
              {formatCurrency(summary.total_revenue)}
            </strong>
          </article>
        </div>
      )}

      <div className="admin-layout">
        <section className="checkout-card">
          <div className="admin-section-heading">
            <h2>Recent orders</h2>
            <small>Update fulfillment status as orders move forward.</small>
          </div>
          <div className="admin-list">
            {orders.length === 0 && <p>No live orders at the moment.</p>}
            {orders.map((order) => (
              <article className="admin-order-row" key={order.id}>
                <div>
                  <span className="order-card-label">#{order.order_number}</span>
                  <h3>
                    {formatCurrency(order.total)} - {order.customer_name}
                  </h3>
                  <p>
                    {order.item_count} item{order.item_count === 1 ? "" : "s"} -
                    {order.delivery_city || "No city"} - {formatDateTime(order.created_at)}
                  </p>
                  <div className="admin-order-meta">
                    <span>{formatEta(order)}</span>
                    <span>
                      {order.delivery_partner
                        ? order.delivery_partner.name
                        : "Partner pending"}
                    </span>
                    <span>
                      {formatPaymentMethod(order.payment_method)} -{" "}
                      {formatLabel(order.payment_status)}
                    </span>
                  </div>
                  <p>{order.tracking_message}</p>
                </div>
                <div className="admin-order-actions">
                  <span className={`status-pill status-${order.status}`}>
                    {formatLabel(order.status)}
                  </span>
                  <select
                    disabled={saving === `order-${order.id}`}
                    onChange={(event) =>
                      handleStatusChange(order.id, event.target.value)
                    }
                    value={order.status}
                  >
                    {orderStatuses.map((status) => (
                      <option key={status} value={status}>
                        {formatLabel(status)}
                      </option>
                    ))}
                  </select>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="checkout-card">
          <div className="admin-section-heading">
            <h2>Categories</h2>
            <small>Create aisles and control public category visibility.</small>
          </div>
          <form className="admin-form-grid" onSubmit={handleCategoryCreate}>
            <label>
              Name
              <input
                required
                onChange={(event) => updateCategoryForm("name", event.target.value)}
                value={categoryForm.name}
              />
            </label>
            <label>
              Slug
              <input
                onChange={(event) => updateCategoryForm("slug", event.target.value)}
                placeholder="Auto from name"
                value={categoryForm.slug}
              />
            </label>
            <label>
              Order
              <input
                min="0"
                onChange={(event) =>
                  updateCategoryForm("display_order", event.target.value)
                }
                type="number"
                value={categoryForm.display_order}
              />
            </label>
            <label className="admin-checkbox-label">
              <input
                checked={categoryForm.is_active}
                onChange={(event) =>
                  updateCategoryForm("is_active", event.target.checked)
                }
                type="checkbox"
              />
              Active
            </label>
            <button
              className="button button-small"
              disabled={saving === "category-new"}
            >
              Add category
            </button>
          </form>

          <div className="admin-list">
            {categories.map((category) => {
              const edit = categoryEdits[category.id] || categoryEdit(category);
              return (
                <article className="category-admin-row" key={category.id}>
                  <label>
                    Name
                    <input
                      onChange={(event) =>
                        updateCategoryEdit(category.id, "name", event.target.value)
                      }
                      value={edit.name}
                    />
                  </label>
                  <label>
                    Slug
                    <input
                      onChange={(event) =>
                        updateCategoryEdit(category.id, "slug", event.target.value)
                      }
                      value={edit.slug}
                    />
                  </label>
                  <label>
                    Order
                    <input
                      min="0"
                      onChange={(event) =>
                        updateCategoryEdit(
                          category.id,
                          "display_order",
                          event.target.value
                        )
                      }
                      type="number"
                      value={edit.display_order}
                    />
                  </label>
                  <label className="admin-checkbox-label">
                    <input
                      checked={Boolean(edit.is_active)}
                      onChange={(event) =>
                        updateCategoryEdit(
                          category.id,
                          "is_active",
                          event.target.checked
                        )
                      }
                      type="checkbox"
                    />
                    Active
                  </label>
                  <small>{category.product_count} products</small>
                  <button
                    className="button button-small"
                    disabled={saving === `category-${category.id}`}
                    onClick={() => handleCategorySave(category.id)}
                    type="button"
                  >
                    Save
                  </button>
                </article>
              );
            })}
          </div>
        </section>

        <section className="checkout-card">
          <div className="admin-section-heading">
            <h2>Add product</h2>
            <small>Create a catalog item with starting stock.</small>
          </div>
          <form className="product-admin-form" onSubmit={handleProductCreate}>
            <label>
              Category
              <select
                required
                onChange={(event) =>
                  updateProductForm("category_id", event.target.value)
                }
                value={productForm.category_id}
              >
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Name
              <input
                required
                onChange={(event) => updateProductForm("name", event.target.value)}
                value={productForm.name}
              />
            </label>
            <label>
              Slug
              <input
                onChange={(event) => updateProductForm("slug", event.target.value)}
                placeholder="Auto from name"
                value={productForm.slug}
              />
            </label>
            <label>
              Unit
              <input
                required
                onChange={(event) => updateProductForm("unit", event.target.value)}
                placeholder="500 g"
                value={productForm.unit}
              />
            </label>
            <label>
              Icon
              <input
                onChange={(event) => updateProductForm("icon", event.target.value)}
                placeholder="SN"
                value={productForm.icon}
              />
            </label>
            <label>
              Price
              <input
                min="0"
                onChange={(event) => updateProductForm("price", event.target.value)}
                required
                type="number"
                value={productForm.price}
              />
            </label>
            <label>
              MRP
              <input
                min="0"
                onChange={(event) => updateProductForm("mrp", event.target.value)}
                required
                type="number"
                value={productForm.mrp}
              />
            </label>
            <label>
              Stock
              <input
                min="0"
                onChange={(event) =>
                  updateProductForm("stock_quantity", event.target.value)
                }
                type="number"
                value={productForm.stock_quantity}
              />
            </label>
            <label>
              Reorder
              <input
                min="0"
                onChange={(event) =>
                  updateProductForm("reorder_level", event.target.value)
                }
                type="number"
                value={productForm.reorder_level}
              />
            </label>
            <label>
              Image URL
              <input
                onChange={(event) =>
                  updateProductForm("image_url", event.target.value)
                }
                value={productForm.image_url}
              />
            </label>
            <label className="admin-wide-field">
              Description
              <textarea
                onChange={(event) =>
                  updateProductForm("description", event.target.value)
                }
                value={productForm.description}
              />
            </label>
            <label className="admin-checkbox-label">
              <input
                checked={productForm.is_active}
                onChange={(event) =>
                  updateProductForm("is_active", event.target.checked)
                }
                type="checkbox"
              />
              Active
            </label>
            <button
              className="button button-small"
              disabled={saving === "product-new"}
            >
              Add product
            </button>
          </form>
        </section>

        <section className="checkout-card">
          <div className="admin-section-heading">
            <h2>Catalog editor</h2>
            <small>Edit product details, pricing, status, and stock together.</small>
          </div>
          <div className="admin-list">
            {products.map((product) => {
              const edit = productEdits[product.id] || productEdit(product);
              return (
                <article className="product-admin-row" key={product.id}>
                  <div className="inventory-product">
                    {product.image_url ? (
                      <img src={product.image_url} alt="" loading="lazy" />
                    ) : (
                      <span>{product.name[0]}</span>
                    )}
                    <div>
                      <strong>{product.name}</strong>
                      <small>
                        {product.category} - available {product.available_quantity}
                      </small>
                      {product.low_stock && <em>Low stock</em>}
                    </div>
                  </div>
                  <label>
                    Name
                    <input
                      onChange={(event) =>
                        updateProductEdit(product.id, "name", event.target.value)
                      }
                      value={edit.name}
                    />
                  </label>
                  <label>
                    Category
                    <select
                      onChange={(event) =>
                        updateProductEdit(
                          product.id,
                          "category_id",
                          event.target.value
                        )
                      }
                      value={edit.category_id}
                    >
                      {categories.map((category) => (
                        <option key={category.id} value={category.id}>
                          {category.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Price
                    <input
                      min="0"
                      onChange={(event) =>
                        updateProductEdit(product.id, "price", event.target.value)
                      }
                      type="number"
                      value={edit.price}
                    />
                  </label>
                  <label>
                    MRP
                    <input
                      min="0"
                      onChange={(event) =>
                        updateProductEdit(product.id, "mrp", event.target.value)
                      }
                      type="number"
                      value={edit.mrp}
                    />
                  </label>
                  <label>
                    Stock
                    <input
                      min="0"
                      onChange={(event) =>
                        updateProductEdit(
                          product.id,
                          "stock_quantity",
                          event.target.value
                        )
                      }
                      type="number"
                      value={edit.stock_quantity}
                    />
                  </label>
                  <label>
                    Reorder
                    <input
                      min="0"
                      onChange={(event) =>
                        updateProductEdit(
                          product.id,
                          "reorder_level",
                          event.target.value
                        )
                      }
                      type="number"
                      value={edit.reorder_level}
                    />
                  </label>
                  <label className="admin-checkbox-label">
                    <input
                      checked={Boolean(edit.is_active)}
                      onChange={(event) =>
                        updateProductEdit(
                          product.id,
                          "is_active",
                          event.target.checked
                        )
                      }
                      type="checkbox"
                    />
                    Active
                  </label>
                  <button
                    className="button button-small"
                    disabled={saving === `product-${product.id}`}
                    onClick={() => handleProductSave(product.id)}
                    type="button"
                  >
                    Save
                  </button>
                </article>
              );
            })}
          </div>
        </section>

        <section className="checkout-card">
          <div className="admin-section-heading">
            <h2>Inventory</h2>
            <small>Adjust stock, reorder level, and active catalog visibility.</small>
          </div>
          <div className="admin-list">
            {inventory.map((item) => {
              const edit = inventoryEdits[item.product_id] || item;
              return (
                <article className="inventory-row" key={item.product_id}>
                  <div className="inventory-product">
                    {item.image_url ? (
                      <img src={item.image_url} alt="" loading="lazy" />
                    ) : (
                      <span>{item.name[0]}</span>
                    )}
                    <div>
                      <strong>{item.name}</strong>
                      <small>
                        {item.category} - available {item.available_quantity}
                      </small>
                      {item.low_stock && <em>Low stock</em>}
                    </div>
                  </div>
                  <label>
                    Stock
                    <input
                      min="0"
                      onChange={(event) =>
                        updateInventoryEdit(
                          item.product_id,
                          "stock_quantity",
                          event.target.value
                        )
                      }
                      type="number"
                      value={edit.stock_quantity}
                    />
                  </label>
                  <label>
                    Reorder
                    <input
                      min="0"
                      onChange={(event) =>
                        updateInventoryEdit(
                          item.product_id,
                          "reorder_level",
                          event.target.value
                        )
                      }
                      type="number"
                      value={edit.reorder_level}
                    />
                  </label>
                  <label className="admin-checkbox-label">
                    <input
                      checked={Boolean(edit.is_active)}
                      onChange={(event) =>
                        updateInventoryEdit(
                          item.product_id,
                          "is_active",
                          event.target.checked
                        )
                      }
                      type="checkbox"
                    />
                    Active
                  </label>
                  <button
                    className="button button-small"
                    disabled={saving === `inventory-${item.product_id}`}
                    onClick={() => handleInventorySave(item.product_id)}
                  >
                    Save
                  </button>
                </article>
              );
            })}
          </div>
        </section>
      </div>
    </section>
  );
}

export default AdminDashboard;
