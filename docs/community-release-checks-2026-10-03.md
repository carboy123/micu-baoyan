# 学员社区 v0.4.0 验收记录

本次范围：成果比例与院校分布、经验分类和分页、学员档案、投稿模板及审核工作流。2026-10-03 完成独立发布目录检查，未包含并行进行的其他阅读排版修改。

## 内容与统计

- 162 篇面经、50 篇 2025 年匿名感言，共 212 条经验；82 份匿名学员档案。
- 2025 年申请 64 条去向样本；2027 届 83 份问卷排除一份完全重复提交后为 82 条。
- 本科、去向层次与院校分布分别核对，维度合计等于各批分母。2025 年感言不增加统计人数。
- 原始资料保留；四份原始输入 SHA256 与整理前一致。私人联系信息、IP、问卷标识和身份对照未进入公开内容。
- 2027 届的统计由已审核档案重算；单独夹具确认新增和修改档案会更新汇总，草稿及未批准计数的档案不计入。
- 面经与个人页只通过确认过的 studentId 关联。本次不推测历史作者，也不自动选出精选学员。

## 自动验证

在固定 Hugo 0.166.0 extended 下执行：

```text
python scripts/check-contributions.py
python -m unittest discover -s tests -p test_contributions.py
node --test tests/core.test.cjs tests/students.test.cjs tests/outcomes.test.cjs
python tests/outcome-aggregation.py --hugo tools/hugo/hugo.exe
hugo --environment production --buildDrafts=false --minify --baseURL https://carboy123.github.io/micu-baoyan/ --destination .runtime/release-preview/micu-baoyan --cacheDir <绝对缓存路径>
python tests/site-check.py .runtime/release-preview/micu-baoyan --prefix /micu-baoyan/ --skip-original
git diff --check
```

投稿字段校验、20 项 Python 测试、22 项 JavaScript 测试、真实 Hugo 统计夹具通过。生产产物检查覆盖 334 个 HTML、20,214 个本地引用和 3 处 JSON。公开克隆不含原件，因此该目录检查显式跳过原始素材哈希；本地资料整理时已单独核对。

## 浏览器验证

在应用内 Chromium 浏览器检查 1440px、768px、390px 布局，并复查独立发布构建的项目子路径：

- 两个成果批次切换、比例表、院校搜索、无结果、清空、展开全部与刷新恢复。
- 学员关键词与院校组合筛选、精选空态、进入档案与返回保留条件。
- 面经分类、院校与阶段组合、分页、刷新、详情返回、感言与 2025 年份联动。
- 390px 学员详情及成果图表无页面横向溢出；桌面与平板图表正常显示。
- 控制台未出现本次功能相关错误。

页面资源与索引已检查为本地依赖。本次未实际关闭系统网络，也未另开独立 Chrome、Edge 客户端测试；这些不记为已完成。自动部署与远端分支规则以 GitHub 的实际状态为准。
