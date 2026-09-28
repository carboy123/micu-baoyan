# 搜索与阅读交互验证

核查日期：2026-09-27。本文记录已执行的检查及整站浏览器验收要点，不将纯逻辑测试等同于页面验收。

## 已执行的检查

在项目根目录执行：

```powershell
node --check static/js/core.js
node --check static/js/site.js
node --test tests/core.test.cjs
```

两个脚本语法检查通过；9 项纯逻辑测试全部通过，覆盖：

- 中文子串搜索与标题优先排序，不修改源数据。
- 多个空格分词采用 AND 匹配，支持跨标题、描述及正文命中；空查询及空资料库返回空结果。
- 英文大小写及全角、半角字符归一化。
- 内容类型、院校、方向、阶段、申请年份与关键词组合筛选；清空条件后返回全部资料。
- 申请年份未知时使用独立筛选项，不根据入学届别推断申请年份；年份降序排列，未知项放在末尾。
- 方向、阶段数组展开、选项去重和空资料库选项。
- URL 参数中中文、空格、加号及全部筛选条件的往返还原，忽略非筛选参数。
- 详情返回链接保留本站经验列表筛选，兼容部署子路径。
- 拒绝外站、协议相对地址、脚本地址、反斜杠、控制字符和非经验列表路径。

测试合成资料仅存在于 `tests/` 内的测试源码及生成的 `.runtime/tests/` 测试站，不写入 `content/`、`data/`、`static/` 或 `public/`；正式经验库仍为空。

## 模板接口核查

- `experience-data.html` 仅收录经验栏目中非草稿且 `status: published` 的文章；正文使用 `.Plain`，描述使用 `.Description`。
- 源字段 `department` 映射为 `college`；`direction` 和 `stage` 兼容单值或数组，分别映射为 `directions`、`stages`。
- `applicationYear` 和 `cohort` 保持独立；未填的申请年份为空，不推断补值。前端使用 `unknown` 作为“年份未提供”筛选参数。
- `search-data.html` 收录 `example`、`published` 状态的非草稿页面与术语，后续已发布经验也可被搜索；`planned`、`preview` 内容不进入搜索。
- 两个索引通过页面内嵌 `application/json` 提供；脚本不使用 `fetch`，也不向外部服务发送关键词。
- 经验空状态更新 `data-status-title`、`data-status-description`；兼容未标记的 `h2`、`p`，保留图标和容器结构。
- 返回链接须带 `data-experience-return` 且默认 `href` 为经验列表；脚本仅允许返回相同列表路径。

## 等待整站浏览器核查

本轮接口 review 未操作浏览器。建议在真实页面完成以下验收，并将结果记录到整体验收文档：

1. **搜索**：从顶部入口进入搜索，查询“推免资格”；输入多个中文关键词验证组合命中，查询不存在的词验证无结果；清空输入显示提示。确认结果标题、摘要、术语锚点和数量一致，控制台无错误。
2. **快捷键**：在非输入区域按 `/` 打开搜索；在搜索页按 `/` 聚焦搜索输入。输入框、下拉框、可编辑区域和中文组合输入不应被快捷键打断。
3. **经验空库**：首次进入和切换四种分类时，数量为零，图标、标题和说明均保留；不会把空库误报为“筛选无匹配”。旧 URL 中不存在的筛选值可见并可清空。
4. **经验有数据时**：后续收录真实数据后，验证分类、院校、方向、阶段、年份与关键词组合，核查无匹配提示、清空、前进后退和刷新恢复。测试时不要把合成资料发布到网站。
5. **详情回链**：从带筛选的经验列表进入详情，上下返回入口均恢复条件；修改 `return` 为外站或其他页面时回到本站默认经验列表。
6. **移动导航**：在 390px 宽度，菜单初始关闭，按钮的 `aria-expanded` 及打开/关闭文字正确；点击菜单链接、外部区域或按 Escape 可关闭，Escape 后焦点回到菜单按钮。切换桌面/手机宽度不遗留错误的隐藏状态。
7. **阅读目录**：在不超过 760px 时，知识库侧栏初次折叠，原生 `summary` 可触摸或键盘展开；桌面展开，跨断点同步。另核查文章的“本页内容”目录在窄屏仍可用，标题锚点不被顶部导航遮挡。
8. **打印与键盘**：打印按钮打开浏览器打印预览，正文可读，导航和交互控件不污染打印；Tab 能到达菜单、搜索、筛选、清空、目录和返回入口，焦点可见。

若浏览器验收引入新修改，须重新执行受影响的检查，并以最后一次改动后的结果为准。

## 独立浏览器测试站

`tests/make-browser-fixture.py` 和 `tests/serve-fixture.py` 均仅使用 Python 标准库。前者复制指定的生产构建到 `.runtime/tests/filter-fixture/`，为经验库写入三条明确标注的合成记录，并生成三篇仅用于回链验证的详情。它不改动源构建、正文或公开交付目录。

重新生成及启动方法：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-site.ps1 -Destination .runtime/builds/fixture-source -BaseURL http://127.0.0.1:1314/
python tests/make-browser-fixture.py --source .runtime/builds/fixture-source
python tests/serve-fixture.py --port 1314
```

测试入口：`http://127.0.0.1:1314/experiences/`。按 Ctrl+C 停止测试服务器。该服务器仅绑定 `127.0.0.1`，每个响应提供 `Cache-Control: no-store`，并附以下策略限制外部资源：

```text
default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data:; connect-src 'self'
```

三条记录的预期结果：

| 记录 | 类型 | 院校 | 方向 | 阶段 | 申请年份 |
| --- | --- | --- | --- | --- | --- |
| fixture-a | 院校面经 | 测试甲大学 | 电子信息、嵌入式 | 夏令营 | 2025 |
| fixture-b | 申请复盘 | 测试甲大学 | 电子信息 | 预推免 | 2024 |
| fixture-c | 院校面经 | 测试乙大学 | 控制 | 夏令营、预推免 | 未提供 |

例如“院校面经 + 测试甲大学 + 嵌入式 + 夏令营 + 2025”仅返回 fixture-a；“申请复盘 + 夏令营”无匹配；“年份未提供”仅返回 fixture-c。第三条另有 `cohort: 2026`，申请年份选择项不能因此出现 2026。

详情链接为同一测试站的 `/experiences/fixture-a/` 等路径，上下返回入口均使用当前正式脚本的 `safeReturnUrl`，无需放宽安全规则。列表筛选、刷新、详情刷新、返回和浏览器前进后退均可在该站独立验证。

生成后的文件与 HTTP 核验已通过：源生产经验索引仍为空；测试索引恰有三条；三篇详情均有两个返回入口；测试站 JS/CSS 与源构建一致；列表和详情返回 HTTP 200，CSP 及禁用缓存响应头正确；`content/` 与 `public/` 未检出三个 fixture ID。以上仍不替代真实浏览器交互验收。
