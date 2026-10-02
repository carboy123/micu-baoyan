(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.MicuOutcomes = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  function percentage(count, total) {
    if (!Number.isFinite(count) || !Number.isFinite(total) || count < 0 || total <= 0 || count > total) return 0;
    return count * 100 / total;
  }
  function readState(search, periods) {
    const params = new URLSearchParams(search);
    let requested = params.get('period');
    if (requested === 'application-2025' && periods.includes('cohort-2026')) requested = 'cohort-2026';
    return {
      period: periods.includes(requested) ? requested : (periods[0] || ''),
      q: (params.get('schoolq') || '').trim(),
      all: params.get('all') === '1'
    };
  }
  function stateURL(currentURL, state) {
    const url = new URL(currentURL);
    if (state.period) url.searchParams.set('period', state.period);
    else url.searchParams.delete('period');
    if (state.q) url.searchParams.set('schoolq', state.q);
    else url.searchParams.delete('schoolq');
    if (state.all) url.searchParams.set('all', '1');
    else url.searchParams.delete('all');
    return url.pathname + url.search + url.hash;
  }
  function rankSchools(schools, query) {
    const q = String(query || '').trim().toLocaleLowerCase('zh-CN');
    return schools.filter(item => Number.isFinite(item.count) && item.count > 0 && String(item.name).toLocaleLowerCase('zh-CN').includes(q))
      .slice().sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, 'zh-CN'));
  }
  function visibleSchools(schools, state, limit) {
    const ranked = rankSchools(schools, state.q);
    return { total: ranked.length, rows: state.all || state.q ? ranked : ranked.slice(0, limit === undefined ? 10 : limit) };
  }
  return { percentage, readState, stateURL, rankSchools, visibleSchools };
});
