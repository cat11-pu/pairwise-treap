"""treap：平衡二叉搜索树内核（结点带优先级的树堆）。

结构约定
--------
* 每个结点存一个键（int）、一个优先级（int，由调用方给出）、一个计数 count
  （同一个键插入多次只增加计数，键在树里不重复出现），以及 size（这棵子树里
  所有元素的个数，含重复副本）。
* 树同时满足两条不变式：中序遍历的键严格递增（二叉搜索树性质），父结点的优先级
  不大于任一孩子的优先级（小顶堆性质）。两条合起来就是 treap。
* 优先级由调用方注入，内核不抽随机数、不读时钟、不做 I/O；同一串插入序列在任何
  平台上都会长出同一棵树，所以调用方自己保证优先级的随机性。
* 插入沿搜索路径下行，回溯时若孩子的优先级更小就把它旋转上来；删除一个键的最后
  一份副本时，直接把左右子树合并（左子树的键全都小于右子树，合并的前提成立）。
* size 与 count 是内核维护的记账字段：len(treap) 等于所有结点 count 之和，也等于
  根结点的 size。
"""

__all__ = ["Node", "Treap"]


def _check_key(key):
    """键必须是 int，bool 不算。"""
    if isinstance(key, bool) or not isinstance(key, int):
        raise TypeError("键必须是 int")


def _check_priority(priority):
    """优先级必须是 int，bool 不算。"""
    if isinstance(priority, bool) or not isinstance(priority, int):
        raise TypeError("优先级必须是 int")


def _size(node):
    """子树里的元素个数；空子树记 0。"""
    return 0 if node is None else node.size


class Node:
    """treap 的一个结点。

    key 是键，priority 是优先级（越小离树根越近），count 是这个键的重复次数，
    left / right 是左右孩子，size 是整棵子树（含孩子）的元素个数。
    """

    __slots__ = ("key", "priority", "count", "left", "right", "size")

    def __init__(self, key, priority, count=1):
        self.key = key
        self.priority = priority
        self.count = count
        self.left = None
        self.right = None
        self.size = count

    def __repr__(self):
        return "Node(key=%r, priority=%r, count=%r)" % (self.key, self.priority, self.count)


def _update(node):
    """重算子树里的元素个数。"""
    node.size = node.count + _size(node.left) + _size(node.right)


def _rotate_right(node):
    """把 node 的左孩子转上来，返回新的子树顶。"""
    top = node.left
    node.left = top.right
    top.right = node
    _update(node)
    _update(top)
    return top


def _rotate_left(node):
    """把 node 的右孩子转上来，返回新的子树顶。"""
    top = node.right
    node.right = top.left
    top.left = node
    _update(node)
    _update(top)
    return top


def _insert(node, key, priority):
    """把 key 插进子树；键已存在时只增加计数。返回子树新的顶。"""
    if node is None:
        return Node(key, priority)
    if key == node.key:
        node.count += 1
        _update(node)
        return node
    if key < node.key:
        node.left = _insert(node.left, key, priority)
        if node.left.priority < node.priority:
            return _rotate_right(node)
    else:
        node.right = _insert(node.right, key, priority)
        if node.right.priority < node.priority:
            return _rotate_left(node)
    _update(node)
    return node


def _merge(left, right):
    """合并两棵子树，返回新的子树顶。

    调用方保证 left 里的键全都小于 right 里的键，且两棵子树各自满足堆序。
    """
    if left is None:
        return right
    if right is None:
        return left
    if left.priority <= right.priority:
        left.right = _merge(left.right, right)
        _update(left)
        return left
    right.left = _merge(left, right.left)
    _update(right)
    return right


def _erase(node, key):
    """删掉 key 的一份副本；返回子树新的顶。键不在子树里时原样返回。"""
    if node is None:
        return None
    if key == node.key:
        if node.count > 1:
            node.count -= 1
            _update(node)
            return node
        return _merge(node.left, node.right)
    if key < node.key:
        node.left = _erase(node.left, key)
    else:
        node.right = _erase(node.right, key)
    _update(node)
    return node


def _collect(node, out):
    """中序遍历，把键按升序收进 out。"""
    if node is None:
        return
    _collect(node.left, out)
    out.append(node.key)
    _collect(node.right, out)


