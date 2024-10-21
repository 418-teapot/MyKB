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

结构化的 op 包括 `linalg.generic`、`linalg.map`、`linalg.reduce`、`linalg.transpose`、`linalg.broadcast`、`linalg.matmul`、`linalg.conv` 等。其中 `linalg.generic` 是最核心的 op；其他 op 被称为 named ops，这些 op 只是某些特定的 `linalg.generic` 的语法糖。例如：

```llvm
module {
  func.func @matmul(%arg0: tensor<128x256xf32>, %arg1: tensor<256x512xf32>) -> tensor<128x512xf32> {
    %0 = tensor.empty() : tensor<128x512xf32>
    %1 = linalg.matmul ins(%arg0, %arg1 : tensor<128x256xf32>, tensor<256x512xf32>) outs(%0 : tensor<128x512xf32>) -> tensor<128x512xf32>
    return %1 : tensor<128x512xf32>
  }
}
```

使用 `--linalg-generalize-named-ops` pass 可以将 named ops 还原为 `linalg.generic`：

```llvm
#map = affine_map<(d0, d1, d2) -> (d0, d2)>
#map1 = affine_map<(d0, d1, d2) -> (d2, d1)>
#map2 = affine_map<(d0, d1, d2) -> (d0, d1)>
module {
  func.func @matmul(%arg0: tensor<128x256xf32>, %arg1: tensor<256x512xf32>) -> tensor<128x512xf32> {
    %0 = tensor.empty() : tensor<128x512xf32>
    %1 = linalg.generic {indexing_maps = [#map, #map1, #map2], iterator_types = ["parallel", "parallel", "reduction"]} ins(%arg0, %arg1 : tensor<128x256xf32>, tensor<256x512xf32>) outs(%0 : tensor<128x512xf32>) {
    ^bb0(%in: f32, %in_0: f32, %out: f32):
      %2 = arith.mulf %in, %in_0 : f32
      %3 = arith.addf %out, %2 : f32
      linalg.yield %3 : f32
    } -> tensor<128x512xf32>
    return %1 : tensor<128x512xf32>
  }
}
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

## 拆分

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

同时会报出 `warning: tiling is not thread safe at axis #0`。我们可以看到 `tile_use_forall` 只是单纯地将算子拆分成了 4 份，并没有将这 4 份结果最后再累加起来。

为了正确地拆分 reduction 轴，我们应当使用 `transform.structured.tile_reduction_using_forall` 和 `transform.structured.tile_reduction_using_for`

```llvm
#map = affine_map<(d0) -> (d0 * 256)>
func.func @sum(%arg0: tensor<1024xf32>) -> tensor<f32> {
  %0 = tensor.empty() : tensor<f32>
  %1 = tensor.empty() : tensor<4xf32>
  %cst = arith.constant 0.000000e+00 : f32
  %2 = linalg.fill ins(%cst : f32) outs(%1 : tensor<4xf32>) -> tensor<4xf32>
  %c4 = arith.constant 4 : index
  %3 = scf.forall (%arg1) in (4) shared_outs(%arg2 = %2) -> (tensor<4xf32>) {
    %4 = affine.apply #map(%arg1)
    %extracted_slice = tensor.extract_slice %arg2[%arg1] [1] [1] : tensor<4xf32> to tensor<f32>
    %5 = affine.apply #map(%arg1)
    %extracted_slice_0 = tensor.extract_slice %arg0[%5] [256] [1] : tensor<1024xf32> to tensor<256xf32>
    %extracted_slice_1 = tensor.extract_slice %extracted_slice[] [] [] : tensor<f32> to tensor<f32>
    %reduced_2 = linalg.reduce { arith.addf } ins(%extracted_slice_0 : tensor<256xf32>) outs(%extracted_slice_1 : tensor<f32>) dimensions = [0]
    scf.forall.in_parallel {
      tensor.parallel_insert_slice %reduced_2 into %arg2[%arg1] [1] [1] : tensor<f32> into tensor<4xf32>
    }
  }
  %reduced = linalg.reduce ins(%3 : tensor<4xf32>) outs(%0 : tensor<f32>) dimensions = [0]
    (%in: f32, %init: f32) {
      %4 = arith.addf %in, %init : f32
      linalg.yield %4 : f32
    }
```

使用 `tile_reduction_using_forall` 之后，在拆分时会将每份的结果先到一个 `tensor` 中，然后再对这个 `tensor` 进行累加操作。

