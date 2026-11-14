(() => {
  const modal = document.getElementById("modal");
  const darkModeKey = "fintrack-dark-mode";

  function applyDarkMode(enabled) {
    document.documentElement.classList.toggle("dark-mode", enabled);
    document.querySelectorAll("[data-dark-mode-toggle]").forEach((toggle) => {
      toggle.classList.toggle("on", enabled);
      toggle.setAttribute("aria-pressed", String(enabled));
    });
  }

  applyDarkMode(localStorage.getItem(darkModeKey) === "true");

  const dashboard = document.querySelector("[data-api-dashboard]");
  if (dashboard) {
    const params = new URLSearchParams(window.location.search);
    fetch(`/api/v1/dashboard?${params.toString()}`, { headers: { Accept: "application/json" } })
      .then((response) => response.ok ? response.json() : null)
      .then((payload) => {
        if (!payload || !payload.data || !payload.data.totals) return;
        Object.entries(payload.data.totals).forEach(([key, value]) => {
          const target = dashboard.querySelector(`[data-dashboard-metric="${key}"]`);
          if (target) target.textContent = value;
        });
      })
      .catch((error) => console.error("Dashboard API request failed", error));
  }

  const transactionRows = document.querySelectorAll("[data-transaction-id]");
  if (transactionRows.length) {
    const query = new URLSearchParams(window.location.search);
    fetch(`/api/v1/transactions?${query.toString()}`, { headers: { Accept: "application/json" } })
      .then((response) => response.ok ? response.json() : null)
      .then((payload) => {
        if (!payload || !Array.isArray(payload.data)) return;
        const byId = new Map(payload.data.map((item) => [String(item.id), item]));
        transactionRows.forEach((row) => {
          const item = byId.get(row.dataset.transactionId);
          if (!item) return;
          const cells = row.querySelectorAll("td");
          cells[2].textContent = item.date;
          cells[3].textContent = item.category;
          cells[4].textContent = item.account;
          cells[5].textContent = item.note || "—";
          cells[6].textContent = `${item.type === "income" ? "+" : "-"}$${Number(item.amount).toFixed(2)}`;
        });
      })
      .catch((error) => console.error("Transactions API request failed", error));
  }

  ["budgets", "goals", "bills"].forEach((resource) => {
    const cards = document.querySelectorAll(`[data-api-resource="${resource}"]`);
    if (!cards.length) return;
    fetch(`/api/v1/${resource}`, { headers: { Accept: "application/json" } })
      .then((response) => response.ok ? response.json() : null)
      .then((payload) => {
        if (!payload || !Array.isArray(payload.data)) return;
        const byId = new Map(payload.data.map((item) => [String(item.id), item]));
        cards.forEach((card) => {
          const item = byId.get(card.dataset.resourceId);
          const name = card.querySelector("[data-resource-name]");
          if (item && name && item.name) name.firstChild.textContent = item.name;
        });
      })
      .catch((error) => console.error(`${resource} API request failed`, error));
  });

  function closeModal() {
    if (modal) modal.classList.add("hidden");
  }

  function openModal() {
    if (modal) modal.classList.remove("hidden");
  }

  document.addEventListener("click", (event) => {
    const menuToggle = event.target.closest("[data-menu-toggle]");
    if (menuToggle) {
      const sidebar = document.getElementById("app-sidebar");
      const open = sidebar && sidebar.classList.toggle("open");
      menuToggle.setAttribute("aria-expanded", String(Boolean(open)));
    }
    const notificationsToggle = event.target.closest("[data-notifications-toggle]");
    const profileToggle = event.target.closest("[data-profile-toggle]");
    if (notificationsToggle || profileToggle) {
      const target = document.getElementById(notificationsToggle ? "notifications-menu" : "profile-menu");
      target.classList.toggle("hidden");
      (notificationsToggle || profileToggle).setAttribute("aria-expanded", String(!target.classList.contains("hidden")));
    }
    if (!event.target.closest(".menu-wrap")) {
      document.querySelectorAll(".popover").forEach((item) => item.classList.add("hidden"));
    }
    if (event.target.closest("[data-open-modal]")) openModal();
    if (event.target.closest("[data-close-modal]")) closeModal();
    if (event.target.matches("[data-modal-backdrop]")) closeModal();
    const toggle = event.target.closest("[data-toggle]");
    if (toggle) toggle.classList.toggle("on");
    const settingsTab = event.target.closest("[data-settings-tab]");
    if (settingsTab) {
      const tab = settingsTab.dataset.settingsTab;
      document.querySelectorAll("[data-settings-tab]").forEach((item) => item.classList.toggle("active", item === settingsTab));
      document.querySelectorAll("[data-settings-panel]").forEach((panel) => panel.classList.toggle("hidden", panel.dataset.settingsPanel !== tab));
      history.replaceState(null, "", `${window.location.pathname}?tab=${tab}`);
    }
    const darkModeToggle = event.target.closest("[data-dark-mode-toggle]");
    if (darkModeToggle) {
      const enabled = !document.documentElement.classList.contains("dark-mode");
      applyDarkMode(enabled);
      localStorage.setItem(darkModeKey, String(enabled));
    }
    if (event.target.matches("[data-loading]")) return;
    const transactionType = event.target.closest("[data-transaction-type]");
    if (transactionType) {
      const typeInput = document.querySelector("[name='transaction_type']");
      const selectedType = transactionType.dataset.transactionType;
      if (typeInput) typeInput.value = selectedType;
      document.querySelectorAll("[data-transaction-type]").forEach((button) => {
        const isSelected = button.dataset.transactionType === selectedType;
        button.classList.toggle("selected", isSelected);
        button.classList.toggle("income", isSelected && selectedType === "income");
        button.classList.toggle("expense", isSelected && selectedType === "expense");
      });
    }
  });

  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", (event) => {
      let valid = true;
      form.querySelectorAll("[required]").forEach((field) => {
        const error = field.parentElement.querySelector(".field-error");
        if (!field.value && field.type !== "checkbox") {
          valid = false;
          field.setAttribute("aria-invalid", "true");
          if (error) error.textContent = "This field is required.";
        } else {
          field.removeAttribute("aria-invalid");
          if (error) error.textContent = "";
        }
      });
      if (!valid) event.preventDefault();
      else {
        const submit = form.querySelector("button[type='submit']");
        if (submit) {
          submit.disabled = true;
          submit.dataset.originalText = submit.textContent;
          submit.textContent = "Saving…";
        }
      }
    });
  });
})();
