"""Trains the FAQ intent classifier and evaluates it honestly: stratified 5-fold cross-validation on the training
phrases, plus a held-out set of 48 new user messages written separately (tests.yaml) that the model never saw.
Model: word (1-2 gram) + character (2-5 gram) TF-IDF -> logistic regression; character n-grams make it robust to
typos ("certifcate"). A confidence threshold sends unclear messages to a fallback instead of guessing.
    python train.py -> model.joblib, results.json"""
import json, yaml, joblib, numpy as np
from sklearn.pipeline import make_pipeline, make_union
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report, accuracy_score
I = yaml.safe_load(open("intents.yaml")); X = [e for k, v in I.items() for e in v["examples"]]; y = [k for k, v in I.items() for _ in v["examples"]]
def model(): return make_pipeline(make_union(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True), TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True)), LogisticRegression(C=12, max_iter=3000))
cv = cross_val_score(model(), X, y, cv=StratifiedKFold(5, shuffle=True, random_state=0))
m = model().fit(X, y); joblib.dump(m, "model.joblib")
T = yaml.safe_load(open("tests.yaml")); tx = [t for k, v in T.items() if k != "out_of_scope" for t in v]; ty = [k for k, v in T.items() if k != "out_of_scope" for _ in v]
pred = m.predict(tx); conf = m.predict_proba(tx).max(1)
oos = T["out_of_scope"]; oos_conf = m.predict_proba(oos).max(1)
best = max(np.arange(.2, .6, .02), key=lambda th: ((pred == np.array(ty)) & (conf >= th)).mean() + (oos_conf < th).mean())
res = dict(intents=len(I), training_phrases=len(X), cv_accuracy_mean=round(cv.mean(), 3), cv_accuracy_std=round(cv.std(), 3), heldout_messages=len(tx),
           heldout_accuracy=round(accuracy_score(ty, pred), 3), threshold=round(float(best), 2),
           heldout_answered_correctly=round(float(((pred == np.array(ty)) & (conf >= best)).mean()), 3), heldout_sent_to_fallback=round(float((conf < best).mean()), 3),
           out_of_scope_messages=len(oos), out_of_scope_caught=round(float((oos_conf < best).mean()), 3),
           errors=[dict(text=t, true=a, pred=b, conf=round(float(c), 2)) for t, a, b, c in zip(tx, ty, pred, conf) if a != b])
json.dump(res, open("results.json", "w"), indent=1); json.dump(dict(threshold=res["threshold"]), open("threshold.json", "w"))
print(json.dumps({k: v for k, v in res.items() if k != "errors"}, indent=1)); print(classification_report(ty, pred, zero_division=0))
for e in res["errors"]: print("ERR", e)
