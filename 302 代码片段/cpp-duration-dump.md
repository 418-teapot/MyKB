---
type: snippet
lang: cpp
kind: util
tags:
  - chrono
  - clock
  - duration
---

# 正文

使用 chrono 库中的高精度时钟，统计并打印两个程序点之间的时间间隔。

---

# 代码

```cpp
class Timer {
public:
  Timer() { reset(); }
  void reset() { point = std::chrono::high_resolution_clock::now(); }
  void dump(llvm::StringRef message) {
    auto now = std::chrono::high_resolution_clock::now();
    auto duration =
        std::chrono::duration_cast<std::chrono::milliseconds>(now - point);
    llvm::errs() << message << " duration: " << duration.count() << " ms\n";
  }
  
private:
  std::chrono::time_point<std::chrono::high_resolution_clock> point;
};
```
