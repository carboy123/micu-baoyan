---
title: "{{ replace .File.ContentBaseName `-` ` ` | title }}"
description: "填写真实经历的简短摘要。"
type: experience
date: {{ .Date }}
draft: true
params:
  status: published
  kind: 院校面经
  school: ""
  department: ""
  direction: ""
  stage: ""
  applicationYear: ""
  cohort: ""
  author: ""
  admissionType: ""
  result: ""
  sources: []
---

仅使用本人真实经历，确认可公开范围。未知字段留空，不根据文件名推断申请年份或入学届次。kind 可填：院校面经、申请复盘、上岸成果、上岸感言。

## 背景概况

填写本人愿意公开的内容。

## 申请与考核过程

按原文记录，注明回忆整理及适用时间。根据文章类型调整标题，可参考本机的四种模板预览。

## 结果及后续

准确记录已核实的结果状态，保留限定条件。

## 个人复盘

区分当时经历与事后建议，保留适用范围。

## 来源与整理说明

记录来源、署名与必要说明。公开前删除填写提示，确认资料后将 draft 改为 false。
