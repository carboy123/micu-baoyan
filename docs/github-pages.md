# GitHub Pages 发布与维护

本项目用 GitHub 保存源码，用 GitHub Actions 构建和检查网站，再将静态产物发布到 GitHub Pages。线上阅读需要联网；原有 Windows 本机预览入口继续可用。

## 工作流

配置文件为 [`.github/workflows/pages.yml`](../.github/workflows/pages.yml)。推送到 `main` 后自动运行，也可以在仓库的 **Actions → Build and deploy Pages → Run workflow** 中选择 `main` 手动运行。其他分支不发布。

构建和部署分成两个任务，检查失败时不会上传新站点：

1. 取出仓库源码，通过 `configure-pages` 读取实际站点地址。
2. 下载固定的 **Hugo 0.166.0 extended / Linux amd64**，校验 SHA256 后解压。
3. 使用仓库内的 Hugo Book 主题、字体和静态资源进行生产构建，排除草稿。
4. 运行 `python3 tests/site-check.py public --prefix <实际路径前缀> --skip-original`，检查页面、内链、锚点、资源、搜索与经验索引隔离。
5. 仅上传 `public/` 产物；构建检查成功后才由 `deploy-pages` 发布。

Hugo Linux 归档固定为 `hugo_extended_0.166.0_linux-amd64.tar.gz`，官方 SHA256 为：

```text
0e39b901e3f919f1daae05c8ff64f0c14c8a348ef46886d63f8e6d1bb2653885
```

工作流固定使用 `checkout@v7.0.1`、`configure-pages@v6.0.0`、`upload-pages-artifact@v5.0.0`、`deploy-pages@v5.0.1` 和 `ubuntu-24.04`。没有额外安装 Node.js、Go、Dart Sass 或主题依赖；检查脚本只使用运行器现有的 Python 3 标准库。

## 首次接入

1. 确定实际 GitHub 账号或组织、仓库名称与公开范围，再将已经核实的源码推送到仓库的 `main` 分支。GitHub Free 的公共仓库支持 Pages。
2. 在仓库 **Settings → Pages → Build and deployment → Source** 中选择 **GitHub Actions**。首次配置前若工作流提示找不到 Pages 站点，完成这一步后重新运行即可。
3. 在 **Actions** 查看工作流，确认 `build` 和 `deploy` 都成功。部署结果与 **Settings → Pages** 会显示实际网址。
4. 打开该网址，检查首页、文章直达与刷新、中文搜索、经验筛选、目录跳转和下载，并检查桌面及手机布局、浏览器控制台和资源加载。

工作流通过 GitHub 自动提供的令牌和 OIDC 完成部署，无需把个人访问令牌写入源码。`github-pages` 环境如配置了审批或分支限制，应按仓库已有规则完成部署。

## 站点地址与子路径

`hugo.toml` 保留本机预览地址，线上构建通过 `configure-pages` 的 `base_url` 覆盖，不把账号或仓库名写死在源码中。构建检查从同一地址提取路径前缀，因此适用于项目子路径、账号主页和配置完成的自定义域名。

更换仓库名或域名后，先在 GitHub Pages 设置中确认新地址，再重新运行工作流。不要只修改页面中的链接或手工编辑 `public/`。

## 日常更新与资料边界

编辑 `content/` 等源文件、本机预览并核实后，提交和推送至 `main`，工作流会自动更新线上网站。多人协作时，可以通过 Pull Request 审阅后合并到 `main`。发生错误时，先修正源码并重新发布；需要恢复旧内容时，用新的提交撤销相应更改，保留修改历史。

`参考资料/`、原始面经、工具下载归档、`.runtime/` 和 `public/` 由 `.gitignore` 排除。它们不应进入源码提交；发布产物只来源于生产构建。后续如需导入真实面经，应先完成授权与内容核验。

普通 GitHub Pages 网站公开可访问，私有源码仓库不等于网站具有访问权限控制。公开库及站点仅收录适合公开的内容。

