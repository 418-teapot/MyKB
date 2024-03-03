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

## 测试失败

当测试返回 error 时，该测试被视为失败，错误报告会输出到标准错误流。

```zig file:testing_failure.zig
const std = @import("std");

test "expect this to fail" {
  try std.testing.expect(false);
}

test "expect this to succeed" {
  try std.testing.expect(true);
}
```

```bash title:Shell
$ zig test testing_failure.zig
1/2 test.expect this to fail... FAIL (TestUnexpectedResult)
...
    try std.testing.expect(false);
    ^
2/2 test.expect this to succeed... OK
1 passed; 0 skipped; 1 failed.
```

## 跳过测试

跳过测试的一种方法是使用 `zig test --test-filter [text]` 命令，这只会构建指定名称的测试，需要注意的是，这不会过滤掉未命名的测试。

当一个 `test` 返回 `error.SkipZigTest` 错误时，*default test runner* 会跳过该测试，所有测试运行结束后，会报告跳过的测试总数。

```zig file:testing_skip.zig
test "this will be skipped" {
  return error.SkipZigTest;
}
```

```bash title:Shell
$ zig test testing_skip.zig
1/1 test.this will be skipped... SKIP
0 passed; 1 skipped; 0 failed.
```

## 报告内存泄漏

当代码使用 Zig 标准库提供的 `std.testing.allocator` 申请内存时，*default test runner* 会报告其发现的内存泄漏。

```zig file:testing_detect_leak.zig
const std = @import("std");

test "detect leak" {
  var list = std.ArrayList(u21).init(std.testing.allocator);
  // missing `defer list.deinit();`
  try list.append('☔');

  try std.testing.expect(list.items.len == 1);
}
```

```bash title:Shell
$ zig test testing_detect_leak.zig
1/1 test.detect leak... OK
[gpa] (err): memory address 0x7f736a84a000 leaked:
...
All 1 tests passed.
1 errors were logged.
1 tests leaked memory.
```

## 检测测试构建

可以使用编译期变量 `@import("builtin").is_test` 来检测是否为测试。

```zig file:testing_detect_test.zig
const std = @import("std");
const builtin = @import("builtin");
const expect = std.testing.expect;

test "builtin.is_test" {
  try expect(isATest());
}

fn isATest() bool {
  return builtin.is_test;
}
```

```bash title:Shell
$ zig test testing_detect_test.zig
1/1 test.builtin.is_test... OK
All 1 tests passed.
```

## 测试输出与日志

*default test runner* 和 Zig 标准库的 `testing` 命名空间会将消息输出到标准错误流。

## `testing` 命名空间

Zig 标准库的 `testing` 命名空间中包含许多有用的函数，例如：

```zig file:testing_namespace.zig
const std = @import("std");

test "expectEqual demo" {
  const expected: i32 = 42;
  const actual = 42;

  // The first argument to `expectEqual` is the known, expected, result.
  // The second argument is the result of some expression.
  // The actual's type is casted to the type of expected.
  try std.testing.expectEqual(expected, actaul);
}

test "expectError demo" {
  const expected_error = error.DemoError;
  const actual_error_union: anyerror!void = error.DemoError;

  // `expectError` will fail when the actual error is different than
  // the expected error.
  try.std.testing.expectError(expected_error, actual_error_union);
}
```

```bash title:Shell
$ zig test testing_namespace.zig
1/2 test.expectEqual demo... OK
2/2 test.expectError demo... OK
All 2 tests passed.
```

## 测试工具

`zig test` 工具有一些影响编译的命令行参数，可以使用 `zig test --help` 获取完整列表。

---

# 变量

变量是用于存储数据的内存区域。

声明变量时通常最好使用 `const` 而不是 `var`，这可以减少人类和计算机的心智负担，并创造更多的优化机会。

`extern` 关键字和 `@extern` 内建函数可用于链接从别的目标文件中导出的变量，`export` 关键字和 `@export` 内建函数可以将变量在链接时导出供其他目标文件使用。在这两种情况下，变量的类型必须与 C ABI 兼容。

## 标志符

变量标志符不允许遮蔽（shadow）外部作用域的标志符。

标志符必须以字母或下划线开头，后面可以跟任意数量的字母数字或下划线。不得与关键字重名。

如果需要的名称不符合这些要求（例如与外部库链接），则需要使用 `@""` 语法。

```zig file:identifiers.zig
const @"identifier with space in it" = 0xff;
const @"1SmallStep4Man" = 112358;

const c = @import("std").c;
pub extern "c" fn @"error"() void;
pub extern "c" fn @"fstat$INODE64"(fd: c.fd_t, buf: *c.Stat) c_int;

const Color = enum {
  red,
  @"really red",
};
const color: Color = .@"really red";
```

## 容器级变量

