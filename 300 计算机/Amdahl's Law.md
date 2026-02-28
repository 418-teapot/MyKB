---
type: law
---

若某系统执行某应用程序需要时间为 $T_{\text{old}}$ 。假设系统某部分所需执行时间与该时间的比例为 $\alpha$ ，而该部分性能提升比例为 $k$ 。即该部分初始所需时间为 $\alpha T_{\text{old}}$ ，现在所需时间为 $(\alpha T_{\text{old}}) / k$ 。因此，总的执行时间应为

$$
T_{\text{new}} = (1 - \alpha) T_{\text{old}} + (\alpha T_{\text{old}}) / k = T_{\text{old}}[(1 - \alpha) + \alpha / k]
$$

由此，可以计算加速比 $S = T_{\text{old}} / T_{\text{new}}$ 为

$$
S = \frac{1}{(1 - \alpha) + \alpha / k}
\tag{1-1}
$$

^1-1
