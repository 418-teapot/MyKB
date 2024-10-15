---
date: 2024-10-13
style: idea
tags:
  - 编译
  - MLIR
---

# 正文

## 背景

MLIR 中用于实现算子拆分与融合的接口是 `TilingInterface`，主要作用在 Linalg Dialect 上，Linalg Dialect 是 MLIR 的重要方言，承担了从描述 tensor 上的逻辑计算到描述 memref 上的硬件计算的转换。

Linalg op 即可以接受 tensor 又可以接受 memref。总体上有两类 Linalg op：结构化的和非结构化的。

非结构化的 op 只有 `linalg.index`、`linalg.yield` 等少数几个，用于辅助操作。

结构化的 op 包括 `linalg.generic`、`linalg.map`、`linalg.reduce`、`linalg.transpose`、`linalg.broadcast`、`linalg.matmul`、`linalg.conv` 等。其中 `linalg.generic` 是最核心的 op；除 `map, reduce, transpose, broadcast` 之外的其他 op 被称为 named ops，这些 op 只是某些特定的 `linalg.generic` 的语法糖。例如：

```llvm
%1 = linalg.add ins(%arg0, %arg1 : tensor<1024xf32>, tensor<1024xf32>) outs(%0 : tensor<1024xf32>) -> tensor<1024xf32>
```

使用 `--linalg-generalize-named-ops` pass 可以将 named ops 还原为 `linalg.generic`：

```llvm
#map = affine_map<(d0) -> (d0)>

%1 = linalg.generic {indexing_maps = [#map, #map, #map], iterator_types = ["parallel"]}
  ins(%arg0, %arg1 : tensor<1024xf32>, tensor<1024xf32>)
   outs(%0 : tensor<1024xf32>) {
   ^bb0(%in: f32, %in_0: f32, %out: f32):
     %2 = arith.addf %in, %in_0 : f32
     linalg.yield %2 : f32  
} -> tensor<1024xf32>
```

结构化的 Linalg op 都实现了 `LinalgOp Interface`，并具有统一的 IR 结构：

- 每个 op 本身都是完美嵌套循环的抽象，可以看作隐式的嵌套循环，每个循环都有显式定义的 iterator 类型（`parallel`、`reduction` 等）；
- 每个输入/输出操作数都有一个相应的访问映射（indexing map），这个映射描述了在隐式嵌套循环中如何访问该操作数的元素，循环的迭代空间完全由操作数来决定；
- 每个 op 的具体计算都由其 region 来定义，提供了极大的灵活性。

> [!info]
> 如果在嵌套循环中，所有操作都在最内层循环中，那么该嵌套循环被成为完美嵌套循环。
> 
> 完美嵌套循环对于循环优化非常重要，因为它支持一些循环优化技术，例如循环交换、循环拆分等。

如前所述，所有结构化的 Linalg op 都是完美嵌套循环的抽象，因此将 Linalg op 转换为循环是非常容易的，MLIR 官方提供了 `--convert-linalg-to-loops` 和 `--convert-linalg-to-parallel-loops` 等 pass，例如：

```llvm
scf.for %arg2 = %c0 to %c1024 step %c1 {
  %3 = memref.load %1[%arg2] : memref<1024xf32, strided<[?], offset: ?>>
  %4 = memref.load %0[%arg2] : memref<1024xf32, strided<[?], offset: ?>>
  %5 = arith.addf %3, %4 : f32
  memref.store %5, %alloc[%arg2] : memref<1024xf32>
}
```

## 循环优化

我们可以从循环的角度来观察 Linalg op 的拆分与融合。

### 循环拆分

以向量加法为例：$A = B + C$，其中 $A$、$B$、$C$ 均为长度为 $L$ 的向量，那么该向量加法可以表示为：

```cpp
for (int i = 0; i < L; ++i) {
  A[i] = B[i] + C[i];
}
```

这等价于 Linalg op 上向量的加法：

```llvm
%1 = linalg.add ins(%arg0, %arg1 : tensor<Lxf32>, tensor<Lxf32>) outs(%0 : tensor<Lxf32>) -> tensor<Lxf32>
```

该循环的迭代变量是 $i$，总共执行了 $L$ 次，如果我们对 $L$ 进行拆分：

```cpp
for (int i = 0; i < (L/K); ++i) {
  for (int j = 0; j < K; ++j) {
    A[i * K + j] = B[i * K + j] + C[i * K + j];
  }
}
```

其中最内层循环可以看成是长度为 $K$ 的 Linalg 上的向量加法：

```llvm
scf.for %arg2 = %c0 to L/K step %c1 {
  %slice0 = tensor.extract_slice %arg0[%arg2 * K] [K] ...
  %slice1 = tensor.extract_slice %arg1[%arg2 * K] [K] ...
  %1 = linalg.add ins(%slice0, %slice1 : tensor<Kxf32>, tensor<Kxf32>) outs(%tmp : tensor<Kxf32>) ...
  tensor.insert_slice %tmp into %0
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

### 其他优化手段

---

# 引用

- [如何评价MLIR项目中Linalg Dialect的设计思想？](https://www.zhihu.com/question/442964082)
- [MLIR Linalg Dialect 以及 Patterns](https://www.lei.chat/zh/posts/mlir-linalg-dialect-and-patterns/)
- [MLIR Linalg Op Fusion – Theory & Practice](https://llvm.org/devmtg/2024-04/slides/TechnicalTalks/Absar-MLIR-LinalgOpFusion.pdf)
- [MLIR: The case for a simplified polyhedral form](https://mlir.llvm.org/docs/Rationale/RationaleSimplifiedPolyhedralForm/)
- [A Primer on “Structured” Linalg Operations](https://mlir.llvm.org/docs/Tutorials/transform/Ch0/#)
