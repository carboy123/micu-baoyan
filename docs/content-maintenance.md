# 内容维护手册

本文对应当前 Hugo 工程。日常修改不需要写网页代码：文章放在 `content/`，分类与描述写在文章开头的 YAML 区域，页面和搜索索引在构建时自动生成。

## 1. 创建与发布一篇文章

在项目根目录打开 PowerShell，按需运行一个命令：

```powershell
# 通用知识文章
& '.\tools\hugo\hugo.exe' new content --kind knowledge 'basics/my-topic.md'

# 学员经验；后续收录真实内容时使用
& '.\tools\hugo\hugo.exe' new content --kind experience 'experiences/my-story.md'

# 资料说明页
& '.\tools\hugo\hugo.exe' new content --kind resource 'resources/my-resource.md'
```

将示例文件名换成要创建的稳定路径；已有文件直接编辑，不使用 `--force` 覆盖。三个命令分别使用 `archetypes/knowledge.md`、`experience.md` 和 `resource.md`，默认 `draft: true`。

1. 填写标题、简介和正文，删除模板里的填写提示。
2. 涉及官方规则时记录适用年度、来源与核对时间。
3. 启动本机预览，检查目录、排版、链接与手机宽度。
4. 内容确认后设置 `draft: false`，并选择正确的 `params.status`。
5. 执行生产构建，再检查搜索、导航及下载是否符合预期。

### 通用字段

```yaml
---
title: 文章标题
description: 一句话说明本文帮助读者解决的问题。
weight: 80
lastmod: 2026-09-27
draft: true
params:
  status: example
  stage: 大三至申请季
  sources:
    - title: 官方文件名称与适用年度
      url: https://yz.chsi.com.cn/tm/
---
```

`title`、`description`、`weight`、`lastmod` 和 `draft` 是顶层字段；`status`、`stage`、`sources` 等项目字段放在 `params` 下，不能将 `status` 写在顶层。`sources` 仅填写与正文相关的官方政策或机构说明，显示在文末“官方依据”中；没有相应依据时省略或留空。学习仓库等外链在资源正文里注明维护方和用途，不归为招生政策。适用范围直接在正文说明，不再设置一般来历说明字段。YAML 使用空格缩进，不用 Tab。`weight` 越小，在同栏目中的顺序越靠前。更新正文后同步修改 `lastmod`。

| 状态 | 使用场景 | 非草稿时的行为 |
| --- | --- | --- |
| `example` | 已可阅读的通用示例 | 正常展示，进入搜索 |
| `published` | 已确认可展示的正式内容 | 正常展示，进入搜索；经验文章进入经验库 |
| `planned` | 只有导读，详细内容待补充 | 显示待补充提示，不进入搜索 |
| `preview` | 字段与排版模板 | 本项目仅用于 `draft: true` 的本地模板，不进入搜索和经验库 |

`draft` 和 `status` 的作用不同：生产构建排除所有草稿，**仅设置 `status: preview` 并不能代替 `draft: true`**。在第一版中，真实经验库保持空态。

## 2. 四类学员经验

真实经验统一放在 `content/experiences/`。面经、复盘、成果和感言可以使用同一份文章模板，按类型调整正文结构。

```yaml
type: experience
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
```

| 字段 | 填写规则 |
| --- | --- |
| `kind` | 只使用：院校面经、申请复盘、上岸成果、上岸感言 |
| `school` | 原文明确的院校名称，统一同校写法 |
| `department` | 学院／院系，不能因同校而合并不同样本 |
| `direction` | 专业方向，可以写单个字符串，或 YAML 数组 |
| `stage` | 原文明确的申请阶段，可以写单个字符串，或数组 |
| `applicationYear` | 实际申请的公历年份，原文缺失时留空 |
| `cohort` | 原文提供的入学届次，保持与申请年份独立 |
| `author` | 本人同意公开的展示名或昵称 |
| `admissionType` | 原文明确的培养类型，未知时留空 |
| `result` | 实际结果状态，不把入营、优营、候补或口头意向改写为录取 |
| `sources` | 仅填写相关官方政策或机构说明；投稿署名、原始来源和必要授权说明写入正文 |