### 多个轴的拆分

我们可以对多个轴同时进行拆分，这相当于对每个轴分别进行拆分。

## 融合

### 算子融合

考虑向量乘法和向量加法：$A = B * C; D = A + E$，均为长度为 `<1024xf32>` 的向量，我们有：

```cpp
for (int i = 0; i < 1024; ++i) {
  A[i] = B[i] * C[i];
}

for (int i = 0; i < 1024; ++i) {
  D[i] = A[i] + E[i];
}
```

由于这两个循环的迭代变量一致，我们可以将这两个循环合并到一起：

```cpp
for (int i = 0; i < 1024; ++i) {
  D[i] = (B[i] * C[i]) + E[i];
}
```

由于 Linalg op 是完美循环的抽象，因此可以表示为：

```llvm
%mul = linalg.map {arith.mulf} ins(%0, %1 : tensor<1024xf32>, tensor<1024xf32>) outs(%2 : tensor<1024xf32>)
%add = linalg.map {arith.addf} ins(%mul, %3 : tensor<1024xf32>, tensor<1024xf32>) outs(%4 : tensor<1024xf32)
```

到

```llvm
%madd = linalg.map ins(%0, %1, %3 : tensor<1024xf32>, tensor<1024xf32>, tensor<1024xf32>) outs(%4 : tensor<1024xf32>)
(%in0: f32, %in1: f32, %in2: f32) {
  %mul = arith.mulf %in0, %in1 : f32
  %add = arith.addf %mul, %in2 : f32
  linalg.yield %add : f32
}
```

的融合。

### 循环融合

以上面的向量乘法和向量加法为例，如果我们先对向量加法进行了拆分：

```llvm
%mul = linalg.map {arith.mulf} ins(%0, %1 : tensor<1024xf32>, tensor<1024xf32>) outs(%2 : tensor<1024xf32>)
%loop = scf.forall (%arg1) in %c4 {
  %mul' = tensor.extract_slice %mul ...
  %e' = tensor.extract_slice %E ...
  %add' = linalg.map {arith.addf} ins(%mul', %e' : tensor<256xf32>, tensor<256xf32>) outs ...
}
```

通过观察，不难发现，我们可以对 `linalg.map {arith.mulf}` 进行相同的拆分，然后将两个循环合并到一起：

```llvm
%loop = scf.forall (%arg1) in %c4 {
  %a' = tensor.extract_slice %A ...
  %b' = tensor.extract_slice %B ...
  %e' = tensor.extract_slice %E ...
  %mul' = linalg.map {arith.mulf} ins(%a', %b') ...
  %add' = linalg.map {arith.addf} ins(%mul', %e') ...
}
```

Linalg Dialect 提供了 `transform.structured.fuse_into_containing` 来将 producer 融入到拆分后的 consumer 循环中，该 op 在实现上分为几个步骤：

1. 统计 producer 在循环中有多少个 user；
2. 在 user 中找到第一个 `tensor.extract_slice`；
3. 根据 `tensor.extract_slice` 的 size 和 offset 等信息，调用 producer 的 tiling interface 实现，在循环中创建拆分后的 op；
4. 如果有非 `tensor.extract_slice` 的 user，将 producer 直接 clone 到循环中；
5. 重复第 2 步，直到 user 计数为 0。

使用 `transform.structured.fuse_into_containing` 时，我们需要先对一个 op 进行拆分，然后不断地 match 其他 op，将其融合到循环中，使用起来较为麻烦。

针对这一场景，genesis 添加了 `fuse_greedily` 这一 trasform op，该 op 可以在对一个 op 进行拆分的同时，将其 producer 链上的所有 op 融合到循环中。

```

  A
 / \
B   C
 \ /
  D
```

例如该情况下，在我们锚定 `D` 的时候，`fuse_greedily` 会进行广度优先搜索，将 `B` 和 `C` 添加到队列中；在融合 `B` 之后，会将其 producer `A` 添加到队列中；在融合 `C` 之后，由于 `B` 和 `C` 都依赖于 `A`，因此在循环中会有 2 个 `A` 的 `tensor.extract_slice`，所以在融合 `A` 后循环中会有 2 个 `A`；`fuse_greedily` 最后会调用一次 CSE 和 canonicalization，当这两个 `A` 的拆分是一致的时候，其中一个 `A` 会被消除。

