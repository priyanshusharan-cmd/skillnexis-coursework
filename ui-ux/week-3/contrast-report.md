# Pulse: colour contrast (WCAG 2.2 AA)

| Theme | Use | Foreground | Background | Ratio | Needs | Result |
|---|---|---|---|---:|---:|---|
| Light | Body text | `#121826` | `#FFFFFF` | 17.73:1 | 4.5:1 | pass |
| Light | Secondary text | `#485264` | `#FFFFFF` | 7.88:1 | 4.5:1 | pass |
| Light | Hint text | `#626C7D` | `#FFFFFF` | 5.30:1 | 4.5:1 | pass |
| Light | Hint text on page bg | `#626C7D` | `#F6F7F9` | 4.95:1 | 4.5:1 | pass |
| Light | Primary button label | `#FFFFFF` | `#2E5BFF` | 5.18:1 | 4.5:1 | pass |
| Light | Danger button label | `#FFFFFF` | `#C2271D` | 5.83:1 | 4.5:1 | pass |
| Light | Success badge | `#12764A` | `#E3F5EC` | 4.99:1 | 4.5:1 | pass |
| Light | Warning badge | `#8F5B00` | `#FFF3D6` | 5.20:1 | 4.5:1 | pass |
| Light | Danger badge | `#C2271D` | `#FDE8E7` | 4.96:1 | 4.5:1 | pass |
| Light | Input border (UI) | `#7A8494` | `#FFFFFF` | 3.78:1 | 3:1 | pass |
| Light | Focus ring (UI) | `#2E5BFF` | `#FFFFFF` | 5.18:1 | 3:1 | pass |
| Light | Chart 1 | `#2E5BFF` | `#FFFFFF` | 5.18:1 | 3:1 | pass |
| Light | Chart 2 | `#0E8A83` | `#FFFFFF` | 4.22:1 | 3:1 | pass |
| Light | Chart 3 | `#B86E00` | `#FFFFFF` | 3.99:1 | 3:1 | pass |
| Light | Chart 4 | `#8E4FC6` | `#FFFFFF` | 5.14:1 | 3:1 | pass |
| Dark | Body text | `#EEF1F6` | `#151B24` | 15.28:1 | 4.5:1 | pass |
| Dark | Secondary text | `#B6BFCC` | `#151B24` | 9.32:1 | 4.5:1 | pass |
| Dark | Hint text | `#959FAE` | `#151B24` | 6.46:1 | 4.5:1 | pass |
| Dark | Primary button label | `#0D1117` | `#6E8EFF` | 6.29:1 | 4.5:1 | pass |
| Dark | Success badge | `#4CC38A` | `#12301F` | 6.46:1 | 4.5:1 | pass |
| Dark | Warning badge | `#F2B84B` | `#33270E` | 8.16:1 | 4.5:1 | pass |
| Dark | Danger badge | `#FF7B72` | `#3A1714` | 6.34:1 | 4.5:1 | pass |
| Dark | Input border (UI) | `#7D8899` | `#151B24` | 4.82:1 | 3:1 | pass |
| Dark | Focus ring (UI) | `#93ABFF` | `#151B24` | 7.83:1 | 3:1 | pass |
| Dark | Chart 1 | `#6E8EFF` | `#151B24` | 5.75:1 | 3:1 | pass |
| Dark | Chart 2 | `#13A8A0` | `#151B24` | 5.88:1 | 3:1 | pass |
| Dark | Chart 3 | `#F59E0B` | `#151B24` | 8.05:1 | 3:1 | pass |
| Dark | Chart 4 | `#B48AE6` | `#151B24` | 6.36:1 | 3:1 | pass |

28/28 pass. First draft failed two chart colours on white (teal 2.94:1, amber 2.15:1); they were darkened for the light theme (4.22:1, 3.99:1) and the bright originals kept for dark mode, where they reach 5.9:1 and 8.1:1.

## Automated audit (axe-core 4.10, WCAG 2.2 AA)
A follow-up axe-core run found what the table above missed: the active navigation label (`primary` on `primary-soft`, 4.46:1) and four avatar colours with white initials (2.8–4.4:1). Fixed: the active label and ghost-button hover now use `primary-strong` (#1D44D6, 6.35:1 on the tint), and the avatar palette was darkened (all ≥ 4.5:1). The prototype and component library now report **0 violations**.
