Test: days 21-28 (23,040 room-minutes, never seen in training). "Still" = someone present but asleep or without motion for > 10 min (4,915 minutes).

| Model | Accuracy | F1 | Recall while people sit still | Empty room called occupied |
|---|---:|---:|---:|---:|
| Motion in last 10 min (PIR timer) | 0.811 | 0.744 | 0.32 | 7.2% |
| Logistic regression | 0.900 | 0.883 | 0.87 | 9.6% |
| Random forest (200 trees) | 0.976 | 0.971 | 0.96 | 2.5% |
| MLP float32 | 0.979 | 0.975 | 0.97 | 2.1% |
| **MLP int8 (TFLite Micro, ESP32)** | 0.979 | 0.975 | 0.97 | 2.0% |

MLP: 649 parameters, int8 flatbuffer **4,112 bytes** (fits easily in ESP32 flash; tensor arena 2 KB), 13 µs per inference on this PC.
Most useful features (random forest): since_motion 0.20, bedroom 0.15, motion_30 0.14, sound_mean5 0.13, motion_15 0.09.
