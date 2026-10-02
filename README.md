# 米醋保研指南

面向电子、嵌入式、自动化和计算机相关专业学员的保研知识网站，支持在线阅读和 Windows 本机预览。当前为 **v0.4.0 学员成果与经验版**：通过知识文章、项目训练、阶段任务和可下载工具，帮助学员理解保研、找到当前阶段的准备事项。

**在线阅读：[米醋保研指南](https://carboy123.github.io/micu-baoyan/)** · [源码仓库](https://github.com/carboy123/micu-baoyan) · [部署状态](https://github.com/carboy123/micu-baoyan/actions/workflows/pages.yml)

技术方案为 **Hugo 0.166.0 extended + 本地 Hugo Book 主题 + Markdown + 原生 JavaScript**，没有数据库、账号系统或后端 API。主题、脚本、字体与资料随完整预览包提供；日常阅读、修改和构建不需要联网，也不需要 Node.js、Python 或云服务器。

## 先把网站打开

在 Windows 10/11 64 位电脑上解压完整预览包，保留目录结构：

1. 双击 **启动预览.cmd**，等待浏览器打开 [本机预览](http://127.0.0.1:1313/)。
2. 修改文章后保存，Hugo 会重新构建；需要时刷新浏览器。
3. 用完后双击 **停止预览.cmd**。关闭浏览器窗口不会停止后台预览。
4. 需要生成静态网站时，双击 **构建网站.cmd**，输出在 `public/`。

预览只监听本机 `127.0.0.1:1313`。重复启动会复用当前项目的预览；端口被其他程序占用时会提示，不会结束无关进程。日志位于 `.runtime/preview.log` 和 `.runtime/preview-error.log`。

本版使用本机预览服务阅读，不提供“直接双击 HTML 文件”模式。更多命令、输出目录保护与故障排查见 [本地运行与构建](docs/runtime.md)。

## 当前有哪些内容

| 栏目 | 当前内容 |
| --- | --- |
| 首页 | 品牌介绍、六阶段入口、常用知识、经验与资料入口 |
| 保研基础 | 概览、本校规则、完整流程、术语词典、阶段路线、培养方向和常见问题 |
| 申请指南 | 材料与文书、院校选择、导师沟通、竞赛项目、报名考核、面试、专业复习、机试、系统确认及年度安排 |
| 学员经验 | 成果比例与去向分布、162 篇面经与 50 篇 2025 年匿名感言（共 212 条经验）、82 份匿名学员档案；组合筛选、分页和 PR 投稿 |
| 资料与工具 | 材料检查清单、六份空白台账与模板、面经投稿模板、临场清单、官方及公共资源入口 |

全站搜索、文章目录、移动菜单、打印与本地下载已接入。经验列表支持内容类型、院校、专业方向、阶段、申请年份与关键词组合，条件保留在网址中。

**已整理两批去向、历史面经与匿名感言。** 成果页分别展示 2025 年申请的 64 份记录与 2027 届的 82 份记录，未知院校单列。经验库收录 162 篇面经和 50 篇 2025 年匿名感言，共 212 条经验；另有 82 份匿名学员档案保存可公开的去向与感言。2025 年感言独立展示，不自动关联个人身份或学员档案。原始问卷及联系信息留在本地。后续投稿使用统一模板；本机 [内容模板预览](http://127.0.0.1:1313/preview/) 仅展示字段占位，不代表真实人物或院校经历。正式构建不包含这些草稿模板。

政策类文章保留官方依据；项目、复习和表达内容提供可按个人情况调整的准备方法。学习资源按专业方向链接项目维护方的仓库与文档，并配有入门任务。年度系统日期单列在 `application/calendar-2027/`，不混入通用路线。资格、日期和招生要求以适用年度的官方通知为准，离线版本不会自动更新招生政策。

本版整理规则、统计维护与验收见 [学员资料整理说明](docs/community-data.md)。知识资源的既有更新见 [专业准备与资源更新](docs/professional-resources-update.md)。

## 内容维护从这里开始

使用文本编辑器编辑 `content/` 中的 Markdown 文件。新增内容的精确命令、字段和图片处理见 [内容维护手册](docs/content-maintenance.md)。

在项目根目录的 PowerShell 中创建草稿：

```powershell
& '.\tools\hugo\hugo.exe' new content --kind knowledge 'basics/my-topic.md'
& '.\tools\hugo\hugo.exe' new content --kind experience 'experiences/my-story.md'
& '.\tools\hugo\hugo.exe' new content --kind resource 'resources/my-resource.md'
```

以上是三个独立示例，按需要运行，并把文件名改成简短、稳定的小写英文名称。命令默认生成草稿，不会覆盖已有文件。完成正文并核实后，再将 `draft` 改为 `false`，设置相应的 `params.status`。

| 位置 | 用途 |
| --- | --- |
| `content/` | 网站文章、栏目说明、仅开发可见的模板预览 |
| `data/` | 六阶段首页数据、术语词典与成果批次/历史匿名汇总 |
| `archetypes/` | 新文章、经验、资源与词条模板 |
| `layouts/` | 米醋首页、列表、文章与索引模板 |
| `static/` | 本地样式、脚本、字体、下载文件 |
| `themes/hugo-book/` | 完整本地主题及其许可 |
| `tools/hugo/` | 固定 Hugo 运行时、来源与校验信息 |
| `scripts/` | Windows 启动、停止和生产构建脚本 |
| `tests/` | 搜索筛选逻辑测试与产物检查脚本 |

`public/`、`.runtime/` 是生成目录，不能用来维护文章。原始面经、工作室标识及其他参考文件目前保存在 `参考资料/`，整个目录不进入站点产物、便携包或 Git 提交。

网站已使用工作室提供的透明 Logo：`static/images/micu-symbol.png` 用于页头及浏览器标签，`static/images/micu-logo.png` 用于页脚。这两份授权用图副本随网站发布和封包，原始素材保持不变。

首页主视觉下方的工作室简介与官网地址在 `content/_index.md` 的 `params.studio` 中维护。简介依据 [工作室官网](https://svip.micu.wiki/) 整理；官网入口在新标签页打开，并标注需联网访问。

## 构建与开发验证

日常用户只需双击入口；下列命令用于维护者验证。在项目根目录运行：

```powershell
# 生产构建：排除草稿，输出到 public/
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-site.ps1

# 模拟 GitHub Pages 项目子路径，仅构建，不发布
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-site.ps1 -BaseURL 'https://example.github.io/micu-baoyan/' -Destination '.runtime/builds/subpath'
```

已有构建目录必须为空或带脚本生成的 `.micu-build-output` 标记。重复构建会清理该输出目录中的旧产物，请不要将手写内容放在那里。

以下开发检查需要另外可用的 Node.js 与 Python，不是启动网站的必需条件。本轮使用 Node.js 24.11.1 和 Python 3.11.4，检查脚本不需要安装第三方包：

```powershell
node --check static/js/core.js
node --check static/js/site.js
node --test tests/core.test.cjs tests/students.test.cjs tests/outcomes.test.cjs
python scripts/check-contributions.py
python -m unittest discover -s tests -p "test_contributions.py"
python tests/site-check.py public
python tests/site-check.py .runtime/builds/subpath --prefix /micu-baoyan/
```

`site-check.py` 检查内链、锚点、资源、页面 H1、JSON、草稿与搜索隔离、远程自动加载依赖，以及本地原始面经哈希。带草稿的测试产物可以增加 `--development`。公开克隆或 CI 不含原始面经时，显式添加 `--skip-original`，只跳过原始文件哈希检查，其他检查保留；本地默认仍检查原件。生产验收检查真实经验编号、学员关联、统计合计、草稿隔离与隐私字段；不再要求经验库为空。

自动检查不能代替浏览器验收。页面改动后仍需检查桌面与手机宽度、中文搜索、筛选、返回与刷新、打印，以及断网时资源可用性。已有结果与验证边界见 [第一版验收记录](docs/acceptance.md)，详细记录见 [运行验证](docs/runtime-validation.md) 与 [交互验证](docs/behavior-validation.md)。

## 完整预览包与 Git 克隆的区别

完整预览包已经附带 `tools/hugo/hugo.exe`。`.gitignore` 特意排除了 Hugo 的 `.exe`、下载归档、生成目录与原始素材，因此 **首次 Git 克隆不会自带 Windows 可执行文件**。

克隆后按 [运行时说明](docs/runtime.md) 从固定的 Hugo 官方 release 准备对应 Windows amd64 extended 版本，核对官方归档校验及 `tools/hugo/runtime.json` 中的程序 SHA256，再放回 `tools/hugo/hugo.exe`。不要为了跳过检查修改校验值。主题及字体文件连同许可应保留在仓库中，不依赖子模块或在线拉取。

## 发布到 GitHub Pages

网站已于 **2026-09-28** 发布至 [carboy123.github.io/micu-baoyan](https://carboy123.github.io/micu-baoyan/)，源码保存在公开仓库 `carboy123/micu-baoyan`。Pages 使用 GitHub Actions，已启用 HTTPS；[首次部署](https://github.com/carboy123/micu-baoyan/actions/runs/36364263752)的构建和发布均成功。

后续更新流程：

1. 修改 `content/`、`data/` 等源文件，本机预览并完成对应检查。
2. 检查提交范围，提交并推送到 `main`；也可直接在 GitHub 编辑单篇 Markdown，预览后提交。原始面经、未经确认的个人资料和运行日志继续留在本地。
3. 查看 [Actions 部署状态](https://github.com/carboy123/micu-baoyan/actions/workflows/pages.yml)，待 `build` 与 `deploy` 成功后检查线上页面。只保存本地文件不会自动更新线上网站。

`.github/workflows/pages.yml` 使用固定 Hugo 版本构建、检查产物，再部署 Pages。工作流读取真实站点地址并处理项目子路径；本机配置保留本地预览地址。详细操作、迁移方式和故障排查见 [GitHub Pages 发布说明](docs/github-pages.md)。

工作流依据 [Hugo 官方 GitHub Pages 指南](https://gohugo.io/host-and-deploy/host-on-github-pages/) 精简，不额外引入 Node.js、Go 或 Sass 工具。只有生产构建生成的 `public/` 成为网站发布产物；原始资料不提交到源码仓库，`.gitignore` 不会自动移除已经被 Git 跟踪的文件。

## 政策依据与许可

文章的 `sources` 字段仅用于列出适用的官方政策或机构说明；学习仓库与课程链接放在资源正文中，标明维护方和用途。本站的练习、组织方法和空白模板不是院校规定，也不构成录取承诺。新增内容应自行组织表达，不复制未经授权的正文、图片或学员经历。

Hugo 运行时许可在 `tools/hugo/LICENSE`；Hugo Book 主题许可在 `themes/hugo-book/LICENSE`；本地思源黑体、思源宋体的许可在 `static/fonts/`。后续加入图片或学员资料时保留来源、署名及已确认的公开范围。

## 学员投稿与去向维护

查看 [投稿说明](CONTRIBUTING.md)。学员主页使用 `archetypes/student.md`，面经沿用 `archetypes/experience.md`；网站内也可下载模板。PR 只做校验，合并 `main` 后由 Pages 工作流发布。`CODEOWNERS` 指定 `@carboy123` 审阅，公开 PR 不具备审核前保密能力。

学员最终去向在其档案元数据中维护，`countInOutcomes` 由维护者核对重复与年份口径后设置。2027 届比例随已发布档案自动计算；2025 年无身份的去向记录保留匿名汇总，50 篇感言作为独立经验展示，不自动关联身份，也不增加成果人数。不要编辑生成页面或重新运行导入覆盖学员后续修改。
