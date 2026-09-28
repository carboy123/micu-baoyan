---
title: "{{ replace .File.ContentBaseName `-` ` ` | title }}"
description: "说明资料用途与适用对象。"
weight: 100
lastmod: {{ .Date }}
draft: true
params:
  status: planned
  resourceCategory: 材料模板
  format: ""
  download: ""
  externalURL: ""
---

说明资料解决什么问题、如何使用，以及是否需要按目标院系要求调整。

## 使用方法

本地文件放入 static/downloads，download 填 downloads/文件名（不加开头斜杠）。外部资源可填写 externalURL，并说明需联网。

资料未完成时保持 status 为 planned，不设置虚假下载路径。资料完成、验证链接后，设置 status 为 published 和 draft 为 false，并删除填写提示。
