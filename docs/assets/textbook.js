// 本文はJavaScriptなしでも読めます。記録はこのブラウザ内だけに保存します。
(() => {
  const defaults = {
    copy: 'コピー', copy_label: '{title}のコードをコピー', copied: 'コピーしました',
    copy_success: 'コードをコピーしました。エディタに貼り付けてください。',
    copy_shortcut: '⌘ Cでコピー', copy_selected: 'コードを選択しました。⌘ Cでコピーしてください。',
    progress: '{count} / {total} ステップ確認済み'
  };
  let messages = defaults;
  try {
    const text = document.querySelector('#textbook-i18n')?.textContent;
    if (text) messages = { ...defaults, ...JSON.parse(text) };
  } catch { /* 古い配布物でも日本語のUIを利用可能 */ }
  const message = (name, values = {}) => messages[name].replace(/\{(\w+)\}/g, (token, key) => values[key] ?? token);
  const checks = [...document.querySelectorAll('[data-check]')];
  // 記録用キーは <body data-progress-key="jec-hybrid-<スラッグ>-v1"> で指定する。
  // 接頭辞を jec-hybrid にしているのは、同じ学生が同じブラウザで開く Kotlin演習の教科書
  // （jec-kotlin-…）と記録が混ざらないようにするため。Chromeは file:// で開いたページの
  // localStorage をすべて同じ場所に保存するので、どちらにも docs/common/setup.html がある
  // 2つの教材は、接頭辞が同じだと同じキーになる。
  // 書き忘れたときの既定値は、ページのパスの末尾2つから作る（例 docs/common/setup.html →
  // jec-hybrid-common-setup-v1）。ここを固定値にすると、キーを書き忘れたページが
  // 別のページの記録を上書きして消してしまう。save() は、そのページで見つかった
  // data-check だけを書き戻すためである。
  const defaultKey = () => {
    const parts = decodeURIComponent(window.location.pathname).split('/').filter(Boolean).slice(-2);
    const slug = parts.join('-').replace(/\.html?$/i, '').replace(/[^A-Za-z0-9-]+/g, '-').replace(/^-+|-+$/g, '');
    return `jec-hybrid-${slug || 'page'}-v1`;
  };
  const key = document.body.dataset.progressKey || defaultKey();
  const timeKey = `${key}:updated-at`;
  const knownIds = new Set(checks.map(item => item.dataset.check));
  const records = {};
  const mergeRecords = incoming => {
    if (!incoming || typeof incoming !== 'object' || Array.isArray(incoming)) return;
    Object.entries(incoming).forEach(([id, record]) => {
      if (!knownIds.has(id) || !record || typeof record.checked !== 'boolean'
          || !Number.isFinite(record.updatedAt) || record.updatedAt < 0) return;
      const previous = records[id];
      // 時刻のない旧形式どうしでは、既存の確認済み記録を優先する。
      if (!previous || record.updatedAt > previous.updatedAt
          || (record.updatedAt === previous.updatedAt && record.checked)) records[id] = record;
    });
  };
  const loadSaved = () => {
    try {
      const saved = JSON.parse(localStorage.getItem(key) || '{}') || {};
      const times = JSON.parse(localStorage.getItem(timeKey) || '{}') || {};
      mergeRecords(Object.fromEntries(Object.entries(saved).filter(([, value]) => typeof value === 'boolean')
        .map(([id, checked]) => [id, { checked, updatedAt: Number.isFinite(times[id]) ? times[id] : 0 }])));
    } catch { /* 保存できない環境でも利用可能 */ }
  };
  const save = () => {
    try {
      // 確認済みの保存形式は旧版でも読めるままにし、更新時刻だけを別に保存する。
      localStorage.setItem(key, JSON.stringify(Object.fromEntries(Object.entries(records).map(([id, value]) => [id, value.checked]))));
      localStorage.setItem(timeKey, JSON.stringify(Object.fromEntries(Object.entries(records).map(([id, value]) => [id, value.updatedAt]))));
    } catch { /* このページ上では引き継ぐ */ }
  };
  loadSaved();
  // file:// のページ別保存にも対応する。未操作のページは既存の記録を上書きしない。
  const parameters = new URLSearchParams(window.location.search);
  if (parameters.has('checks')) {
    try {
      mergeRecords(JSON.parse(parameters.get('checks')));
      save();
    } catch { /* 不正な引き継ぎ値は保存済みの記録に影響させない */ }
    parameters.delete('checks');
    const clean = new URL(window.location.href);
    clean.search = parameters.toString();
    try { history.replaceState(null, '', clean.href); } catch { /* file:// の履歴更新が禁止でも本文は利用可能 */ }
  }
  const update = () => {
    const count = checks.filter(input => input.checked).length;
    const label = document.querySelector('[data-progress-label]');
    const progress = document.querySelector('progress');
    if (label) label.textContent = message('progress', { count, total: checks.length });
    if (progress) { progress.max = checks.length; progress.value = count; }
  };
  checks.forEach(input => {
    input.checked = records[input.dataset.check]?.checked === true;
    input.addEventListener('change', () => {
      loadSaved();
      const id = input.dataset.check;
      records[id] = { checked: input.checked, updatedAt: Math.max(Date.now(), (records[id]?.updatedAt || 0) + 1) };
      update();
      save();
    });
  });
  update();

  document.querySelectorAll('pre').forEach(pre => {
    const heading = pre.previousElementSibling;
    if (!heading?.classList.contains('code-head')) return;
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = message('copy');
    button.setAttribute('aria-label', message('copy_label', { title: heading.textContent.trim() }));
    heading.append(button);
    button.addEventListener('click', async () => {
      const status = document.querySelector('[data-copy-status]');
      try {
        await navigator.clipboard.writeText(pre.textContent);
        button.textContent = message('copied');
        if (status) status.textContent = message('copy_success');
      } catch {
        const range = document.createRange();
        range.selectNodeContents(pre);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        button.textContent = message('copy_shortcut');
        if (status) status.textContent = message('copy_selected');
      }
      setTimeout(() => { button.textContent = message('copy'); }, 3000);
    });
  });

  const links = [...document.querySelectorAll('.sidebar a[href^="#"]')];
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        links.forEach(link => {
          if (link.hash === `#${entry.target.id}`) link.setAttribute('aria-current', 'step');
          else link.removeAttribute('aria-current');
        });
      });
    }, { rootMargin: '0px 0px -65% 0px', threshold: 0 });
    document.querySelectorAll('main section[id]').forEach(section => observer.observe(section));
  }

  // from は最初の単元、back は共通資料をたどった順の「ファイル名#節」。
  // URLに持たせることで、file://・新しいタブ・言語切替でも直前へ戻れる。
  const from = parameters.get('from');
  const backTo = from && /^[a-z0-9-]+$/.test(from) ? from : null;
  const backValues = parameters.getAll('back');
  const backPages = backValues.every(value => /^[a-z0-9-]+\.html(?:#[a-z0-9-]+)?$/.test(value)) ? backValues : [];
  const setNavigation = (target, pages) => {
    if (backTo) target.searchParams.set('from', backTo);
    target.searchParams.delete('back');
    pages.forEach(page => target.searchParams.append('back', page));
  };
  document.querySelectorAll('a[data-back]').forEach(link => {
    if (backPages.length) {
      const target = new URL(backPages.at(-1), window.location.href);
      setNavigation(target, backPages.slice(0, -1));
      link.setAttribute('href', target.href);
    } else if (backTo) {
      const target = new URL(`../${backTo}/index.html`, window.location.href);
      const fallback = new URL(link.getAttribute('href'), window.location.href);
      // 同じ単元なら、HTMLに書いた既定の復帰位置（#step-1 など）も残す。
      if (fallback.pathname === target.pathname) target.hash = fallback.hash;
      link.setAttribute('href', target.href);
    }
    // 戻り先がない直接起動では、HTMLにある既定のリンクを使う。
  });
  document.querySelectorAll('a[data-keep-from]').forEach(link => {
    const href = link.getAttribute('href');
    if (!href) return;
    const current = new URL(window.location.href);
    const target = new URL(href, current);
    const directory = new URL('.', current);
    const filename = current.pathname.split('/').at(-1);
    if (!/\/common\/$/.test(directory.pathname) || !/^[a-z0-9-]+\.html$/.test(filename)
        || new URL('.', target).href !== directory.href || !/^[a-z0-9-]+\.html$/.test(target.pathname.split('/').at(-1))) return;
    const section = link.closest('section[id]');
    const previous = `${filename}${section ? `#${section.id}` : current.hash}`;
    // 本文の「setupへ戻る」などで既に読んだページへ戻るときは、履歴を巻き戻す。
    const previousIndex = backPages.findIndex(page => new URL(page, current).pathname === target.pathname);
    // リンクに節の指定がなければ、前に読んでいた節へ戻す。
    if (previousIndex >= 0 && !target.hash) target.hash = new URL(backPages[previousIndex], current).hash;
    setNavigation(target, previousIndex < 0 ? [...backPages, previous] : backPages.slice(0, previousIndex));
    link.setAttribute('href', target.href);
  });

  // 言語名が折り返しても、固定メニューの下に目次とSTEPを表示する。
  const languageNav = document.querySelector('.language-nav');
  if (languageNav) {
    const resizeNav = () => document.documentElement.style.setProperty('--language-nav-height', `${languageNav.getBoundingClientRect().height}px`);
    resizeNav();
    document.documentElement.classList.add('has-language-nav');
    if ('ResizeObserver' in window) new ResizeObserver(resizeNav).observe(languageNav);
    else window.addEventListener('resize', resizeNav);
  }

  // 言語を替えても、共通資料の戻り先・いま読んでいるSTEP・確認済みの記録を保つ。
  document.querySelectorAll('a[data-language-link]').forEach(link => {
    const base = link.getAttribute('href');
    const updateTarget = () => {
      const target = new URL(base, window.location.href);
      setNavigation(target, backPages);
      loadSaved();
      if (checks.length && Object.keys(records).length) target.searchParams.set('checks', JSON.stringify(records));
      const section = [...document.querySelectorAll('main section[id]')].filter(item => item.getBoundingClientRect().top <= window.innerHeight / 3).at(-1);
      target.hash = section ? section.id : window.location.hash;
      link.href = target.href;
    };
    updateTarget();
    link.addEventListener('click', updateTarget);
    link.addEventListener('contextmenu', updateTarget);
    // キーボード操作・新しいタブで開く操作でも、最新のリンク先を使う。
    link.addEventListener('focus', updateTarget);
    window.addEventListener('hashchange', updateTarget);
  });

  let closedForScreen = [];
  window.addEventListener('beforeprint', () => {
    closedForScreen = [...document.querySelectorAll('details:not([open])')];
    closedForScreen.forEach(detail => { detail.open = true; });
  });
  window.addEventListener('afterprint', () => {
    closedForScreen.forEach(detail => { detail.open = false; });
    closedForScreen = [];
  });
})();
