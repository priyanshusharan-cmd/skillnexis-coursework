# Test design: equivalence partitions and boundary values

The technique: split each input into groups (partitions) the system should treat the same, test one typical value from each, then test the values **at and next to every boundary**, because that is where off-by-one mistakes hide. Executable versions are in `bva.test.js`.

## 1. Password length
**Specification (the app's real rule):** at least 8 characters. Extra rule found by testing: at most 72 bytes (see DEF-3).

| Partition | Valid? | Values tested | Result |
| --- | --- | --- | --- |
| Empty | No | 0 | 400 |
| Too short | No | 1, 7 (just below the boundary) | 400 |
| Lower boundary | Yes | 8 | 201 |
| Just above | Yes | 9 | 201 |
| Typical long | Yes | 64 | 201 |
| Upper boundary | Yes | 72 bytes | 201 |
| Over the limit | No | 73 bytes | 400 |
| Wrong type | No | the number `12345678` | 400 |
These were run against the live API. The 73-byte row exists because of DEF-3.

## 2. Age (exercise on a reference rule; the app has no age field)
**Specification used:** a whole number from 18 to 65 inclusive.

| Partition | Valid? | Values |
| --- | --- | --- |
| Below range | No | 17 (boundary), 0, -1 |
| In range | Yes | 18 (boundary), 19, 40 (typical), 64, 65 (boundary) |
| Above range | No | 66 (boundary), 1000 |
| Not a whole number | No | 18.5 |
| Not a number | No | `'30'`, NaN, null, undefined |

## 3. Purchase quantity (exercise on a reference rule)
**Specification used:** a whole number from 1 to 10 per order.

| Partition | Valid? | Values |
| --- | --- | --- |
| Below range | No | 0 (boundary), -1 |
| In range | Yes | 1 (boundary), 2, 5 (typical), 9, 10 (boundary) |
| Above range | No | 11 (boundary), 1e9 |
| Not a whole number | No | 1.5, Infinity |
| Not a number | No | `'5'`, null |

The age and quantity tests check small validator functions written from the stated rule. They demonstrate the technique; they do not test the app.
