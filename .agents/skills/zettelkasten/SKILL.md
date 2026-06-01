---
name: zettelkasten
description: Use when the user asks to organize a source text into permanent notes, create literature notes or glossary entries from readings, or follow the Zettelkasten workflow. Triggers on keywords: Zettelkasten, 整理, 永久笔记, 文献笔记, 概念笔记, literature note, permanent note, evergreen note.
---

# Zettelkasten 笔记工作流

遵循 Zettelkasten 方法论，将原始文献转化为永久笔记。

## 核心流程

```
原始出处 ──→ 文献笔记 ──→ 永久笔记
(外部链接)   (原文+批注)  (纯用自己的话)
```

## 关键原则

1. **必须用自己的话消化**。"收集信息不会增加知识"（Zettelkasten.de）。
2. **永久笔记应 atomic**：一个概念一篇笔记（Andy Matuschak）。
3. **原文不必全文张贴**：只摘录关键段落，添加批注。

## 模板

### 文献笔记（`001 模板/literature.md`）

```yaml
---
type: literature
author: {{author}}
date: {{date}}
tags:
  - {{dummy}}
---
```

结构：批注在前（`> [!note | aside-r]`），原文摘录在后，末尾 `# 引用` 用 `- [标题](url)` 格式列出原始出处。

创建命令：`obsidian create path="目录/笔记名.md" template="literature"`

### 永久笔记

根据内容性质在以下模板中选择：

| 模板 | 用途 |
|------|------|
| `glossary` | 概念/术语/定律词条 |
| `idea` | 个人观点或综合思考 |
| `manual` | 操作指南/How-to |

纯用自己的话，末尾 `# 引用` 链回文献笔记和原始出处。

## 目录与 type

**根据笔记内容自行判断**放在哪个目录、使用哪种 `type`。目录选择参考现有目录结构，`type` 从现有模板中选取。不确定时暂放 `000 收集箱/`。

**一条永久笔记对应一个概念。** 如果原文包含多个独立概念，拆分为多条永久笔记。

## 批注风格

- 原文高亮：`==重点内容==`
- 批注：`> [!note | aside-r]` 放在被批注段落的**上方**
- 在批注中解释原文试图说什么、为什么值得注意、有什么隐含意味