Zig 中的容器是指任何可以充当命名空间的语法结构，用于保存变量和函数声明。容器也是可以被实例化的类型定义。`struct`、`enum`、`union`、`opaque`，甚至 Zig 源文件本身都是容器。

尽管容器（Zig 源文件除外）使用大括号来包围其定义，但不应该将它们与块或函数混淆，容器不能包含任何语句。

容器级变量就是定义在容器中的变量。容器级变量具有：

- 静态生命周期（static lifetime）：生命周期与容器相同，被所有容器的实例共享。
- 顺序独立性（order-independent）：声明顺序对其行为没有影响。无论它们在容器内部的声明顺序如何，都不会影响它们的初始化或访问顺序。
- 惰性分析（lazily analyzed）：编译器只有在变量被实际使用时才会对其进行分析，而不会提前分析所有变量。

容器级变量的初始化值在声明时会被隐式地标记为 `comptime`。如果容器级变量被 `const` 修饰，那么该值为编译时已知的，否则就为运行时已知的。

```zig file:test_namespaced_container_level_varibal.zig
const std = @import("std");
const expect = std.testing.expect;

test "namespaced container level variable" {
  try expect(foo() == 1235);
  try expect(foo() == 1236);
}

const S = struct {
  var x: i32 = 1234;
};

fn foo() i32 {
  S.x += 1;
  return S.x;
}
```

```bash title:Shell
$ zig test test_namespaced_container_level_variable.zig
1/1 test.namespaced container level variable... OK
All 1 tests passed.
```

## 静态局部变量

通过在函数内部使用容器级变量，还可以使局部变量具有静态声明周期：

```zig file:test_static_local_variable.zig
const std = @import("std");
const expect = std.testing.expect;

test "static local variable" {
  try expect(foo() == 1235);
  try expect(foo() == 1236);
}

fn foo() i32 {
  const S = struct {
    var x: i32 = 1234;
  };
  S.x += 1;
  return S.x;
}
```

```bash title:Shell
$ zig test test_static_local_variable.zig
1/1 test.static local variable... OK
All 1 tests passed.
```

## 线程局部变量

可以使用 `threadlocal` 关键字将变量指定为线程局部变量，使得每个线程都可以使用该变量的单独实例：

```zig file:test_thread_local_variables.zig
const std = @import("std");
const assert = std.debug.assert;

threadlocal var x: i32 = 1234;

test "thread local storage" {
  const thread1 = try std.Thread.spawn(.{}, testTls, .{});
  const thread2 = try std.Thread.spawn(.{}, testTls, .{});
  testTls();
  thread1.join();
  thread2.join();
}

fn testTls() void {
  assert(x == 1234);
  x += 1;
  assert(x == 1235);
}
```

```bash title:Shell
$ zig test test_thread_local_variables.zig
1/1 test_thread_local_variables.test.thread local storage... OK
All 1 tests passed.
```

对于单线程的构建来说，所有线程局部变量都会被视为常规的容器极变量。

## 局部变量

局部变量出现在函数、`comptime` 块和 `@cImport` 块中。

当局部变量被 `const` 关键字修饰时，说明该变量的值在初始化后不会发生任何改变。如果 `const` 变量的初始化值是编译期已知的，那么该变量也是编译期已知的。

局部变量可以被 `comptime` 关键字修饰。这说明该变量的值是编译期已知的，并且该变量的所有读写操作都在程序的语义分析期间发生，而不是在运行时发生。在 `comptime` 表达式中声明的所有变量都是隐式的 `comptime` 变量。

```zig file:test_comptime_variables.zig
const std = @import("std");
const expect = std.testing.expect;

test "comptime vars" {
  var x: i32 = 1;
  comptime var y: i32 = 1;

  x += 1;
  y += 1;

  try expect(x == 2);
  try expect(y == 2);

  if (y != 2) {
    // This compile error never triggers because y is a comptime
    // variable, and so `y != 2` is a comptime value, and this if is
    // statically evaluated.
    @compileError("wrong y value");
  }
}
```

```bash title:Shell
$ zig test test_comptime_variables.zig
1/1 test_comptime_variables.test.comptime vars... OK
All 1 tests passed.
```

---

# 整数

## 整数字面量

```zig file:integer_literals.zig
const decimal_int = 98222;
const hex_int = 0xff;
const another_hex_int = 0xFF;
const octal_int = 0o755;
const binary_int = 0b11110000;

// underscores may be placed between two digits as a visual separator
const one_billion = 1_000_000_000;
const binary_mask = 0b1_1111_1111;
const permissions = 0o7_5_5;
const big_address = 0xFF80_0000_0000_0000;
```

## 运行时整数值

整数字面量没有大小限制，如果发生任何未定义行为，编译器会进行捕获。

然而，一旦整数值不再是编译期已知的，那么它就必须具有一个确定的大小，并且它还容易受到未定义行为的影响。

