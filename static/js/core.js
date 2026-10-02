(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.MicuCore = api;
}(typeof window !== 'undefined' ? window : null, function () {
  'use strict';

  var filterKeys = ['q', 'kind', 'school', 'direction', 'stage', 'year', 'cohort', 'student', 'page'];
  var unknownYear = 'unknown';

  function normalize(value) {
    return String(value == null ? '' : value).normalize('NFKC').toLocaleLowerCase('zh-CN').trim();
  }

  function words(query) {
    return normalize(query).split(/\s+/u).filter(Boolean);
  }

  function list(value) {
    return Array.isArray(value) ? value : (value ? [value] : []);
  }

  function searchPages(pages, query) {
    var terms = words(query);
    if (!terms.length) return [];
    return list(pages).map(function (page, index) {
      var fields = [
        [normalize(page.title), 12],
        [normalize(page.description), 5],
        [normalize([page.section, page.kind].join(' ')), 3],
        [normalize(page.body), 1]
      ];
      var score = 0;
      var matches = terms.every(function (term) {
        var termScore = fields.reduce(function (total, field) {
          return total + (field[0].includes(term) ? field[1] : 0);
        }, 0);
        score += termScore;
        return termScore > 0;
      });
      return { page: page, index: index, score: matches ? score : 0 };
    }).filter(function (entry) {
      return entry.score > 0;
    }).sort(function (a, b) {
      return b.score - a.score || a.index - b.index;
    }).map(function (entry) {
      return entry.page;
    });
  }

  function yearValue(record) {
    var value = String(record.applicationYear == null ? '' : record.applicationYear).trim();
    return value || unknownYear;
  }

  function filterExperiences(records, filters) {
    filters = filters || {};
    var terms = words(filters.q);
    return list(records).filter(function (record) {
      if (filters.kind && record.kind !== filters.kind) return false;
      if (filters.school && record.school !== filters.school) return false;
      if (filters.direction && !list(record.directions).includes(filters.direction)) return false;
      if (filters.stage && !list(record.stages).includes(filters.stage)) return false;
      if (filters.year && yearValue(record) !== String(filters.year)) return false;
      if (filters.cohort && String(record.cohort || '') !== String(filters.cohort)) return false;
      if (filters.student && record.studentId !== filters.student) return false;
      var text = normalize([
        record.title, record.description, record.body, record.kind,
        record.school, record.college, list(record.directions).join(' '),
        list(record.stages).join(' '), record.applicationYear,
        record.cohort, record.author, record.resultStatus
      ].join(' '));
      return terms.every(function (term) { return text.includes(term); });
    });
  }

  function facetValues(records, facet) {
    var key = { direction: 'directions', stage: 'stages', year: 'applicationYear' }[facet] || facet;
    var values = [];
    list(records).forEach(function (record) {
      var entries = key === 'applicationYear' ? [yearValue(record)] : list(record[key]);
      entries.forEach(function (value) {
        value = String(value == null ? '' : value).trim();
        if (value && !values.includes(value)) values.push(value);
      });
    });
    return values.sort(function (a, b) {
      if (a === unknownYear) return 1;
      if (b === unknownYear) return -1;
      if (key === 'applicationYear') return b.localeCompare(a, 'zh-CN', { numeric: true });
      return a.localeCompare(b, 'zh-CN', { numeric: true });
    });
  }

  function parseQuery(search) {
    var params = new URLSearchParams(String(search || '').replace(/^\?/, ''));
    return filterKeys.reduce(function (result, key) {
      result[key] = (params.get(key) || '').trim();
      return result;
    }, {});
  }

  function paginate(records, requestedPage, perPage) {
    perPage = Math.max(1, Math.floor(Number(perPage) || 12));
    var pages = Math.max(1, Math.ceil(records.length / perPage));
    var page = Math.min(pages, Math.max(1, Math.floor(Number(requestedPage) || 1)));
    return { records: records.slice((page - 1) * perPage, page * perPage), page: page, pages: pages };
  }

  function buildQuery(filters) {
    var params = new URLSearchParams();
    filterKeys.forEach(function (key) {
      var value = String((filters || {})[key] || '').trim();
      if (value) params.set(key, value);
    });
    var query = params.toString();
    return query ? '?' + query : '';
  }

  function safeReturnUrl(value, fallback) {
    var origin = 'https://micu.invalid';
    fallback = fallback || '/experiences/';
    var base = new URL(fallback, origin);
    var defaultUrl = base.pathname + buildQuery(parseQuery(base.search));
    if (typeof value !== 'string' || !value.startsWith('/') || value.startsWith('//') || /[\\\u0000-\u0020]/u.test(value)) return defaultUrl;
    try {
      var target = new URL(value, origin);
      if (target.origin !== origin || target.pathname !== base.pathname) return defaultUrl;
      return target.pathname + buildQuery(parseQuery(target.search));
    } catch (_) {
      return defaultUrl;
    }
  }

  return {
    searchPages: searchPages,
    filterExperiences: filterExperiences,
    facetValues: facetValues,
    parseQuery: parseQuery,
    buildQuery: buildQuery,
    safeReturnUrl: safeReturnUrl,
    paginate: paginate,
    unknownYear: unknownYear
  };
}));
