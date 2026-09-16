(() => {
  const tg = window.Telegram && window.Telegram.WebApp;
  if (tg) {
    tg.ready();
    tg.expand();
    try {
      tg.setHeaderColor("#0c1018");
      tg.setBackgroundColor("#0c1018");
    } catch (_) {}
  }

  const DEFAULT_PLACES = [
    { title: "Ish", subtitle: "Amir Temur ko'chasi, 15" },
    { title: "Uy", subtitle: "Yunusobod tumani, 24-uy" },
    { title: "Tashkent Siti", subtitle: "Mirzo Ulug'bek tumani" },
  ];

  const home = document.getElementById("home");
  const request = document.getElementById("request");
  const placesEl = document.getElementById("places");
  const hello = document.getElementById("hello");
  const form = document.getElementById("form");
  const fromPlace = document.getElementById("fromPlace");
  const toPlace = document.getElementById("toPlace");
  const needExtra = document.getElementById("needExtra");
  const needWrap = document.getElementById("needWrap");
  const phone = document.getElementById("phone");
  const note = document.getElementById("note");
  const submit = document.getElementById("submit");
  const status = document.getElementById("status");
  const requestTitle = document.getElementById("requestTitle");
  const requestLead = document.getElementById("requestLead");

  let kind = "passenger";

  const user = tg && tg.initDataUnsafe && tg.initDataUnsafe.user;
  if (user && user.first_name) {
    hello.textContent = `Xush kelibsiz, ${user.first_name}`;
  }

  function pinSvg() {
    return `<span class="place-pin" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none">
        <path d="M12 21s7-6.2 7-11.2A7 7 0 1 0 5 9.8C5 14.8 12 21 12 21Z" stroke="#9aa8bd" stroke-width="1.8"/>
        <circle cx="12" cy="9.6" r="2.2" fill="#9aa8bd"/>
      </svg>
    </span>`;
  }

  placesEl.innerHTML = DEFAULT_PLACES.map(
    (p) => `<button type="button" class="place" data-title="${p.title}" data-sub="${p.subtitle}">
      ${pinSvg()}
      <span><b>${p.title}</b><small>${p.subtitle}</small></span>
      <span class="chev">›</span>
    </button>`
  ).join("");

  function showStatus(text, ok) {
    status.hidden = false;
    status.className = `status ${ok ? "ok" : "err"}`;
    status.textContent = text;
  }

  function openRequest(nextKind, presetTo) {
    kind = nextKind;
    const cargo = kind === "cargo";
    requestTitle.textContent = cargo ? "Yuk / buyum" : "Yo'lovchi";
    requestLead.textContent = cargo
      ? "Sement, oziq-ovqat va boshqalar — haydovchi bilan ulashamiz."
      : "Shaharga yoki shahar ichida safar.";
    needWrap.hidden = !cargo;
    toPlace.value = presetTo || "";
    fromPlace.value = "";
    needExtra.value = "";
    note.value = "";
    status.hidden = true;
    home.hidden = true;
    request.hidden = false;
  }

  document.querySelectorAll(".kind").forEach((btn) => {
    btn.addEventListener("click", () => openRequest(btn.dataset.kind, ""));
  });

  placesEl.addEventListener("click", (ev) => {
    const btn = ev.target.closest(".place");
    if (!btn) return;
    openRequest(kind || "passenger", `${btn.dataset.title}, ${btn.dataset.sub}`);
  });

  document.getElementById("back").addEventListener("click", () => {
    request.hidden = true;
    home.hidden = false;
  });

  function getInitData() {
    return (tg && tg.initData) || "";
  }

  function getTelegramUser() {
    if (!user || !user.id) return null;
    return {
      id: user.id,
      first_name: user.first_name || "",
      last_name: user.last_name || "",
      username: user.username || "",
    };
  }

  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const to = (toPlace.value || "").trim();
    const tel = (phone.value || "").trim();
    const extra = (needExtra.value || "").trim();
    if (!to || !tel) {
      showStatus("Manzil va telefonni to‘ldiring", false);
      return;
    }
    const need =
      kind === "cargo"
        ? extra
          ? `Yuk / buyum: ${extra}`
          : "Yuk / buyum"
        : extra
          ? `Yo'lovchi: ${extra}`
          : "Yo'lovchi: shaharga yoki shahar ichida safar";

    submit.disabled = true;
    submit.textContent = "Yuborilmoqda…";
    try {
      const initData = getInitData();
      const headers = { "Content-Type": "application/json" };
      if (initData) headers["X-Telegram-Init-Data"] = initData;
      const res = await fetch("/api/vosita", {
        method: "POST",
        headers,
        body: JSON.stringify({
          need,
          from_place: (fromPlace.value || "").trim(),
          to_place: to,
          phone: tel,
          note: (note.value || "").trim(),
          initData,
          telegram_user: getTelegramUser(),
        }),
      });
      const raw = await res.text();
      let data = null;
      try {
        data = raw ? JSON.parse(raw) : null;
      } catch {
        data = raw;
      }
      if (!res.ok) {
        const msg =
          typeof data === "string"
            ? data
            : (data && (data.error || data.message)) || raw || res.statusText;
        throw new Error(msg || "Xatolik");
      }
      showStatus(
        `So‘rov #${data.request_id} qabul qilindi. Tez orada qo‘ng‘iroq qilamiz.`,
        true
      );
      if (tg && tg.HapticFeedback) {
        try {
          tg.HapticFeedback.notificationOccurred("success");
        } catch (_) {}
      }
    } catch (err) {
      showStatus((err && err.message) || "Yuborilmadi. Qayta urinib ko‘ring.", false);
    } finally {
      submit.disabled = false;
      submit.textContent = "So‘rov yuborish";
    }
  });
})();