```zig file:runtime_vs_compime.zig
fn divide(a: i32, b: i32) i32 {
  return a / b;
}
```

在这个函数中，变量 `a` 和 `b` 只有在运行时才已知，因此该除法操作对于*整型溢出*和*除零*是脆弱的。

`+` 和 `-` 等运算符在*整型溢出*时会发生未定义行为，为了避免未定义行为，Zig 提供了额外的运算符，`+%` 和 `-%` 执行回绕（wrapping）运算，`+|` 和 `-|` 执行饱和（saturating）运算。

Zig 支持任意位宽的整数，通过使用 `i` 或 `u` 标识符后跟数字来使用。对于有符号整数，Zig 使用二进制补码来表示。

---

# 浮点数

## 浮点数字面量

浮点数字面量的类型为 `comptime_float`，与最大的浮点类型（`f128`）具有相同的精度与运算。

浮点数字面量可以强制转换为任何浮点类型，并且在没有小数部分时可以强制转换为任何整数类型。

```zig file:float_literals.zig
const floating_point = 123.0E+77;
const another_float = 123.0;
const yet_another = 123.0e+77;

const hex_floating_point = 0x103.70p-5;
const another_hex_float = 0x103.70;
const yet_another_hex_float = 0x103.70P-5;

// underscores may be placed between two digits as a visual separator
const lightspeed = 299_792_458.000_000;
const nanosecond = 0.000_000_001;
const more_hex = 0x1234_5678.9ABC_CDEFp-10;
```

浮点数字面量不能表示 NAN、正无穷和负无穷。对于这些特殊值，必须使用标准库：

```zig file:float_special_values.zig
const std = @import("std");

const inf = std.math.inf(f32);
const negative_inf = -std.math.inf(f64);
const nan = std.math.nan(f128);
```

## 浮点运算

默认情况下，浮点运算使用 `Strict` 模式，但可以在某个块内切换到 `Optimized` 模式：

```zig file:float_mode_obj.zig
const std = @import("std");
const big = @as(f64, 1 << 40);

export fn foo_strict(x: f64) f64 {
  return x + big - big;
}

export fn foo_optimized(x: f64) f64 {
  @setFloatMode(.Optimized);
  return x + big - big;
}
```

```bash title:Shell
$ zig build-obj float_mode_obj.zig -O ReleaseFast
```

对于该测试，我们必须将代码分成两个目标文件，否则优化器会在编译期使用 `Strict` 模式计算出所有值。

```zig file:float_mode_exe.zig
const print = @import("std").debug.print;

extern fn foo_strict(x: f64) f64;
extern fn foo_optimized(x: f64) f64;

pub fn main() void {
  const x = 0.001;
  print("optimized = {}\n", .{foo_optimized(x)});
  print("strict = {}\n", .{foo_strict(x)});
}
```

```bash title:Shell
$ zig build-exe float_mode_exe.zig float_mode_obj.o
$ ./float_mode_exe
optimized = 9.765625e-04
strict = 9.765625e-04
```

---

# 运算符

Zig 中不存在运算符重载。

## 运算符表

