import random

import pytest

from structures import BST, HashMap, LinkedList, Queue, Stack


class TestStack:
    def test_lifo_order_and_len(self):
        s = Stack([1, 2])
        s.push(3)
        assert len(s) == 3 and s.peek() == 3
        assert [s.pop(), s.pop(), s.pop()] == [3, 2, 1]
        assert s.is_empty()

    def test_iter_is_top_to_bottom_and_repr_bottom_to_top(self):
        s = Stack("abc")
        assert list(s) == ["c", "b", "a"]
        assert repr(s) == "Stack(['a', 'b', 'c'])"

    @pytest.mark.parametrize("op", ["pop", "peek"])
    def test_empty_raises(self, op):
        with pytest.raises(IndexError):
            getattr(Stack(), op)()


class TestQueue:
    def test_fifo_and_growth_past_capacity(self):
        q = Queue(capacity=2)
        for i in range(10):
            q.enqueue(i)
        assert len(q) == 10 and q.peek() == 0
        assert [q.dequeue() for _ in range(10)] == list(range(10))
        assert q.is_empty()

    def test_wraparound_keeps_order(self):
        q = Queue([1, 2, 3], capacity=4)
        q.dequeue(), q.dequeue()
        q.enqueue(4), q.enqueue(5), q.enqueue(6)  # wraps around the end of the buffer, then grows
        assert list(q) == [3, 4, 5, 6] and repr(q) == "Queue([3, 4, 5, 6])"

    @pytest.mark.parametrize("op", ["dequeue", "peek"])
    def test_empty_raises(self, op):
        with pytest.raises(IndexError):
            getattr(Queue(), op)()

    def test_bad_capacity(self):
        with pytest.raises(ValueError):
            Queue(capacity=0)


class TestLinkedList:
    def test_append_prepend_insert_getitem(self):
        ll = LinkedList([2, 4])
        ll.prepend(1)
        ll.insert(2, 3)
        ll.insert(4, 5)
        ll.insert(0, 0)
        assert list(ll) == [0, 1, 2, 3, 4, 5]
        assert ll[0] == 0 and ll[-1] == 5 and len(ll) == 6

    def test_remove_head_middle_tail_and_find(self):
        ll = LinkedList([1, 2, 3, 4])
        ll.remove(1)
        ll.remove(3)
        ll.remove(4)
        assert list(ll) == [2] and ll.find(2) == 0 and ll.find(9) == -1
        ll.append(7)  # tail pointer still correct after removing the old tail
        assert list(ll) == [2, 7]

    def test_reverse_and_pop_front(self):
        ll = LinkedList(range(5))
        ll.reverse()
        assert list(ll) == [4, 3, 2, 1, 0]
        ll.append(-1)
        assert ll[-1] == -1
        assert [ll.pop_front() for _ in range(6)] == [4, 3, 2, 1, 0, -1]
        ll.append(9)  # works after emptying
        assert list(ll) == [9]

    def test_errors(self):
        ll = LinkedList()
        with pytest.raises(IndexError):
            ll.pop_front()
        with pytest.raises(IndexError):
            ll[0]
        with pytest.raises(IndexError):
            ll.insert(2, "x")
        with pytest.raises(ValueError):
            ll.remove("x")

    def test_repr(self):
        assert repr(LinkedList([1, 2])) == "LinkedList([1 -> 2])"


class TestBST:
    def test_insert_search_update_and_sorted_iteration(self):
        t = BST()
        for k in [50, 30, 70, 20, 40, 60, 80]:
            t.insert(k, str(k))
        t.insert(40, "forty")
        assert t.search(40) == "forty" and t.search(99, "none") == "none"
        assert list(t) == [20, 30, 40, 50, 60, 70, 80] and len(t) == 7
        assert 60 in t and 65 not in t
        assert (t.min(), t.max(), t.height()) == (20, 80, 2)

    @pytest.mark.parametrize("key", [20, 30, 50, 70])  # leaf, two children, root, two children
    def test_delete_cases(self, key):
        t = BST()
        for k in [50, 30, 70, 20, 40, 60, 80]:
            t.insert(k)
        t.delete(key)
        expected = sorted({50, 30, 70, 20, 40, 60, 80} - {key})
        assert list(t) == expected and len(t) == 6

    def test_delete_one_child_and_root_with_one_child(self):
        t = BST()
        for k in [10, 5, 3]:
            t.insert(k)
        t.delete(5)
        assert list(t) == [3, 10]
        t.delete(10)
        assert list(t) == [3]
        t.delete(3)
        assert len(t) == 0 and t.height() == -1

    def test_matches_sorted_on_random_data(self):
        rng = random.Random(7)
        keys = rng.sample(range(10_000), 500)
        t = BST()
        for k in keys:
            t.insert(k)
        for k in keys[:250]:
            t.delete(k)
        assert list(t) == sorted(keys[250:])

    def test_degenerate_tree_does_not_recurse(self):
        t = BST()
        for k in range(5000):  # sorted input: height 4999
            t.insert(k)
        assert t.height() == 4999 and list(t)[-1] == 4999

    def test_errors(self):
        t = BST()
        with pytest.raises(KeyError):
            t.delete(1)
        with pytest.raises(ValueError):
            t.min()
        with pytest.raises(ValueError):
            t.max()


class TestHashMap:
    def test_put_get_overwrite_delete(self):
        m = HashMap()
        m["a"] = 1
        m.put("b", 2)
        m["a"] = 3
        assert m["a"] == 3 and m.get("b") == 2 and m.get("z", 0) == 0 and len(m) == 2
        del m["a"]
        assert "a" not in m and len(m) == 1

    def test_resizes_and_keeps_everything(self):
        m = HashMap(capacity=2)
        for i in range(100):
            m[i] = i * i
        assert m.capacity >= 128 and len(m) == 100
        assert all(m[i] == i * i for i in range(100))
        assert sorted(m) == list(range(100)) and sorted(m.items())[3] == (3, 9)

    def test_collisions_in_one_bucket(self):
        class SameHash:
            def __init__(self, n):
                self.n = n

            def __hash__(self):
                return 1

            def __eq__(self, other):
                return self.n == other.n

        m = HashMap(capacity=64)
        keys = [SameHash(i) for i in range(10)]
        for k in keys:
            m[k] = k.n
        m.delete(keys[4])
        assert [m.get(k) for k in keys] == [0, 1, 2, 3, None, 5, 6, 7, 8, 9]

    def test_errors(self):
        m = HashMap()
        with pytest.raises(KeyError):
            m["missing"]
        with pytest.raises(KeyError):
            m.delete("missing")
        with pytest.raises(ValueError):
            HashMap(capacity=0)
