# Colour contrast (computed from tokens.json)

| App | Text / element | On | Used for | Ratio | WCAG 2.2 AA |
|---|---|---|---|---:|---|
| Haat (e-commerce) | `ink-900` | `surface` | body | 17.17:1 | pass (AAA) |
| Haat (e-commerce) | `ink-700` | `surface` | body | 9.47:1 | pass (AAA) |
| Haat (e-commerce) | `ink-500` | `surface` | body | 5.57:1 | pass |
| Haat (e-commerce) | `ink-900` | `canvas` | body | 15.96:1 | pass (AAA) |
| Haat (e-commerce) | `ink-500` | `canvas` | caption | 5.18:1 | pass |
| Haat (e-commerce) | `surface` | `brand-600` | label | 5.96:1 | pass |
| Haat (e-commerce) | `brand-600` | `surface` | label | 5.96:1 | pass |
| Haat (e-commerce) | `brand-600` | `brand-100` | label | 4.99:1 | pass |
| Haat (e-commerce) | `leaf-700` | `leaf-100` | label | 5.47:1 | pass |
| Haat (e-commerce) | `danger-700` | `surface` | caption | 6.54:1 | pass |
| Haat (e-commerce) | `warn-700` | `surface` | caption | 5.93:1 | pass |
| Haat (e-commerce) | `line` | `surface` | decorative | 1.30:1 | pass |
| Haat (e-commerce) | `brand-500` | `surface` | ui | 3.99:1 | pass |
| Haat (e-commerce) | `ink-500` | `surface` | ui | 5.57:1 | pass |
| Circle (social) | `ink-900` | `surface` | body | 18.12:1 | pass (AAA) |
| Circle (social) | `ink-700` | `surface` | body | 9.96:1 | pass (AAA) |
| Circle (social) | `ink-500` | `surface` | caption | 5.65:1 | pass |
| Circle (social) | `ink-500` | `canvas` | caption | 5.26:1 | pass |
| Circle (social) | `surface` | `brand-600` | label | 7.00:1 | pass |
| Circle (social) | `brand-600` | `surface` | label | 7.00:1 | pass |
| Circle (social) | `brand-600` | `brand-100` | label | 5.92:1 | pass |
| Circle (social) | `accent-600` | `surface` | label | 6.53:1 | pass |
| Circle (social) | `surface` | `accent-600` | label | 6.53:1 | pass |
| Circle (social) | `online` | `surface` | ui | 5.30:1 | pass |
| Circle (social) | `brand-500` | `surface` | ui | 5.04:1 | pass |
| Circle (social) | `ink-500` | `surface` | ui | 5.65:1 | pass |
| Circle (social) | `line` | `surface` | decorative | 1.26:1 | pass |

27/27 pairs pass. Normal text needs 4.5:1, large text and UI parts (borders, icons, focus rings) 3:1.
`line` (1.3:1) is only used for decorative dividers between list rows, which WCAG 1.4.11 exempts; anything that identifies a control (input borders, checkboxes, outline buttons) uses `ink-500` or `brand-600`, checked above at >= 3:1.
