---
style: manual
tags:
  - GDB
---

# 正文

## 启动 GDB

调试可执行文件：

```bash
gdb <program>
```

调试 core dump 文件：

```bash
gdb <program> <core dump file>
```

调试服务程序：

```bash
gdb <program> <PID>
```

## 交互命令

### 运行

- `run`（简写为 `r`）：运行程序，当遇到断点时停止运行，等待用户输入下一步的命令；
- `continuie`（简写为 `c`）：继续执行到下一个断点处（或运行结束）；
- `next`（简写为 `n`）：单步执行，当遇到函数调用时，不会进入函数体；
- `step`（简写为 `s`）：单步执行，当遇到函数调用时，进入函数体；
- `until`：单步调试时跳出循环体；
- `until <line number>`：单步调试时运行至 `<line number>`；
- `finish`：运行程序，直到当前函数完成并返回；
- `call <func(arg)>`：调用程序中可见的函数；
- `quit`（简写为 `q`）：退出 GDB。

### 断点

- `break <line number/func>, b <line number/func>`：在 `<line number>` 处或者函数 `<func>` 的入口处设置断点；
- `break <line number/func> if <cond>`：当条件 `<cond>` 为真时设置断点；
- `delete <n>`：删除第 `<n>` 个断点；
- `disable <n>`：暂停第 `<n>` 个断点；
- `enable <n>`：启用第 `<n>` 个断点；
- `clear <line number>`：清除 `<line number>` 处的断点；
- `info b, info breakpoints`：显示当前程序的断点情况；
- `delete breakpoints`：清除所有断点。

### 打印

- `print <expr>, p <expr>`：打印表达式 `<expr>` 的值；
- `display <expr>`：每次单步运行时均会打印表达式 `<expr>` 的值；
- `watch <expr>`：设置监视点，当被监视的表达式 `<expr>` 的值发生变化，暂停执行并打印表达式 `<expr>` 的值；
- `whatis <expr>`：打印表达式 `<expr>` 的数据类型；

### 运行信息

- `backtrace, bt, where`：显示当前的调用堆栈；
- `up/down`：改变当前显示的堆栈深度

### 窗口

- `layout src`：显示源代码窗口；
- `<C-l>`：刷新窗口；
- `<C-x>a`：退出窗口。
