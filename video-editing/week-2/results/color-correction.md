| Clip | Problem | Correction (ffmpeg) | Mean luma before → after (original) | Luma range before → after (original) |
|---|---|---|---|---|
| coffee | Underexposed | `eq=gamma=2.2:brightness=0.12:contrast=1.15:saturation=1.1` | 25 → **104** (103) | 0–56 → **62–147** (35–162) |
| rocket | Overexposed | `eq=gamma=0.45:brightness=-0.2:contrast=1.45` | 174 → **73** (71) | 160–190 → **51–101** (50–97) |
| astronaut | Colour cast + underexposed | `colorbalance=rs=0.15:gs=-0.05:bs=-0.25:rm=0.12:bm=-0.18,eq=gamma=1.4:saturation=1.05` | 94 → **123** (118) | 9–178 → **45–198** (16–198) |
