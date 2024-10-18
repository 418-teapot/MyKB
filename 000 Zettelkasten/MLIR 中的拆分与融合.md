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

## 循环拆分/算子拆分

### parallel 轴的拆分

以向量加法为例：$A = B + C$，其中 $A$、$B$、$C$ 均为长度为 1024 的向量，那么该向量加法可以表示为：

```cpp
for (int i = 0; i < 1024; ++i) {
  A[i] = B[i] + C[i];
}
```

这等价于 Linalg op 上向量的加法：

```llvm
%1 = linalg.add ins(%arg0, %arg1 : tensor<1024xf32>, tensor<1024xf32>) outs(%0 : tensor<1024xf32>) -> tensor<1024xf32>
```

该循环的迭代变量是 $i$，总共执行了 1024 次，如果我们对这个向量在长度拆分 4 次：

```cpp
for (int i = 0; i < 4; ++i) {
  for (int j = 0; j < 256; ++j) {
    A[i * 256 + j] = B[i * 256 + j] + C[i * 256 + j];
  }
}
```

其中最内层循环可以看成是长度为 256 的向量加法，但是这样面临着一个问题：上述的拆分都将 `tensor` 考虑为了一个数组，这样的考虑对 `memref` 是可行的，因为 `memref` 允许对部分分块的读写；但对 `tensor` 来说分块语义就不再明确了，因为 `tensor` 在语义上是不可分的整体，是不支持部分读写的，哪怕是一个元素的改动也会产生一个全新的和原 `tensor` 具有相同 shape 的 `tensor`。为了解决这一问题，社区引入了 `tensor.extract_slice` 和 `tensor.insert_slice` 算子。

有了这些算子，我们就可以将上述对循环的拆分映射到对 Linalg op 的拆分，社区提供了 `transform.structured.tile_using_forall` 和 `transform.structured.tile_using_for` 来对 op 进行拆分：

```llvm
func.func @add(%arg0 : tensor<1024xf32>, %arg1 : tensor<1024xf32>) -> tensor<1024xf32> {
 %0 = tensor.empty() : tensor<1024xf32>
 %1 = linalg.add ins(%arg0, %arg1 : tensor<1024xf32>, tensor<1024xf32>) outs(%0 : tensor<1024xf32>) -> tensor<1024xf32>
 return %1 : tensor<1024xf32>
}

transform.with_pdl_patterns {
^bb0(%arg0: !pdl.operation):
 transform.sequence %arg0 : !pdl.operation failures(propagate) {
   ^bb0(%arg1: !pdl.operation):
     %func = transform.structured.match ops{["func.func"]} in %arg1 : (!pdl.operation) -> !pdl.operation
     %add = transform.structured.match ops{["linalg.add"]} in %func : (!pdl.operation) -> !pdl.operation
     %forall_op, %tiled_op = transform.structured.tile_using_forall %add num_threads [4] : (!pdl.operation) -> (!pdl.operation, !pdl.operation)
 }
}
```

`transform.structured.tile_using_forall` 需要提供 `num_threads` 或 `tile_sizes` 来指示拆分块的大小，其中 `num_threads` 是控制拆分后外层循环的迭代次数，`tile_sizes` 是控制拆分后向量的长度；还有一个可选的参数 `mapping`，用来控制循环迭代变量映射到的轴。

```llvm
#map = affine_map<(d0) -> (d0 * 256)>
func.func @add(%arg0: tensor<1024xf32>, %arg1: tensor<1024xf32>) -> tensor<1024xf32> {
  %0 = tensor.empty() : tensor<1024xf32>
  %c4 = arith.constant 4 : index
  %1 = scf.forall (%arg2) in (4) shared_outs(%arg3 = %0) -> (tensor<1024xf32>) {
    %2 = affine.apply #map(%arg2)
    %3 = affine.apply #map(%arg2)
    %4 = affine.apply #map(%arg2)
    %5 = affine.apply #map(%arg2)
    %extracted_slice = tensor.extract_slice %arg0[%3] [256] [1] : tensor<1024xf32> to tensor<256xf32>
    %extracted_slice_0 = tensor.extract_slice %arg1[%4] [256] [1] : tensor<1024xf32> to tensor<256xf32>
    %extracted_slice_1 = tensor.extract_slice %arg3[%5] [256] [1] : tensor<1024xf32> to tensor<256xf32>
    %6 = linalg.add ins(%extracted_slice, %extracted_slice_0 : tensor<256xf32>, tensor<256xf32>) outs(%extracted_slice_1 : tensor<256xf32>) -> tensor<256xf32>
    %7 = affine.apply #map(%arg2)
    scf.forall.in_parallel {
      tensor.parallel_insert_slice %6 into %arg3[%7] [256] [1] : tensor<256xf32> into tensor<1024xf32>
    }
  }
  return %1 : tensor<1024xf32>
}
```

`transform.structured.tile_using_for` 只能通过 `tile_sizes` 来控制，而且没有 `mapping`。

