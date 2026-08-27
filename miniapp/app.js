(() => {
  const tg = window.Telegram && window.Telegram.WebApp;
  if (tg) {
    tg.ready();
    tg.expand();
    try {
      tg.setHeaderColor("#e8f5e4");
      tg.setBackgroundColor("#eef6ea");
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
    giftPromo: document.getElementById("giftPromo"),
    giftPromoText: document.getElementById("giftPromoText"),
    giftProgress: document.getElementById("giftProgress"),
    categories: document.getElementById("categories"),
    products: document.getElementById("products"),
    cartList: document.getElementById("cartList"),
    subtotalLabel: document.getElementById("subtotalLabel"),
    deliveryLabel: document.getElementById("deliveryLabel"),
    discountLabel: document.getElementById("discountLabel"),
    totalLabel: document.getElementById("totalLabel"),
    deliveryRates: document.getElementById("deliveryRates"),
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

  function cartKey(item) {
    const productId = item.product_id;
    const variantId = item.variant_id || 0;
    const grams = item.pack_grams || 0;
    const amount = item.pack_amount || 0;
    const ml = item.pack_ml || 0;
    return `${productId}:${variantId}:${grams}:${amount}:${ml}`;
  }

  function hasSizeChoice(product) {
    return (
      (product.variants && product.variants.length > 0) ||
      (product.kg_packs && product.kg_packs.length > 0) ||
      (product.kg_money && product.kg_money.length > 0) ||
      (product.liter_packs && product.liter_packs.length > 0) ||
      (product.piece_packs && product.piece_packs.length > 0) ||
      product.ask_qty
    );
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

  function deliveryRatesText() {
    const cfg = state.config || {};
    const thr = Number(cfg.delivery_fee_threshold) || 50000;
    const low = Number(cfg.delivery_fee_low) || 5000;
    const high =
      Number(cfg.delivery_fee_high) || Number(cfg.delivery_price) || 10000;
    const fmt = (n) => formatMoney(n).replace(" so'm", "");
    return (
      `Yetkazish narxi: ${fmt(thr)} so‘mgacha — ${fmt(low)} so‘m; ` +
      `${fmt(thr)} so‘mdan yuqori — ${fmt(high)} so‘m`
    );
  }

  function giftThreshold() {
    return Number((state.config || {}).gift_drink_threshold) || 100000;
  }

  function giftPromoText() {
    const thr = formatMoney(giftThreshold()).replace(" so'm", "");
    return (
      `🎁 SUPER AKSIYA! ${thr} so‘m+ buyurtmaga BEPUL 1L ichimlik: ` +
      `🥤 Coca-Cola · 🔵 Pepsi · 🧡 Fanta`
    );
  }

  function giftProgressText(subtotal) {
    const thr = giftThreshold();
    if (subtotal >= thr) {
      return "🎉 Tabriklaymiz! Sovg‘angiz tayyor — tanlang: 🥤 Coca-Cola · 🔵 Pepsi · 🧡 Fanta (1L)";
    }
    const left = thr - subtotal;
    return (
      `🎁 Yana ${formatMoney(left)} qo‘shsangiz — BEPUL 🥤 Coca-Cola / 🔵 Pepsi / 🧡 Fanta 1L!`
    );
  }

  function fireCelebration() {
    const DURATION_MS = 5000;
    // 1) Full-screen overlay (kamida 4–5 soniya)
    const overlay = document.createElement("div");
    overlay.setAttribute("aria-hidden", "true");
    Object.assign(overlay.style, {
      position: "fixed",
      inset: "0",
      zIndex: "10000",
      pointerEvents: "none",
      display: "grid",
      placeItems: "center",
      background:
        "radial-gradient(ellipse at center, rgba(0,80,60,0.55), rgba(0,0,0,0.72))",
      fontSize: "clamp(2.8rem, 12vw, 4.5rem)",
      textAlign: "center",
      lineHeight: "1.35",
      animation: "celebratePop 0.55s ease",
    });
    overlay.innerHTML =
      "🎊🎆🎈<br/><b style='color:#fff;font-size:0.42em;font-family:system-ui,sans-serif;" +
      "letter-spacing:0.04em;text-shadow:0 2px 12px rgba(0,0,0,.5)'>BONUS SOHIBI!</b>" +
      "<br/><span style='color:#ffe9a8;font-size:0.28em;font-family:system-ui,sans-serif;" +
      "text-shadow:0 2px 10px rgba(0,0,0,.55)'>🎁 1L Coca-Cola / Pepsi / Fanta</span>" +
      "<br/>🎆🎉🎈";
    if (!document.getElementById("celebrate-style")) {
      const style = document.createElement("style");
      style.id = "celebrate-style";
      style.textContent = `
        @keyframes celebratePop {
          from { opacity: 0; transform: scale(0.65); }
          to { opacity: 1; transform: scale(1); }
        }
        @keyframes celebrateFloat {
          0% { transform: translateY(0) rotate(0deg); opacity: 1; }
          100% { transform: translateY(-120vh) rotate(48deg); opacity: 0; }
        }
        @keyframes celebratePulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.06); }
        }
      `;
      document.head.appendChild(style);
    }
    overlay.style.animation =
      "celebratePop 0.55s ease, celebratePulse 1.2s ease-in-out 0.55s infinite";
    document.body.appendChild(overlay);

    // 2) Floating emojis (juda ko‘rinadigan)
    const emojis = ["🎈", "🎉", "✨", "💎", "🎊", "⭐", "🎆", "🎇", "💫"];
    const floatNodes = [];
    for (let i = 0; i < 42; i++) {
      const span = document.createElement("span");
      span.textContent = emojis[i % emojis.length];
      Object.assign(span.style, {
        position: "fixed",
        left: `${Math.random() * 100}%`,
        bottom: "-2.5rem",
        fontSize: `${1.4 + Math.random() * 2.2}rem`,
        zIndex: "10001",
        pointerEvents: "none",
        animation: `celebrateFloat ${2.4 + Math.random() * 2.2}s ease-out forwards`,
        animationDelay: `${Math.random() * 1.1}s`,
      });
      document.body.appendChild(span);
      floatNodes.push(span);
    }

    // 3) Canvas confetti (katta, to‘liq ekran)
    const canvas = document.createElement("canvas");
    Object.assign(canvas.style, {
      position: "fixed",
      inset: "0",
      width: "100%",
      height: "100%",
      pointerEvents: "none",
      zIndex: "9999",
    });
    document.body.appendChild(canvas);
    const ctx = canvas.getContext("2d");
    let raf = 0;
    if (ctx) {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.floor(window.innerWidth * dpr);
      canvas.height = Math.floor(window.innerHeight * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const palette = [
        "#e63946",
        "#f4a261",
        "#2a9d8f",
        "#457b9d",
        "#e9c46a",
        "#ff006e",
        "#ffffff",
      ];
      const parts = [];
      const spawnBurst = (ox, oy) => {
        for (let i = 0; i < 55; i++) {
          const ang = -Math.PI / 2 + (Math.random() - 0.5) * 1.6;
          const sp = 5 + Math.random() * 11;
          parts.push({
            x: ox,
            y: oy,
            vx: Math.cos(ang) * sp,
            vy: Math.sin(ang) * sp,
            r: 2.5 + Math.random() * 5,
            c: palette[(Math.random() * palette.length) | 0],
            a: 1,
            rot: Math.random() * Math.PI,
            vr: (Math.random() - 0.5) * 0.3,
          });
        }
      };
      for (let b = 0; b < 6; b++) {
        spawnBurst(window.innerWidth * (0.1 + 0.16 * b), window.innerHeight * 0.78);
      }
      // mid-burst for visibility
      setTimeout(() => {
        spawnBurst(window.innerWidth * 0.5, window.innerHeight * 0.55);
        spawnBurst(window.innerWidth * 0.25, window.innerHeight * 0.65);
        spawnBurst(window.innerWidth * 0.75, window.innerHeight * 0.65);
      }, 900);

      const start = performance.now();
      const tick = (now) => {
        const elapsed = now - start;
        ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
        for (const p of parts) {
          p.x += p.vx;
          p.y += p.vy;
          p.vy += 0.18;
          p.vx *= 0.995;
          p.rot += p.vr;
          p.a *= 0.988;
          ctx.save();
          ctx.translate(p.x, p.y);
          ctx.rotate(p.rot);
          ctx.globalAlpha = Math.max(0, p.a);
          ctx.fillStyle = p.c;
          ctx.fillRect(-p.r, -p.r * 0.4, p.r * 2, p.r * 0.8);
          ctx.restore();
        }
        ctx.globalAlpha = 1;
        if (elapsed < DURATION_MS) raf = requestAnimationFrame(tick);
        else canvas.remove();
      };
      raf = requestAnimationFrame(tick);
    }

    setTimeout(() => {
      overlay.remove();
      floatNodes.forEach((n) => n.remove());
      if (raf) cancelAnimationFrame(raf);
      if (canvas.parentNode) canvas.remove();
    }, DURATION_MS);

    try {
      if (tg && tg.HapticFeedback) tg.HapticFeedback.notificationOccurred("success");
    } catch (_) {}
  }

  function shouldCelebrateOrder(subtotal, total) {
    const thr = giftThreshold();
    return Number(subtotal || 0) >= thr || Number(total || 0) >= thr;
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
      body.querySelector(".card-title").textContent =
        product.card_name || product.name;
      body.querySelector(".card-price").textContent =
        product.display_price || formatMoney(product.price);
      if (product.ask_qty && product.qty_presets && product.qty_presets.length) {
        const hint = document.createElement("p");
        hint.className = "card-packs muted";
        hint.textContent = product.qty_presets.map((n) => `${n} dona`).join(" · ");
        body.appendChild(hint);
      } else if (
        (product.kg_packs && product.kg_packs.length) ||
        (product.liter_packs && product.liter_packs.length) ||
        (product.piece_packs && product.piece_packs.length)
      ) {
        const hint = document.createElement("p");
        hint.className = "card-packs muted";
        const labels = (product.kg_packs || [])
          .concat(product.liter_packs || [])
          .concat(product.piece_packs || []);
        hint.textContent = labels.map((p) => p.label).join(" · ");
        body.appendChild(hint);
      }

      const addBtn = document.createElement("button");
      addBtn.type = "button";
      addBtn.className = "btn add";
      const pieces = product.piece_packs || [];
      addBtn.textContent = product.ask_qty
        ? "2 / 5 / 15 dona"
        : !hasSizeChoice(product)
          ? "Qo'shish"
          : pieces.length
            ? "Tanlash"
            : "Hajm tanlash";
      addBtn.addEventListener("click", () => addProduct(product));
      body.appendChild(addBtn);

      card.appendChild(body);
      els.products.appendChild(card);
    });
  }

  function addProduct(product) {
    const variants = product.variants || [];
    const packs = product.kg_packs || [];
    const money = product.kg_money || [];
    const liters = product.liter_packs || [];
    const pieces = product.piece_packs || [];
    if (variants.length) {
      openVariantPicker(product);
      return;
    }
    if (product.ask_qty) {
      openQtyPicker(product);
      return;
    }
    if (packs.length || money.length || liters.length || pieces.length) {
      openKgPicker(product);
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

  function addOptionButton(text, onPick) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = text;
    btn.addEventListener("click", () => {
      onPick();
      els.variantDialog.close();
    });
    els.variantOptions.appendChild(btn);
  }

  function openVariantPicker(product) {
    els.variantTitle.textContent = product.name;
    els.variantOptions.innerHTML = "";
    (product.variants || []).forEach((v) => {
      addOptionButton(`${v.name} — ${formatMoney(v.price)}`, () => {
        upsertCartItem({
          product_id: product.id,
          variant_id: v.id,
          name: `${product.name} (${v.name})`,
          price: v.price,
          quantity: 1,
        });
      });
    });
    els.variantDialog.showModal();
  }

  function openQtyPicker(product) {
    const title = product.card_name || product.name;
    els.variantTitle.textContent = `${title} — nechta dona?`;
    els.variantOptions.innerHTML = "";
    const unit = Number(product.price) || 0;
    const presets = product.qty_presets || [2, 5, 10, 15, 30];
    presets.forEach((n) => {
      const qty = Number(n);
      addOptionButton(`${qty} dona — ${formatMoney(unit * qty)}`, () => {
        upsertCartItem({
          product_id: product.id,
          variant_id: 0,
          name: product.name,
          price: unit,
          quantity: qty,
        });
      });
    });
    const wrap = document.createElement("div");
    wrap.className = "qty-custom";
    const input = document.createElement("input");
    input.type = "number";
    input.min = "1";
    input.max = "200";
    input.step = "1";
    input.inputMode = "numeric";
    input.placeholder = "Boshqa son";
    const addBtn = document.createElement("button");
    addBtn.type = "button";
    addBtn.textContent = "Qo'shish";
    const addCustom = () => {
      const qty = Math.floor(Number(input.value));
      if (!Number.isFinite(qty) || qty < 1 || qty > 200) {
        input.focus();
        return;
      }
      upsertCartItem({
        product_id: product.id,
        variant_id: 0,
        name: product.name,
        price: unit,
        quantity: qty,
      });
      els.variantDialog.close();
    };
    addBtn.addEventListener("click", addCustom);
    input.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") {
        ev.preventDefault();
        addCustom();
      }
    });
    wrap.appendChild(input);
    wrap.appendChild(addBtn);
    els.variantOptions.appendChild(wrap);
    els.variantDialog.showModal();
    input.focus();
  }

  function productStem(name) {
    return String(name || "")
      .replace(/\d+(?:[.,]\d+)?\s*(kg|g|gr|gramm|l|lt|litr|ml)\b/gi, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  function openKgPicker(product) {
    els.variantTitle.textContent = `${product.card_name || product.name} — tanlang`;
    els.variantOptions.innerHTML = "";
    const stem = productStem(product.name) || product.name;
    (product.kg_packs || []).forEach((pack) => {
      addOptionButton(`${pack.label} — ${formatMoney(pack.price)}`, () => {
        const useReal = !pack.virtual;
        upsertCartItem({
          product_id: pack.product_id || product.id,
          variant_id: 0,
          pack_grams: useReal ? 0 : pack.grams,
          name: useReal && product.id === pack.product_id
            ? product.name
            : `${stem} ${pack.label}`.trim(),
          price: pack.price,
          quantity: 1,
        });
      });
    });
    (product.liter_packs || []).forEach((pack) => {
      addOptionButton(`${pack.label} — ${formatMoney(pack.price)}`, () => {
        const useReal = !pack.virtual;
        upsertCartItem({
          product_id: pack.product_id || product.id,
          variant_id: 0,
          pack_ml: useReal ? 0 : pack.ml,
          name: useReal && product.id === pack.product_id
            ? product.name
            : `${stem} ${pack.label}`.trim(),
          price: pack.price,
          quantity: 1,
        });
      });
    });
    (product.piece_packs || []).forEach((pack) => {
      addOptionButton(`${pack.label} — ${formatMoney(pack.price)}`, () => {
        upsertCartItem({
          product_id: pack.product_id || product.id,
          variant_id: 0,
          name: pack.name || pack.label,
          price: pack.price,
          quantity: 1,
        });
      });
    });
    (product.kg_money || []).forEach((opt) => {
      const detail = opt.detail ? ` (${opt.detail})` : "";
      addOptionButton(`${opt.label}${detail} — ${formatMoney(opt.amount)}`, () => {
        upsertCartItem({
          product_id: opt.product_id || product.id,
          variant_id: 0,
          pack_amount: opt.amount,
          name: `${stem} ${opt.label}${detail}`.trim(),
          price: opt.amount,
          quantity: 1,
        });
      });
    });
    els.variantDialog.showModal();
  }

  function upsertCartItem(item) {
    const key = cartKey(item);
    const existing = state.cart.find((c) => cartKey(c) === key);
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

  function setQty(item, delta) {
    const key = cartKey(item);
    const found = state.cart.find((c) => cartKey(c) === key);
    if (!found) return;
    found.quantity += delta;
    if (found.quantity <= 0) {
      state.cart = state.cart.filter((c) => cartKey(c) !== key);
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
    if (els.deliveryRates) {
      els.deliveryRates.textContent = deliveryRatesText();
    }
    if (els.giftProgress) {
      if (subtotal > 0) {
        els.giftProgress.hidden = false;
        els.giftProgress.textContent = giftProgressText(subtotal);
        els.giftProgress.classList.toggle("earned", subtotal >= giftThreshold());
      } else {
        els.giftProgress.hidden = true;
      }
    }
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
        setQty(item, -1)
      );
      row.querySelector('[data-act="inc"]').addEventListener("click", () =>
        setQty(item, 1)
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
    if (els.giftPromo) {
      els.giftPromo.hidden = false;
      if (els.giftPromoText) els.giftPromoText.textContent = giftPromoText();
    }
    renderCart();

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
        pack_grams: item.pack_grams || undefined,
        pack_amount: item.pack_amount || undefined,
        pack_ml: item.pack_ml || undefined,
      })),
    };
    if (devUser && !payload.initData && !telegramUser) {
      payload.dev_user_id = Number(devUser);
    }

    els.submit.disabled = true;
    els.submit.textContent = "Yuborilmoqda...";

    // 1) Eng ishonchli: botga sendData (klaviatura Do'kon tugmasi)
    const checkoutTotals = calcTotals();
    const willCelebrate = shouldCelebrateOrder(
      checkoutTotals.subtotal,
      checkoutTotals.total
    );
    if (checkoutViaSendData(payload)) {
      state.cart = [];
      state.discount = 0;
      if (els.bonus) els.bonus.value = "";
      saveCart();
      updateBadge();
      renderCart();
      els.status.hidden = false;
      els.status.classList.remove("error");
      if (willCelebrate) {
        fireCelebration();
        els.status.textContent =
          "🎊 Tabriklaymiz! Sovg‘angiz: 1L Coca-Cola / Pepsi / Fanta — yetkazishda tanlaysiz! Buyurtma botga yuborildi…";
      } else {
        els.status.textContent = "Buyurtma botga yuborildi…";
      }
      els.submit.disabled = true;
      els.submit.textContent = "Yuborildi ✓";
      if (tg) {
        try {
          tg.HapticFeedback && tg.HapticFeedback.notificationOccurred("success");
        } catch (_) {}
        // Celebrating bo‘lsa animatsiya tugaguncha yopilmasin (~5s)
        setTimeout(() => {
          try {
            tg.close();
          } catch (_) {}
        }, willCelebrate ? 5200 : 1200);
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
      const celebrate =
        result.celebrate ||
        shouldCelebrateOrder(result.subtotal, result.total);
      if (celebrate) {
        fireCelebration();
        els.status.textContent =
          `🎊 Tabriklaymiz! Buyurtma #${result.order_id} — sovg‘angiz 1L Coca-Cola / Pepsi / Fanta (yetkazishda tanlaysiz)!`;
      } else {
        els.status.textContent = `Buyurtma #${result.order_id} qabul qilindi!`;
      }
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
        }, celebrate ? 5200 : 1800);
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
