---
type: manual
tags:
  - nushell
  - 环境变量
---

# 简介

Nushell 使用 `$env` 前缀操作环境变量，支持临时设置、持久化和跨平台 PATH 处理。

---

# 正文

## 示例

```nu
$env.FOO = 'BAR' # 设置环境变量
$env.FOO # 读取环境变量
$env.FOO = 'NEW' # 重新赋值即覆盖
$env.FOO? | default 'BAR' # 变量可能不存在时用可选链 + 默认值

load-env { FOO: 'BAR', BAZ: 'QUX' } # 批量设置环境变量

with-env { FOO: 'BAR' } { $env.FOO } # 临时设置，不污染外层
^echo $env.FOO # 传给外部命令需加 ^ 前缀（非字符串值会自动转为字符串）

hide-env FOO # 删除环境变量

env # 列出所有环境变量（输出为 Record）
$env # 直接查看整个环境变量 Record

$env.PATH | append '/new/path' # 追加 PATH 到末尾
$env.Path | prepend '/new/path' # 追加 PATH 到开头
use std/util "path add"; path add '/new/path' # 推荐：标准库 helper
```

## 常用命令

```nu
$env.VAR # 读取，大小写不敏感（$env.PATH 等价 $env.Path）
$env.VAR = 'val' # 当前 scope 赋值（仅当前 scope 有效）
load-env { K1: v1, K2: v2 } # 批量赋值
with-env { K: val } { block } # 块内临时，块外不受影响（词法作用域）
hide-env VAR # 删除当前 scope 定义；无法删系统继承变量
env # 列出所有环境变量（输出为 Record）
config nu # 编辑 config.nu，其中 $env 赋值可持久化
path add "path" # 追加 PATH（跨平台）
```

> 注意：`FOO=BAR cmd` 内联语法在 Nushell 中无效，需使用 `with-env`。

---

# 引用

- [Nushell - Environment](https://www.nushell.sh/book/environment.html)
- [Nushell - Configuration](https://www.nushell.sh/book/configuration.html)
- [load-env 命令文档](https://www.nushell.sh/commands/docs/load-env.html)
- [hide-env 命令文档](https://www.nushell.sh/commands/docs/hide-env.html)
