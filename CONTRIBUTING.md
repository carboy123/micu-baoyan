# 向米醋保研指南投稿

你可以提交学员档案、面经、申请复盘、成长感言及已有内容的更正。优秀学员展示当前留空，待本人投稿并经工作室审核后上线。每位学员都可以建立档案；`featured` 是工作室的内容推荐字段，投稿时保持 `false`。

## 公开之前

本仓库公开。Fork、PR、提交历史和检查日志在合并前也可能公开；昵称不会隐藏 GitHub 账号，`draft: true` 也不是保密开关。只上传已经同意公开的内容。原始问卷、电话、私人邮箱、证件、授权凭据与身份映射通过已有私下渠道交工作室，不提交到本仓库。

不熟悉 GitHub 或希望避免账号与经历关联的同学，可直接将自己的经历或更正内容私下交工作室整理。本项目没有在线表单或后台投稿系统；不要用公开 Issue 接收私密材料。

## 浏览器投稿步骤

1. 在 https://github.com/carboy123/micu-baoyan 点击 Fork，建立自己的副本。
2. 在副本中新建内容分支，例如 `my-story`。
3. 已有本人档案时修改原文件。新增档案放在 `content/students/<student-id>/index.md`，字段参照 `archetypes/student.md`；新面经放在 `content/experiences/<article-id>/index.md`，字段参照 `archetypes/experience.md`。可通过 Add file → Create new file 完成。
4. 填写并删除所有模板提示，使用本人愿意公开的昵称。头像和成绩均可不提供；图片放在文章同目录并补充替代文本。
5. 保存 Commit changes，在原仓库点 Compare & pull request，目标为 `carboy123/micu-baoyan:main`，来源为自己的内容分支。
6. 填写 PR 清单，等待工作室审阅；继续编辑同一分支会更新同一个 PR。合并后 GitHub Pages 自动发布。

首次外部投稿的检查可能需要维护者批准运行。这只是检查授权，不是内容发布批准。投稿者不需要发布密钥或主仓库写入权限，不修改工作流、布局、脚本或构建配置。

## 优秀学员案例模板

使用 [优秀学员案例模板](archetypes/student.md)，简写基本背景、成果概况、所获 offer、最终去向和感言。学员只需填写正文，文件开头的 YAML 字段交工作室整理。

成果概况与感言选填，不要求论文题目、作者信息、竞赛过程或项目技术细节。“所获 offer”逐条简写院校、学院、培养类型与实际结果；“最终去向”单独填写。只写本人愿意公开的信息，暂无 offer 或去向未定时如实说明。

档案元数据的 `school`、`department`、`direction`、`admissionType`、`result` 只对应最终去向；正文中的多个 offer 不分别计入成果统计。工作室审核后再发布，模板本身不会生成学员案例。

## 内容字段与关系

- `studentId`：稳定的英文、数字、连字符 ID，不使用身份证、手机号或学号。已有档案沿用原 ID；面经仅在确认作者及其同意后关联，否则留空。
- `recordId`：每篇经验文章唯一的英文小写、数字、连字符标识；修改已有面经时保留原 ID，新建时不能重复使用。
- `displayName` / `author`：本人同意公开的昵称，分别用于档案和经验文章。
- `avatar`：可留空；填写本页图片名或 `static/` 下的相对路径，如 `avatar.png` 或 `images/avatar.png`。只使用本地 PNG、JPEG、WebP、GIF、AVIF，不填远程网址。
- `applicationYear`、`cohort`：分别为实际申请年份与已确认的本科毕业届别；未知项留空，不从文件名推断。历史原文的届次写法可另存 `originalCohort`，不自动当作本科毕业届别。
- `periodId`：工作室维护的成果统计分组标识，投稿者不要猜填。新年度分组由维护者先补充统计元数据。
- `undergraduateTier`、`destinationTier`：原始资料提供的本科、最终去向层次，未知可留空；不能从院校名字猜填。
- `countInOutcomes`：新投稿默认为 `false`。只有维护者核对是新增、获准统计的样本，才设为 `true`；此时须有有效 `periodId`。认领原始匿名旧样本必须先核对汇总口径，不能再次计数。
- `result`：准确保留问卷自报、入营、候补、拟录取等状态，不能把意向或优秀营员写成录取。
- `kind`：经验文章仅使用“院校面经”或“申请复盘”。独立上岸感言放在 `content/outcomes/reflections/`，使用 `type: reflection`、`kind: 上岸感言` 和有效 `periodId`，由整体成果页展示。最终去向由档案维护，不从面经中的 offer 字样生成成果。
- `draft`：待整理内容设为 `true`；确认发布的文章由维护者改为 `false`。正式内容的 `params.status` 为 `published`。

只提交本人真实经历，不替他人建立身份关联；不同院系、阶段和样本独立成文。保留必要署名与版权说明，区分回忆与建议，遵守考核保密要求。更正或撤回注明已有页面，私密说明通过私下渠道交工作室。删除页面不会自动清除历史提交及他人 Fork。

## 维护者审核与发布

PR 自动检查 Hugo 生产构建、站内链接、字段、ID 唯一性、经验关联、明显私密字段和未删除的模板占位。检查不能证明身份、真实性或完整隐私授权，这些由工作室人工核对。无关联作者的合法匿名面经允许发布，缺失年份不补齐。

建议远端 `main` 要求：PR 合并、`Validate contribution` 检查通过、CODEOWNERS 审阅、新提交使旧批准失效。CODEOWNERS 本身不强制阻止合并，须配合远端分支规则。仅有一名维护者时保留经过记录的管理员例外或增加第二审阅人，避免维护者自己的 PR 因不能自我批准而锁住。

`pr-check.yml` 只由 `pull_request` 触发，只有 `contents: read`，不部署、不使用发布密钥；`pages.yml` 在 `main` 更新后构建发布。正式审核还需回看全部变更文件，确认未夹带程序或工作流修改。

项目根目录可执行：

```powershell
python scripts/check-contributions.py
python -m unittest discover -s tests -p "test_*.py"
node --test tests/students.test.cjs
```

生产构建和页面预览沿用 README 命令。PR 合并与部署成功应分别确认。

官方说明：[Fork 后提 PR](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/creating-a-pull-request-from-a-fork)、[CODEOWNERS 与分支保护](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)、[Fork 工作流权限](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request)。
