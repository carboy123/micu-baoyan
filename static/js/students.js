(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (!root || !root.document) return;
  var document = root.document;
  var page = document.querySelector('[data-students-page]');
  var back = document.querySelector('[data-student-return]');
  if (back) back.href = api.safeReturn(new URLSearchParams(root.location.search).get('from'), back.getAttribute('href'));
  if (!page) return;
  var form = page.querySelector('[data-student-filters]');
  var cards = Array.from(page.querySelectorAll('[data-student-card]'));
  var records = cards.map(function (card) { return Object.assign({}, card.dataset); });
  var empty = page.querySelector('[data-student-empty]');
  var clear = page.querySelector('[data-student-clear]');
  var controls = ['q', 'school', 'cohort', 'year', 'featured'];
  var filters = api.parseQuery(root.location.search);
  function fillControls() {
    controls.forEach(function (key) {
      var input = form.elements.namedItem(key);
      if (key === 'featured') { input.checked = filters[key] === '1'; return; }
      if (input.tagName === 'SELECT' && filters[key] && !Array.from(input.options).some(function (option) { return option.value === filters[key]; })) {
        var option = document.createElement('option'); option.value = filters[key]; option.textContent = filters[key] + '（当前无此项）'; input.appendChild(option);
      }
      input.value = filters[key];
    });
  }
  function render() {
    var visible = api.filterStudents(records, filters);
    var ids = new Set(visible.map(function (record) { return record.id; }));
    cards.forEach(function (card) { card.hidden = !ids.has(card.dataset.id); });
    page.querySelector('[data-student-count]').textContent = visible.length + ' 位学员';
    empty.hidden = visible.length > 0;
    var featuredOnlyEmpty = filters.featured === '1' && !records.some(function (record) { return record.featured === '1'; });
    page.querySelector('[data-student-empty-title]').textContent = !records.length ? '故事正在整理，等待本人补充。' : featuredOnlyEmpty ? '精选故事尚未发布。' : '当前条件没有匹配的学员。';
    page.querySelector('[data-student-empty-text]').textContent = featuredOnlyEmpty ? '每位学员都可以分享；工作室将在内容补充后推荐精选。取消此条件可查看全部学员。' : !records.length ? '学员可以按模板分享背景、准备过程与成长感言，由工作室审核后展示。' : '试试其他关键词，或清空筛选查看全部学员。';
    var from = root.location.pathname + api.buildQuery(filters);
    page.querySelectorAll('[data-student-link]').forEach(function (link) { link.href = link.dataset.base + '?from=' + encodeURIComponent(from); });
  }
  function apply() {
    controls.forEach(function (key) { var input = form.elements.namedItem(key); filters[key] = key === 'featured' ? (input.checked ? '1' : '') : input.value.trim(); });
    root.history.replaceState(null, '', root.location.pathname + api.buildQuery(filters)); render();
  }
  form.addEventListener('submit', function (event) { event.preventDefault(); apply(); });
  form.addEventListener('input', apply);
  form.addEventListener('change', apply);
  clear.addEventListener('click', function () { filters = api.parseQuery(''); fillControls(); apply(); });
  root.addEventListener('popstate', function () { filters = api.parseQuery(root.location.search); fillControls(); render(); });
  form.hidden = false; clear.hidden = false; fillControls(); render();
}(typeof window !== 'undefined' ? window : null, function () {
  'use strict';
  var keys = ['q', 'school', 'cohort', 'year', 'featured'];
  function normalize(value) { return String(value == null ? '' : value).normalize('NFKC').toLocaleLowerCase('zh-CN').trim(); }
  function parseQuery(search) { var params = new URLSearchParams(String(search || '').replace(/^\?/, '')); return keys.reduce(function (state, key) { state[key] = (params.get(key) || '').trim(); if (key === 'featured' && state[key] !== '1') state[key] = ''; return state; }, {}); }
  function buildQuery(filters) { var params = new URLSearchParams(); keys.forEach(function (key) { if (filters[key]) params.set(key, filters[key]); }); return params.size ? '?' + params.toString() : ''; }
  function filterStudents(records, filters) {
    var terms = normalize(filters.q).split(/\s+/u).filter(Boolean);
    return records.filter(function (record) {
      return (!filters.school || record.school === filters.school) && (!filters.cohort || (record.cohort || 'unknown') === filters.cohort) && (!filters.year || (record.year || 'unknown') === filters.year) && (filters.featured !== '1' || record.featured === '1') && terms.every(function (term) { return normalize(record.search).includes(term); });
    });
  }
  function safeReturn(value, fallback) {
    if (typeof value !== 'string' || !value.startsWith('/') || value.startsWith('//') || /[\\\u0000-\u0020]/u.test(value)) return fallback;
    try { var url = new URL(value, 'https://micu.invalid'); if (url.origin !== 'https://micu.invalid' || url.pathname !== fallback) return fallback; return fallback + buildQuery(parseQuery(url.search)); } catch (_) { return fallback; }
  }
  return { parseQuery: parseQuery, buildQuery: buildQuery, filterStudents: filterStudents, safeReturn: safeReturn };
}));
