'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const core = require('../static/js/core.js');

// These synthetic records are test fixtures only; they must not enter the site's content index.
const pages = [
  { id: 'body', title: '准备事项', description: '', body: '理解推免资格，准备电子项目。', section: '指南', url: '/guide/' },
  { id: 'title', title: '推免资格入门', description: '电子类申请指南', body: '', section: '知识', url: '/basics/' },
  { id: 'other', title: '英语面试', description: '英语准备方法', body: '', section: '指南', url: '/english/' }
];
const records = [
  { id: 'a', title: '测试甲院校面经', description: '电子项目答辩', kind: '院校面经', school: '测试甲大学', college: '测试学院', directions: ['电子信息', '嵌入式'], stages: ['夏令营'], applicationYear: 2025, cohort: 2026, author: '测试作者甲', resultStatus: '已录取' },
  { id: 'b', title: '测试申请复盘', description: '电子项目复盘', kind: '申请复盘', school: '测试甲大学', directions: ['电子信息'], stages: ['预推免'], applicationYear: '2024', cohort: 2025 },
  { id: 'c', title: '测试乙院校面经', description: '控制方向面试', kind: '院校面经', school: '测试乙大学', directions: ['控制'], stages: ['夏令营', '预推免'], applicationYear: '', cohort: 2026 },
  { id: 'd', title: '测试感言', kind: '上岸感言', school: '测试乙大学' }
];

test('中文子串搜索，标题权重高于正文，且不修改输入', () => {
  const before = structuredClone(pages);
  assert.deepEqual(core.searchPages(pages, '推免').map(p => p.id), ['title', 'body']);
  assert.deepEqual(pages, before);
});

test('空格关键词是 AND，可以命中不同字段', () => {
  assert.deepEqual(core.searchPages(pages, '推免   电子').map(p => p.id), ['title', 'body']);
  assert.deepEqual(core.searchPages(pages, '推免 英语'), []);
  assert.deepEqual(core.searchPages(pages, '   '), []);
  assert.deepEqual(core.searchPages([], '推免'), []);
});

test('英文忽略大小写和全半角差异', () => {
  assert.equal(core.searchPages([{ title: 'CET6 英语' }], 'ｃｅｔ６').length, 1);
});

test('分类、院校、方向、阶段、申请年份与文本可组合过滤', () => {
  const filters = { kind: '院校面经', school: '测试甲大学', direction: '嵌入式', stage: '夏令营', year: '2025', q: '电子 答辩' };
  assert.deepEqual(core.filterExperiences(records, filters).map(r => r.id), ['a']);
  assert.deepEqual(core.filterExperiences(records, { ...filters, stage: '预推免' }), []);
  assert.deepEqual(core.filterExperiences(records, {}).map(r => r.id), ['a', 'b', 'c', 'd']);
});

test('缺失申请年份不会从届别推断，并且可单独筛选', () => {
  assert.deepEqual(core.filterExperiences(records, { year: 'unknown' }).map(r => r.id), ['c', 'd']);
  assert.deepEqual(core.filterExperiences(records, { year: '2026' }), []);
  assert.deepEqual(core.facetValues(records, 'year'), ['2025', '2024', 'unknown']);
});

test('选项去重并展开多值方向、阶段，空资料库提供空选项', () => {
  assert.deepEqual(new Set(core.facetValues(records, 'direction')), new Set(['电子信息', '嵌入式', '控制']));
  assert.deepEqual(new Set(core.facetValues(records, 'stage')), new Set(['夏令营', '预推免']));
  assert.deepEqual(core.facetValues([], 'year'), []);
  assert.deepEqual(core.filterExperiences([], { q: '测试' }), []);
});

test('URL 完整还原中文、空格、加号和所有筛选条件', () => {
  const filters = { q: '电子 C++', kind: '院校面经', school: '测试甲大学', direction: '嵌入式', stage: '夏令营', year: 'unknown', cohort: '', student: '', page: '' };
  assert.deepEqual(core.parseQuery(core.buildQuery(filters)), filters);
  assert.equal(core.buildQuery(core.parseQuery('')), '');
  assert.equal(core.buildQuery({ q: '  推免  ', ignored: 'secret' }), '?q=%E6%8E%A8%E5%85%8D');
  assert.equal(core.parseQuery('?q=first&q=second&unknown=x').q, 'first');
});

test('详情返回链接仅允许本站经验列表路径，保留有效筛选', () => {
  const filters = { school: '测试甲大学', stage: '夏令营' };
  const destination = '/experiences/' + core.buildQuery(filters);
  assert.equal(core.safeReturnUrl(destination), destination);
  assert.equal(core.safeReturnUrl('/prefix/experiences/?year=2025', '/prefix/experiences/'), '/prefix/experiences/?year=2025');
  assert.equal(core.safeReturnUrl('/experiences/?q=abc&redirect=https%3A%2F%2Fevil.test#x'), '/experiences/?q=abc');
});

test('拒绝外站、协议相对路径、脚本、反斜杠及非列表路径', () => {
  [
    'https://evil.test/experiences/', '//evil.test/experiences/', 'javascript:alert(1)',
    '/\\evil.test/experiences/', '/experiences/../other/', '/other/',
    '/experiences/%2f%2fevil.test', '/experiences/\n?q=test', null
  ].forEach(value => assert.equal(core.safeReturnUrl(value), '/experiences/'));
});


test('届次和学员关联独立筛选，不能凭年份或名字误匹配', () => {
  const linked = records.map((r, i) => ({ ...r, studentId: i < 2 ? 'micu-test' : '' }));
  assert.deepEqual(core.filterExperiences(linked, { student: 'micu-test', cohort: '2026' }).map(r => r.id), ['a']);
  assert.deepEqual(core.filterExperiences(linked, { student: 'missing' }), []);
  const query = core.buildQuery({ student: 'micu-test', cohort: '2026', page: '2' });
  assert.equal(core.parseQuery(query).page, '2');
  assert.equal(core.safeReturnUrl('/experiences/' + query), '/experiences/' + query);
});

test('分页覆盖首末页、越界与空结果，不修改原始数据', () => {
  const items = Array.from({length: 25}, (_, i) => i);
  assert.deepEqual(core.paginate(items, '2', 12).records, items.slice(12, 24));
  assert.deepEqual(core.paginate(items, 999, 12), { records: [24], page: 3, pages: 3 });
  assert.equal(core.paginate(items, -1, 12).page, 1);
  assert.equal(core.paginate(items, 'bad', 12).page, 1);
  assert.deepEqual(core.paginate([], 3, 12), { records: [], page: 1, pages: 1 });
  assert.equal(items.length, 25);
});

test('多校合填记录可由任一院校找到，组合筛选与返回恢复不重复计数', () => {
  const multi = { id: 'multi', kind: '院校面经', school: '多校记录', schools: ['测试甲大学', '测试丙大学'], stages: ['预推免'], applicationYear: 2026 };
  const source = [...records, multi];
  const filters = { school: '测试丙大学', stage: '预推免', year: '2026' };
  assert.deepEqual(core.filterExperiences(source, core.parseQuery(core.buildQuery(filters))).map(r => r.id), ['multi']);
  assert.equal(core.filterExperiences(source, {}).length, 5);
  assert.deepEqual(core.filterExperiences(source, { ...filters, year: '2025' }), []);
  assert.deepEqual(core.facetValues(source, 'school'), ['测试丙大学', '测试甲大学', '测试乙大学']);
  assert.deepEqual(core.filterExperiences(source, { q: '测试丙大学' }).map(r => r.id), ['multi']);
});
