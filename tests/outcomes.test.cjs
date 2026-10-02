'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const core = require('../static/js/outcome-core.js');

test('占比使用完整样本分母，缺失类别仍纳入统计', () => {
  assert.equal(core.percentage(16, 64), 25);
  assert.equal(core.percentage(8, 64), 12.5);
  assert.equal(core.percentage(0, 64), 0);
  assert.equal(core.percentage(0, 0), 0);
  assert.equal(core.percentage(1, 0), 0);
  assert.equal(core.percentage(-1, 64), 0);
  assert.equal(core.percentage(65, 64), 0);
  assert.equal(core.percentage(NaN, 64), 0);
  const categories = [40, 16, 8];
  assert.equal(categories.reduce((sum, n) => sum + core.percentage(n, 64), 0), 100);
});
test('成果按毕业届别切换，未知批次回退，不猜申请年份', () => {
  const periods = ['cohort-2026', 'cohort-2027'];
  assert.deepEqual(core.readState('?period=cohort-2027&schoolq=%E5%A4%A7%E5%AD%A6&all=1', periods), { period: 'cohort-2027', q: '大学', all: true });
  assert.equal(core.readState('?period=2026', periods).period, 'cohort-2026');
  assert.deepEqual(core.readState('', []), { period: '', q: '', all: false });
});
test('旧2025申请批次链接准确映射到2026届，保留院校筛选与展开状态', () => {
  const periods = ['cohort-2027', 'cohort-2026'];
  const state = core.readState('?period=application-2025&schoolq=%E5%A4%A7%E5%AD%A6&all=1', periods);
  assert.deepEqual(state, { period: 'cohort-2026', q: '大学', all: true });
  const migrated = new URL(core.stateURL('https://example.test/micu-baoyan/outcomes/?period=application-2025', state), 'https://example.test');
  assert.equal(migrated.searchParams.get('period'), 'cohort-2026');
  assert.deepEqual(core.readState(migrated.search, periods), state);
  assert.equal(core.readState('?period=application-2025', ['application-2025']).period, 'application-2025');
});
test('网址保留部署子路径和其他参数，刷新与返回可以恢复状态', () => {
  const state = { period: 'cohort-2027', q: '学校 名称', all: true };
  const url = core.stateURL('https://example.test/micu-baoyan/outcomes/?campaign=test#outcome-data', state);
  assert.match(url, /^\/micu-baoyan\/outcomes\/\?/);
  assert.match(url, /campaign=test/);
  assert.match(url, /#outcome-data$/);
  const parsed = new URL(url, 'https://example.test');
  assert.deepEqual(core.readState(parsed.search, ['cohort-2026', 'cohort-2027']), state);
  const cleared = new URL(core.stateURL(parsed.href, { period: 'cohort-2026', q: '', all: false }), 'https://example.test');
  assert.equal(cleared.searchParams.has('schoolq'), false);
  assert.equal(cleared.searchParams.has('all'), false);
});
test('从感言区切换届别时锚点同步，院校搜索与其他参数保持不变', () => {
  const current = 'https://example.test/micu-baoyan/outcomes/?period=cohort-2026&schoolq=%E5%A4%A7%E5%AD%A6&campaign=test#reflections-cohort-2026';
  const state = { period: 'cohort-2027', q: '大学', all: false };
  const next = new URL(core.stateURL(current, state, true), current);
  assert.equal(next.pathname, '/micu-baoyan/outcomes/');
  assert.equal(next.hash, '#reflections-cohort-2027');
  assert.equal(next.searchParams.get('schoolq'), '大学');
  assert.equal(next.searchParams.get('campaign'), 'test');
  assert.deepEqual(core.readState(next.search, ['cohort-2026', 'cohort-2027']), state);
  const back = new URL(core.stateURL(next.href, { ...state, period: 'cohort-2026' }, true), next);
  assert.equal(back.hash, '#reflections-cohort-2026');
});
test('其他区块切届回到统计区，普通搜索和展开操作不改当前锚点', () => {
  const state = { period: 'cohort-2027', q: '学院', all: true };
  for (const hash of ['', '#outcome-data', '#schools-cohort-2026']) {
    const switched = new URL(core.stateURL('https://example.test/outcomes/?period=cohort-2026' + hash, state, true), 'https://example.test');
    assert.equal(switched.hash, '#outcome-data');
    assert.equal(switched.searchParams.get('all'), '1');
  }
  const searched = new URL(core.stateURL('https://example.test/outcomes/?period=cohort-2027#reflections-cohort-2027', state), 'https://example.test');
  assert.equal(searched.hash, '#reflections-cohort-2027');
  assert.equal(searched.searchParams.get('schoolq'), '学院');
  assert.equal(searched.searchParams.get('all'), '1');
});
test('院校按数量排序且不修改原数据，支持搜索和无匹配', () => {
  const rows = [{ name: '测试甲大学', count: 1 }, { name: '测试乙大学', count: 5 }, { name: '测试丙学院', count: 0 }];
  assert.deepEqual(core.rankSchools(rows, '').map(row => row.name), ['测试乙大学', '测试甲大学']);
  assert.equal(rows[0].name, '测试甲大学');
  assert.deepEqual(core.rankSchools(rows, '  甲大  ').map(row => row.name), ['测试甲大学']);
  assert.deepEqual(core.rankSchools(rows, '不匹配'), []);
});
test('默认前10条、完整列表、搜索与清空后的结果', () => {
  const rows = Array.from({ length: 12 }, (_, i) => ({ name: '测试院校' + String(i).padStart(2, '0'), count: 12 - i }));
  assert.equal(core.visibleSchools(rows, { q: '', all: false }).rows.length, 10);
  assert.equal(core.visibleSchools(rows, { q: '', all: true }).rows.length, 12);
  assert.equal(core.visibleSchools(rows, { q: '测试院校', all: false }).rows.length, 12);
  assert.deepEqual(core.visibleSchools(rows, { q: '无结果', all: false }), { total: 0, rows: [] });
  assert.equal(core.visibleSchools(rows, { q: '', all: false }).rows.length, 10);
  assert.deepEqual(core.visibleSchools([], { q: '', all: false }), { total: 0, rows: [] });
});

test('院校结果摘要只写入独立状态段落，不会覆盖首条院校及其链接', () => {
  const template = fs.readFileSync(path.join(__dirname, '../layouts/outcomes.html'), 'utf8');
  const script = fs.readFileSync(path.join(__dirname, '../static/js/outcomes.js'), 'utf8');
  // Exercise the actual textContent destination against the template. The prior
  // selector matched both a school <li> and the footer <p>, destroying row one.
  const assignment = script.match(/panel\.querySelector\('(\[data-school-(?:count|summary)\])'\)\.textContent/);
  assert.ok(assignment, '必须能够找到院校结果摘要的写入目标');
  const attribute = assignment[1].slice(1, -1);
  const destinations = [...template.matchAll(new RegExp('<([a-z]+)\\b[^>]*\\b' + attribute + '(?=[\\s=>])[^>]*>', 'g'))];
  assert.equal(destinations.length, 1, '状态文字选择器必须只匹配一个模板节点');
  assert.equal(destinations[0][1], 'p', '只能写入摘要段落，不能覆盖院校行');
  assert.match(destinations[0][0], /aria-live="polite"/);
  assert.match(template, /<li\b[^>]*data-school-count=/, '院校数量字段应保留用于数据计算');
});