```llvm
func.func @add(%arg0: tensor<1024xf32>, %arg1: tensor<1024xf32>) -> tensor<1024xf32> {
  %0 = tensor.empty() : tensor<1024xf32>
  %c0 = arith.constant 0 : index
  %c1024 = arith.constant 1024 : index
  %c256 = arith.constant 256 : index
  %1 = scf.for %arg2 = %c0 to %c1024 step %c256 iter_args(%arg3 = %0) -> (tensor<1024xf32>) {
    %extracted_slice = tensor.extract_slice %arg0[%arg2] [256] [1] : tensor<1024xf32> to tensor<256xf32>
    %extracted_slice_0 = tensor.extract_slice %arg1[%arg2] [256] [1] : tensor<1024xf32> to tensor<256xf32>
    %extracted_slice_1 = tensor.extract_slice %arg3[%arg2] [256] [1] : tensor<1024xf32> to tensor<256xf32>
    %2 = linalg.add ins(%extracted_slice, %extracted_slice_0 : tensor<256xf32>, tensor<256xf32>) outs(%extracted_slice_1 : tensor<256xf32>) -> tensor<256xf32>
    %inserted_slice = tensor.insert_slice %2 into %arg3[%arg2] [256] [1] : tensor<256xf32> into tensor<1024xf32>
    scf.yield %inserted_slice : tensor<1024xf32>
  }
  return %1 : tensor<1024xf32>
}
```

上面两个 transform op 的实现较为简单，主体方法就是首先创建 `scf.forall` 或 `scf.for` op，然后根据给定的 `num_threads` 或 `tile_sizes` 计算每次迭代的偏移和大小，然后传给 `TilingInterface` 的实现拿到拆分后的结果，最后创建 `insert_slice`。

### reduction 轴的拆分

上面的结果只有在拆分的轴是 `parallel` 的情况下才是正确的，考虑向量归约计算：$a = sum(A)$，其中 $A$ 是长度为 1024 的向量，那么该向量归约可以表示为：

```cpp
for (int i = 0; i < 1024; ++i) {
  a += A[i];
}
```

如果我们对向量在长度上拆分 4 次：

```cpp
for (int i = 0; i < 4; ++i) {
  for (int j = 0; j < 256; ++j) {
    a += A[i * 256 + j] 
  }
}
```

这在循环上的拆分是显而易见的，但如果我们对 Linalg op 直接调用 `transform.structured.tile_using_forall`：

```llvm
func.func @sum(%arg0 : tensor<1024xf32>) -> tensor<f32> {
 %0 = tensor.empty() : tensor<f32>
 %1 = linalg.reduce { arith.addf } ins(%arg0 : tensor<1024xf32>) outs(%0 : tensor<f32>) dimensions = [0]
 return %1 : tensor<f32>
}

transform.with_pdl_patterns {
^bb0(%arg0: !pdl.operation):
 transform.sequence %arg0 : !pdl.operation failures(propagate) {
   ^bb0(%arg1: !pdl.operation):
     %func = transform.structured.match ops{["func.func"]} in %arg1 : (!pdl.operation) -> !pdl.operation
     %reduce = transform.structured.match ops{["linalg.reduce"]} in %func : (!pdl.operation) -> !pdl.operation
     %result:2 = transform.structured.tile_using_forall %reduce num_threads [4] : (!pdl.operation) -> (!pdl.operation, !pdl.operation)
 }
}
```

会得到：

```llvm
#map = affine_map<(d0) -> (d0 * 256)>
func.func @sum(%arg0: tensor<1024xf32>) -> tensor<f32> {
  %0 = tensor.empty() : tensor<f32>
  %c4 = arith.constant 4 : index
  %1 = scf.forall (%arg1) in (4) shared_outs(%arg2 = %0) -> (tensor<f32>) {
    %2 = affine.apply #map(%arg1)
    %3 = affine.apply #map(%arg1)
    %extracted_slice = tensor.extract_slice %arg0[%3] [256] [1] : tensor<1024xf32> to tensor<256xf32>
    %extracted_slice_0 = tensor.extract_slice %arg2[] [] [] : tensor<f32> to tensor<f32>
    %reduced = linalg.reduce { arith.addf } ins(%extracted_slice : tensor<256xf32>) outs(%extracted_slice_0 : tensor<f32>) dimensions = [0]
    scf.forall.in_parallel {
      tensor.parallel_insert_slice %reduced into %arg2[] [] [] : tensor<f32> into tensor<f32>
    }
  }
  return %1 : tensor<f32>
}
```

同时会报出 `warning: tiling is not thread safe at axis #0`。

---

# 引用

- [如何评价MLIR项目中Linalg Dialect的设计思想？](https://www.zhihu.com/question/442964082)
- [MLIR Linalg Dialect 以及 Patterns](https://www.lei.chat/zh/posts/mlir-linalg-dialect-and-patterns/)
- [MLIR Linalg Op Fusion – Theory & Practice](https://llvm.org/devmtg/2024-04/slides/TechnicalTalks/Absar-MLIR-LinalgOpFusion.pdf)
- [MLIR: The case for a simplified polyhedral form](https://mlir.llvm.org/docs/Rationale/RationaleSimplifiedPolyhedralForm/)
- [A Primer on “Structured” Linalg Operations](https://mlir.llvm.org/docs/Tutorials/transform/Ch0/#)
