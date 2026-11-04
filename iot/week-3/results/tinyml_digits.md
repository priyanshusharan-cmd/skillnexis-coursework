| Model | Test accuracy | Size |
|---|---:|---:|
| Keras float32 | 0.980 | 38.8 KB of weights |
| **TFLite int8** | **0.978** | **15.3 KB** file |

Parameters: 9,930. int8 inference: 22 µs per image on this PC (single thread). Most common confusion: 4 read as 9 (2 times). Test set: 450 images, never seen in training.
