# 本地运行与构建

## 日常使用

需要 Windows 10/11 64 位与系统自带的 Windows PowerShell 5.1。完整预览包已包含 Hugo 0.166.0 extended（Windows amd64），不需要另外安装 Node.js、Python、Git 或服务器软件；日常阅读不需要联网。

1. 双击项目根目录的 `启动预览.cmd`，浏览器会在构建就绪后打开 <http://127.0.0.1:1313/>。
2. 再次启动会复用已确认属于当前项目的进程。关闭浏览器后，预览进程仍在后台运行。
3. 双击 `停止预览.cmd` 停止当前项目的预览。它只处理运行记录中且程序路径、启动时间都匹配的进程。

预览只绑定 `127.0.0.1`，同局域网其他设备无法访问。项目目录可以包含中文和空格。启动脚本不自动结束占用端口的其他进程；如果 `1313` 已被占用，请自行关闭相应程序后重试。

修改 Markdown 后 Hugo 自动重新构建。开发预览包含 draft 模板，使用内存渲染，不将开发草稿写入生产输出目录。

## 命令行入口

在项目根目录打开 PowerShell，可运行：

```powershell
# 不打开浏览器，适用于验证或自动化
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-preview.ps1 -NoBrowser

# 停止属于当前项目的本机预览
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\stop-preview.ps1

# 默认生成 public/，排除 draft 内容
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-site.ps1

# 模拟 GitHub Pages 项目子路径；此命令仅构建，不会发布
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-site.ps1 -BaseURL 'https://example.github.io/micu-baoyan/' -Destination '.runtime/builds/subpath'
```

`构建网站.cmd` 等价于默认构建命令，也接受 `-BaseURL` 和 `-Destination`。构建目录只能位于当前项目内；源文件目录不可作为输出目录。首次目标目录必须为空，脚本会写入 `.micu-build-output` 标记。再次构建会清理这一输出目录中的旧产物，因此不要将手写内容放入构建输出目录。`.runtime` 下只允许使用 `.runtime/builds/子目录` 作为输出。

`public/` 是生成产物，修改应回到 `content/`、`layouts/`、`assets/` 或 `static/`。正式发布时只上传构建产物，不上传整个项目、原始面经或 `.runtime/`。

## 启动失败与日志

启动失败返回非零退出码，并提示日志位置：

- `.runtime/preview.log`：Hugo 常规输出。
- `.runtime/preview-error.log`：构建与运行错误。
- `.runtime/preview.json`：当前项目预览进程的 PID、启动时间、程序路径和项目路径。

启动前会核对 Hugo 程序的 SHA-256。若文件缺失、程序被修改或配置不完整，请恢复对应文件；不要随意修改校验值。预览异常可先运行停止入口，再重新启动。脚本遇到无法确认所有权的进程时不会将其结束。

## 运行时来源与许可

固定运行时来自 [Hugo 官方 v0.166.0 release](https://github.com/gohugoio/hugo/releases/tag/v0.166.0)。下载文件为 `hugo_extended_0.166.0_windows-amd64.zip`，已与同一 release 的官方 checksums 核对。

`tools/hugo/runtime.json` 记录版本、下载来源、归档 SHA-256 和程序 SHA-256；`tools/hugo/checksums.txt` 保留官方校验清单，`tools/hugo/LICENSE` 保留 Apache 2.0 许可。固定完整工具、主题与字体之后，预览和构建均不依赖在线拉取。

后续升级需重新下载官方归档并校验，再同步版本清单；不要只覆盖 `hugo.exe`。本次不自动检查更新、不创建远程仓库、不触发公开发布。

## 本地主题与字体

`static/fonts/` 包含 Adobe 官方思源黑体 `SourceHanSansCN-Regular.otf`、思源宋体 `SourceHanSerifCN-Regular.otf` 及两份 SIL Open Font License。`DEPENDENCIES.json` 记录主题版本与目录树 SHA-256，以及字体和许可的官方提交、Git Blob 标识、文件大小和 SHA-256。字体原件未经过裁切或改名转换。

`dev/prepare_assets.py` 仅供开发者恢复依赖时使用，需要 Python 3.10 或更新版本；日常运行与构建不会调用它。已验证的本地主题、字体和许可将直接复用，重复执行不会重新下载。缺失或损坏的字体会从固定的 Adobe 官方 GitHub 提交恢复；大文件优先使用官方 Git Blob API，失败后尝试固定提交的 raw URL，网络请求有超时与最多三次重试。主题目录如果发生修改，脚本会停止并保留本地修改，不直接覆盖。

## 封装可转发的本机预览包

在确认网站、说明和验收完成后运行：

```powershell
# 仅验证必需文件、运行时、字体校验和与允许打包的文件，不生成 ZIP
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\package-preview.ps1 -ValidateOnly

# 生成离线预览源码包及 SHA-256 校验文件，不发布到网络
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\package-preview.ps1
```

当前产物为 `dist/米醋保研指南-v0.2.2.zip` 和相邻的 `.zip.sha256` 文件。解压后只有一个顶层目录“米醋保研指南”，进入后双击 `启动预览.cmd` 即可使用。

封包采用明确白名单，包括网站源文件、Markdown 模板、主题、字体与许可、Hugo 运行时、启停与构建脚本、维护文档和开发测试脚本。`参考资料/` 中的原始素材、`工作室logo/`、`.git/`、`.runtime/`、`public/`、`dist/`、缓存及临时下载文件均不进入归档；已授权用于网站的两份 `static/images/` Logo 副本包含在包内。脚本不会递归删除临时工程或源目录，也不会下载依赖；依赖缺失或校验失败时直接提示错误。
