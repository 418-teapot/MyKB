---
type: glossary
tags:
  - 工具
aliases:
  - "DOT"
  - "Graphviz"
---

**DOT 语言**是一种文本图形描述语言，用于以纯文本形式描述图的结点、连线和属性。它是 [Graphviz](https://www.graphviz.org/) 工具包的标准输入语言，由 AT&T 实验室开源。

DOT 将图抽象为三种基本结构：图（`graph`/`digraph`）、结点（`node`）和连线（`edge`）。无向图用 `graph` 声明，用 `--` 连线；有向图用 `digraph` 声明，用 `->` 连线。

Graphviz 提供多种布局器（`dot`、`neato`、`circo`、`twopi`、`fdp` 等），根据 DOT 脚本自动计算结点位置并渲染为 SVG、PNG、PDF 等格式。

---

# 引用

- [[000 收集箱/DOT 语言]]
- [DOT Language](https://www.graphviz.org/doc/info/lang.html)