将 producer 融入到 consumer 对于一个 consumer 对应多个 producer 是有利的：

```
A   B
 \ /
  C
```

但对一个 producer 对应多个 consumer 的情况是不利的：

```

  A
 / \
B   C
```

针对这种情况，genesis 添加了将 consumer 融合到 producer 的方法。

## 标准化

在循环拆分的时候我们已经知道，“对多个轴同时进行拆分，相当于对每个轴分别进行拆分”。

### 循环交换

以向量加法为例，$A = B + C$，$A$、$B$、$C$ 均为长度为 `<256x1024xf32>` 的向量，如果我们分别对第 0 维和第 1 维进行拆分：

```cpp
for (int i = 0; i < 2; ++i) {
  for (int j = 0; j < 4; ++j) {
    for (int ti = 0; ti < 128; ++ti) {
      for (int tj = 0; tj < 256; ++tj) {
        A[i * 128 + ti][j * 256 + tj] =
          B[i * 128 + ti][j * 256 + tj] + C[i * 128 + ti][j * 256 + tj];
      }
    }
  }
}
```

最内层循环可以看成是长度 `<128x256xf32>` 的向量加法，在 MLIR 中可以表示为：

```llvm
%0 = scf.forall (%arg1) in (%c2) {
  %1 = scf.forall (%arg2) in (%c4) {
    %a' = tensor.extract_slice %A ...
    %b' = tensor.extract_slice %B ...
    %c' = linalg.add ins(%a', %b' : tensor<128x256xf32>, tensor<128x256xf32>)
  }
}
```

如果 `%0` 和 `%1` 循环都是对 parallel 轴的拆分，只要在两层 for 循环之间没有其他操作，我们交换这两个循环的顺序就没有任何影响：

```llvm
%1 = scf.forall (%arg2) in (%c4) {
  %0 = scf.forall (%arg1) in (%c2) {
    %a' = tensor.extract_slice %A ...
    %b' = tensor.extract_slice %B ...
    %c' = linalg.add ins(%a', %b' : tensor<128x256xf32>, tensor<128x256xf32>)
  }
}
```

我们进行循环交换的目的是：

- 为后面的循环折叠简化 pattern；
- 将对特定轴的拆分交换到最里面，以符合编程模型。

### 循环折叠

以向量加法为例，$A = B + C$，$A$、$B$、$C$ 均为长度为 `<256x1024xf32>` 的向量。

如果我们对不同的轴进行拆分：

```llvm
%0 = scf.forall (%arg1) in (%c2) {
  %1 = scf.forall (%arg2) in (%c4) {
    %a' = tensor.extract_slice %A ...
    %b' = tensor.extract_slice %B ...
    %c' = linalg.add ins(%a', %b' : tensor<128x256xf32>, tensor<128x256xf32>)
  }
}
```

这些拆分可以合并到一个 `scf.forall` 中：

```llvm
%0 = scf.forall (%arg1, %arg2) in (%c2, %c4) {
  ...
}
```

如果我们对同一轴进行多次拆分：

```llvm
%0 = scf.forall (%arg1) in %c2 {
  %1 = scf.forall (%arg2) in %c4 {
    %a' = tensor.extract_slice %A ...
    %b' = tensor.extract_slice %B ...
    %c' = linalg.add ins(%a', %b' : tensor<256x128xf32>)
  }
}
```

这些拆分也可以合并到同一个 `scf.forall` 中，但需要更改迭代变量的迭代范围：

```llvm
%0 = scf.forall (%arg1) in %c8 {
  ...
}
```

### 标准化后的形式

当前 genesis 会进行两次“标准化”操作，第一次标准化通过循环交换、循环折叠等操作，将 `scf.forall` 循环压缩到 2 个，并将所有对 `xpe` 的拆分交换到最里面，对其他轴的拆分交换到最外面：

```llvm
scf.forall (%arg0, %arg1, %arg2, %arg3, %arg4) in (...) {
  ...
  scf.forall (%arg5, %arg6, %arg7, %arg8, %arg9) in (...) {
    ...
  } {mapping = [#aux_ext.task<z>, #aux_ext.task<y>, #aux_ext.task<xseq>, #aux_ext.task<xtask>, #aux_ext.task<xpe>]}
} {mapping = [#aux_ext.task<z>, #aux_ext.task<y>, #aux_ext.task<xseq>, #aux_ext.task<xtask>, #aux_ext.task<xpe>]}
```

