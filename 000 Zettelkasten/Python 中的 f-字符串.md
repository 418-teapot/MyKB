---
style: manual
tags:
  - Python
  - 字符串
---

# 简介

f-string，也被称为格式化字符串常量（formatted string literals），是一种简便的字符串格式化方法。f-string 在形式上是以 `f` 或者 `F` 修饰符引领的字符串（`f'xxx'` 或 `F'xxx'`），以大括号 `{}` 标明被替换的字段。

> [!info]
> While other string literals always have a constant value, formatted strings are really expressions evaluated at run time.
> 
> 与具有定值的其他字符串字面量不同，格式化字符串实际上是运行时求值的表达式。

---

# 正文

## 简单使用

f- 字符串用大括号 `{}` 表示被替换字段，其中直接填入替换内容：

```python
>>> name = 'Eric'
>>> f'Hello, my name is {name}'
'Hello, my name is Eric'

>>> number = 7
>>> f'My lucky number is {number}'
'My lucky number is 7'

>>> price = 19.99
>>> f'The price of this book is {price}'
'The price of this book is 19.99'
```

## 表达式求值与函数调用

f- 字符串的大括号 `{}` 可以填入表达式或函数调用，Python 会求出其结果并填入字符串内：

```python
>>> f'A total number of {24 * 8 + 4}'
'A total number of 196'

>>> f'Complex number {(2 + 2j) / (2 - 3j)}'
'Complex number (-0.15384615384615388+0.7692307692307692j)'

>>> name = 'ERIC'
>>> f'My name is {name.lower()}'
'My name is eric'

>>> import math
>>> f'The answer is {math.log(math.pi)}'
'The answer is 1.1447298858494002'
```

## 引号、大括号与反斜杠

f- 字符串大括号内所用的引号不能和大括号外的引号定界符冲突，可根据情况灵活切换 `'` 和 `"`：

```python
>>> f'I am {"Eric"}'
'I am Eric'

>>> f'I am {'Eric'}'
  File "<stdin>", line 1
    f'I am {'Eric'}'
             ^^^^
SyntaxError: f-string: expecting '}'
```

若 `'` 和 `"` 不足以满足要求，还可以使用 `'''` 和 `"""`：

```python
>>> f"""He said {"I'm Eric"}"""
"He said I'm Eric"

>>> f'''He said {"I'm Eric"}'''
"He said I'm Eric"
```

大括号外的引号还可以使用 `\` 转义，但大括号内不能使用 `\` 转义：

```python
>>> f'''He\'ll say {"I'm Eric"}'''
"He'll say I'm Eric"

>>> f'''He'll say {"I\'m Eric"}'''
 File "<stdin>", line 1  
   f'''He'll say {"I\'m Eric"}'''  
                                 ^  
SyntaxError: f-string expression part cannot include a backslash
```

大括号内不允许出现 `\` 字符，如果确实需要，则应首先将包含 `\` 字符的内容赋予一个变量，再使用该变量：

```python
>>> f"newline: {ord('\n')}"
 File "<stdin>", line 1  
   f"newline: {ord('\n')}"  
                          ^  
SyntaxError: f-string expression part cannot include a backslash

>>> newline = ord('\n')
>>> f'newline: {newline}'
'newline: 10'
```

f- 字符串大括号外如果需要显示大括号，需要输入连续两个大括号 `{{` 和 `}}`：

```python
>>> f'5 {"{stars}"}'
'5 {stars}'

