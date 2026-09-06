(() => {
  const key = 'mendonet-theme';
  const root = document.documentElement;
  const stored = localStorage.getItem(key);
  if (stored) root.dataset.theme = stored;
  const cycle = ['classic', 'reader', 'dark'];
  function updateButton() {
    const button = document.querySelector('[data-theme-toggle]');
    if (button) button.textContent = `Theme: ${root.dataset.theme || 'auto'}`;
  }
  window.addEventListener('DOMContentLoaded', () => {
    updateButton();
    const button = document.querySelector('[data-theme-toggle]');
    if (!button) return;
    button.addEventListener('click', () => {
      const current = root.dataset.theme || 'classic';
      const next = cycle[(cycle.indexOf(current) + 1) % cycle.length] || 'classic';
      root.dataset.theme = next;
      localStorage.setItem(key, next);
      updateButton();
    });
  });
})();