$$
\begin{array}{llll}
  \hline
  语法 & 关联类型 & 描述 & 示例 \\
  \hline
  \texttt{a + b} & \text{· 整型} & \text{Addition} & \texttt{2 + 5 == 7} \\
  \texttt{a += b} & \text{· 浮点型} & \text{· 在整型下可能发生溢出} & \\
  & & \text{· 调用操作数的 Peer Type Resolution} & \\
  \hline
  \texttt{a +\% b} & \text{· 整型} & \text{Wrapping Addition} & \texttt{@as(u32, std.math.maxInt(u32)) +\% 1 == 0} \\
  \texttt{a +\% = b} & & \text{· 保证具有二进制补码回绕行为} & \\
  & & \text{· 调用操作数的 Peer Type Resolution} & \\
  \hline
  \texttt{a +| b} & \text{· 整型} & \text{Saturating Addition} & \texttt{@as(u32, std.math.maxInt(u32)) +| 1 ==} \\
  \texttt{a +| = b} & & \text{· 调用操作数的 Peer Type Resolution} & \texttt{@as(u32, std.math.maxInt(u32))} \\
  \hline
  \texttt{a - b} & \text{· 整型} & \text{Subtraction} & \texttt{2 - 5 == -3} \\
  \texttt{a -= b} & \text{· 浮点型} & \text{· 在整型下可能发生溢出} & \\
  & & \text{· 调用操作数的 Peer Type Resolution} & \\
  \hline
  \texttt{a -\% b} & \text{· 整型} & \text{Wrapping Subration} & \texttt{@as(u32, 0) -\% 1 == std.math.maxInt(u32)} \\
  \texttt{a -\% = b} & & \text{· 保证具有二进制补码回绕行为} & \\
  & & \text{· 调用操作数的 Peer Type Resolution} & \\
  \hline
  \texttt{a -| b} & \text{· 整型} & \text{Saturating Subration} & \texttt{@as(u32, 0) -| 1 == 0} \\
  \texttt{a -| = b} & & \text{· 调用操作数的 Peer Type Resolution} & \\
  \hline
  \texttt{-a} & \text{· 整型} & \text{Negation} & \texttt{-1 == 0 - 1} \\
  & \text{· 浮点型} & \text{· 在整型下可能发生溢出} & \\
  \hline
  \texttt{-\%a} & \text{· 整型} & \text{Wrapping Negation} & \texttt{-\%@as(i32, std.math.minInt(i32)) ==} \\
  & & \text{· 保证具有二进制补码回绕行为} & \texttt{@as(i32. std.math.minInt(i32))} \\
  \hline
  \texttt{a * b} & \text{· 整型} & \text{Multiplication} & \texttt{2 * 5 == 10} \\
  \texttt{a *= b} & \text{· 浮点型} & \text{· 在整型下可能发生溢出} & \\
  & & \text{· 调用操作数的 Peer Type Resolution} & \\
  \hline
  \texttt{a *\% b} & \text{· 整型} & \text{Wrapping Multiplication} & \texttt{@as(u8, 200) *\% 2 == 144} \\
  \texttt{a *\% = b} & & \text{· 保证具有二进制补码回绕行为} & \\
  & & \text{· 调用操作数的 Peer Type Resolution} & \\
  \hline
  \texttt{a *| b} & \text{· 整型} & \text{Saturating Multiplication} & \texttt{@as(u8, 200) *| 2 == 255} \\
  \texttt{a +| = b} & & \text{· 调用操作数的 Peer Type Resolution} & \\
  \hline
  \texttt{a / b} & \text{· 整型} & \text{Division} & \texttt{10 / 5 == 2} \\
  \texttt{a /= b} & \text{· 浮点型} & \text{· 在整型下可能发生溢出} & \\
  & & \text{· 在整型下可能发生除 0 异常} & \\
  & & \text{· 在浮点型的 Optimized 模式下可能发生除 0 异常} & \\
  & & \text{· 有符号整型必须编译期已知且为正数} & \\
  & & \text{· 调用操作数的 Peer Type Resolution} & \\
  \hline
  \texttt{a \% b} & \text{· 整型} & \text{Remainder Division} & \texttt{10 \% 3 == 1} \\
  \texttt{a \%= b} & \text{· 浮点型} & \text{· 在整型下可能发生溢出} & \\
  & & \text{· 在整型下可能发生除 0 异常} & \\
  & & \text{· 在浮点型的 Optimized 模式下可能发生除 0 异常} & \\
  & & \text{· 有符号整型和浮点型必须编译期已知且为正数} & \\
  & & \text{· 调用操作数的 Peer Type Resolution} & \\
  \hline
  \texttt{a << b} & \text{· 整型} & \text{Bit Shift Left} & \texttt{1 << 8 == 256} \\
  \texttt{a <<= b} & & \text{· \texttt{b} 必须为编译期已知或与 \texttt{a} 的位宽的 log2 对数具} \\
  & & \text{有相同的类型} & \\
  \hline
  \texttt{a <<| b} & \text{· 整型} & \text{Saturating Bit Shift Left} & \texttt{@as(u8, 1) <<| 8 == 255} \\
  \texttt{a <<|= b} & & & \\
  \hline
  \texttt{a >> b} & \text{· 整型} & \text{Bit Shift Right} & \texttt{10 >> 1 == 5} \\
  \texttt{a >>= b} & & \text{· \texttt{b} 必须为编译期已知或与 \texttt{a} 的位宽的 log2 对数具} \\
  & & \text{有相同的类型} & \\
  \hline
  \texttt{a \& b} & \text{· 整型} & \text{Bitwise AND} & \texttt{0b011 \& 0b101 == 0b001} \\
  \texttt{a \&= b} & & \text{· 调用操作数的 Peer Type Resolution} & \\
  \hline
  \texttt{a | b} & \text{· 整型} & \text{Bitwise OR} & \texttt{0b010 \& 0b100 == 0b110} \\
  \texttt{a |= b} & & \text{· 调用操作数的 Peer Type Resolution} & \\
  \hline
  \texttt{a \^{} b} & \text{· 整型} & \text{Bitwise XOR} & \texttt{0b011 \^{} 0b101 == 0b110} \\
  \texttt{a \^{}\,= b} & & \text{· 调用操作数的 Peer Type Resolution} & \\
  \hline
  \texttt{\~{} b} & \text{· 整型} & \text{Bitwise NOT} & \texttt{\~{}\,@as(u8, 0b10101111) == 0b01010000} \\
\end{array}
$$
