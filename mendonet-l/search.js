const input = document.querySelector('[data-search-input]');
const results = document.querySelector('[data-search-results]');
const statusNode = document.querySelector('[data-search-status]');
const yearFilter = document.querySelector('[data-search-year]');
const archiveBase = document.documentElement.dataset.base || '/';
let pagefind;

async function loadPagefind() {
  if (!pagefind) {
    pagefind = await import(`${archiveBase}pagefind/pagefind.js`);
    await pagefind.options({ excerptLength: 24 });
  }
  return pagefind;
}

function renderMessage(text) {
  if (statusNode) statusNode.textContent = text;
}

function replaceResults(items) {
  const fragment = document.createDocumentFragment();
  if (!items.length) {
    const empty = document.createElement('p');
    empty.textContent = 'No matches.';
    fragment.append(empty);
  }
  for (const item of items) {
    const article = document.createElement('article');
    article.className = 'index-card';
    const heading = document.createElement('h2');
    const link = document.createElement('a');
    const baseUrl = new URL(archiveBase, window.location.origin);
    const indexedUrl = new URL(String(item.url || ''), window.location.origin);
    const relativePath = indexedUrl.pathname.startsWith(baseUrl.pathname)
      ? indexedUrl.pathname.slice(baseUrl.pathname.length)
      : indexedUrl.pathname.replace(/^\/+/, '');
    const candidate = new URL(`${relativePath}${indexedUrl.search}${indexedUrl.hash}`, baseUrl);
    link.href = indexedUrl.origin === window.location.origin ? candidate.href : baseUrl.href;
    link.textContent = item.meta.title || item.url;
    heading.append(link);
    const excerpt = document.createElement('p');
    // Pagefind excerpts contain <mark> tags. Display them as plain text so that
    // indexed historical message content can never become active markup.
    const parsedExcerpt = new DOMParser().parseFromString(item.excerpt || '', 'text/html');
    excerpt.textContent = parsedExcerpt.body.textContent || '';
    article.append(heading, excerpt);
    fragment.append(article);
  }
  results.replaceChildren(fragment);
}

async function runSearch(query) {
  if (!query.trim()) {
    const prompt = document.createElement('p');
    prompt.textContent = 'Type a word or phrase to search the archive.';
    results.replaceChildren(prompt);
    renderMessage('');
    return;
  }
  renderMessage('Searching local index…');
  const pf = await loadPagefind();
  const filters = yearFilter && yearFilter.value ? { year: yearFilter.value } : {};
  const search = await pf.search(query, { filters });
  const top = await Promise.all(search.results.slice(0, 50).map((result) => result.data()));
  renderMessage(`${search.results.length} result${search.results.length === 1 ? '' : 's'} found. Showing ${top.length}.`);
  replaceResults(top);
}

if (input && results) {
  if (new URLSearchParams(window.location.search).get('focus')) input.focus();
  let timer;
  input.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => runSearch(input.value), 200);
  });
  if (yearFilter) yearFilter.addEventListener('change', () => runSearch(input.value));
  const q = new URLSearchParams(window.location.search).get('q');
  if (q) {
    input.value = q;
    runSearch(q);
  }
}
