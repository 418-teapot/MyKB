# AGENTS.md

此文件为 AI 编程助手使用此仓库中的代码时提过指南。

## 项目概述

MyKB 是个人知识库，使用 Obsidian 编写和阅读。内容涵盖编程语言、计算机体系结构、LeetCode 题解、中国古典文学、公共事务笔记等。笔记以中文为主。

## 构建

```bash
python make.py           # 编译所有 LaTeX 图表（latexmk → PDF → SVG）
python make.py --clean   # 清理编译产物
```

依赖：`make`、`poppler`（提供 `pdftocairo`）、`python`、`texlive`。构建产物（`*.aux`、`*.pdf`、`*.svg`、`*.xdv` 等）已被 `.gitignore` 忽略。

## 关键约束

- **新笔记必须从模板创建**：用 `obsidian create path="路径.md" template="类型"`，不要手动写 frontmatter。
- **移动/重命名用 `obsidian move`，不要用 `mv`**：`obsidian move` 会自动更新所有 wiki 链接。
- **`.obsidian/workspace.json` 已 gitignore**，切勿提交。

## 目录结构与编号体系

数字前缀遵循类似 Zettelkasten 的组织方式：

| 目录 | 用途 |
|------|------|
| `000 收集箱/` | 快速捕获暂存 |
| `001 模板/` | 笔记模板 |
| `101 中国古典文学/` | 诗词（按 `朝代/作者/标题.md` 组织） |
| `200 公共生活/` | 公共事务（`求是/`、`睡前消息/`） |
| `300 概念/` | 词典式概念词条（定律、术语解释等） |
| `301 编程语言/` | 语言学习笔记 + `语言列表.md` + `结构模版.md` |
| `302 代码片段/` | 代码片段 |
| `303 LeetCode/` | LeetCode 题解 |
| `304 体系结构/` | 计算机体系结构笔记（含 LaTeX 图表） |

图片放在对应笔记目录下的 `Img/` 子文件夹中。

## 笔记规范

### YAML Frontmatter

每篇笔记必须包含 YAML frontmatter，其中 `type` 字段决定所需的其他字段：

| type | 必填字段 | 用途 |
|------|---------|------|
| `glossary` | `tags`, `aliases` | 词典式概念词条（定律、术语等） |
| `manual` | `tags` | 操作指南/How-to |
| `idea` | `date`, `tags` | 概念笔记 |
| `text` | `author`, `tags` | 一般文本笔记 |
| `poetry` | `author`, `tags` | 古典诗词（内容放在 `> [!poetry]` callout 中） |
| `snippet` | `lang`, `kind`（algorithm/util/config）, `tags` | 代码片段 |
| `leetcode` | `difficulty`, `tags` | LeetCode 题解 |

模板文件位于 `001 模板/`，新笔记应从对应模板创建。

### 编程语言笔记

放在 `301 编程语言/` 下，遵循 `结构模版.md` 中定义的 10 节结构：词法与基础 → 控制流 → 函数抽象 → 作用域与闭包 → 类型系统 → 对象与封装 → 模块化 → 错误处理 → 并发与并行 → 系统与 IO。

## Git 提交规范

使用语义化提交信息：`type(scope): message`。类型包括 `feat`、`fix`、`refactor`、`chore`。常用 scope：`zig`、`ocaml`、`obsidian`、`csapp`、`btnews`、`lit`（文学）、`LeetCode`、`manual`、`idea`。

## Obsidian CLI

文件操作：

```bash
obsidian open path="路径/笔记.md"                              # 打开笔记
obsidian create path="路径/笔记.md" template="manual"         # 从模板创建
obsidian move path="路径/笔记.md" to="新路径/"                # 移动/重命名（自动更新所有引用链接）
obsidian search query="关键词"                                 # 全文搜索
```

vault 健康检查：

```bash
obsidian backlinks path="路径/笔记.md"    # 查看反向链接
obsidian deadends                        # 列出无出链的笔记
obsidian orphans                         # 列出无入链的笔记
obsidian unresolved                      # 列出失效链接
obsidian tags                            # 列出所有标签
obsidian tasks todo                      # 列出未完成任务
```

## Obsidian 配置

- 编辑器：Vim 模式，tab = 2 空格，显示行号，默认预览模式
- 新笔记默认存入 `000 收集箱/`
- Markdown 链接格式：绝对路径，自动更新链接
- `obsidian-linter` 插件在保存时自动格式化（CJK 与英文间距、标题空行、有序列表递增等）
