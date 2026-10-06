"""treap.core 的行为测试：插入旋转、堆序、删除合并、区间计数、高度与秩。"""

import unittest

from treap.core import Treap


def shuffled(count):
    """1..count 的固定乱序：用乘法散列排序，跨平台每次一样。"""
    keys = list(range(1, count + 1))
    keys.sort(key=lambda key: (key * 2654435761) % 4294967296)
    return keys


def priority_stream(count, seed):
    """count 个固定优先级：线性同余序列，跨平台每次一样，也不会整段单调。"""
    out = []
    value = seed * 7919 + 104729
    for _ in range(count):
        value = (value * 1103515245 + 12345) % 2147483648
        out.append(value)
    return out


class TreapTest(unittest.TestCase):
    """平衡二叉搜索树内核。"""

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------
    def build(self, pairs):
        treap = Treap()
        for key, priority in pairs:
            treap.insert(key, priority)
        return treap

    def measured_height(self, node):
        """从实际孩子指针独立数一遍层数。"""
        if node is None:
            return 0
        return 1 + max(self.measured_height(node.left), self.measured_height(node.right))

    def check_invariants(self, treap, expected=None):
        """核对二叉搜索树性质、堆序、计数与 size 记账。"""
        root = treap.root
        if root is None:
            self.assertEqual(len(treap), 0, "空树的总数必须是 0")
            self.assertEqual(treap.keys(), [], "空树的键列表必须是空的")
            self.assertEqual(treap.entries(), [], "空树的条目列表必须是空的")
            self.assertEqual(treap.height(), 0, "空树的高度必须是 0")
            if expected is not None:
                self.assertEqual(expected, 0)
            return
        seen = set()
        counts = {}
        nodes = 0
        stack = [root]
        while stack:
            node = stack.pop()
            self.assertNotIn(id(node), seen, "同一个结点不能在树里出现两次")
            seen.add(id(node))
            nodes += 1
            self.assertGreaterEqual(node.count, 1, "结点的计数至少是 1")
            counts[node.key] = counts.get(node.key, 0) + node.count
            left_size = 0 if node.left is None else node.left.size
            right_size = 0 if node.right is None else node.right.size
            self.assertEqual(node.size, node.count + left_size + right_size,
                             "size 必须等于自身计数加两棵子树")
            for side, child in (("left", node.left), ("right", node.right)):
                if child is None:
                    continue
                if side == "left":
                    self.assertLess(child.key, node.key, "左子树的键必须小于父键")
                else:
                    self.assertGreater(child.key, node.key, "右子树的键必须大于父键")
                self.assertGreaterEqual(child.priority, node.priority,
                                        "堆序：父的优先级不能大于孩子")
                stack.append(child)
        keys = treap.keys()
        self.assertEqual(keys, sorted(keys), "中序遍历必须按升序给出键")
        self.assertEqual(len(keys), nodes, "每个结点恰好贡献一个键")
        self.assertEqual(treap.entries(), sorted(counts.items()),
                         "entries 必须与树上数出来的 (键, 计数) 一致")
        self.assertEqual(sum(counts.values()), len(treap),
                         "所有结点的计数之和必须等于总数")
        self.assertEqual(root.size, len(treap), "根结点的 size 必须等于总数")
        self.assertEqual(treap.height(), self.measured_height(root),
                         "height 必须等于实际层数")
        if expected is not None:
            self.assertEqual(len(treap), expected)

    # ------------------------------------------------------------------
    # 用例
    # ------------------------------------------------------------------
    def test_01_empty_treap_and_argument_checks(self):
        """空树的边界行为，以及非法参数的类型校验。"""
        treap = Treap()
        self.assertEqual(len(treap), 0)
        self.assertTrue(treap.is_empty())
        self.assertIsNone(treap.root)
        self.assertEqual(treap.keys(), [])
        self.assertEqual(treap.entries(), [])
        self.assertEqual(treap.height(), 0)
        self.assertIsNone(treap.search(3))
        self.assertFalse(treap.contains(3))
        self.assertEqual(treap.count(3), 0)
        self.assertFalse(treap.erase(3))
        self.assertEqual(treap.rank(3), 0)
        self.assertEqual(treap.range_count(1, 9), 0)
        self.assertEqual(treap.range_count(9, 1), 0)
        for bad in ("7", 2.5, None, True, (1,)):
            with self.assertRaises(TypeError):
                treap.insert(bad, 1)
            with self.assertRaises(TypeError):
                treap.insert(1, bad)
            with self.assertRaises(TypeError):
                treap.search(bad)
            with self.assertRaises(TypeError):
                treap.count(bad)
            with self.assertRaises(TypeError):
                treap.erase(bad)
            with self.assertRaises(TypeError):
                treap.rank(bad)
            with self.assertRaises(TypeError):
                treap.range_count(bad, 5)
            with self.assertRaises(TypeError):
                treap.range_count(5, bad)
        self.assertEqual(len(treap), 0)
        with self.assertRaises(IndexError):
            treap.kth(0)
        with self.assertRaises(IndexError):
            treap.kth(1)
        node = treap.insert(5, 7)
        self.assertEqual(len(treap), 1)
        self.assertIs(treap.search(5), node)
        self.assertTrue(treap.erase(5))
        self.assertEqual(len(treap), 0)
        self.assertIsNone(treap.root)

    def test_02_single_key_and_counters(self):
        """单键树的计数、查找与删除，以及取空之后的边界。"""
        treap = Treap()
        node = treap.insert(4, 20)
        self.assertEqual(len(treap), 1)
        self.assertIs(treap.search(4), node)
        self.assertEqual(treap.entries(), [(4, 1)])
        self.assertEqual(treap.count(4), 1)
        self.assertTrue(treap.erase(4))
        self.assertEqual(len(treap), 0)
        self.assertTrue(treap.is_empty())
        self.assertIsNone(treap.search(4))
        self.assertFalse(treap.erase(4))
        self.assertEqual(treap.height(), 0)
        treap.insert(2, 30)
        treap.insert(2, 10)
        self.assertEqual(len(treap), 2)
        self.assertEqual(treap.count(2), 2)
        self.assertEqual(treap.entries(), [(2, 2)])
        self.assertEqual(treap.kth(1), 2)
        self.assertEqual(treap.kth(2), 2)
        self.assertTrue(treap.erase(2))
        self.assertEqual(len(treap), 1)
        self.assertEqual(treap.count(2), 1)
        self.assertTrue(treap.contains(2))
        self.assertIsNotNone(treap.search(2))
        self.assertTrue(treap.erase(2))
        self.assertEqual(len(treap), 0)
        self.assertEqual(treap.count(2), 0)
        self.assertFalse(treap.contains(2))

    def test_03_duplicate_keys_keep_the_first_priority(self):
        """同一个键只占一个结点：计数累加，优先级用先到者。"""
        treap = Treap()
        first = treap.insert(6, 40)
        again = treap.insert(6, 5)
        self.assertIs(again, first, "同一个键只有一个结点")
        self.assertEqual(again.priority, 40, "重复插入不改变先到者的优先级")
        self.assertEqual(treap.count(6), 2)
        self.assertEqual(len(treap), 2)
        self.assertEqual(treap.height(), 1)
        self.assertEqual(treap.entries(), [(6, 2)])
        self.assertEqual(treap.keys(), [6])
        self.assertEqual(treap.range_count(6, 6), 2)
        self.assertEqual(treap.kth(2), 6)
        self.check_invariants(treap, expected=2)
        pairs = [(4, 90), (9, 30), (4, 12), (7, 25), (9, 8), (2, 60),
                 (9, 44), (4, 3), (5, 70)]
        treap = self.build(pairs)
        counts = {}
        for key, _ in pairs:
            counts[key] = counts.get(key, 0) + 1
        self.assertEqual(treap.keys(), sorted(counts))
        self.assertEqual(treap.entries(), sorted(counts.items()))
        self.assertEqual(len(treap), len(pairs))
        self.check_invariants(treap, expected=len(pairs))
        flat = sorted(key for key, _ in pairs)
        self.assertEqual([treap.kth(index) for index in range(1, len(flat) + 1)], flat)
        self.assertEqual(treap.rank(5), sum(1 for key in flat if key < 5))

    def test_04_inorder_and_heap_order_after_many_inserts(self):
        """两百多个键建树之后：中序升序、堆序、记账都必须站得住。"""
        keys = shuffled(240)
        priorities = priority_stream(240, 3)
        treap = self.build(zip(keys, priorities))
        self.assertEqual(len(treap), 240)
        self.assertEqual(treap.keys(), sorted(keys))
        self.assertEqual(treap.root.priority, min(priorities),
                         "树根必须是优先级最小的结点")
        self.check_invariants(treap, expected=240)
        for key in keys[:40]:
            self.assertTrue(treap.erase(key))
        self.check_invariants(treap, expected=200)
        rest = sorted(keys[40:])
        self.assertEqual(treap.keys(), rest)
        self.assertEqual([treap.kth(index) for index in range(1, 201)], rest)

    def test_05_erase_merges_the_two_children(self):
        """删掉只有一个副本的键：孩子合并回树上，键集与记账不能乱。"""
        keys = shuffled(200)
        priorities = priority_stream(200, 5)
        treap = self.build(zip(keys, priorities))
        self.check_invariants(treap, expected=200)
        gone = keys[3:63]
        for key in gone:
            self.assertTrue(treap.erase(key))
        self.check_invariants(treap, expected=140)
        for key in gone:
            self.assertFalse(treap.erase(key))
            self.assertIsNone(treap.search(key))
            self.assertEqual(treap.count(key), 0)
        self.assertEqual(len(treap), 140)
        rest = sorted(set(keys) - set(gone))
        self.assertEqual(treap.keys(), rest)
        self.assertEqual(treap.entries(), [(key, 1) for key in rest])
        self.assertEqual([treap.kth(index) for index in range(1, 141)], rest)
        self.check_invariants(treap, expected=140)

    def test_06_range_count_matches_recomputation(self):
        """区间计数与按清单独立复算的元素个数逐段对齐。"""
        keys = shuffled(120)
        priorities = priority_stream(120, 6)
        pairs = []
        for index, key in enumerate(keys):
            for _ in range(1 + key % 3):
                pairs.append((key, priorities[index]))
        treap = self.build(pairs)
        flat = sorted(key for key, _ in pairs)
        self.assertEqual(len(treap), len(flat))
        spans = [(1, 1), (1, 40), (40, 40), (39, 41), (2, 3), (17, 19),
                 (60, 59), (100, 119), (120, 120), (0, 200), (3, 117)]
        for lo, hi in spans:
            self.assertEqual(treap.range_count(lo, hi),
                             sum(1 for key in flat if lo <= key <= hi),
                             "区间 [%d, %d] 里的元素个数" % (lo, hi))
        self.assertEqual(treap.range_count(121, 300), 0)
        self.assertEqual(treap.range_count(-50, 0), 0)

    def test_07_kth_and_rank_over_a_multiset(self):
        """第 k 小与秩：与按清单独立复算的升序序列逐个对齐。"""
        keys = shuffled(60)
        priorities = priority_stream(60, 7)
        pairs = []
        for index, key in enumerate(keys):
            for _ in range(1 + key % 3):
                pairs.append((key, priorities[index]))
        treap = self.build(pairs)
        flat = sorted(key for key, _ in pairs)
        self.assertEqual(len(treap), len(flat))
        for position, key in enumerate(flat, start=1):
            self.assertEqual(treap.kth(position), key, "第 %d 小" % position)
        for probe in range(0, 65):
            self.assertEqual(treap.rank(probe),
                             sum(1 for key in flat if key < probe),
                             "rank(%d)" % probe)
        with self.assertRaises(IndexError):
            treap.kth(0)
        with self.assertRaises(IndexError):
            treap.kth(len(flat) + 1)

    def test_08_height_of_hand_checked_shapes(self):
        """高度：手算的几棵树与一条单调右脊。"""
        treap = Treap()
        treap.insert(2, 10)
        self.assertEqual(treap.height(), 1)
        treap.insert(1, 20)
        treap.insert(3, 30)
        self.assertEqual(treap.height(), 2)
        self.assertEqual(treap.root.key, 2)
        self.check_invariants(treap, expected=3)
        treap.insert(4, 5)
        self.assertEqual(treap.root.key, 4, "优先级 5 的新键要一路旋到树根")
        self.assertEqual(treap.height(), 3)
        self.check_invariants(treap, expected=4)
        chain = Treap()
        for key in range(1, 121):
            chain.insert(key, key * 3)
        self.assertEqual(len(chain), 120)
        self.assertEqual(chain.height(), 120, "键与优先级同向递增会压成一条右脊")
        self.assertEqual(chain.keys(), list(range(1, 121)))
        self.assertEqual([chain.kth(index) for index in range(1, 121)],
                         list(range(1, 121)))
        self.check_invariants(chain, expected=120)

    def test_09_mixed_operations_against_a_plain_model(self):
        """插入、重复插入、删除、补插混合跑：每一步都与清单复算值对齐。"""
        keys = shuffled(150)
        priorities = priority_stream(150, 9)
        treap = Treap()
        flat = []
        for key, priority in zip(keys, priorities):
            treap.insert(key, priority)
            flat.append(key)
        self.assertEqual(len(treap), 150)
        self.check_invariants(treap, expected=150)
        for key in keys[::7]:
            treap.insert(key, 1)
            flat.append(key)
        self.assertEqual(len(treap), len(flat))
        self.check_invariants(treap, expected=len(flat))
        flat.sort()
        self.assertEqual(treap.keys(), sorted(set(keys)))
        self.assertEqual([treap.kth(index) for index in range(1, len(flat) + 1)], flat)
        removed = keys[5:55]
        for key in removed:
            self.assertTrue(treap.erase(key))
            flat.remove(key)
        self.assertEqual(len(treap), len(flat))
        self.check_invariants(treap, expected=len(flat))
        self.assertEqual(treap.keys(), sorted(set(flat)))
        for key in removed[:25]:
            treap.insert(key, 4242)
            flat.append(key)
        flat.sort()
        self.assertEqual(len(treap), len(flat))
        self.assertEqual(treap.keys(), sorted(set(flat)))
        self.assertEqual(treap.range_count(10, 90),
                         sum(1 for key in flat if 10 <= key <= 90))
        self.assertEqual(treap.rank(75), sum(1 for key in flat if key < 75))
        self.assertEqual([treap.kth(index) for index in range(1, len(flat) + 1)], flat)
        self.check_invariants(treap, expected=len(flat))


if __name__ == "__main__":
    unittest.main()
