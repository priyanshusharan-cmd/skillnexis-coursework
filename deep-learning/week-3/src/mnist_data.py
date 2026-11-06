"""MNIST (LeCun et al.) and Fashion-MNIST (Xiao et al. 2017) in the original IDX format, read as raw bytes.
Fashion-MNIST comes from Zalando's official repository; MNIST from a GitHub mirror of the original files."""
import gzip, os, urllib.request
import numpy as np
D = os.environ.get("MNIST_DIR", "/tmp/claude-0/mnist")
SRC = {"fashion": "https://raw.githubusercontent.com/zalandoresearch/fashion-mnist/master/data/fashion/", "mnist": "https://raw.githubusercontent.com/fgnt/mnist/master/"}
FILES = {"xtr": "train-images-idx3-ubyte.gz", "ytr": "train-labels-idx1-ubyte.gz", "xte": "t10k-images-idx3-ubyte.gz", "yte": "t10k-labels-idx1-ubyte.gz"}
def load(which="fashion"):
    os.makedirs(os.path.join(D, which), exist_ok=True); out = {}
    for k, f in FILES.items():
        p = os.path.join(D, which, f)
        if not os.path.exists(p): urllib.request.urlretrieve(SRC[which] + f, p)
        b = gzip.open(p).read(); out[k] = np.frombuffer(b, np.uint8, offset=16).reshape(-1, 28, 28) if k.startswith("x") else np.frombuffer(b, np.uint8, offset=8)
    assert out["xtr"].shape == (60000, 28, 28) and out["xte"].shape == (10000, 28, 28)
    return out["xtr"], out["ytr"], out["xte"], out["yte"]
FASHION = ["T-shirt/top", "Trouser", "Pullover", "Dress", "Coat", "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"]