CI 的 `--skip-original` 仅跳过未随仓库公开的原始面经哈希检查；页面与资源检查仍执行。本地保留原稿时，继续运行不带该参数的检查，核验原始资料未改变。

## 发布前本机验证

在项目根目录的 PowerShell 中运行下面的示例，它模拟项目子路径，不发布网站。正式发布前应把示例 BaseURL 和检查前缀替换成实际地址与路径；站点位于域名根目录时前缀为 `/`。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-site.ps1 -BaseURL 'https://example.github.io/micu-baoyan/' -Destination '.runtime/builds/pages-check'
python tests/site-check.py .runtime/builds/pages-check --prefix /micu-baoyan/
```

公开仓库克隆副本没有原始资料时，检查命令增加 `--skip-original`。Windows Hugo 的准备方式见 [本地运行与构建](runtime.md)。上述检查不能代替部署后的浏览器验证，也不能证明 GitHub 账号权限、Pages 配置与网络可访问性已经通过。

## 常见问题

| 现象 | 检查方法 |
| --- | --- |
| `Configure Pages` 报错 | 检查仓库是否已启用 Pages、Source 是否为 GitHub Actions，以及账号或组织的权限和套餐是否支持该仓库。 |
| Hugo 下载或校验失败 | 查看该次运行的网络错误；重新下载并核对官方 release，不能为了让构建通过而跳过或随意更改校验值。 |
| `site-check.py` 失败 | 按日志修复源文件中的路径、锚点、草稿或索引问题，再重新构建；不要绕过检查。 |
| 部署等待审批 | 查看 `github-pages` 环境的审批和分支规则。 |
| 部署成功但页面或资源 404 | 以 Pages 设置中的实际网址为准，确认工作流使用其 `base_url`，检查文章路径与资源大小写，排除尚未完成的首次发布。 |

## 配置验证记录

2026-09-28 在现有 WSL Ubuntu 24.04 中核验 YAML 结构及全部内嵌 Bash 脚本语法，并使用 Linux Hugo 0.166.0 extended 实际执行工作流的归档校验、解压、生产构建和站点检查。验证副本只包含公开源码，不包含 `参考资料/`；根路径和 `/micu-baoyan/` 两种地址均通过，每种检查覆盖 39 个 HTML、3182 个本地引用和 2 处 JSON。

本机 WSL 下载受代理连接影响，因此归档通过 Windows 从同一官方 URL 下载，SHA256 在 Windows 与 Linux 分别核对通过。GitHub 托管运行器中的下载、权限、产物上传和部署仍应以实际 Actions 运行结果为准；本机验证不代表已经发布。

## 参考依据

以下资料在 2026-09-28 核对：

- [Hugo 官方 GitHub Pages 部署文档](https://gohugo.io/host-and-deploy/host-on-github-pages/)：借鉴构建、上传和部署分离以及动态 BaseURL；本项目使用本地主题，省去示例中的 Node.js、Go、Dart Sass、子模块和缓存管理。
- [Hugo v0.166.0 官方 release](https://github.com/gohugoio/hugo/releases/tag/v0.166.0)：固定 extended Linux 归档及 SHA256。
- [GitHub Pages 自定义工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)：核对任务依赖、权限和部署环境。
- [GitHub Pages 发布源设置](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)：核对首次启用方式与公开访问边界。
- [OpenSHTU 保研 Wiki 仓库说明](https://github.com/OpenSHTU/Baoyan-Wiki#readme)：参考保存源码、审阅后合并到 `main` 并自动发布的维护方式；本项目继续使用已有的本地 Hugo Book 主题与资源。
- [官方 checkout 发布记录](https://github.com/actions/checkout/releases)、[configure-pages 发布记录](https://github.com/actions/configure-pages/releases)、[upload-pages-artifact 发布记录](https://github.com/actions/upload-pages-artifact/releases)、[deploy-pages 发布记录](https://github.com/actions/deploy-pages/releases)：核对实际可用版本。GitHub 通用文档中的部分示例仍使用旧主版本，工作流采用已核验的正式版本。
