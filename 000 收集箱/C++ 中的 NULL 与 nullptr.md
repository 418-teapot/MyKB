---
style: manual
tags:
  - C
  - Cpp
  - 编程语言
---

# 简介

---

# 正文

C 语言中，使用 `NULL` 表示空指针，定义如下：

```c
#define NULL ((void*)0)
```

C++ 中，由于 `void*` 不能隐式转换成其他指针类型， `NULL` 通常定义如下：

```cpp
#ifdef __cplusplus
#define NULL 0
#else
#define NULL ((void*)0)
#endif
```

通常情况下，C++ 使用 `NULL` 是没有问题的，但是在以下情况：

函数原型：

```cpp
void foo(int *);
void foo(int);
```

调用：

```cpp
foo(NULL);
```

编译时报错，提示具有二义性错误。

C++ 11 中引入了 `nullptr` 作为空指针用于解决该问题。

需要注意的是，以下代码也是不允许的，同样会发生二义性错误：

```cpp
void foo(int *)
void foo(char *);

foo(nullptr);
```

这时应该对 `nullptr` 进行强制类型转换：

```cpp
foo(static_cast<char *>(nullptr));
```

---

# 引用
