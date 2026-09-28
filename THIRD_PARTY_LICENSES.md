# 第三方组件与许可

本项目保留各组件的原始许可。字体和主题随项目提供，页面不从远端加载这些资源。

| 组件 | 固定版本 / 来源 | 许可文件 |
| --- | --- | --- |
| Hugo Extended | 0.166.0，官方 Windows amd64 发行包 | `tools/hugo/LICENSE` |
| Hugo Book | v0.15.0，完整保存在 `themes/hugo-book/` | `themes/hugo-book/LICENSE` |
| 思源黑体 CN Regular | Adobe Source Han Sans，固定提交见依赖清单 | `static/fonts/source-han-sans-LICENSE.txt` |
| 思源宋体 CN Regular | Adobe Source Han Serif，固定提交见依赖清单 | `static/fonts/source-han-serif-LICENSE.txt` |

字体采用 SIL Open Font License 1.1；不修改字体文件或移除许可。Hugo 为 Apache License 2.0，Hugo Book 为 MIT License。

`DEPENDENCIES.json` 记录主题、字体及其许可文件的来源和校验信息；`tools/hugo/runtime.json` 记录 Hugo 的来源和 SHA-256。`dev/prepare_assets.py` 用于开发者联网重建主题与字体依赖，日常预览无需运行它。

米醋品牌文案、知识示例、布局及脚本由本项目维护。站内官方来源链接用于说明和核对事实，不意味着相关机构背书本网站。

## 工作室 Logo

用户提供并授权在本网站使用的米醋电子工作室标识，来自 `参考资料/工作室logo/`。网站使用以下原图的逐字节副本，保留透明背景、颜色与比例：

- `logo简化版透明版  .png` → `static/images/micu-symbol.png`，用于页头及浏览器标签图标。
- `logo透明版  .png` → `static/images/micu-logo.png`，用于页脚。

品牌图片不适用上方第三方组件的开源许可。原始素材目录仍不进入封包；已授权的网站用图副本随网站及离线包提供。