例如多方向可以填写 `direction: [电子信息, 嵌入式]`。未知字段使用 `""` 或省略，不填造出的背景数据，也不要从文件名推断时间。不要在公开文章内填写不必要的证件、电话或私人邮箱。

本机 [模板预览](http://127.0.0.1:1313/preview/) 中有四个排版示例，对应 `content/preview/`。该目录下的占位页全部为草稿；后续真实文章应新建到 `content/experiences/`，不要直接把模板改成公开案例。

资料整理时保留署名、版权与来源声明，确认本人同意公开的范围。个人回忆、当时回答和事后复盘分别表达；历史通知不能作为本年度规则。

## 3. 术语与阶段路线

### 新增术语

词典只有一份数据源：`data/glossary.yaml`。复制 `archetypes/glossary.yaml` 的条目并填写后追加，不运行 `hugo new --kind glossary`。

```yaml
- id: unique-term-id
  term: 术语名称
  aliases: [别名]
  definition: 用一句话解释概念。
  note: 说明常见误解与需要核对的条件。
  related:
    - title: 相关页面
      url: basics/overview/
```

`id` 使用唯一的小写英文和连字符，同时作为词条锚点。`related.url` 填站点相对路径，不加开头斜杠，模板会用 `relURL` 添加部署前缀。每次构建会把新增术语同步到词典和全站搜索。

### 调整阶段路线

首页的六阶段卡片来自 `data/roadmap.yaml`，正文来自 `content/basics/roadmap.md`。数据字段为 `id`、`label`、`title`、`description`、`output`、`link`。修改阶段标题或锚点时同步检查两处。

正文标题使用稳定锚点，例如：

```markdown
## 大一 · 了解规则，打好基础 {#stage-1}
```

对应的数据链接为 `basics/roadmap/#stage-1`。不要仅改一边造成首页跳转失效。

## 4. 资料、下载与本地图片

### 添加下载资料

把可公开的文件放入 `static/downloads/`，再创建资料说明页：

```yaml
params:
  status: published
  resourceCategory: 准备清单
  format: Markdown
  download: downloads/my-checklist.md
```

`download` 不写 `static/`，也不加开头斜杠。资源页面会通过 `relURL` 生成兼容子路径的下载入口。当前分组名称为材料模板、准备清单、申请记录、投稿模板、官方信息入口；保持相同写法便于归类。

外部资源使用 `externalURL`，正文注明需要联网。未完成的资料保持 `status: planned`，`download` 与 `externalURL` 留空，不挂无效按钮。

### 在文章中加入图片

为图片编写替代文本，保留比例、来源和必要署名，不依赖远程图片地址。

文章专用图片建议使用 Hugo 页面包：将文章建立为 `content/experiences/my-story/index.md`，图片放在相同文件夹，再用普通相对链接：

```markdown
![项目结构图](project-overview.png)
```

这样网页和图片随同一条路径输出，部署到项目子路径后仍可访问。使用这种组织方式时，新建命令可写为：

```powershell
& '.\tools\hugo\hugo.exe' new content --kind experience 'experiences/my-story/index.md'
```

共用图片可以新建到 `static/images/`。在布局模板中使用 Hugo 函数：

```go-html-template
<img src="{{ "images/project-overview.png" | relURL }}" alt="项目结构图">
```

`relURL` 是模板函数，不能直接作为普通 Markdown 中的函数调用。如果在现有两层文章路径（例如 `/application/projects/`）里引用 `static/images/` 图片，可写 `![项目结构图](../../images/project-overview.png)`，但页面移动后必须重新检查相对层级；文章专用图片优先使用上面的页面包方式。

## 5. 站内链接、导航和搜索

Markdown 中连接其他文章使用当前项目已有的 `relref` 写法：

```markdown
[申请材料清单]({{< relref "application/materials.md" >}})
[大一阶段]({{< relref "basics/roadmap.md#stage-1" >}})
```

Hugo 会解析目标页面，并使用当前站点前缀。布局模板中的固定站点路径使用 `{{ "basics/" | relURL }}`，不要写成 `{{ "/basics/" | relURL }}`；前导斜杠会从域名根目录计算，可能跳过 GitHub Pages 仓库前缀。[Hugo relURL 说明](https://gohugo.io/functions/urls/relurl/)

页面生成规则如下：

- 一级导航在 `hugo.toml` 的 `menus.main` 维护，当前固定五项。
- 栏目列表与基础／申请／资料侧栏读取相应栏目的页面，并按 `weight` 排序。新增文章通常不需要手工改列表。
- 搜索模板自动收录非草稿且 `params.status` 为 `example` 或 `published` 的文章，以及词典数据；`planned`、`preview` 和草稿不收录。
- 经验模板只收录 `content/experiences/` 下非草稿且状态为 `published` 的文章，筛选选项从真实记录生成。
- 文章目录根据二级、三级标题生成；标题含义应清楚，不用空标题占位。

首页精选入口、阶段数据与正文中的手写链接不是自动目录。移动或删除页面时，还要检查这些位置、面包屑与相关文章链接。

## 6. 修改后的检查

保存后先本机预览，再执行 `构建网站.cmd`。确认文章没有乱码，目录锚点正确，链接与本地图片可用，手机窄屏下没有横向撑开。

维护者具备 Python 时可运行：

```powershell
python tests/site-check.py public
```

涉及路径调整，额外构建项目子路径并核验：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-site.ps1 -BaseURL 'https://example.github.io/micu-baoyan/' -Destination '.runtime/builds/subpath'
python tests/site-check.py .runtime/builds/subpath --prefix /micu-baoyan/
```

当前脚本会检查本地原始面经哈希，并要求第一版真实经验为空。将来开始收录真实经验时，应按新的任务范围更新这项验收约束，不能用测试数据充当学员内容。

原始面经与内部采集材料不提交到公开仓库。发布前逐项检查待提交文件和公开范围，只让确认后的文章及所需资源进入站点。运行与构建问题见 [运行手册](runtime.md)，后续 GitHub Pages 接入步骤见 [项目 README](../README.md)。

## 7. 已执行的维护验证

核查日期：2026-09-27。为验证“新增文章不需要同时手动维护列表”，将 `content/` 复制到 `.runtime/tests/growth-content/`，只在副本新增一篇明显标记为测试的知识文章 `basics/maintenance-fixture/index.md`，并附一张本地 SVG 图片。主工程 `content/` 未添加测试文章。

在隔离副本中将该文章设为 `draft: false`、`params.status: published`，正文包含唯一检索词及两条 `relref` 链接。实际执行：

```powershell
$contentRoot = (Resolve-Path -LiteralPath '.runtime/tests/growth-content').Path
& '.\tools\hugo\hugo.exe' --contentDir $contentRoot --destination '.runtime/builds/growth-test' --environment production --buildDrafts=false --minify --baseURL 'https://example.github.io/micu-baoyan/'
python tests/site-check.py .runtime/builds/growth-test --prefix /micu-baoyan/
```

检查结果：

- 测试文章自动进入保研基础列表和申请材料文章的侧栏，无需修改导航模板。
- 搜索索引中恰好出现一次测试文章，正文的唯一关键词已收录。
- 页面包图片正常复制；图片路径、文章链接及阶段锚点都保留 `/micu-baoyan/` 前缀。
- 产物检查通过：28 个 HTML、1549 个本地引用、2 处 JSON；生产中无预览页、经验库为空、原始面经哈希一致。
- 三种 Hugo 新建文章命令已在 `.runtime/docs-archetype-check/` 的隔离内容目录验证，生成的字段和草稿状态与上述说明一致。

这些文件仅存在于被 Git 忽略的 `.runtime/` 中，不属于日常站点、主内容源或交付给学员的案例数据。此节记录自动维护验证，页面视觉和浏览器交互仍按单独验收记录检查。
