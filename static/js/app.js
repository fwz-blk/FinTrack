(() => {
  const modal = document.getElementById("modal");

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
  });

  document.addEventListener("submit", (event) => {
    if (event.target.matches(".modal")) {
      event.preventDefault();
      closeModal();
    }
  });
})();
