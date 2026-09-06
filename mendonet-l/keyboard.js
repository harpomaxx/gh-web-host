(() => {
  const archiveBase = document.documentElement.dataset.base || '/';

  function isTypingTarget(element) {
    return element && ['INPUT', 'TEXTAREA', 'SELECT'].includes(element.tagName);
  }
  function href(selector) {
    const link = document.querySelector(selector);
    return link ? link.getAttribute('href') : '';
  }
  window.addEventListener('keydown', (event) => {
    if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.altKey || isTypingTarget(document.activeElement)) return;
    const key = event.key.toLowerCase();
    const target = key === 'j' ? href('[data-shortcut-next]')
      : key === 'k' ? href('[data-shortcut-prev]')
      : key === 't' ? href('[data-shortcut-thread]')
      : key === '/' ? `${archiveBase}search/`
      : '';
    if (!target) return;
    event.preventDefault();
    window.location.href = key === '/' ? `${target}?focus=1` : target;
  });
})();
