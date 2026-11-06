"""Plant disease detector (Flask). Upload a tomato-leaf photo -> predicted disease, confidence, top-3, a Grad-CAM heat
map of where the model looked, and care advice. Below the confidence threshold it says it isn't sure instead of guessing.
    pip install -r requirements.txt && python app.py      -> http://localhost:5000
API: POST /api/predict with form field 'image' -> JSON"""
import base64, io, json, os
import numpy as np
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
from flask import Flask, jsonify, render_template, request
from PIL import Image, UnidentifiedImageError
import keras, tensorflow as tf
HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = keras.models.load_model(os.path.join(HERE, "model", "plant_mnv2.keras")); META = json.load(open(os.path.join(HERE, "model", "labels.json")))
ADVICE = json.load(open(os.path.join(HERE, "model", "advice.json")))
S, TH = META["image_size"], META["threshold"]; app = Flask(__name__); app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
BASE = MODEL.get_layer([l.name for l in MODEL.layers if "mobilenet" in l.name][0])
def predict(img):
    x = np.asarray(img.convert("RGB").resize((S, S), Image.BILINEAR), dtype="float32")[None]
    # Grad-CAM on the backbone's last feature map
    pre = MODEL.get_layer("preprocess"); gap, drop, dense = MODEL.layers[-3], MODEL.layers[-2], MODEL.layers[-1]
    with tf.GradientTape() as t:
        f = BASE(pre(x), training=False); t.watch(f); p = dense(gap(f))
        c = int(tf.argmax(p[0])); score = p[:, c]
    g = t.gradient(score, f)[0]; cam = tf.nn.relu(tf.reduce_sum(f[0] * tf.reduce_mean(g, (0, 1)), -1)).numpy(); cam /= cam.max() + 1e-8
    probs = p.numpy()[0]; top = probs.argsort()[::-1][:3]
    heat = (np.asarray(Image.fromarray((cam * 255).astype("uint8")).resize((S, S), Image.BILINEAR)) / 255.)[..., None]
    jet = np.concatenate([np.clip(1.5 - abs(4 * heat - 3), 0, 1), np.clip(1.5 - abs(4 * heat - 2), 0, 1), np.clip(1.5 - abs(4 * heat - 1), 0, 1)], -1)
    over = (0.55 * x[0] / 255 + 0.45 * jet).clip(0, 1); buf = io.BytesIO(); Image.fromarray((over * 255).astype("uint8")).resize((320, 320)).save(buf, "PNG")
    name = META["classes"][c]; sure = bool(probs[c] >= TH)
    return dict(prediction=name if sure else "Not sure", confident=sure, confidence=round(float(probs[c]), 4), top3=[dict(label=META["classes"][i], p=round(float(probs[i]), 4)) for i in top],
                advice=ADVICE.get(name, "") if sure else "The model isn't confident. Retake the photo: one leaf, in daylight, filling the frame, on a plain background.",
                heatmap="data:image/png;base64," + base64.b64encode(buf.getvalue()).decode())
def load_image():
    f = request.files.get("image")
    if not f or not f.filename: return None, ("No image uploaded", 400)
    try: return Image.open(f.stream), None
    except UnidentifiedImageError: return None, ("That file isn't an image (use JPG or PNG)", 415)
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET": return render_template("index.html")
    img, err = load_image()
    if err: return render_template("index.html", error=err[0]), err[1]
    buf = io.BytesIO(); img.convert("RGB").resize((320, 320)).save(buf, "JPEG"); up = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    return render_template("index.html", r=predict(img), upload=up)
@app.post("/api/predict")
def api():
    img, err = load_image()
    if err: return jsonify(error=err[0]), err[1]
    r = predict(img); r.pop("heatmap"); return jsonify(r)
@app.errorhandler(413)
def too_big(e): return jsonify(error="Image larger than 8 MB"), 413
if __name__ == "__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
