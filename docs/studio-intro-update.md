# v0.2.2 首页工作室介绍

日期：2026-09-27。根据用户给出的 [米醋电子工作室官网](https://svip.micu.wiki/) 首页，将竞赛培训、项目实践、主要专业方向与学习支持整理为一段简短介绍。

首页主视觉下方新增工作室简介，使用已有本地Logo。官网按钮链接至 `https://svip.micu.wiki/`，在新标签页打开，带 `noopener noreferrer` 和需联网提示。正文不包含价格、招生统计或成果承诺。

维护入口：`content/_index.md` 的 `params.studio`；呈现使用 `layouts/home.html` 和 `static/css/site.css`。

验证结果：

- 官网内容实际访问并核对，按钮网址与用户给出的地址一致。
- 生产及子路径构建通过，各39个HTML、3182个本地引用、2处JSON；没有新增远程自动加载资源。
- 内置浏览器检查1440px与390px布局，无整页横向溢出；简介、Logo、按钮和联网提示正常，未记录脚本错误或警告。
- 桌面与手机截图位于 `screenshots/studio-intro-desktop.png` 和 `screenshots/studio-intro-mobile.png`。
- 离线包版本更新为v0.2.2；本轮未重复测试系统打印、独立Chrome／Edge或系统断网。
