---
type: snippet
lang: cpp
kind: util
tags:
  - llvm
  - debug
  - macro
---

# 正文

在 Release 构建中打印 `LLVM_DEBUG` 调试信息。

---

# 代码

```cpp
#undef LLVM_DEBUG
#define LLVM_DEBUG(x)                                                          \
  {                                                                            \
    x;                                                                         \
  }
#define dbgs errs
```
