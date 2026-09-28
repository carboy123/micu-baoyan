---
title: "{{ replace .File.ContentBaseName `-` ` ` | title }}"
description: "用一句话说明这篇文章帮助读者解决什么问题。"
weight: 100
lastmod: {{ .Date }}
draft: true
params:
  status: example
  stage: "适用阶段"
  sourceNote: ""
  sources: []
---

开头说明本文适合谁、解决什么问题。涉及资格、日期或院系要求时，核对适用年度的官方来源。

## 核心内容

填写清楚、可执行的解释或建议。公开前删除所有填写提示，将 draft 改为 false，并按内容设置 params.status。

## 可以开始做的事

填写任务和可检查的成果。

## 相关内容

添加存在的站内文章链接，推荐使用 Hugo relref，以兼容站点子路径。
