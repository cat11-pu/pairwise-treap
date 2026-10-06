# treap

一个纯标准库、可确定复现的平衡二叉搜索树内核：结点带上由调用方注入的优先级，
同时满足中序递增与小顶堆序；支持插入并旋转、按键查找、计数式重复键、删除并合并
左右子树、区间计数、第 k 小与秩、高度统计。内核不抽随机数、不读时钟、不做 I/O，
同一串插入序列在任何平台上都会长出同一棵树。

## 目录

- `treap/core.py`：内核实现（`Node`、`Treap`）
- `tests/test_core.py`：行为与结构不变量测试

## 语义约定

- 每个结点是一个 `Node`：`key` 是键（int），`priority` 是优先级（int，越小离树根
  越近），`count` 是这个键的重复次数，`size` 是这棵子树里所有元素的个数（含重复）。
- 同一个键只占一个结点：再次插入只把 `count` 加一，优先级保持先到者的值。
- 树同时满足两条不变式：中序遍历的键严格递增；父结点的优先级不大于任一孩子。
  `size` 等于自身计数加两棵子树，`len(treap)` 等于所有结点计数之和。
- 删除一个键的副本：还有副本就只减计数，最后一份副本被删掉时把左右子树合并回去。
- 对外接口：

      treap = Treap()
      treap.insert(3, 17)        # 插入键 3、优先级 17；返回该键的结点
      treap.search(3)            # 键所在的结点；没有返回 None
      treap.contains(3)          # 键是否在树里
      treap.count(3)             # 键的重复次数；不在树里记 0
      treap.erase(3)             # 删掉一份；键不在树里返回 False
      treap.keys()               # 所有键的升序列表，重复键只出现一次
      treap.entries()            # (键, 计数) 的升序列表
      treap.range_count(2, 9)    # 键在闭区间 [2, 9] 里的元素个数（含重复）
      treap.kth(1)               # 1 起算：第 1 小元素的键；越界抛 IndexError
      treap.rank(3)              # 严格小于 3 的元素个数（含重复）
      treap.height()             # 层数：空树 0，单结点 1
      len(treap)                 # 元素总个数（含重复）
      treap.is_empty()           # 树里是否一个元素都没有

- 优先级由调用方给出，内核只负责按堆序摆放；想要期望意义上的平衡，调用方自己
  保证优先级的随机性。

## 怎么跑测试

在项目根目录执行：

    python3 -m unittest discover -s tests -v

Windows 上把 `python3` 换成你的解释器路径，例如：

    C:/Users/<你>/AppData/Local/Programs/Python/Python313/python.exe -m unittest discover -s tests -v

只依赖 Python 3 标准库，不需要装任何包，也不需要联网。
