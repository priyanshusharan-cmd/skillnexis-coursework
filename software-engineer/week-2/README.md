# Software Engineer — Week 2: DSA, Design Patterns & Testing

Python 3.10+, standard library only. Tests use pytest and pytest-cov.

| Brief item | Where | Notes |
| --- | --- | --- |
| **5 data structures from scratch**: stack, queue, linked list, BST, hash map | `structures/` | Stack on linked nodes; queue on a growable circular buffer; singly linked list with a tail pointer and in-place reverse; BST with iterative insert/search/delete (all three delete cases) so a sorted-input tree of 5,000 nodes cannot overflow the stack; hash map with separate chaining that doubles above a 0.75 load factor. |
| **10 algorithm problems: 3 easy, 4 medium, 3 hard** | `algorithms/problems.py` | Easy: Two Sum (1), Valid Parentheses (20), Best Time to Buy and Sell Stock (121). Medium: Longest Substring Without Repeating Characters (3), 3Sum (15), Coin Change (322), Number of Islands (200). Hard: Trapping Rain Water (42), Median of Two Sorted Arrays (4) in O(log min(m, n)), Minimum Window Substring (76). Each states its complexity. |
| **Unit tests, 90%+ coverage** | `tests/` | **86 tests, 99% branch coverage**, enforced by `fail_under = 90` in `pyproject.toml`. Report: `results/coverage.txt`. 3Sum and the median solution are also checked against brute force on random inputs. |
| **3 design patterns: Singleton, Factory, Observer** | `patterns/` | Thread-safe Singleton metaclass (a 16-thread test confirms one instance), self-registering Factory (new kinds added without editing it), Observer with unsubscribe. |
| **Mini project: library management system** | `library/` | See below. |

## Library management system

| Pattern | Class | Role |
| --- | --- | --- |
| **Factory** | `books.BookFactory` | Builds `PrintedBook`, `EBook` or `AudioBook` from a kind name or a database row, and validates title, author, copies and the ISBN-13 check digit. Book CRUD in `service.py` goes through it. |
| **Observer** | `events.EventBus` + `MemberNotifier`, `AuditLog`, `LowStockAlert` | The service publishes `book_added`, `book_borrowed`, `book_returned`, `waitlisted`, `book_available` and others, and never knows who is listening. When a waitlisted book comes back, the first member in line is notified. |
| **Singleton** | `db.Database` | One SQLite connection per process, with foreign keys on and checks in the schema (`available` stays between 0 and `copies`). |

Rules enforced: no duplicate ISBNs or member emails; a member can't borrow the same book twice; copies can't be cut below the number on loan; a book can't be deleted while it is on loan.

```sh
cd software-engineer/week-2
python -m library.cli add printed "Clean Code" "Robert C. Martin" 9780132350884 --copies 1 --extra 464
python -m library.cli member "Priya Rao" priya@example.com
python -m library.cli borrow 1 1
#   Loan 1 created
#     -> notify priya@example.com: Hi Priya Rao, you borrowed 'Clean Code'. Enjoy!
#     !! Last copy of 'Clean Code' is out
python -m library.cli list --search code
python -m library.cli return 1
python -m library.cli --help
```

## Run the tests

```sh
pip install pytest pytest-cov
python -m pytest --cov        # fails if coverage drops below 90%
```

## Note on the algorithm problems
They were solved and tested locally, not submitted on LeetCode or HackerRank (that needs a personal account). The tests use each problem's published examples plus edge cases.
