'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { parseQuery, buildQuery, filterStudents, safeReturn } = require('../static/js/students.js');
const rows = [
  {id:'a',school:'甲大学',cohort:'2027届',year:'',featured:'0',search:'匿名01 甲大学 电子信息'},
  {id:'b',school:'乙大学',cohort:'2027届',year:'2026',featured:'1',search:'匿名02 乙大学 自动化'},
  {id:'c',school:'甲大学',cohort:'',year:'2025',featured:'0',search:'匿名03 甲大学 自动化'}
];
test('Chinese keyword and combined filters select the same record', () => {
  assert.deepEqual(filterStudents(rows, {q:'甲大学 电子',school:'甲大学',cohort:'2027届',year:'unknown'}).map(x=>x.id), ['a']);
});
test('years remain independent from cohorts and unknown is selectable', () => {
  assert.deepEqual(filterStudents(rows, {year:'2026'}).map(x=>x.id), ['b']);
  assert.deepEqual(filterStudents(rows, {cohort:'unknown'}).map(x=>x.id), ['c']);
});
test('no match, featured-only, and clear filters', () => {
  assert.equal(filterStudents(rows, {school:'不存在'}).length, 0);
  assert.deepEqual(filterStudents(rows, {featured:'1'}).map(x=>x.id), ['b']);
  assert.equal(filterStudents(rows, parseQuery('')).length, 3);
});
test('URL state survives reload and removes unsupported keys', () => {
  const state = parseQuery('?q=电子&school=甲大学&cohort=2027届&year=unknown&featured=1&unsafe=x');
  assert.deepEqual(parseQuery(buildQuery(state)), state);
  assert.equal(parseQuery('?featured=true').featured, '');
  assert.equal(buildQuery(state).includes('unsafe'), false);
});
test('return URL preserves filters only for the exact student-list path', () => {
  const path = '/micu-baoyan/students/';
  assert.equal(safeReturn(path+'?q=电子&year=unknown&unsafe=x', path), path+'?q=%E7%94%B5%E5%AD%90&year=unknown');
  for (const value of ['https://evil.example/', '//evil.example/', '/other/?q=x', '/\\evil.example', null]) assert.equal(safeReturn(value, path), path);
});
