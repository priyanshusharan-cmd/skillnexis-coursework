# Hisaab: developer handoff

Everything a developer needs to build the screens without guessing. Source of truth: [design/tokens.css](../design/tokens.css) and
[design/hisaab.py](../design/hisaab.py). Annotated screens: [exports/spec/](../exports/spec/).
All 18 screens are exported at 2× (780 × 1688) in [exports/screens/](../exports/screens/).

## 1. Tokens
| Group | Token | Value | Use |
|---|---|---|---|
| Colour | `brand-600` | `#0F766E` | Primary buttons, active tab, links |
| | `brand-500` | `#0D9488` | Focus ring, icons on white (UI only, 3.7:1) |
| | `brand-100` | `#D5F5EF` | Tinted cards, icon tiles, highlight of a new row |
| | `brand-900` | `#0B3B37` | Balance hero card |
| | `owe-700` / `owe-100` | `#B42318` / `#FDECEA` | "You owe": text / tint |
| | `owed-700` / `owed-100` | `#067647` / `#DCFAE6` | "You are owed", success |
| | `amber-700` / `amber-100` | `#B54708` / `#FEF0C7` | Reminders, insights |
| | `ink-900 / 700 / 500` | `#101828 / #344054 / #5D6B82` | Text, secondary text, hints and input borders |
| | `line` | `#E4E7EC` | Decorative dividers only |
| | `surface` / `canvas` | `#FFFFFF` / `#F5F8F7` | Screen / subtle panels |
| Type | caption | Inter 500 12/16 | Meta lines, tab labels |
| | label | Inter 600 14/20 | Buttons, list titles, pills |
| | body | Inter 400 16/24 | Paragraphs |
| | title | Inter Display 600 20/28 | App bar, section titles |
| | headline | Inter Display 700 25/32 | Screen titles |
| | display | Inter Display 700 31/38 | Onboarding titles, balances |
| | amount | Inter Display 800 52/60 | Amount entry, payment |
| Space | `s1…s8` | 4, 8, 12, 16, 24, 32, 48, 64 | Screen gutter 16; card padding 14–16; section gap 20–24 |
| Radius | `sm / md / lg / pill` | 8 / 12 / 20 / 999 | Inputs 12, cards 16–20, chips pill, FAB 20 |

Contrast: [contrast.md](contrast.md), 15/15 pairs pass WCAG 2.2 AA.

## 2. Components
| Component | Size | Spec | States |
|---|---|---|---|
| Primary button | h 52, full width in bottom bar | `brand-600`, label 14/20 600 white, r 12 | pressed: 0.97 scale; disabled: 45 % opacity; loading: spinner, same width |
| Secondary (tonal) | h 44–52 | `brand-100` bg, `brand-600` label | as primary |
| Input | h 52 | border 1.5 `ink-500` (≥ 3:1), r 12, padding 14; focus border 2 `brand-600` | error: border `owe-700` + message below |
| List row | min h 68 | padding 12/16, gap 14, icon tile 44 r 14, divider `line` | pressed: `canvas` bg; new item: `brand-100` bg for 2 s |
| Amount pill | h 22 | caption 12/16 600, r pill, `owe`/`owed` tint | always includes the words "you owe" / "owes you" |
| Chip | h 36 | border 1 `line`, label 14/20 | selected: `ink-900` bg, white text |
| Segmented control | h 40 | `canvas` track, p 4, r 12; selected segment white with shadow | — |
| FAB | 60 × 60, r 20 | `brand-600`, icon 28 white, shadow 0 8 20 rgba(15,118,110,.4); 20 px from the right, 110 px from the bottom | hidden while the keyboard is open |
| Tab bar | h 84 (incl. home indicator) | 5 items, icon 24, caption 12/16; active `brand-600` | badge: 18 px, `owe-700` |
| Number keypad | key h 56, 3 columns, gap 6 | Inter Display 600 24 | pressed: `canvas` circle ripple |

## 3. Behaviour
* **Amounts** are stored in paise (integers). The display uses Indian grouping (₹1,24,000) and never shows decimals for whole rupees.
* **Equal split rounding**: remainders go to the payer. ₹100 split 3 ways is ₹33 + ₹33 + ₹34, with the payer taking ₹34, and the UI shows "Totals ₹100 ✓".
* **Simplify debts**: a minimum-cash-flow algorithm over net balances. It runs only within a group and never changes totals; the UI shows "5 payments → 3".
* **Settle with UPI**: build a `upi://pay?pa=<vpa>&pn=<name>&am=<amount>&tn=Hisaab%20<group>&cu=INR` intent and open the system chooser.
  * Mark the payment *pending* until the payer confirms or the UPI app reports success, because UPI intents don't reliably return status.
  * Hisaab never handles PINs or money.
* **Undo**: deleting or saving an expense shows "Undo" for 10 s, then the change syncs.
* **Reminders** are sent only by the user (WhatsApp share sheet), never automatically.
* **Motion**:
  * forward navigation: new screen slides in from the right, 380 ms `cubic-bezier(.2,.8,.2,1)`; back reverses it;
  * success screens rise and fade in;
  * reduced-motion users get instant changes.
* **Accessibility**:
  * hit targets ≥ 44 pt;
  * every icon button has a label ("Add expense", "Back");
  * amounts are read as "you owe 120 rupees", not "minus 120";
  * Dynamic Type and Android font scale reflow the rows (no fixed heights on text).

## 4. Assets ([assets/](assets/))
| Asset | Files |
|---|---|
| App icon | `app-icon.svg` (master), `app-icon-1x.png` 60, `-2x` 120, `-3x` 180, `-store` 1024 |
| Icons | 19 SVGs in `assets/icons/` on a 24 × 24 grid, 1.8 stroke, round caps, `currentColor` (tint them with CSS or a vector drawable) |
| Illustrations | inline SVG in `hisaab.py` (`ART1`–`ART3`); export them from `exports/screens/0{1,2,3}-*.png` if raster is needed |

## 5. Screen inventory
| # | Screen | Entry from | Exits to |
|---|---|---|---|
| 01–03 | Onboarding (value, how it works, settle) | first launch | Sign in (or Skip) |
| 04 | Sign in (phone) | onboarding | Home (after OTP) |
| 05 | Home | tab | Group, Settle, Remind, New group |
| 06 | Group | Home | Expense detail, Balances, Add (FAB) |
| 07 | Add expense | FAB or tab | Split options, Saved |
| 08 | Split options | Add | Add |
| 09 | Expense saved (group, with new row highlighted) | Add | Home / Group |
| 10 | Expense detail | Group row | Edit |
| 11 | Balances & simplify | Group | Settle up |
| 12 | Settle up | Home, Balances | UPI app → Payment success |
| 13 | Payment success | UPI | Home, or settle the next debt |
| 14 | Create group & invite | Home | Group |
| 15 | Activity | tab | — |
| 16 | Monthly insights | You | — |
| 17 | You (profile) | tab | Insights, Reminders, Settings |
| 18 | Friendly reminder | Home | WhatsApp |
