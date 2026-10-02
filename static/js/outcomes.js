(function () {
  'use strict';
  const page = document.querySelector('[data-outcome-page]');
  const core = window.MicuOutcomes;
  if (!page || !core) return;
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
    return { panel, rows, input: panel.querySelector('[data-school-query]'), more: panel.querySelector('[data-school-more]') };
  });
  function updateURL(replace) {
    const url = core.stateURL(window.location.href, state);
    if (url !== window.location.pathname + window.location.search + window.location.hash) {
      window.history[replace ? 'replaceState' : 'pushState']({}, '', url);
    }
  }
  function render() {
    links.forEach(link => {
      const selected = link.dataset.periodLink === state.period;
      if (selected) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
      link.href = core.stateURL(window.location.href, { ...state, period: link.dataset.periodLink, all: false });
    });
    panelData.forEach(({ panel, rows, input, more }) => {
      const selected = panel.dataset.outcomePeriod === state.period;
      panel.hidden = !selected;
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
    state = { ...state, period: link.dataset.periodLink, all: false };
    updateURL(false);
    render();
  }));
  panelData.forEach(({ panel, input, more }) => {
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
  render();
})();
