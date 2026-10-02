---
title: "{{ replace .File.ContentBaseName `-` ` ` | title }}"
description: "填写真实经历的简短摘要。"
type: experience
date: {{ .Date }}
draft: true
params:
  status: published
  kind: 院校面经
  recordId: ""
  school: ""
  department: ""
  direction: ""
  stage: ""
  applicationYear: ""
  cohort: ""
  author: ""
  studentId: ""
  admissionType: ""
  result: ""
  sources: []
---

仅使用本人真实经历，确认可公开范围。recordId 填本篇文章唯一的英文小写、数字和连字符标识，修改旧文时沿用原 ID。未知信息留空，不根据文件名推断申请年份或原始届次。kind 只填写院校面经或申请复盘；独立上岸感言放在 content/outcomes/reflections/，使用 type: reflection。studentId 只填写已存在且确认属于本人的学员 ID；不愿关联或身份未确认时留空，文章仍可独立展示。最终去向以学员档案为准，不从本文的 offer 字样自动生成成果。

## 背景概况

填写本人愿意公开的内容。

## 申请与考核过程

按原文记录，注明回忆整理及适用时间。根据文章类型调整标题，可参考已有真实文章的字段与结构。

## 结果及后续

准确记录已核实的结果状态，保留限定条件。

## 个人复盘

区分当时经历与事后建议，保留适用范围。

## 署名与整理说明

保留原作者署名、必要版权与授权说明，注明回忆整理和适用年份。公开 PR 中的内容在合并前也可见，请先删除不愿公开的信息。公开前删除填写提示，确认资料后将 draft 改为 false。
