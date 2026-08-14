(() => {
  const tg = window.Telegram && window.Telegram.WebApp;
  if (tg) {
    tg.ready();
    tg.expand();
    try {
      tg.setHeaderColor("#e8f5ee");
      tg.setBackgroundColor("#f3f7f0");
    } catch (_) {
      /* eski klientlar */
    }
  }

  const CART_KEY = "miniapp_cart_v1";
  const state = {
    config: null,
    categories: [],
    products: [],
    categoryId: null,
    cart: loadCart(),
    bonusPoints: 0,
    discount: 0,
  };

  const els = {
    shopName: document.getElementById("shopName"),
    shopMeta: document.getElementById("shopMeta"),
    categories: document.getElementById("categories"),
    products: document.getElementById("products"),
    cartList: document.getElementById("cartList"),
    subtotalLabel: document.getElementById("subtotalLabel"),
    deliveryLabel: document.getElementById("deliveryLabel"),
    discountLabel: document.getElementById("discountLabel"),
    totalLabel: document.getElementById("totalLabel"),
    minOrderHint: document.getElementById("minOrderHint"),
    bonusHint: document.getElementById("bonusHint"),
    phone: document.getElementById("phone"),
    address: document.getElementById("address"),
    slot: document.getElementById("slot"),
    bonus: document.getElementById("bonus"),
    paymentMethod: document.getElementById("paymentMethod"),
    note: document.getElementById("note"),
    form: document.getElementById("checkoutForm"),
    submit: document.getElementById("submitOrder"),
    status: document.getElementById("orderStatus"),
    cartBadge: document.getElementById("cartBadge"),
    variantDialog: document.getElementById("variantDialog"),
    variantTitle: document.getElementById("variantTitle"),
    variantOptions: document.getElementById("variantOptions"),
  };

  function formatMoney(amount) {
    const n = Math.round(Number(amount) || 0);
    return `${String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ")} so'm`;
  }

  function loadCart() {
    try {
      const raw = localStorage.getItem(CART_KEY);
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  function saveCart() {
    localStorage.setItem(CART_KEY, JSON.stringify(state.cart));
  }

  function cartKey(productId, variantId) {
    return `${productId}:${variantId || 0}`;
  }

  function cartCount() {
    return state.cart.reduce((sum, item) => sum + item.quantity, 0);
  }

  function cartSubtotal() {
    return state.cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
  }

  function bonusSpentValue() {
    const raw = els.bonus ? Number(els.bonus.value || 0) : 0;
    if (!Number.isFinite(raw) || raw < 0) return 0;
    return Math.min(Math.floor(raw), state.bonusPoints || 0);
  }

  function deliveryFeeFor(subtotal) {
    const cfg = state.config || {};
    const thr = Number(cfg.delivery_fee_threshold) || 50000;
    const low = Number(cfg.delivery_fee_low) || 5000;
    const high =
      Number(cfg.delivery_fee_high) || Number(cfg.delivery_price) || 10000;
    if (!(subtotal > 0)) return 0;
    return subtotal <= thr ? low : high;
  }

  function calcTotals() {
    const subtotal = cartSubtotal();
    const discount = Math.max(0, Number(state.discount) || 0);
    const bonus = subtotal > 0 ? bonusSpentValue() : 0;
    const deliveryFee = deliveryFeeFor(subtotal);
    const total = Math.max(0, subtotal + deliveryFee - discount - bonus);
    return { subtotal, delivery: deliveryFee, discount, bonus, total };
  }

  async function api(path, options) {
    const res = await fetch(path, options);
    const text = await res.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = text;
    }
    if (!res.ok) {
      const msg =
        typeof data === "string"
          ? data
          : (data && (data.error || data.message)) || text || res.statusText;
      throw new Error(msg || "Xatolik");
    }
    return data;
  }

  function showView(name) {
    document.querySelectorAll(".view").forEach((el) => el.classList.remove("active"));
    document.querySelectorAll(".nav-btn").forEach((el) => el.classList.remove("active"));
    const view = name === "cart" ? "viewCart" : "viewCatalog";
    document.getElementById(view).classList.add("active");
    document
      .querySelector(`.nav-btn[data-view="${name === "cart" ? "cart" : "catalog"}"]`)
      .classList.add("active");
    if (name === "cart") renderCart();
  }

  function renderCategories() {
    els.categories.innerHTML = "";
    const all = document.createElement("button");
    all.type = "button";
    all.className = `chip${state.categoryId == null ? " active" : ""}`;
    all.textContent = "Hammasi";
    all.addEventListener("click", () => {
      state.categoryId = null;
      renderCategories();
      loadProducts();
    });
    els.categories.appendChild(all);

    state.categories.forEach((cat) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `chip${state.categoryId === cat.id ? " active" : ""}`;
      btn.textContent = cat.label || `${cat.emoji || "📦"} ${cat.name}`.trim();
      btn.addEventListener("click", () => {
        state.categoryId = cat.id;
        renderCategories();
        loadProducts();
      });
      els.categories.appendChild(btn);
    });
  }

  function photoEl(product) {
    if (product.photo_url) {
      const img = document.createElement("img");
      img.className = "card-photo";
      img.alt = product.name;
      img.loading = "lazy";
      img.src = product.photo_url;
      img.onerror = () => {
        img.replaceWith(placeholderEl(product.name));
      };
      return img;
    }
    return placeholderEl(product.name);
  }

  function placeholderEl(name) {
    const div = document.createElement("div");
    div.className = "card-photo placeholder";
    div.textContent = (name || "?").trim().charAt(0).toUpperCase();
    return div;
  }

  function renderProducts() {
    els.products.innerHTML = "";
    if (!state.products.length) {
      els.products.innerHTML = `<p class="empty">Mahsulotlar topilmadi</p>`;
      return;
    }

    state.products.forEach((product) => {
      const card = document.createElement("article");
      card.className = "card";
      card.appendChild(photoEl(product));

      const body = document.createElement("div");
      body.className = "card-body";
      body.innerHTML = `
        <h3 class="card-title"></h3>
        <p class="card-price"></p>
      `;
      body.querySelector(".card-title").textContent = product.name;
      body.querySelector(".card-price").textContent =
        product.display_price || formatMoney(product.price);

      const addBtn = document.createElement("button");
      addBtn.type = "button";
      addBtn.className = "btn add";
      addBtn.textContent = "Qo'shish";
      addBtn.addEventListener("click", () => addProduct(product));
      body.appendChild(addBtn);

      card.appendChild(body);
      els.products.appendChild(card);
    });
  }

  function addProduct(product) {
    const variants = product.variants || [];
    if (variants.length) {
      openVariantPicker(product);
      return;
    }
    upsertCartItem({
      product_id: product.id,
      variant_id: 0,
      name: product.name,
      price: product.price,
      quantity: 1,
    });
  }

  function openVariantPicker(product) {
    els.variantTitle.textContent = product.name;
    els.variantOptions.innerHTML = "";
    (product.variants || []).forEach((v) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = `${v.name} — ${formatMoney(v.price)}`;
      btn.addEventListener("click", () => {
        upsertCartItem({
          product_id: product.id,
          variant_id: v.id,
          name: `${product.name} (${v.name})`,
          price: v.price,
          quantity: 1,
        });
        els.variantDialog.close();
      });
      els.variantOptions.appendChild(btn);
    });
    els.variantDialog.showModal();
  }

  function upsertCartItem(item) {
    const key = cartKey(item.product_id, item.variant_id);
    const existing = state.cart.find(
      (c) => cartKey(c.product_id, c.variant_id) === key
    );
    if (existing) {
      existing.quantity += item.quantity;
    } else {
      state.cart.push({ ...item });
    }
    saveCart();
    updateBadge();
    if (document.getElementById("viewCart").classList.contains("active")) {
      renderCart();
    }
  }

  function setQty(productId, variantId, delta) {
    const key = cartKey(productId, variantId);
    const item = state.cart.find((c) => cartKey(c.product_id, c.variant_id) === key);
    if (!item) return;
    item.quantity += delta;
    if (item.quantity <= 0) {
      state.cart = state.cart.filter(
        (c) => cartKey(c.product_id, c.variant_id) !== key
      );
    }
    saveCart();
    updateBadge();
    renderCart();
  }

  function updateBadge() {
    const count = cartCount();
    els.cartBadge.hidden = count === 0;
    els.cartBadge.textContent = String(count);
  }

  function renderCart() {
    const minOrder = state.config ? state.config.min_order : 0;
    const { subtotal, delivery, discount, bonus, total } = calcTotals();

    els.subtotalLabel.textContent = formatMoney(subtotal);
    els.deliveryLabel.textContent = formatMoney(delivery);
    if (els.discountLabel) {
      const off = discount + bonus;
      els.discountLabel.textContent =
        off > 0 ? `−${formatMoney(off)}` : formatMoney(0);
    }
    els.totalLabel.textContent = formatMoney(total);

    if (subtotal > 0 && subtotal < minOrder) {
      els.minOrderHint.textContent = `Minimal buyurtma: ${formatMoney(minOrder)}`;
    } else {
      els.minOrderHint.textContent = "";
    }

    if (els.bonusHint) {
      els.bonusHint.textContent = state.bonusPoints
        ? `Bonus balansi: ${formatMoney(state.bonusPoints)}`
        : "";
    }

    els.submit.disabled = state.cart.length === 0 || subtotal < minOrder;

    if (!state.cart.length) {
      els.cartList.innerHTML = `<p class="empty">Savatcha bo'sh. Katalogdan mahsulot qo'shing.</p>`;
      return;
    }

    els.cartList.innerHTML = "";
    state.cart.forEach((item) => {
      const row = document.createElement("div");
      row.className = "cart-item";
      row.innerHTML = `
        <div>
          <h4></h4>
          <p></p>
        </div>
        <div class="qty">
          <button type="button" data-act="dec">−</button>
          <span></span>
          <button type="button" data-act="inc">+</button>
        </div>
      `;
      row.querySelector("h4").textContent = item.name;
      row.querySelector("p").textContent = `${formatMoney(item.price)} × ${item.quantity}`;
      row.querySelector("span").textContent = String(item.quantity);
      row.querySelector('[data-act="dec"]').addEventListener("click", () =>
        setQty(item.product_id, item.variant_id, -1)
      );
      row.querySelector('[data-act="inc"]').addEventListener("click", () =>
        setQty(item.product_id, item.variant_id, 1)
      );
      els.cartList.appendChild(row);
    });
  }

  function fillSlots() {
    const slots = (state.config && state.config.slots) || [];
    els.slot.innerHTML = "";
    if (!slots.length) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "Hozircha slot yo'q";
      els.slot.appendChild(opt);
      return;
    }
    slots.forEach((s, i) => {
      const opt = document.createElement("option");
      opt.value = s;
      opt.textContent = s;
      if (i === 0) opt.selected = true;
      els.slot.appendChild(opt);
    });
  }

  async function loadProducts() {
    const q =
      state.categoryId != null
        ? `/api/products?category_id=${encodeURIComponent(state.categoryId)}`
        : "/api/products";
    state.products = await api(q);
    renderProducts();
  }

  async function loadUserBonus() {
    const initData = getInitData();
    if (!initData) return;
    try {
      const data = await api(`/api/user?initData=${encodeURIComponent(initData)}`, {
        headers: { "X-Telegram-Init-Data": initData },
      });
      state.bonusPoints = Number(data.bonus_points) || 0;
      if (els.bonus) {
        els.bonus.max = String(state.bonusPoints);
        els.bonus.placeholder = state.bonusPoints
          ? `0 — ${state.bonusPoints}`
          : "0";
      }
      if (els.bonusHint) {
        els.bonusHint.textContent = state.bonusPoints
          ? `Bonus balansi: ${formatMoney(state.bonusPoints)}`
          : "";
      }
    } catch (_) {
      state.bonusPoints = 0;
    }
  }

  async function bootstrap() {
    document.querySelectorAll(".nav-btn").forEach((btn) => {
      btn.addEventListener("click", () => showView(btn.dataset.view));
    });

    els.form.addEventListener("submit", onCheckout);

    if (els.bonus) {
      els.bonus.addEventListener("input", () => renderCart());
      els.bonus.addEventListener("change", () => renderCart());
    }

    const [config, categories] = await Promise.all([
      api("/api/config"),
      api("/api/categories"),
    ]);
    state.config = config;
    state.categories = categories;

    els.shopName.textContent = config.shop_name || "Do'kon";
    const metaParts = [config.shop_hours, config.shop_phone].filter(Boolean);
    els.shopMeta.textContent = metaParts.join(" · ");

    if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
      const u = tg.initDataUnsafe.user;
      if (!els.phone.value && u.phone_number) {
        els.phone.value = u.phone_number;
      }
    }

    fillSlots();
    renderCategories();
    updateBadge();
    await Promise.all([loadProducts(), loadUserBonus()]);
  }

  function getInitData() {
    if (!tg) return "";
    try {
      tg.ready();
    } catch (_) {}
    return tg.initData || "";
  }

  function getTelegramUser() {
    const u = tg && tg.initDataUnsafe && tg.initDataUnsafe.user;
    if (!u || !u.id) return null;
    return {
      id: u.id,
      first_name: u.first_name || "",
      last_name: u.last_name || "",
      username: u.username || "",
    };
  }

  function checkoutViaSendData(payload) {
    if (!tg || typeof tg.sendData !== "function") return false;
    try {
      tg.sendData(
        JSON.stringify({
          action: "checkout",
          phone: payload.phone,
          address: payload.address,
          slot: payload.slot,
          note: payload.note,
          items: payload.items,
          promo_code: payload.promo_code || "",
          bonus_spent: payload.bonus_spent || 0,
          payment_method: payload.payment_method || "pending",
        })
      );
      return true;
    } catch (_) {
      return false;
    }
  }

  async function onCheckout(event) {
    event.preventDefault();
    els.status.hidden = true;
    els.status.classList.remove("error");

    if (!state.cart.length) {
      els.status.hidden = false;
      els.status.classList.add("error");
      els.status.textContent = "Savatcha bo'sh";
      return;
    }

    const initData = getInitData();
    const telegramUser = getTelegramUser();
    const params = new URLSearchParams(window.location.search);
    const devUser = params.get("dev_user_id");
    const { bonus } = calcTotals();

    const payload = {
      initData,
      telegram_user: telegramUser,
      phone: els.phone.value.trim(),
      address: els.address.value.trim(),
      slot: els.slot.value,
      note: els.note.value.trim(),
      promo_code: "",
      bonus_spent: bonus,
      payment_method: (els.paymentMethod && els.paymentMethod.value) || "pending",
      items: state.cart.map((item) => ({
        product_id: item.product_id,
        quantity: item.quantity,
        variant_id: item.variant_id || undefined,
      })),
    };
    if (devUser && !payload.initData && !telegramUser) {
      payload.dev_user_id = Number(devUser);
    }

    els.submit.disabled = true;
    els.submit.textContent = "Yuborilmoqda...";

    // 1) Eng ishonchli: botga sendData (klaviatura Do'kon tugmasi)
    if (checkoutViaSendData(payload)) {
      state.cart = [];
      state.discount = 0;
      if (els.bonus) els.bonus.value = "";
      saveCart();
      updateBadge();
      renderCart();
      els.status.hidden = false;
      els.status.classList.remove("error");
      els.status.textContent = "Buyurtma botga yuborildi…";
      els.submit.disabled = true;
      els.submit.textContent = "Yuborildi ✓";
      if (tg) {
        try {
          tg.HapticFeedback && tg.HapticFeedback.notificationOccurred("success");
        } catch (_) {}
        setTimeout(() => {
          try {
            tg.close();
          } catch (_) {}
        }, 1200);
      }
      return;
    }

    // 2) API orqali (Menu Button / ba'zi klientlar)
    if (!initData && !telegramUser && !payload.dev_user_id) {
      els.status.hidden = false;
      els.status.classList.add("error");
      els.status.textContent =
        "Telegram orqali ochilmagan. Botdan «🛒 Do'kon» tugmasini bosing.";
      els.submit.disabled = false;
      els.submit.textContent = "Buyurtma berish";
      return;
    }

    try {
      const result = await api("/api/order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      state.cart = [];
      state.discount = 0;
      if (els.bonus) els.bonus.value = "";
      saveCart();
      updateBadge();
      await loadUserBonus();
      renderCart();
      els.status.hidden = false;
      els.status.textContent = `Buyurtma #${result.order_id} qabul qilindi!`;
      els.submit.disabled = true;
      els.submit.textContent = "Yuborildi ✓";
      if (tg) {
        try {
          tg.HapticFeedback && tg.HapticFeedback.notificationOccurred("success");
        } catch (_) {}
        setTimeout(() => {
          try {
            tg.close();
          } catch (_) {}
        }, 1800);
      }
    } catch (err) {
      els.status.hidden = false;
      els.status.classList.add("error");
      els.status.textContent = err.message || "Buyurtma yuborilmadi";
      els.submit.disabled = false;
      els.submit.textContent = "Buyurtma berish";
      renderCart();
    }
  }

  bootstrap().catch((err) => {
    els.products.innerHTML = `<p class="empty">Yuklash xatosi: ${err.message}</p>`;
  });
})();
