# 简介

[Zig](https://ziglang.org) 是一种通用的编程语言和工具链，用于维护健壮、最优和可重用的软件。

- 健壮：即使对于 OOM 等 corner case，行为也总是正确的；
- 最优：以程序能够最佳执行的方式来编写代码；
- 可重用：相同的代码可以在具有不同限制的环境中运行；
- 可维护：可以精确得向编译器和其他程序员传达意图。

---

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

---

# 注释

## 普通注释

普通注释以 `//` 开始，普通注释会被 Zig 编译器忽略。

```zig file:comments.zig
const print = @import("std").debug.print

pub fn main() void {
  // Comments in Zig start with "//" and end at the next LF byte (end of line).
  // The line below is a comment and won't be executed.
  // print("Hello?", .{});
  print("Hello, world!", .{}); // another comment
}
```

## 文档注释

文档注释以 `///` 开始，是对紧随其后的内容的注释。文档注释只允许出现在特定的地方，否则（如在表达式中间或非文档注释之前）会出现编译错误。

```zig file:doc_comments.zig
/// A structure for storing a timestamp, with nanosecond precision (this is a
/// multiline doc comment).
const Timestamp = struct {
  /// The number of seconds since the epoch (this is also a doc comment).
  seconds: i64,  // signed so we can represent pre-1970 (not a doc comment)
  /// The number of nanoseconds past the second (doc comment again).
  nanos: u32,
  
  /// Returns a `Timestamp` struct representing the Unix epoch; that is, the
  /// moment of 1970 Jan 1 00:00:00 UTC (this is a doc comment too).
  pub fn unixEpoch() Timestamp {
    return Timestamp{
      .seconds = 0,
      .nanos = 0,
    };
  }
};
```

```zig file:unattached_doc-comment.zig
pub fn main() void {}

/// End of file
```

```bash title:Shell
$ zig build-obj unattached_doc-comment.zig
docgen_tmp/unattached_doc-comment.zig:3:1: error: unattached documentation comment
/// End of file
^~~~~~~~~~~~~~~
```

文档注释可以与普通注释交织在一起。目前，在生成包文档时，普通注释会与文档注释合并。

## 顶级文档注释

顶级文档注释以 `//!` 开始，是对当前 `module` 的注释。如果顶级文档注释不是放在容器的开头，则会出现编译错误。

```zig file:tldoc_comments.zig
//! This module provides functions for retrieving the current date and
//! time with varying degrees of precision and accuracy. It does not
//! depend on libc, but will use functions from it if available.

const S = struct {
  //! Top level comments are allowed inside a container other than a
  //! module, but it is not very useful. Currently, when producing
  //! the package documentation, these comments are ignored.
};
```

---

# 值

## 内建类型

| 类型             | 等价的 C 类型         | 描述                                                                   |
| ---------------- | --------------------- | ---------------------------------------------------------------------- |
| `i8`             | `int8_t`              | 8-bit 有符号整型                                                       |
| `u8`             | `uint8_t`             | 8-bit 无符号整型                                                       |
| `i16`            | `int16_t`             | 16-bit 有符号整型                                                      |
| `u16`            | `uint16_t`            | 16-bit 无符号整型                                                      |
| `i32`            | `int32_t`             | 32-bit 有符号整型                                                      |
| `u32`            | `uint32_t`            | 32-bit 无符号整型                                                      |
| `i64`            | `int64_t`             | 64-bit 有符号整型                                                      |
| `u64`            | `uint64_t`            | 64-bit 无符号整型                                                      |
| `i128`           | `__int128`            | 128-bit 有符号整型                                                     |
| `u128`           | `unsigned __int128`   | 128-bit 无符号整型                                                     |
| `isize`          | `intptr_t`            | 有符号指针大小类型                                                     |
| `usize`          | `uintptr_t`, `size_t` | 无符号指针大小整型                                                     |
| `c_char`         | `char`                | C ABI 兼容类型                                                         |
| `c_short`        | `short`               | C ABI 兼容类型                                                         |
| `c_ushort`       | `unsigned short`      | C ABI 兼容类型                                                         |
| `c_int`          | `int`                 | C ABI 兼容类型                                                         |
| `c_uint`         | `unsigned int`        | C ABI 兼容类型                                                         |
| `c_long`         | `long`                | C ABI 兼容类型                                                         |
| `c_ulong`        | `unsigned long`       | C ABI 兼容类型                                                         |
| `c_longlong`     | `long long`           | C ABI 兼容类型                                                         |
| `c_ulonglong`    | `unsigned long long`  | C ABI 兼容类型                                                         |
| `c_longdouble`   | `long double`         | C ABI 兼容类型                                                         |
| `f16`            | `_Float16`            | 16-bit 浮点型（10-bit 尾数）IEEE-754-2008 binary16                     |
| `f32`            | `float`               | 32-bit 浮点型（23-bit 尾数）IEEE-754-2008 binary32                     |
| `f64`            | `double`              | 64-bit 浮点型（52-bit 尾数）IEEE-754-2008 binary64                     |
| `f80`            | `double`              | 80-bit 浮点型（64-bit 尾数）IEEE-754-2008 80-bit extended precision    |
| `f128`           | `_Float128`           | 128-bit 浮点型（112-bit 尾数）IEEE-754-2008 binary128                  |
| `bool`           | `bool`                | `true` 或者 `false`                                                    |
| `anyopaque`      | `void`                | 用于类型擦除指针                                                       |
| `void`           |                       | 总为 `void{}`                                                          |
| `noreturn`       |                       | `break`, `continue`, `return`, `unreachable`, `while (true) {}` 的类型 |
| `type`           |                       | 类型的类型                                                             |
| `anyerror`       |                       | 错误代码                                                               |
| `comptime_int`   |                       | 编译期已知的整型字面量                                                 |
| `comptime_float` |                       | 编译期已知的浮点型字面量                                               |

除了上面的整型之外，还可以在 `i` 或 `u` 标识符后跟数字来使用任意位宽的整型，例如 `i7` 表示 7-bit 有符号整型。

## 内建值

| 值                | 描述                   |
| ----------------- | ---------------------- |
| `true` or `false` | `bool` 值              |
| `null`            | 用于设置 optional 类型 | 
| `undefined`       | 用于未指定值的变量     |

## 字符串字面量与 Unicode 字面量

字符串字面量是指向以 `null` 为终止符的字节数组的常指针，可以被强制转为切片和 Null 终止指针。对字符串字面量解引用会将其转为数组。

由于 Zig 采用 UTF-8 编码，因此字符串字面量中的任何字节都会按照 UTF-8 含义进行编解码，编译器不会修改任何字节。如果要嵌入非 UTF-8 字节，可以使用 `\xNN` 表示法。

Unicode 字面量都拥有 `comptime_int` 类型，与整型字面量一致。所有转译序列在字符串字面量和 Unicode 字面量中均有效。

### 转义序列

| 转义序列     | 名称               |
| ------------ | ------------------ |
| `\n`         | Newline            |
| `\r`         | Carriage Return    |
| `\t`         | Tab                |
| `\\`         | Backslash          |
| `\'`         | 单引号             |
| `\"`         | 双引号             | 
| `\xNN`       | 16 进制字节值      |
| `\u{NNNNNN}` | 16 进制 Unicode 值 |

需要注意的是 Unicode 值最大为 `\0x10ffff`。

### 多行字符串

多行字符串没有转义序列并且可以跨越多行。多行字符串在每一行都需要以 `\\` 开头，除了最后一行外，每一行的行尾换行符也会被包含在字符串字面量中。

```zig file:multiline_string_literals.zig
const hello_world_in_c =
  \\#include <stdio.h>
  \\
  \\int main(int argc, char **argv) {
  \\  printf("hello world\n");
  \\  return 0;
  \\}
;
```

## 赋值

使用 `=` 将一个值赋给一个标志符。

可以用 `const` 关键字来修饰该标志符不可变，这仅适用于该标志符能够立即寻址到的所有字节。

```zig file:constant_identifier_cannot_change.zig
const x = 1234;

fn foo() void {
  // It works at file scope as well as inside functions.
  const y = 5678;

  // Once assigned, an identifier cannot be changed.
  y += 1;
}

pub fn main() void {
  foo();
}
```

```bash title:Shell
$ zig build-exe constant_identifier_cannot_change.zig
constant_identifier_cannot_change.zig:8:7: error: cannot assign to constant
    y += 1;
    ~~^~~~
```

对于能够修改值的变量，需要用 `var` 关键字修饰：

```zig file:mutable_var.zig
const print = @import("std").debug.print;

pub fn main() void {
  var y: i32 = 5678;
  y += 1;
  print("{d}", .{y});
}
```

```bash title:Shell
$ zig build-exe mutable_var.zig
$ ./mutable_var
5679
```

变量必须被初始化：

```zig title:var_must_be_initialized.zig
pub fn main() void {
  var x: i32;
  x = 1;
}
```

```bash title:Shell
$ zig build-exe var_must_be_initialized.zig
var_must_be_initialized.zig:2:5: error: variables must be initialized
    var x: i32;
    ^~~~~~~~~~
```

### undefined

可以使用 `undefined` 关键字使变量保持未初始化状态：

```zig file:assign_undefined.zig
pub fn main() void {
  var x: i32 = undefined;
  x = 1;
}
```

`undefined` 可以被强制转为任何类型，一旦发生转换，就不再能检测到该值是否为 `undefined` 了。

在 Debug 模式下，Zig 会将 `0xaa` 写入到未定义的内存，该行为仅供调试使用，并非语言语义。

---

# Zig 测试

在 `test` 声明中的代码可以确保行为满足预期：

```zig file:testing_introduction.zig
const std = @import("std");

test "expect addOne adds one to 41" {
  // The Standard Library contains useful functions to help create tests.
  // `expect` is a function that verifies its argument is true. It will
  // return an error if its argument is false to indicate a failure.
  // `try` is used to return an error to the test runner to notify it
  // that the test failed.
  try std.testing.expect(addOne(41) == 42);
}

test addOne {
  // A test name can also be written using an identifier.
  try std.testing.expect(addOne(41) == 42);
}

fn addOne(number: i32)  i32 {
  return number + 1;
}
```

`zig test` 是一个创建并运行测试构建的工具。默认情况下，它使用 Zig 标准库提供的 *default test runner* 作为 `main` 入口点来构建并运行可执行程序。*default test runner* 会将测试结果打印到标准错误流：

```bash title:Shell
$ zig test testing_introduction.zig
1/2 test.expect addOne adds one to 41... OK
2/2 decltest.addOne... OK
All 2 tests passed.
```

## 测试声明

Zig 测试使用 `test` 关键字进行声明，后跟可选的字符串字面量或者标志符作为测试名，最后是合法的 Zig 代码块。

按照惯例，未命名的测试只用于运行其他测试。

测试声明与函数类似：它们都具有返回类型和代码块。`test` 的返回类型是隐式的，为 `anyerror!void` 的 `Error Union Type`，并且该返回类型不能被更改。如果 Zig 源文件没有使用 `zig test` 工具进行构建，那么测试声明会被忽略。

测试声明可以写在被测试代码相同的文件中，也可以写入单独的源文件中。由于测试声明是顶级声明，因此它们的顺序无关紧要，可以写在被测试代码之前或者之后。

### 文档测试

使用标志符命名的测试声明是文档测试。该标志符必须要引用相同作用域里的另一个声明。文档测试与文档注释一样，是作为关联的声明的文档，并且会出现在生成的文档中。
