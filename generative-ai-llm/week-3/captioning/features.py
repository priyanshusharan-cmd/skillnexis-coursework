"""Image captioning, step 1: encode every Flickr8k image once with a pretrained CNN (MobileNetV2, ImageNet weights
from the official Keras release file): the 5x5x1280 grid of the last feature map at 160x160 input, kept as 25
'visual tokens' so the decoder can attend to regions.
Data: Flickr8k (Hodosh, Young & Hockenmaier 2013): 8,091 photos x 5 human captions; the official 6k/1k/1k split.
    python features.py -> cache/features.npz"""
import os, numpy as np
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
import keras
from PIL import Image
IMG = os.environ.get("FLICKR_IMG", "/tmp/claude-0/flickr/img/Flicker8k_Dataset"); TXT = os.environ.get("FLICKR_TXT", "/tmp/claude-0/flickr/text")
os.makedirs("cache", exist_ok=True)
names = sorted(f for f in os.listdir(IMG) if f.endswith(".jpg"))
base = keras.applications.MobileNetV2(include_top=False, weights=None, input_shape=(160, 160, 3)); base.load_weights(os.environ.get("MNV2_WEIGHTS", "/tmp/claude-0/mobilenetv2_notop.h5"))
F = np.zeros((len(names), 25, 1280), np.float16)
for k in range(0, len(names), 64):
    x = np.stack([np.asarray(Image.open(os.path.join(IMG, n)).convert("RGB").resize((160, 160))) for n in names[k:k + 64]]).astype("float32") / 127.5 - 1
    F[k:k + 64] = base.predict(x, verbose=0).reshape(len(x), 25, 1280)
    if k % 1280 == 0: print(k, flush=True)
np.savez("cache/features.npz", names=np.array(names), feats=F); print(F.shape)