在经过这次“标准化”后，genesis 有了明确的编程模型，由于 `xpe` 轴在最终循环分配后会被分配到 IPU 上，所以我们可以认为在最内层 `forall` 中都是 IPU 执行的代码，在两层 `forall` 之间的是 MPU 执行的代码。

因此，在第二次“标准化”之前，genesis 会对 `forall` 中的算子分别标上 `executor = "ipu"` 或 `executor = "mpu"` 的属性，来指示算子的执行位置。

第二次“标准化”后，所有 `forall` 循环会被压缩到 1 个，同时会计算出 kernel launch 的类型，并将 `#aux_ext.task` 转换到对应的 `#cnapi.task` 上，用于之后的循环分配：

```llvm
scf.forall (%arg0, %arg1, %arg2) in (...) {
  ...
} {cnapi.task_type = "union1", mapping = [#cnapi.task<z>, #cnapi.task<y>, #cnapi.task<x>]}
```

## 分配

循环分配就是把划分好的分块指定给不同的计算单元。 通常来说，`scf.for` 循环表示的是时间序列上顺序执行。这种循环我们没有办法判断循环迭代之间有无依赖，如循环中可能会出现写下一个循环需要读的数据。因此执行只能是顺序的。

在 `scf.forall` 循环和 `scf.forall.in_parallel` 中的 op 是没有前后依赖的，是可以放心的并发执行的。

以上面的向量加法为例，原先为长度 `1024` 的向量计算，我们可以让一个硬件计算单元来进行处理；在使用 `tile_using_forall` 拆分 4 次之后，由于 `scf.forall` 中的 op 可以并发执行，我们可以将这 4 次循环分别分配到不同的硬件计算单元上，每个计算单元执行长度为 `256` 的向量计算。

### 并行模型

MLU 在每一次 launch kernel 的时候需要指定任务类型。MLU 上支持 BLOCK 任务（1 个 IPU），Un 任务（一般来说是 4n 个 IPU + n 个 MPU）。

任务下发后，任务中所有的处理单元并行地执行“同一份代码”。值得注意的是，在编译器底层将同一份代码拆分给了 MPU 和 IPU。编程模型上，MPU 和 IPU 是不对称的两种处理单元，MPU 一般只处理 shared memory 之间，shared memory 和 dram 之间的数据搬移。

### 轴绑定

这种并发执行在 CPU 上，可以使用多线程的方式来执行，线程的 id 就是循环的迭代变量，在 MLU 上同样也可以使用 launch kernel 的形式，kernel 中的 block_id/thread_id 对应循环的迭代变量，如下所示：

```mlir
cnapi.launch_func  queue [%arg0] @add_mlu_kernel_kernel::@add_mlu_kernel_kernel tasks in (%c4, %c1, %c1) %c1 args(%A : memref<256xf32, 1>, %B : memref<256xf32, 1>, %C : memref<256xf32, 1>)
```

从 scf 到 launch 这种转换是可以通过代码自动完成的，需要的额外信息就是每一个循环的轴到 launch 轴的映射关系， 这叫做轴映射。这个信息一般都来自于使用 `tile_using_forall` 时给定的 `mapping`。

在 `genesis/CodeGen/IR/DeviceMappingAttr.td` 中我们有如下定义：

```tablegen
def DimXPE : I64EnumAttrCase<"DimXPE", 1, "xpe">;  
def DimXTask : I64EnumAttrCase<"DimXTask", 2, "xtask">;  
def DimXSeq : I64EnumAttrCase<"DimXSeq", 4, "xseq">;  
def DimY : I64EnumAttrCase<"DimY", 8, "y">;  
def DimZ : I64EnumAttrCase<"DimZ", 16, "z">;  
def DimSeq : I64EnumAttrCase<"DimSeq", 32, "seq">;  
  
// Using for tiling to forall thread or reduction op.  
// DimXPE will map thread to ipu cores in the same cluster.  
// DimXTask will map thread to clusters in the same task.  
// DimXSeq will map thread to task in the same job.  
// DimY will map thread to the hardware y dimension.  
// DimZ will map thread to the hardware z dimension.  
// DimSeq won't do any mapping, the code will be lowered to loop.  
def TasksEnum : I64EnumAttr<"Tasks", "tasks for loop mapping", [  
   DimXPE, DimXTask, DimXSeq, DimY, DimZ, DimSeq]> {  
 let cppNamespace = "::mlir::genesis";  
}
```

