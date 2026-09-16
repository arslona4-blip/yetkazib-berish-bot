(() => {
  const tg = window.Telegram && window.Telegram.WebApp;
  if (tg) {
    tg.ready();
    tg.expand();
    try {
      tg.setHeaderColor("#1e3a5f");
      tg.setBackgroundColor("#eef3f8");
    } catch (_) {}
  }

  const els = {
    form: document.getElementById("form"),
    need: document.getElementById("need"),
    fromPlace: document.getElementById("fromPlace"),
    toPlace: document.getElementById("toPlace"),
    phone: document.getElementById("phone"),
    note: document.getElementById("note"),
    submit: document.getElementById("submit"),
    status: document.getElementById("status"),
  };

  function getInitData() {
    return (tg && tg.initData) || "";
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

  function showStatus(text, ok) {
    els.status.hidden = false;
    els.status.className = `status ${ok ? "ok" : "err"}`;
    els.status.textContent = text;
  }

  els.form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const need = (els.need.value || "").trim();
    const toPlace = (els.toPlace.value || "").trim();
    const phone = (els.phone.value || "").trim();
    if (!need || !toPlace || !phone) {
      showStatus("Nima kerak, manzil va telefonni to‘ldiring", false);
      return;
    }
    els.submit.disabled = true;
    els.submit.textContent = "Yuborilmoqda…";
    try {
      const initData = getInitData();
      const telegramUser = getTelegramUser();
      const headers = { "Content-Type": "application/json" };
      if (initData) headers["X-Telegram-Init-Data"] = initData;
      const res = await fetch("/api/vosita", {
        method: "POST",
        headers,
        body: JSON.stringify({
          need,
          from_place: (els.fromPlace.value || "").trim(),
          to_place: toPlace,
          phone,
          note: (els.note.value || "").trim(),
          initData,
          telegram_user: telegramUser,
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
      els.form.reset();
      if (tg && tg.HapticFeedback) {
        try {
          tg.HapticFeedback.notificationOccurred("success");
        } catch (_) {}
      }
    } catch (err) {
      showStatus((err && err.message) || "Yuborilmadi. Qayta urinib ko‘ring.", false);
    } finally {
      els.submit.disabled = false;
      els.submit.textContent = "So‘rov yuborish";
    }
  });
})();