def _collect_entries(node, out):
    """中序遍历，把 (键, 计数) 按升序收进 out。"""
    if node is None:
        return
    _collect_entries(node.left, out)
    out.append((node.key, node.count))
    _collect_entries(node.right, out)


def _range(node, lo, hi):
    """统计子树里键落在闭区间 [lo, hi] 内的元素个数。"""
    if node is None:
        return 0
    if node.key < lo:
        return _range(node.right, lo, hi)
    if node.key > hi:
        return _range(node.left, lo, hi)
    return node.count + _range(node.left, lo, hi) + _range(node.right, lo, hi)


def _height(node):
    """子树的层数；空子树记 0。"""
    if node is None:
        return 0
    return 1 + max(_height(node.left), _height(node.right))


class Treap:
    """treap 内核：插入、查找、删除、区间计数、秩与高度。

    语义：
        insert(key, priority)   插入一个键；已存在则只增加计数；返回该键的结点
        search(key)             找到键所在的结点；没有返回 None
        contains(key)           键是否在树里
        count(key)              键的重复次数；不在树里记 0
        erase(key)              删掉该键的一份副本；键不在树里返回 False
        keys()                  所有键的升序列表，重复键只出现一次
        entries()               (键, 计数) 的升序列表
        range_count(lo, hi)     键在闭区间 [lo, hi] 里的元素个数（含重复）
        kth(index)              1 起算：第 index 小元素的键；越界抛 IndexError
        rank(key)               严格小于 key 的元素个数（含重复）
        height()                层数；空树 0，单结点 1
        __len__()               元素总个数（含重复）
    """

    def __init__(self):
        self.root = None
        self.total = 0

    def __len__(self):
        return self.total

    def __repr__(self):
        return "Treap(size=%d, height=%d)" % (self.total, self.height())

    def is_empty(self):
        """树里是否一个元素都没有。"""
        return self.root is None

    def insert(self, key, priority):
        """插入一个键；键已存在时只增加计数。返回该键对应的结点。"""
        _check_key(key)
        _check_priority(priority)
        self.root = _insert(self.root, key, priority)
        self.total += 1
        return self.search(key)

    def search(self, key):
        """找到键所在的结点；没有返回 None。"""
        _check_key(key)
        node = self.root
        while node is not None:
            if key == node.key:
                return node
            node = node.left if key < node.key else node.right
        return None

    def contains(self, key):
        """键是否在树里。"""
        return self.search(key) is not None

    def count(self, key):
        """键的重复次数；不在树里记 0。"""
        node = self.search(key)
        return 0 if node is None else node.count

    def erase(self, key):
        """删掉键的一份副本；键不在树里返回 False，否则返回 True。"""
        _check_key(key)
        if self.search(key) is None:
            return False
        self.root = _erase(self.root, key)
        self.total -= 1
        return True

    def keys(self):
        """所有键的升序列表，重复键只出现一次。"""
        out = []
        _collect(self.root, out)
        return out

    def entries(self):
        """(键, 计数) 的升序列表。"""
        out = []
        _collect_entries(self.root, out)
        return out

    def range_count(self, lo, hi):
        """键落在闭区间 [lo, hi] 里的元素个数（含重复）；lo 大于 hi 记 0。"""
        _check_key(lo)
        _check_key(hi)
        if lo > hi:
            return 0
        return _range(self.root, lo, hi)

    def kth(self, index):
        """1 起算：第 index 小元素的键。index 越界抛 IndexError。"""
        if index < 1 or index > self.total:
            raise IndexError("index 越界")
        node = self.root
        while node is not None:
            left = _size(node.left)
            if index <= left:
                node = node.left
            elif index <= left + node.count:
                return node.key
            else:
                index -= left + node.count
                node = node.right
        return None  # 收尾：循环里的三个分支覆盖了 index 落在树内的全部情况

    def rank(self, key):
        """严格小于 key 的元素个数（含重复）。"""
        _check_key(key)
        node = self.root
        total = 0
        while node is not None:
            if key <= node.key:
                node = node.left
            else:
                total += _size(node.left) + node.count
                node = node.right
        return total

    def height(self):
        """层数：空树 0，单结点 1。"""
        return _height(self.root)
