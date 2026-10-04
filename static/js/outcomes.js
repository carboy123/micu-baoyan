(function () {
  'use strict';
  const page = document.querySelector('[data-outcome-page]');
  const core = window.MicuOutcomes;
  const contentCore = window.MicuCore;
  if (!page || !core || !contentCore) return;
  const panels = Array.from(page.querySelectorAll('[data-outcome-period]'));
  const periods = panels.map(panel => panel.dataset.outcomePeriod);
  if (!periods.length) return;
  const links = Array.from(page.querySelectorAll('[data-period-link]'));
  let state = core.readState(window.location.search, periods);
  const panelData = panels.map(panel => {
    const rows = Array.from(panel.querySelectorAll('[data-school-name]')).map(element => ({
      name: element.dataset.schoolName, count: Number(element.dataset.schoolCount), element
    }));
    rows.forEach(row => {
      row.element.querySelector('.outcome-school-track span').style.width = core.percentage(row.count, Number(panel.dataset.sampleCount)) + '%';
    });
    return { panel, rows, input: panel.querySelector('[data-school-query]'), more: panel.querySelector('[data-school-more]'),
      reflections: Array.from(panel.querySelectorAll('.outcome-reflection-entry')),
      pagination: panel.querySelector('[data-reflection-pagination]') };
  });
  function updateURL(replace, changePeriod, anchor) {
    const target = new URL(core.stateURL(window.location.href, state, changePeriod), window.location.href);
    if (anchor) target.hash = anchor;
    const url = target.pathname + target.search + target.hash;
    if (url !== window.location.pathname + window.location.search + window.location.hash) {
      window.history[replace ? 'replaceState' : 'pushState']({}, '', url);
    }
  }
  function renderPeriodLinks() {
    links.forEach(link => {
      const selected = link.dataset.periodLink === state.period;
      if (selected) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
      link.href = core.stateURL(window.location.href, { ...state, period: link.dataset.periodLink, all: false }, true);
    });
  }
  function render() {
    const current = panelData.find(item => item.panel.dataset.outcomePeriod === state.period);
    state.reflectionPage = contentCore.paginate(current.reflections, state.reflectionPage, 10).page;
    renderPeriodLinks();
    panelData.forEach(({ panel, rows, input, more, reflections, pagination }) => {
      const selected = panel.dataset.outcomePeriod === state.period;
      panel.hidden = !selected;
      if (pagination) {
        const result = contentCore.paginate(reflections, selected ? state.reflectionPage : 1, 10);
        const visible = new Set(result.records);
        reflections.forEach(entry => { entry.hidden = !visible.has(entry); });
        pagination.hidden = result.pages <= 1;
        pagination.querySelector('[data-reflection-prev]').disabled = result.page <= 1;
        pagination.querySelector('[data-reflection-next]').disabled = result.page >= result.pages;
        pagination.querySelector('[data-reflection-status]').textContent = '第 ' + result.page + ' / ' + result.pages + ' 页';
      }
      if (!input) return;
      if (input.value !== state.q) input.value = state.q;
      panel.querySelector('[data-school-form]').hidden = false;
      const result = core.visibleSchools(rows, state, 10);
      const visible = new Set(result.rows.map(row => row.element));
      const list = panel.querySelector('[data-school-list]');
      core.rankSchools(rows, '').forEach((row, index) => {
        row.element.hidden = !visible.has(row.element);
        row.element.querySelector('.outcome-school-rank').textContent = String(index + 1).padStart(2, '0');
        list.appendChild(row.element);
      });
      panel.querySelector('[data-school-empty]').hidden = result.total > 0;
      panel.querySelector('[data-school-footer]').hidden = false;
      panel.querySelector('[data-school-summary]').textContent = state.q
        ? '匹配 ' + result.total + ' 个院校条目'
        : '显示 ' + result.rows.length + ' / ' + result.total + ' 个院校条目';
      more.hidden = result.total <= 10 || !!state.q;
      more.setAttribute('aria-expanded', String(state.all));
      more.textContent = state.all ? '收起院校列表 ↑' : '展开全部院校 ↓';
      panel.querySelector('[data-school-clear]').disabled = !state.q;
    });
  }
  links.forEach(link => link.addEventListener('click', event => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    state = { ...state, period: link.dataset.periodLink, all: false, reflectionPage: 1 };
    updateURL(false, true);
    render();
    document.getElementById(window.location.hash.slice(1))?.scrollIntoView({ block: 'start' });
  }));
  panelData.forEach(({ panel, input, more, pagination }) => {
    if (pagination) pagination.addEventListener('click', event => {
      const previous = event.target.closest('[data-reflection-prev]');
      const next = event.target.closest('[data-reflection-next]');
      if ((!previous && !next) || (previous || next).disabled) return;
      state = { ...state, reflectionPage: state.reflectionPage + (previous ? -1 : 1) };
      const section = pagination.closest('.outcome-reflections');
      updateURL(false, false, section.id);
      render();
      section.focus({ preventScroll: true });
      section.scrollIntoView({ block: 'start' });
    });
    if (!input) return;
    panel.querySelector('[data-school-form]').addEventListener('submit', event => event.preventDefault());
    function handleInput(event) {
      if (event.isComposing) return;
      state = { ...state, q: input.value, all: false };
      updateURL(true);
      render();
    }
    input.addEventListener('input', handleInput);
    input.addEventListener('compositionend', handleInput);
    panel.querySelector('[data-school-clear]').addEventListener('click', () => {
      state = { ...state, q: '', all: false };
      updateURL(false);
      render();
      input.focus();
    });
    more.addEventListener('click', () => {
      state = { ...state, all: !state.all };
      updateURL(false);
      render();
    });
  });
  window.addEventListener('popstate', () => {
    state = core.readState(window.location.search, periods);
    render();
  });
  window.addEventListener('hashchange', renderPeriodLinks);
  render();
  updateURL(true);
})();
