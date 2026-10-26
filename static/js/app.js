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

  function closeModal() {
    if (modal) modal.classList.add("hidden");
  }

  function openModal() {
    if (modal) modal.classList.remove("hidden");
  }

  document.addEventListener("click", (event) => {
    if (event.target.closest("[data-open-modal]")) openModal();
    if (event.target.closest("[data-close-modal]")) closeModal();
    if (event.target.matches("[data-modal-backdrop]")) closeModal();
    const toggle = event.target.closest("[data-toggle]");
    if (toggle) toggle.classList.toggle("on");
    const darkModeToggle = event.target.closest("[data-dark-mode-toggle]");
    if (darkModeToggle) {
      const enabled = !document.documentElement.classList.contains("dark-mode");
      applyDarkMode(enabled);
      localStorage.setItem(darkModeKey, String(enabled));
    }
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
})();
