"""Task 1: LSTM sentiment analysis on IMDB movie reviews (Maas et al. 2011; the 50,000-review CSV distribution).
418 duplicate reviews are removed BEFORE splitting (otherwise copies leak between train and test).
Model: TextVectorization (20k words, 300 tokens) -> Embedding 128 -> bidirectional LSTM 64 -> dropout -> sigmoid.
Baseline for honesty: TF-IDF + logistic regression on the same split (a strong classical baseline on IMDB).
    python src/sentiment_lstm.py -> results/sentiment.json, results/sentiment_curves.png, results/sentiment_lstm.keras"""
import json, os, re, sys, time
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
import numpy as np, pandas as pd, tensorflow as tf, keras
T = int(os.environ.get("THREADS", 0))
if T: tf.config.threading.set_intra_op_parallelism_threads(T); tf.config.threading.set_inter_op_parallelism_threads(1)
from keras import layers
from sklearn.model_selection import train_test_split
tf.keras.utils.set_random_seed(0)
d = pd.read_csv(os.environ.get("IMDB_CSV", "/tmp/claude-0/imdb/imdb.csv")).drop_duplicates("review")
d["text"] = d["review"].str.replace(r"<br\s*/?>", " ", regex=True); d["y"] = (d["sentiment"] == "positive").astype(int)
tr, te = train_test_split(d, test_size=.2, random_state=0, stratify=d["y"]); tr, va = train_test_split(tr, test_size=.1, random_state=0, stratify=tr["y"])
res = dict(reviews=len(d), train=len(tr), val=len(va), test=len(te), duplicates_removed=50000 - len(d))
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=200000, sublinear_tf=True); lr = LogisticRegression(C=4, max_iter=2000).fit(vec.fit_transform(tr["text"]), tr["y"])
res["tfidf_logreg_test_accuracy"] = round(float((lr.predict(vec.transform(te["text"])) == te["y"]).mean()), 4)
V = layers.TextVectorization(max_tokens=20000, output_sequence_length=300, standardize="lower_and_strip_punctuation"); V.adapt(tf.data.Dataset.from_tensor_slices(tr["text"].values).batch(512))
def ds(df, sh=False):
    x = tf.data.Dataset.from_tensor_slices((df["text"].values, df["y"].values))
    if sh: x = x.shuffle(len(df), seed=0)
    return x.batch(128).map(lambda a, b: (V(a), b), num_parallel_calls=tf.data.AUTOTUNE).prefetch(2)
i = keras.Input((300,), dtype="int64"); x = layers.Embedding(20000, 128, mask_zero=True)(i); x = layers.Bidirectional(layers.LSTM(64))(x); x = layers.Dropout(.4)(x)
m = keras.Model(i, layers.Dense(1, activation="sigmoid")(x)); m.compile(keras.optimizers.Adam(1e-3), "binary_crossentropy", metrics=["accuracy"])
t = time.time(); h = m.fit(ds(tr, True), validation_data=ds(va), epochs=int(os.environ.get("EPOCHS", 4)), verbose=2, callbacks=[keras.callbacks.EarlyStopping("val_accuracy", patience=1, restore_best_weights=True)])
p = m.predict(ds(te), verbose=0).ravel(); yte = te["y"].values
from sklearn.metrics import roc_auc_score, confusion_matrix
res.update(lstm_test_accuracy=round(float(((p > .5) == yte).mean()), 4), lstm_test_auc=round(float(roc_auc_score(yte, p)), 4), minutes=round((time.time() - t) / 60, 1), params=m.count_params(),
           confusion=confusion_matrix(yte, p > .5).tolist(), history={k: [round(v, 4) for v in vs] for k, vs in h.history.items()})
demo = ["An absolute masterpiece, the acting and the score gave me chills.", "I wanted to love it, but the plot was a mess and it dragged on forever.",
        "Not bad at all. Not great either, but I'd watch it again.", "The movie was not good."]
res["demo"] = [dict(text=s, p_positive=round(float(m.predict(V(tf.constant([s])), verbose=0)[0, 0]), 3)) for s in demo]
m.save("results/sentiment_lstm.keras"); json.dump(V.get_vocabulary(), open("results/sentiment_vocab.json", "w"))   # model + its vocabulary (rebuild TextVectorization(vocabulary=...))
json.dump(res, open("results/sentiment.json", "w"), indent=1)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(6, 4)); ax.plot(h.history["accuracy"], "o-", label="train"); ax.plot(h.history["val_accuracy"], "o-", label="validation"); ax.axhline(res["tfidf_logreg_test_accuracy"], ls="--", c="gray", label="TF-IDF + LR (test)")
ax.set_xlabel("epoch"); ax.set_title(f"BiLSTM test accuracy {res['lstm_test_accuracy']:.1%}"); ax.legend(); fig.tight_layout(); fig.savefig("results/sentiment_curves.png", dpi=130)
print(json.dumps({k: v for k, v in res.items() if k != "history"}, indent=1))