>>> f'{{5}} {"stars"}'
'{5} stars'
```

## 多行字符串

f- 字符串可以表示多行字符串：

```python
>>> name = 'Eric'
>>> age = 27
>>> f"""Hello!
...     I'm {name}.
...     I'm {age}."""
"Hello!\n   I'm Eric.\n   I'm 27."
```

## 自定义格式

f- 字符串采用 `{content:format}` 设置字符串格式，其中 `content` 是填入字符串的内容，可以是变量、表达式或函数，`format` 是格式描述符。采用默认格式时不必指定 `{:format}`。

### 对齐相关格式描述符

| 格式描述符 | 含义与作用                   |
| ---------- | ---------------------------- |
| `<`        | 左对齐（字符串默认对齐方式） |
| `>`        | 右对齐（数值默认对齐方式）   |
| `^`        | 居中                         | 

### 数字符号相关格式描述符

| 格式描述符  | 含义与作用                                      |
| ----------- | ----------------------------------------------- |
| `+`         | 负数前加负号（`-`），正数前加正号（`+`）        |
| `-`         | 负数前加负号（`-`），正数前不加任何符号（默认） |
| ` `（空格） | 负数前加负号（`-`），正数前加一个空格           | 

### 数字显示方式相关格式描述符

| 格式描述符 | 含义与作用       |
| ---------- | ---------------- |
| `#`        | 切换数字显示方式 | 

该表述符近适用于数值类型，对不同数值类型的作用效果不同，如下：

| 数值类型                 | 不加 `#`（默认） | 加 `#`        | 区别              |
| ------------------------ | ---------------- | ------------- | ----------------- |
| 二进制整数               | `'1111011`       | `'0b1111011'` | 开头是否显示 `0b` |
| 八进制整数               | `'173'`          | `'0o173'`     | 开头是否显示 `0o` |
| 十进制整数               | `'123'`          | `'123'`       | 无区别            |
| 十六进制整数（小写字母） | `'7b'`           | `'0x7b'`      | 开头是否显示 `0x` |
| 十六进制整数（大写字母） | `'7B'`           | `'0X7B'`      | 开头是否显示 `0X` | 

### 宽度与精度相关格式描述符

| 格式描述符        | 含义与作用                                                |
| ----------------- | --------------------------------------------------------- |
| `width`           | 整数 `width` 指定宽度                                     |
| `0width`          | 整数 `width` 指定宽度，开头的 `0` 指定高位用 `0` 补足宽度 |
| `width.precision` | 整数 `width` 指定宽度，整数 `precision` 指定显示精度      | 

### 千位分隔符相关格式描述符

| 格式描述符 | 含义与作用              |
| ---------- | ----------------------- |
| `,`        | 使用 `,` 作为千位分隔符 |
| `_`        | 使用 `_` 作为千位分隔符 | 

### 格式类型相关格式描述符

| 格式描述符 | 含义与作用                                           | 适用变量类型                           |
| ---------- | ---------------------------------------------------- | -------------------------------------- |
| `s`        | 普通字符串格式                                       | 字符串                                 |
| `b`        | 二进制整数格式                                       | 整数                                   |
| `c`        | 字符格式，按 unicode 编码将整数转换为对应字符        | 整数                                   |
| `d`        | 十进制整数格式                                       | 整数                                   |
| `o`        | 八进制整数格式                                       | 整数                                   |
| `x`        | 十六进制整数格式（小写字母）                         | 整数                                   |
| `X`        | 十六进制整数格式（大写字母）                         | 整数                                   |
| `e`        | 科学计数格式，以 `e` 表示                            | 浮点数、复数、整数（自动转换为浮点数） |
| `E`        | 科学计数格式，以 `E` 表示                            | 浮点数、复数、整数（自动转换为浮点数） |
| `f`        | 定点数格式，默认精度（`precision`）为 6              | 浮点数、复数、整数（自动转换为浮点数） |
| `F`        | 与 `f` 等价，但将 `nan` 和 `inf` 换为 `NAN` 和 `INF` | 浮点数、复数、整数（自动转换为浮点数） |
| `g`        | 通用格式，小数使用 `f`，大数使用 `e`                 | 浮点数、复数、整数（自动转换为浮点数） |
| `G`        | 通用格式，小数使用 `F`，大数使用 `E`                 | 浮点数、复数、整数（自动转换为浮点数） |
| `%`        | 百分比格式，按 `f` 格式排版，并加上 `%` 后缀         | 浮点数、整数（自动转换为浮点数）       |

---

# 引用

- [f-strings](https://docs.python.org/3/reference/lexical_analysis.html#formatted-string-literals)
