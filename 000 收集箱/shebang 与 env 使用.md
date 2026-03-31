---
type: manual
tags:
  - Shell
  - 工具
---

# 简介

shebang 就是字符串 `#!` 的名称（`#` 的名字是 sharp/hash，`!` 的名字是 bang）。 shebang 是脚本第一行的特殊标识，作用是告诉操作系统用哪个解释器来执行该脚本。

---

# 正文

## 示例

可以使用硬编码的解释器路径：

```bash
#!/usr/bin/bash
```

也可以使用 `env` 命令在系统的 `$PATH` 环境变量中搜索解释器，更推荐使用该方法：

```bash
#!/usr/bin/env bash
```

由于在解析 shebang 时，最多只识别一个解释器参数，当出现多个参数时，会把这些参数作为一个整体字符串传给解释器，从而导致错误。这时只能使用 `env` 命令的 `-S` 参数，进行参数的拆分：

```bash
#!/usr/bin/env -S uv run
```

## 常用参数选项

直接执行 `env` 会打印当前的所有环境变量。

```bash
-S, --split-string # 将后面的字符串按空格拆分成多个参数
-C DIR, --chdir=DIR # 执行前先切换工作目录
-i, --ignore-environment # 清空所有继承的环境变量
NAME=VAL # 临时设置环境变量
-u NAME, --unset=NAME # 临时移除环境变量
-0, --null # 打印环境时，使用 \0 (NUL) 分隔每一行（非执行时用）
```

---

# 引用

- [GNU Coreutils: env invocation](https://www.gnu.org/software/coreutils/manual/html_node/env-invocation.html)
