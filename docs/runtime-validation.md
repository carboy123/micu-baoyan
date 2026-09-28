# 本机运行时验收记录

验收日期：2026-09-27。环境：Windows，系统 Windows PowerShell 5.1；Hugo 0.166.0 extended windows/amd64。

为避免改动正式内容，运行测试使用 `.runtime/启动验证 中文路径/` 下的独立最小 Hugo 工程，复制实际运行时和启动脚本，配置两个页面：已发布文章与 draft 模板。测试工程未进入生产内容目录或搜索索引。

## 已执行

| 场景 | 操作与结果 |
|---|---|
| 官方运行时校验 | 官方 `v0.166.0` release 的 extended Windows amd64 归档与官方 checksums 对比通过；可执行 `hugo version`。完整 hash 保存在 `tools/hugo/runtime.json`。 |
| PowerShell 兼容 | 用 Windows PowerShell 5.1 的 AST Parser 解析四个实际脚本，无语法错误；脚本使用 UTF-8 BOM 保证中文字符串正确读取。 |
| 中文与空格路径 | 在 `启动验证 中文路径` 工程内实际完成启动、访问、构建、停止。 |
| 首次启动 | `start-preview.ps1 -NoBrowser` 返回 0；页面返回 HTTP 200。 |
| 重复启动 | 再次执行返回 0，`preview.json` 中的 PID 与首次一致，没有启动第二个 Hugo。 |
| 本机绑定 | 启动参数明确绑定 `127.0.0.1:1313`。根网站的监听地址由整体验收进一步检查。 |
| 生产与子路径构建 | 用 `build-site.ps1 -BaseURL 'https://example.github.io/micu-baoyan/' -Destination '.runtime/builds/subpath'` 构建成功；已发布文章存在，draft 页面不存在，HTML 中的站内链接带 `/micu-baoyan/`。 |
| 旧页面清理 | 在已标记的输出目录加入旧 HTML 再重新构建，旧页面被移除，正式页面与输出标记正常生成。已修正单独使用 Hugo `cleanDestinationDir` 无法清理这类残留的行为，改为校验目录边界与标记后清理产物。 |
| 停止与重复停止 | 停止入口返回 0，原 PID 消失；再次停止返回 0，没有结束其他程序。 |
| 端口冲突 | 独立 TCP listener 占用 1313 时，启动入口返回非 0 并给出冲突提示；停止入口未影响该 listener。测试完由测试自身关闭 listener。 |
| 配置错误 | 向测试配置写入无效 TOML，启动入口返回非 0，保留两个日志文件，移除失败状态文件，没有残留 1313 监听。 |
| 输出路径保护 | 拒绝源码目录、项目外部路径、非空未标记目录和运行记录目录，避免清理用户文件。 |
| 本地字体 | 思源黑体 8,429,224 字节、思源宋体 11,626,108 字节与 Adobe 官方 Git Blob SHA-1、OTF 文件头及文件长度比对通过；两份许可同样与官方 Blob 标识比对通过。SHA-256 和固定来源提交已记录。 |
| 依赖准备的离线缓存 | 禁用准备脚本中的网络下载函数后重复执行仍成功，清单文件保持不变；截断字体与许可数据会被校验函数拒绝。再次正常执行 `python dev/prepare_assets.py` 全部显示复用已验证缓存。 |
| 封包脚本预检 | Windows PowerShell 5.1 解析 `package-preview.ps1` 无语法错误，`-ValidateOnly` 验证必需文件、运行时和字体校验和并枚举明确白名单；预检不会生成或修改发布 ZIP。另用 Windows PowerShell 5.1 内存 ZIP 验证中文顶层目录和中文文件名编码正常。最终封包后的完整归档核验由交付验收覆盖。 |

独立运行测试结束后已释放 1313，未启动或停止正式根项目。整体页面视觉、离线字体、搜索筛选与真实站点构建，由主项目验收记录覆盖。

## 可复验命令

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-preview.ps1 -NoBrowser
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\stop-preview.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-site.ps1 -BaseURL 'https://example.github.io/micu-baoyan/' -Destination '.runtime/builds/subpath'
```

默认输出目录 `public/` 首次需为空，后续由 `.micu-build-output` 标记识别为可重新生成的产物。使用裸 `hugo` 命令生成的非空目录不会被脚本自动接管或清空；应先核实其内容，再选择新的空输出目录。
