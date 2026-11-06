"""CIFAR-10 (Krizhevsky 2009) from the binary distribution (6 files of 10,000 records: 1 label byte + 3072 pixel bytes).
The files are read as raw bytes (no pickle), and each was checked against its Git LFS SHA-256 when downloaded."""
import os, numpy as np
D = os.environ.get("CIFAR_DIR", "/tmp/claude-0/cifar")
CLASSES = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
def _read(f):
    a = np.fromfile(os.path.join(D, f), np.uint8).reshape(-1, 3073); return a[:, 1:].reshape(-1, 3, 32, 32).transpose(0, 2, 3, 1), a[:, 0].astype(np.int64)
def load():
    xs, ys = zip(*[_read(f"data_batch_{i}.bin") for i in range(1, 6)]); xt, yt = _read("test_batch.bin")
    return np.concatenate(xs), np.concatenate(ys), xt, yt
