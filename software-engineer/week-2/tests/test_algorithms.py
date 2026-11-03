import itertools
import random
import statistics

import pytest

from algorithms import problems as p


def test_ten_problems_split_3_4_3():
    assert [len(p.PROBLEMS[k]) for k in ("easy", "medium", "hard")] == [3, 4, 3]


@pytest.mark.parametrize("nums,target,expected", [([2, 7, 11, 15], 9, [0, 1]), ([3, 2, 4], 6, [1, 2]), ([3, 3], 6, [0, 1]), ([1, 2], 7, [])])
def test_two_sum(nums, target, expected):
    assert p.two_sum(nums, target) == expected


@pytest.mark.parametrize("s,ok", [("()[]{}", True), ("([{}])", True), ("(]", False), ("(", False), (")", False), ("", True), ("a(b)c", True)])
def test_valid_parentheses(s, ok):
    assert p.valid_parentheses(s) is ok


@pytest.mark.parametrize("prices,best", [([7, 1, 5, 3, 6, 4], 5), ([7, 6, 4, 3, 1], 0), ([], 0)])
def test_max_profit(prices, best):
    assert p.max_profit(prices) == best


@pytest.mark.parametrize("s,n", [("abcabcbb", 3), ("bbbbb", 1), ("pwwkew", 3), ("", 0), ("abba", 2), ("dvdf", 3)])
def test_longest_substring(s, n):
    assert p.length_of_longest_substring(s) == n


def test_three_sum_examples_and_brute_force():
    assert p.three_sum([-1, 0, 1, 2, -1, -4]) == [[-1, -1, 2], [-1, 0, 1]]
    assert p.three_sum([0, 0, 0, 0]) == [[0, 0, 0]]
    rng = random.Random(3)
    for _ in range(50):
        nums = [rng.randint(-6, 6) for _ in range(rng.randint(0, 12))]
        brute = sorted({tuple(sorted(c)) for c in itertools.combinations(nums, 3) if sum(c) == 0})
        assert sorted(map(tuple, p.three_sum(nums))) == brute


@pytest.mark.parametrize("coins,amount,n", [([1, 2, 5], 11, 3), ([2], 3, -1), ([1], 0, 0), ([186, 419, 83, 408], 6249, 20)])
def test_coin_change(coins, amount, n):
    assert p.coin_change(coins, amount) == n


def test_num_islands_and_grid_untouched():
    grid = [list("11000"), list("11000"), list("00100"), list("00011")]
    copy = [row[:] for row in grid]
    assert p.num_islands(grid) == 3 and grid == copy
    assert p.num_islands([]) == 0 and p.num_islands([list("111"), list("101"), list("111")]) == 1


@pytest.mark.parametrize("h,w", [([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1], 6), ([4, 2, 0, 3, 2, 5], 9), ([], 0), ([3], 0)])
def test_trap(h, w):
    assert p.trap(h) == w


def test_median_examples_and_random():
    assert p.find_median_sorted_arrays([1, 3], [2]) == 2.0
    assert p.find_median_sorted_arrays([1, 2], [3, 4]) == 2.5
    assert p.find_median_sorted_arrays([], [1]) == 1.0
    rng = random.Random(5)
    for _ in range(200):
        a = sorted(rng.randint(-50, 50) for _ in range(rng.randint(0, 9)))
        b = sorted(rng.randint(-50, 50) for _ in range(rng.randint(0 if a else 1, 9)))
        assert p.find_median_sorted_arrays(a, b) == statistics.median(a + b)
    with pytest.raises(ValueError):
        p.find_median_sorted_arrays([], [])


@pytest.mark.parametrize("s,t,w", [("ADOBECODEBANC", "ABC", "BANC"), ("a", "a", "a"), ("a", "aa", ""), ("", "a", ""), ("ab", "", ""), ("aaflslflsldkalskaaa", "aaa", "aaa")])
def test_min_window(s, t, w):
    assert p.min_window(s, t) == w
