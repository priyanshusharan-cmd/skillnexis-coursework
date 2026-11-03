"""10 classic interview problems: 3 easy, 4 medium, 3 hard (LeetCode numbering in brackets).
Each function states its time and space complexity."""
from collections import Counter, deque


# ---------------------------------------------------------------- easy
def two_sum(nums, target):
    """[1] Indices of the two numbers that add to target. O(n) time, O(n) space."""
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []


def valid_parentheses(s):
    """[20] Brackets close in the right order. O(n) time, O(n) space."""
    pairs, stack = {")": "(", "]": "[", "}": "{"}, []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
    return not stack


def max_profit(prices):
    """[121] Best single buy-then-sell profit. O(n) time, O(1) space."""
    best, low = 0, float("inf")
    for p in prices:
        low = min(low, p)
        best = max(best, p - low)
    return best


# ---------------------------------------------------------------- medium
def length_of_longest_substring(s):
    """[3] Longest substring without repeating characters. Sliding window, O(n) time."""
    last, start, best = {}, 0, 0
    for i, ch in enumerate(s):
        if last.get(ch, -1) >= start:
            start = last[ch] + 1
        last[ch] = i
        best = max(best, i - start + 1)
    return best


def three_sum(nums):
    """[15] All unique triplets summing to zero. Sort + two pointers, O(n^2) time."""
    nums, out = sorted(nums), []
    for i in range(len(nums) - 2):
        if i and nums[i] == nums[i - 1]:
            continue
        lo, hi = i + 1, len(nums) - 1
        while lo < hi:
            s = nums[i] + nums[lo] + nums[hi]
            if s < 0:
                lo += 1
            elif s > 0:
                hi -= 1
            else:
                out.append([nums[i], nums[lo], nums[hi]])
                while lo < hi and nums[lo] == nums[lo + 1]:
                    lo += 1
                lo, hi = lo + 1, hi - 1
    return out


def coin_change(coins, amount):
    """[322] Fewest coins to make amount, or -1. Bottom-up DP, O(amount * len(coins)) time."""
    INF = amount + 1
    dp = [0] + [INF] * amount
    for a in range(1, amount + 1):
        for c in coins:
            if c <= a and dp[a - c] + 1 < dp[a]:
                dp[a] = dp[a - c] + 1
    return dp[amount] if dp[amount] != INF else -1


def num_islands(grid):
    """[200] Count 4-connected groups of '1'. BFS, O(rows * cols) time. Does not modify grid."""
    if not grid:
        return 0
    rows, cols, seen, count = len(grid), len(grid[0]), set(), 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "1" and (r, c) not in seen:
                count += 1
                seen.add((r, c))
                q = deque([(r, c)])
                while q:
                    y, x = q.popleft()
                    for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                        if 0 <= ny < rows and 0 <= nx < cols and grid[ny][nx] == "1" and (ny, nx) not in seen:
                            seen.add((ny, nx))
                            q.append((ny, nx))
    return count


# ---------------------------------------------------------------- hard
def trap(height):
    """[42] Water trapped between bars. Two pointers, O(n) time, O(1) space."""
    lo, hi, left_max, right_max, water = 0, len(height) - 1, 0, 0, 0
    while lo < hi:
        if height[lo] < height[hi]:
            left_max = max(left_max, height[lo])
            water += left_max - height[lo]
            lo += 1
        else:
            right_max = max(right_max, height[hi])
            water += right_max - height[hi]
            hi -= 1
    return water


def find_median_sorted_arrays(a, b):
    """[4] Median of two sorted arrays. Binary search on the partition, O(log(min(m, n)))."""
    if len(a) > len(b):
        a, b = b, a
    m, n = len(a), len(b)
    if m + n == 0:
        raise ValueError("both arrays are empty")
    lo, hi, half = 0, m, (m + n + 1) // 2
    while lo <= hi:
        i = (lo + hi) // 2
        j = half - i
        a_left = a[i - 1] if i > 0 else float("-inf")
        a_right = a[i] if i < m else float("inf")
        b_left = b[j - 1] if j > 0 else float("-inf")
        b_right = b[j] if j < n else float("inf")
        if a_left <= b_right and b_left <= a_right:
            if (m + n) % 2:
                return float(max(a_left, b_left))
            return (max(a_left, b_left) + min(a_right, b_right)) / 2
        if a_left > b_right:
            hi = i - 1
        else:
            lo = i + 1
    raise ValueError("inputs must be sorted")  # pragma: no cover - only reached on unsorted input


def min_window(s, t):
    """[76] Shortest substring of s containing every character of t (with counts). O(|s| + |t|)."""
    if not t or not s:
        return ""
    need, missing = Counter(t), len(t)
    start = best_start = 0
    best_len = float("inf")
    for end, ch in enumerate(s, 1):
        if need[ch] > 0:
            missing -= 1
        need[ch] -= 1
        if missing == 0:
            while need[s[start]] < 0:  # drop surplus characters from the left
                need[s[start]] += 1
                start += 1
            if end - start < best_len:
                best_start, best_len = start, end - start
            need[s[start]] += 1  # give up the first needed char and keep searching
            missing += 1
            start += 1
    return "" if best_len == float("inf") else s[best_start:best_start + best_len]


PROBLEMS = {
    "easy": [two_sum, valid_parentheses, max_profit],
    "medium": [length_of_longest_substring, three_sum, coin_change, num_islands],
    "hard": [trap, find_median_sorted_arrays, min_window],
}
