"""AI document classifier, training. Data: AG News, 120,000 training and 7,600 test news articles in 4 topics
(World, Sports, Business, Sci/Tech). It's the standard academic benchmark from Zhang, Zhao & LeCun (2015); the copy
used is github.com/mhjabreel/CharCnn_Keras/data/ag_news_csv.
Model: TF-IDF (word 1-2 grams, sublinear tf) -> linear SVM, calibrated so it outputs confidence scores. It's fast,
small and runs on any laptop; documents below the confidence threshold go to "needs review" instead of being guessed.
    python train.py  -> model.joblib, results/metrics.json, results/confusion.png"""
import json, os, time
import joblib, numpy as np, pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.svm import LinearSVC
LABELS = ["World", "Sports", "Business", "Sci/Tech"]
def load(p):
    d = pd.read_csv(p, header=None, names=["label", "title", "desc"]); d["text"] = (d["title"] + ". " + d["desc"].str.replace("\\", " ", regex=False)).str.replace(r"#\d+;", " ", regex=True)
    return d["text"].tolist(), (d["label"] - 1).map(lambda i: LABELS[i]).tolist()
Xtr, ytr = load("data/train.csv"); Xte, yte = load("data/test.csv")
t = time.time()
m = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, max_features=400000), CalibratedClassifierCV(LinearSVC(C=0.5), cv=3)).fit(Xtr, ytr)
fit_s = time.time() - t; pred = m.predict(Xte); proba = m.predict_proba(Xte).max(1)
TH = 0.6; sure = proba >= TH
os.makedirs("results", exist_ok=True); joblib.dump(m, "model.joblib", compress=3)
cm = confusion_matrix(yte, pred, labels=LABELS)
res = dict(train_docs=len(Xtr), test_docs=len(Xte), test_accuracy=round(accuracy_score(yte, pred), 4), macro_f1=round(f1_score(yte, pred, average="macro"), 4), fit_seconds=round(fit_s, 1),
           threshold=TH, auto_classified_share=round(float(sure.mean()), 4), accuracy_when_auto=round(float((np.array(pred) == np.array(yte))[sure].mean()), 4),
           baseline_majority=0.25, confusion=dict(labels=LABELS, matrix=cm.tolist()), report=classification_report(yte, pred, output_dict=True))
json.dump(res, open("results/metrics.json", "w"), indent=1)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(5.6, 4.8)); ax.imshow(cm, cmap="Blues")
for i in range(4):
    for j in range(4): ax.text(j, i, cm[i, j], ha="center", va="center", color="white" if cm[i, j] > cm.max() / 2 else "black")
ax.set_xticks(range(4), LABELS); ax.set_yticks(range(4), LABELS); ax.set_xlabel("predicted"); ax.set_ylabel("true"); ax.set_title(f"AG News test set, accuracy {res['test_accuracy']:.1%}")
fig.tight_layout(); fig.savefig("results/confusion.png", dpi=130)
print({k: v for k, v in res.items() if k not in ("report", "confusion")})
