"""Task 4: what has the CNN learned? (1) first-layer filters, (2) feature maps of every stage for one image, and
(3) Grad-CAM heat maps (Selvaraju et al. 2017): the gradient of the predicted class score with respect to the last
convolutional feature map, averaged per channel, weights that map; the ReLU of the weighted sum shows where the
evidence is.   python src/gradcam.py -> results/filters.png, results/feature_maps.png, results/gradcam.png"""
import os, sys
import numpy as np
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
import tensorflow as tf, keras
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
from cifar_data import load, CLASSES
def gradcam(model, img, layer, cls=None):
    gm = keras.Model(model.inputs, [model.get_layer(layer).output, model.output])
    with tf.GradientTape() as t:
        fmap, logits = gm(img[None].astype("float32")); c = int(tf.argmax(logits[0])) if cls is None else cls; score = logits[:, c]
    g = t.gradient(score, fmap)[0]; w = tf.reduce_mean(g, axis=(0, 1)); cam = tf.nn.relu(tf.reduce_sum(fmap[0] * w, -1)).numpy()
    cam = cam / (cam.max() + 1e-8); return tf.image.resize(cam[..., None], img.shape[:2]).numpy()[..., 0], c, tf.nn.softmax(logits[0]).numpy()
if __name__ == "__main__":
    m = keras.models.load_model(sys.argv[1] if len(sys.argv) > 1 else "results/cifar_cnn.keras")
    _, _, XT, YT = load(); convs = [l for l in m.layers if isinstance(l, keras.layers.Conv2D)]; adds = [l.name for l in m.layers if isinstance(l, keras.layers.ReLU)]
    k = convs[0].get_weights()[0]; k = (k - k.min()) / (k.max() - k.min()); n = k.shape[-1]; cols = 8
    fig, axs = plt.subplots(int(np.ceil(n / cols)), cols, figsize=(cols * 1.1, np.ceil(n / cols) * 1.1))
    for i, a in enumerate(axs.flat):
        a.axis("off")
        if i < n: a.imshow(k[..., i])
    fig.suptitle("First-layer 3x3 filters (colour/edge detectors)"); fig.tight_layout(); fig.savefig("results/filters.png", dpi=130)
    img = XT[7]; stages = [adds[0], adds[4], adds[8], adds[-1]]; fm = keras.Model(m.inputs, [m.get_layer(s).output for s in stages])(img[None].astype("float32"))
    fig, axs = plt.subplots(4, 9, figsize=(13, 6.4))
    for r, (s, f) in enumerate(zip(stages, fm)):
        f = f[0].numpy(); top = np.argsort(-f.mean((0, 1)))[:8]; axs[r, 0].imshow(img); axs[r, 0].set_ylabel(f"{s}\n{f.shape[0]}x{f.shape[1]}x{f.shape[2]}", fontsize=8)
        for j, ch in enumerate(top): axs[r, j + 1].imshow(f[..., ch], cmap="viridis")
        for a in axs[r]: a.set_xticks([]); a.set_yticks([])
    fig.suptitle("Feature maps: the 8 most active channels per stage (resolution falls, abstraction rises)"); fig.tight_layout(); fig.savefig("results/feature_maps.png", dpi=120)
    last = adds[-1]; pick = [i for i in range(200) if True][:0]
    rng = np.random.default_rng(3); idx = []
    for c in range(10): idx.append(int(rng.choice(np.where(YT == c)[0])))
    fig, axs = plt.subplots(2, 10, figsize=(17, 4))
    for j, i in enumerate(idx):
        cam, c, p = gradcam(m, XT[i], last); axs[0, j].imshow(XT[i]); axs[0, j].set_title(f"true: {CLASSES[YT[i]]}", fontsize=9)
        axs[1, j].imshow(XT[i]); axs[1, j].imshow(cam, cmap="jet", alpha=.45); axs[1, j].set_title(f"pred: {CLASSES[c]} {p[c]:.0%}", fontsize=9, color="green" if c == YT[i] else "red")
        for a in axs[:, j]: a.axis("off")
    fig.suptitle("Grad-CAM on the last residual stage: where the network looks for its prediction"); fig.tight_layout(); fig.savefig("results/gradcam.png", dpi=120)
    print("ok")
