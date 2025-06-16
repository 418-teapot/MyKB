---
style: manual
tags:
  - 工具
  - 压缩
---

# 简介

---

# 正文

## 示例

```bash
tar -cf archive.tar foo bar # 将文件 foo 与 bar 打包为 archive.tar
tar -tvf archive.tar # 列出 archive.tar 中的所有文件
tar -xf archive.tar # 解出 archive.tar

tar -czvf archive.tar.gz foo bar # 将文件 foo 与 bar 打包并压缩
tar -xzvf archive.tar.gz # 解压并解出 archive.tar.gz
```

## 常用参数选项

```bash
-c, --create # 创建新的归档文件
-t, --list # 列出归档的内容
-x, --extract, --get # 从归档中解出文件
-C, --directory=DIR # 解出文件至指定的目录
-f, --file # 要操作的文件名
-x, --extract # 解压文件
-z, --gzip, --gunzip, --ungzip # 通过 gzip 过滤归档
-v, --verbose # 详细显示处理过程
-j, --bzip2 # 通过 bzip2 过滤归档
-J, --xz # 通过 xz 过滤归档
```

---

# 引用
