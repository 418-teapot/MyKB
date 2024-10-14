---
date: 2024-10-13
style: idea
tags:
  - 编译
  - MLIR
---

# 正文

## 背景

MLIR 中 Linalg Op 是多层完美嵌套循环的抽象，在了解 op 的拆分与融合之前，有必要先了解循环的拆分与融合。

### 循环拆分

以向量加法为例：$A = B + C$，其中 $A$、$B$、$C$ 均为长度为 $L$ 的向量，那么该向量加法可以表示为：

```cpp
for (int i = 0; i < L; ++i) {
  A[i] = B[i] + C[i];
}
```

该循环的迭代变量是 $i$，总共执行了 $L$ 次，我们可以对 $L$ 进行拆分：

```cpp
for (int i = 0; i < (L/K); ++i) {
  A[i * K] = B[i * K] + C[i * K]; // 长度为 K 的向量加法
}
```

即：

```cpp
for (int i = 0; i < (L/K); ++i) {
  for (int j = 0; j < K; ++j) {
    A[i * K + j] = B[i * K + j] + C[i * K + j];
  }
}
```

### 循环融合

我们有向量加法 $A = B + C$ 和向量乘法 $D = A * E$，其中 $A$、$B$、$C$、$D$、$E$ 均为长度为 $L$ 的向量，我们在数学层面上可以很容易地写出这等价于 $D = (B + C) * E$，对应到循环上就是：

```cpp
for (int i = 0; i < L; ++i) {
  A[i] = B[i] + C[i];
}

for (int i = 0; i < L; ++i) {
  D[i] = A[i] * E[i];
}
```

到：

```cpp
for (int i = 0; i < L; ++i) {
  A[i] = B[i] + C[i];
  D[i] = A[i] * E[i];
}
```

再到：

```cpp
for (int i = 0; i < L; ++i) {
  D[i] = (B[i] + C[i]) * E[i];
}
```

### 其他循环优化

---

# 引用

- [如何评价MLIR项目中Linalg Dialect的设计思想？](https://www.zhihu.com/question/442964082)
- [MLIR Linalg Dialect 以及 Patterns](https://www.lei.chat/zh/posts/mlir-linalg-dialect-and-patterns/)
- [MLIR Linalg Op Fusion – Theory & Practice](https://llvm.org/devmtg/2024-04/slides/TechnicalTalks/Absar-MLIR-LinalgOpFusion.pdf)
- [MLIR: The case for a simplified polyhedral form](https://mlir.llvm.org/docs/Rationale/RationaleSimplifiedPolyhedralForm/)
