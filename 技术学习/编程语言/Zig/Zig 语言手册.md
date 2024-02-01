# 简介

[Zig](https://ziglang.org) 是一种通用的编程语言和工具链，用于维护健壮、最优和可重用的软件。

- 健壮：即使对于 OOM 等 corner case，行为也总是正确的；
- 最优：以程序能够最佳执行的方式来编写代码；
- 可重用：相同的代码可以在具有不同限制的环境中运行；
- 可维护：可以精确得向编译器和其他程序员传达意图。

# Hello World

```zig file:hello.zig
const std = @import("std");

pub fn main() !void {
  const stdout = std.io.getStdOut().writer();
  try stdout.print("Hello, {s}!\n", .{"world"});
}
```

```bash title:Shell
$ zig build-exe hello.zig
$ ./hello
Hello, world!
```

该代码首先使用 `@import` 内置函数将 Zig 标准库添加进来。然后使用 `pub fn` 声明一个 `public` 函数 `main`，告诉 Zig 编译器该程序的入口。

在该示例中，`main` 函数的返回值是 `!void` 类型，这是一个 `Error Union Type`，该类型可以是一个 `Error Set Type` 或者任意的数据类型，类似于其他语言中的 `option` 类型或者 llvm 中的 `FailureOr` 类型。该类型的完整形式是 `<ErrorSetType>!<AnyDataType>`，当 `ErrorSetType` 没有指明时，Zig 编译器会自行推断。

写入标准输出流有可能会产生错误，而大多数时候写入标准错误流会更加合适，这种情况下是否成功写入也无关紧要：

```zig file:hello_again.zig
const std = @import("std")

pub fn main() void {
  std.debug.print("Hello, world!\n", .{});
}
```

```bash title:Shell
$ zig build-exe hello_again.zig
$ ./hello_again
Hello, world!
```

这种情况下，返回值的 `!` 可以被省略，因为该函数不会返回异常。