- `DimXPE` 表示绑定到一个 cluster 的多个 IPU 之间。
- `DimXTask` 表示绑定到一个 task 的多个 cluster 之间。
- `DimXSeq` 表示绑定到一个 job 的 x task 之间。
- `DimY` 表示绑定到硬件的 dimy 维度。
- `DimZ` 表示绑定到硬件的 dimz 维度。
- `Seq` 表示该循环不做绑定，最后会下降成自然循环。

## 示例与回顾

以矩阵乘 MatMul 运算作为示例，进行回顾：

```llvm
func.func @matmul(%arg0: tensor<128x256xf32>,
                  %arg1: tensor<256x256xf32>) -> tensor<128x256xf32> {
 %cst = arith.constant 0.0 : f32
 %init_out = tensor.empty () : tensor<128x256xf32>
 %fill = linalg.fill ins(%cst : f32) outs(%init_out: tensor<128x256xf32>) -> tensor<128x256xf32>
 
 %matmul = linalg.matmul ins(%arg0, %arg1 : tensor<128x256xf32>, tensor<256x256xf32>)
   outs(%fill: tensor<128x256xf32>) -> tensor<128x256xf32>  

 return %matmul : tensor<128x256xf32>
}
```

```llvm
transform.with_pdl_patterns {
^bb0(%arg0: !pdl.operation):
 transform.sequence %arg0 : !pdl.operation failures(propagate) {
   ^bb0(%arg1: !pdl.operation):
     %mlu_exec = transform.genesis.match ops{["aux_ext.executable_mlu"]} in %arg1 : (!pdl.operation) -> !pdl.operation
     %device_func = transform.genesis.match ops{["func.func"]} in %mlu_exec : (!pdl.operation) -> !pdl.operation
     
     // DecomposeInterface
     %0 = transform.genesis.match ops{["linalg.matmul"]} in %device_func : (!pdl.operation) -> !pdl.operation
     transform.genesis.decompose_interface %0 : (!pdl.operation) -> !pdl.operation
     
     transform.genesis.run_pipeline %device_func {pass_pipeline = "linalg-canonicalize", op_name = "func.func"}
     transform.genesis.apply_canonicalization to %mlu_exec : !pdl.operation
     
     // split to multiple clusters
     %root = transform.genesis.match ops{["linalg.conv_2d_nhwc_fhwc"]} in %device_func : (!pdl.operation) -> !pdl.operation
     %forall_op = transform.genesis.fuse_greedily %root num_threads [0, 4, 0, 0] (mapping = [ #aux_ext.task<xtask> ])
  
     %producer1 = transform.genesis.match ops{["linalg.transpose"]} in %device_func : (!pdl.operation) -> !pdl.operation
     %p1_relay = transform.genesis.add_relay %producer1 {operands_to_relay = [0]}
     %tiled_op = transform.genesis.match ops{["linalg.conv_2d_nhwc_fhwc"]} in %device_func : (!pdl.operation) -> !pdl.operation
     %tiled_relay = transform.genesis.add_relay %tiled_op {operands_to_relay = [0, 2]}

     %forall_op1 = transform.genesis.fuse_greedily %tiled_relay num_threads [0, 0, 0, 4] (mapping = [ #aux_ext.task<xpe> ])

     transform.genesis.apply_canonicalization to %mlu_exec : !pdl.operation
     transform.genesis.run_pipeline %device_func {pass_pipeline = "loop-early-coalesce", op_name = "func.func"}
 }  
}
```

---

# 引用

- [如何评价MLIR项目中Linalg Dialect的设计思想？](https://www.zhihu.com/question/442964082)
- [MLIR Linalg Dialect 以及 Patterns](https://www.lei.chat/zh/posts/mlir-linalg-dialect-and-patterns/)
- [MLIR Linalg Op Fusion – Theory & Practice](https://llvm.org/devmtg/2024-04/slides/TechnicalTalks/Absar-MLIR-LinalgOpFusion.pdf)
- [MLIR: The case for a simplified polyhedral form](https://mlir.llvm.org/docs/Rationale/RationaleSimplifiedPolyhedralForm/)
- [A Primer on “Structured” Linalg Operations](https://mlir.llvm.org/docs/Tutorials/transform/Ch0/#)
