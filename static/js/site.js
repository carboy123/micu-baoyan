(function () {
  'use strict';
  var core = window.MicuCore;
  if (!core) return;

  function readData(id) {
    var source = document.getElementById(id);
    if (!source) return { records: [], valid: false };
    try {
      var data = JSON.parse(source.textContent);
      return { records: Array.isArray(data) ? data : [], valid: Array.isArray(data) };
    } catch (_) {
      return { records: [], valid: false };
    }
  }

  function element(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function internalUrl(value) {
    if (!value || /[\\\u0000-\u0020]/u.test(value)) return null;
    try {
      var target = new URL(value, window.location.href);
      return target.origin === window.location.origin && /^https?:$/u.test(target.protocol) ? target : null;
    } catch (_) {
      return null;
    }
  }

  function setText(root, selector, value) {
    var node = root.querySelector(selector);
    if (node) node.textContent = value;
  }

  function setStatus(root, selector, value) {
    var node = root.querySelector(selector);
    if (node) {
      node.hidden = !value;
      if (!value) return;
      if (typeof value === 'string') {
        node.textContent = value;
        return;
      }
      var title = node.querySelector('[data-status-title], h2');
      var description = node.querySelector('[data-status-description], p');
      if (title || description) {
        if (title) title.textContent = value.title;
        if (description) description.textContent = value.description;
      } else {
        node.textContent = value.title + ' ' + value.description;
      }
    }
  }

  function updateUrl(query, replace) {
    var next = window.location.pathname + query;
    if (next !== window.location.pathname + window.location.search) {
      window.history[replace ? 'replaceState' : 'pushState']({}, '', next);
    }
  }

  function debounce(fn, delay) {
    var timeout;
    function debounced() {
      window.clearTimeout(timeout);
      timeout = window.setTimeout(fn, delay);
    }
    debounced.cancel = function () { window.clearTimeout(timeout); };
    return debounced;
  }

  function setupSearch() {
    var root = document.querySelector('[data-search-page]');
    if (!root) return;
    var input = root.querySelector('[name="q"]');
    var results = root.querySelector('[data-search-results]');
    var form = input && input.form;
    var data = readData('search-data');
    if (!input || !results) return;

    function render() {
      var query = input.value.trim();
      var matches = core.searchPages(data.records, query);
      results.replaceChildren();
      setText(root, '[data-search-count]', query ? '找到 ' + matches.length + ' 条结果' : '搜索保研知识与经验');
      setStatus(root, '[data-search-status]', !data.valid ? '搜索资料暂时无法读取，请通过导航浏览内容。' : !query ? '输入院校、术语或准备事项，空格可组合多个关键词。' : !matches.length ? '没有找到相关内容，请缩短关键词或换一种说法。' : '');
      var fragment = document.createDocumentFragment();
      matches.forEach(function (record) {
        var target = internalUrl(record.url);
        if (!target) return;
        var article = element('article', 'search-result');
        var heading = element('h2', 'search-result-title');
        var link = element('a', '', record.title || '未命名文章');
        link.href = target.pathname + target.search + target.hash;
        heading.append(link);
        article.append(heading);
        if (record.section || record.kind) article.append(element('p', 'search-result-meta', record.section || record.kind));
        article.append(element('p', 'search-result-description', record.description || String(record.body || '').slice(0, 160)));
        fragment.append(article);
      });
      results.append(fragment);
    }

    function restore() {
      liveSearch.cancel();
      input.value = core.parseQuery(window.location.search).q;
      render();
    }

    var liveSearch = debounce(function () {
      updateUrl(core.buildQuery({ q: input.value }), true);
      render();
    }, 160);
    input.addEventListener('input', liveSearch);
    if (form) form.addEventListener('submit', function (event) {
      event.preventDefault();
      liveSearch.cancel();
      updateUrl(core.buildQuery({ q: input.value }), false);
      render();
    });
    window.addEventListener('popstate', restore);
    restore();
  }

  function setupExperiences() {
    var root = document.querySelector('[data-experience-page]');
    if (!root) return;
    var form = root.querySelector('[data-experience-filters]');
    var results = root.querySelector('[data-experience-results]');
    var data = readData('experience-data');
    if (!form || !results) return;
    var filters = core.parseQuery(window.location.search);
    var kindButtons = Array.from(root.querySelectorAll('[data-kind]'));
    var facetNames = ['school', 'direction', 'stage', 'year', 'cohort'];
    var labels = { school: '全部院校', direction: '全部方向', stage: '全部阶段', year: '全部申请年份', cohort: '全部原始届次' };
    var pagination = root.querySelector('[data-experience-pagination]');
    var pageState = { page: 1, pages: 1 };

    facetNames.forEach(function (name) {
      var select = form.elements.namedItem(name);
      if (!select) return;
      select.replaceChildren(new Option(labels[name], ''));
      core.facetValues(data.records, name).forEach(function (value) {
        select.add(new Option(value === core.unknownYear && name === 'year' ? '年份未提供' : value, value));
      });
    });

    function syncControls() {
      ['q'].concat(facetNames).forEach(function (name) {
        var control = form.elements.namedItem(name);
        if (!control) return;
        if (name !== 'q') {
          Array.from(control.options).filter(function (option) { return option.dataset.unavailable; }).forEach(function (option) { option.remove(); });
          if (filters[name] && !Array.from(control.options).some(function (option) { return option.value === filters[name]; })) {
            var missing = new Option(filters[name] + '（暂无条目）', filters[name]);
            missing.dataset.unavailable = 'true';
            control.add(missing);
          }
        }
        if (name !== 'q' || document.activeElement !== control) control.value = filters[name];
        if (name === 'direction') {
          control.disabled = control.options.length < 2;
          if (control.disabled) control.options[0].textContent = '可用关键词查找专业';
        }
      });
      kindButtons.forEach(function (button) {
        var active = button.dataset.kind === filters.kind;
        button.setAttribute('aria-pressed', String(active));
        button.classList.toggle('is-active', active);
      });
    }

    function render() {
      var matches = core.filterExperiences(data.records, filters);
      pageState = core.paginate(matches, filters.page, 12);
      filters.page = pageState.page > 1 ? String(pageState.page) : '';
      updateUrl(core.buildQuery(filters), true);
      var returnPath = window.location.pathname + core.buildQuery(filters);
      results.replaceChildren();
      setText(root, '[data-experience-count]', '共 ' + matches.length + ' 篇');
      var status = null;
      if (!data.valid) status = { title: '暂时无法读取经验资料。', description: '请刷新页面后重试，或先通过导航浏览其他内容。' };
      else if (!data.records.length) status = { title: '故事还未写入，期待真实的分享。', description: '目前暂无已收录内容。后续将逐步整理学员的申请与成长经历。' };
      else if (!matches.length) status = { title: '还没有找到符合条件的经历。', description: '试试减少筛选条件，或清空筛选后重新查找。' };
      setStatus(root, '[data-experience-status]', status);
      var fragment = document.createDocumentFragment();
      pageState.records.forEach(function (record) {
        var target = internalUrl(record.url);
        if (!target) return;
        target.searchParams.set('return', returnPath);
        var article = element('article', 'experience-card');
        var meta = [record.kind, record.school];
        if (record.cohort) meta.push(String(record.cohort).includes('届') ? record.cohort : record.cohort + ' 届');
        else if (record.applicationYear) meta.push(record.applicationYear + ' 年申请');
        else if (record.collectionYear) meta.push(record.collectionYear + ' 年收集 · 考核年份未提供');
        else meta.push('申请年份未提供');
        article.append(element('p', 'card-meta', meta.filter(Boolean).join(' · ')));
        var heading = element('h2', 'card-title');
        var link = element('a', 'experience-title-link', record.title || '未命名经验');
        link.href = target.pathname + target.search + target.hash;
        heading.append(link);
        article.append(heading);
        if (record.description) article.append(element('p', 'card-description', record.description));
        var tags = element('div', 'card-tags');
        (record.directions || []).concat(record.stages || []).forEach(function (tag) { tags.append(element('span', 'tag', tag)); });
        if (tags.childNodes.length) article.append(tags);
        if (record.author) article.append(element('p', 'card-author', record.author));
        fragment.append(article);
      });
      results.append(fragment);
      if (pagination) {
        pagination.hidden = pageState.pages <= 1;
        pagination.querySelector('[data-page-prev]').disabled = pageState.page <= 1;
        pagination.querySelector('[data-page-next]').disabled = pageState.page >= pageState.pages;
        setText(pagination, '[data-page-status]', '第 ' + pageState.page + ' / ' + pageState.pages + ' 页');
      }
      var studentContext = root.querySelector('[data-student-context]');
      if (studentContext) studentContext.hidden = !filters.student;
      var studentInput = form.elements.namedItem('student');
      if (studentInput) studentInput.value = filters.student;
      syncControls();
    }

    function change(replace) {
      filters.page = '';
      ['q'].concat(facetNames).forEach(function (name) {
        var control = form.elements.namedItem(name);
        if (control) filters[name] = control.value.trim();
      });
      updateUrl(core.buildQuery(filters), replace);
      render();
    }

    if (pagination) pagination.addEventListener('click', function (event) {
      var previous = event.target.closest('[data-page-prev]');
      var next = event.target.closest('[data-page-next]');
      if (!previous && !next) return;
      liveFilter.cancel();
      filters.page = String(pageState.page + (previous ? -1 : 1));
      updateUrl(core.buildQuery(filters), false);
      render();
      results.scrollIntoView({ block: 'start' });
    });

    var liveFilter = debounce(function () { change(true); }, 160);
    form.addEventListener('input', function (event) {
      if (event.target.name === 'q') liveFilter();
    });
    form.addEventListener('change', function (event) {
      if (facetNames.includes(event.target.name)) {
        liveFilter.cancel();
        change(false);
      }
    });
    form.addEventListener('submit', function (event) {
      event.preventDefault();
      liveFilter.cancel();
      change(false);
    });
    kindButtons.forEach(function (button) {
      button.addEventListener('click', function () {
        liveFilter.cancel();
        filters.kind = button.dataset.kind;
        change(false);
      });
    });
    var clear = root.querySelector('[data-clear-filters]');
    if (clear) clear.addEventListener('click', function () {
      liveFilter.cancel();
      filters = core.parseQuery('');
      var input = form.elements.namedItem('q');
      if (input) input.value = '';
      updateUrl('', false);
      render();
    });
    window.addEventListener('popstate', function () {
      liveFilter.cancel();
      filters = core.parseQuery(window.location.search);
      var input = form.elements.namedItem('q');
      if (input) input.value = filters.q;
      render();
    });
    render();
  }

  function setupMenu() {
    var toggle = document.querySelector('[data-menu-toggle]');
    if (!toggle) return;
    var menu = document.getElementById(toggle.getAttribute('aria-controls'));
    if (!menu) return;
    var mobile = window.matchMedia('(max-width: 760px)');
    function setOpen(open, focusToggle) {
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? '关闭导航菜单' : '打开导航菜单');
      menu.hidden = mobile.matches && !open;
      menu.classList.toggle('is-open', open);
      if (focusToggle) toggle.focus();
    }
    toggle.addEventListener('click', function () { setOpen(toggle.getAttribute('aria-expanded') !== 'true'); });
    menu.addEventListener('click', function (event) { if (event.target.closest('a') && mobile.matches) setOpen(false); });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') setOpen(false, true);
    });
    document.addEventListener('click', function (event) {
      if (mobile.matches && !menu.contains(event.target) && !toggle.contains(event.target)) setOpen(false);
    });
    mobile.addEventListener('change', function () { setOpen(false); });
    setOpen(false);
  }

  function setupUtilities() {
    document.querySelectorAll('[data-print]').forEach(function (button) {
      button.addEventListener('click', function () { window.print(); });
    });
    var requestedReturn = new URLSearchParams(window.location.search).get('return');
    document.querySelectorAll('[data-experience-return]').forEach(function (link) {
      var fallback = internalUrl(link.getAttribute('href'));
      if (fallback) link.href = core.safeReturnUrl(requestedReturn, fallback.pathname);
    });
    document.addEventListener('keydown', function (event) {
      var target = event.target;
      if (event.key !== '/' || event.ctrlKey || event.metaKey || event.altKey || event.isComposing || event.repeat) return;
      if (target.isContentEditable || target.closest('input, textarea, select, [contenteditable="true"]')) return;
      var searchLink = document.querySelector('.header-search');
      var searchInput = document.querySelector('[data-search-page] [name="q"]');
      if (!searchInput && !searchLink) return;
      event.preventDefault();
      if (searchInput) searchInput.focus();
      else searchLink.click();
    });
  }

  function setupReadingNavigation() {
    var navigation = document.querySelector('.sidebar-details');
    if (!navigation) return;
    var mobile = window.matchMedia('(max-width: 760px)');
    function sync() { navigation.open = !mobile.matches; }
    mobile.addEventListener('change', sync);
    sync();
  }

  setupSearch();
  setupExperiences();
  setupMenu();
  setupUtilities();
  setupReadingNavigation();
}());
