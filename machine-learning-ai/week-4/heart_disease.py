"""Week 4 capstone, Option 1: heart disease prediction (full pipeline)."""
import warnings
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.datasets import fetch_openml
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score, confusion_matrix, precision_score, recall_score,
                             roc_auc_score, roc_curve)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

warnings.filterwarnings("ignore")
out = Path(__file__).parent / "output"
out.mkdir(exist_ok=True)
SEED = 42

# ---------- 1. Load and clean ----------
raw = fetch_openml("heart-statlog", version=1, as_frame=True, parser="auto").frame
df = raw.copy()
y = (df.pop("class") == "present").astype(int)
print(f"HEART DISEASE (UCI Statlog Heart): {len(df)} patients, {df.shape[1]} features, {y.mean():.1%} have heart disease")
print(f"Missing values: {int(df.isna().sum().sum())}, duplicate rows: {int(df.duplicated().sum())}")

# Categorical-coded columns are one-hot encoded; measurements are standardised (feature scaling).
categorical = ["chest", "resting_electrocardiographic_results", "slope", "thal", "number_of_major_vessels"]
for c in categorical:
    df[c] = df[c].astype(int).astype(str)
numeric = [c for c in df.columns if c not in categorical and df[c].nunique() > 2]
binary = [c for c in df.columns if c not in categorical + numeric]
pre = ColumnTransformer([
    ("num", StandardScaler(), numeric),
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
    ("bin", "passthrough", binary),
])

# ---------- 2. Train two models ----------
Xtr, Xte, ytr, yte = train_test_split(df, y, test_size=0.25, random_state=SEED, stratify=y)
models = {
    "Logistic Regression": Pipeline([("pre", pre), ("clf", LogisticRegression(max_iter=1000))]),
    "Decision Tree (depth 3)": Pipeline([("pre", pre), ("clf", DecisionTreeClassifier(max_depth=3, random_state=SEED))]),
}
cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
rows = {}
print(f"\nTest set: {len(Xte)} patients. With so few patients, one test split is noisy, so 5-fold cross-validation is shown too.")
for name, m in models.items():
    cvs = cross_val_score(m, Xtr, ytr, cv=cv, scoring="accuracy")
    m.fit(Xtr, ytr)
    p = m.predict(Xte)
    prob = m.predict_proba(Xte)[:, 1]
    rows[name] = {
        "accuracy": accuracy_score(yte, p), "precision": precision_score(yte, p), "recall": recall_score(yte, p),
        "ROC AUC": roc_auc_score(yte, prob), "5-fold CV accuracy": cvs.mean(), "CV std": cvs.std(),
    }
print(pd.DataFrame(rows).T.round(3).to_string())
print(f"Baseline (always predict 'no disease'): accuracy {1 - yte.mean():.3f}")

# ---------- 3. Confusion matrix and ROC curve ----------
best = "Logistic Regression"
cm = confusion_matrix(yte, models[best].predict(Xte))
tn, fp, fn, tp = cm.ravel()
print(f"\n{best} confusion matrix: {tp} sick patients found, {fn} sick patients missed, {tn} healthy correctly cleared, {fp} healthy flagged.")
print("For a screening tool, missed patients (false negatives) are the costly error, so recall matters more than accuracy here.")

fig, ax = plt.subplots(1, 2, figsize=(11, 4.6))
ConfusionMatrixDisplay(cm, display_labels=["absent", "present"]).plot(ax=ax[0], cmap="Blues", colorbar=False)
ax[0].set_title(f"Confusion matrix: {best}")
for name, m in models.items():
    fpr, tpr, _ = roc_curve(yte, m.predict_proba(Xte)[:, 1])
    ax[1].plot(fpr, tpr, label=f"{name} (AUC {rows[name]['ROC AUC']:.2f})")
ax[1].plot([0, 1], [0, 1], "k--", label="chance")
ax[1].set(title="ROC curve", xlabel="False positive rate", ylabel="True positive rate")
ax[1].legend()
fig.tight_layout()
fig.savefig(out / "heart_disease_evaluation.png", dpi=120)

# ---------- 4. Which features matter ----------
lr = models[best]
names = lr.named_steps["pre"].get_feature_names_out()
coef = pd.Series(lr.named_steps["clf"].coef_[0], index=names).sort_values(key=abs, ascending=False)
print("\nStrongest logistic regression coefficients (positive = raises the predicted risk):")
print(coef.head(6).round(2).to_string())

joblib.dump(lr, out / "heart_model.joblib")
print("\nSaved the fitted pipeline to output/heart_model.joblib")
print("This is a classroom exercise on 270 patients. It is not a medical tool and must not be used to assess anyone's health.")
