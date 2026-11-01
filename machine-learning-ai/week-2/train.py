"""Week 2: supervised learning. Linear regression on housing prices, logistic regression on Titanic."""
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.datasets import fetch_california_housing, fetch_openml
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import ConfusionMatrixDisplay, accuracy_score, confusion_matrix, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

warnings.filterwarnings("ignore")
out = Path(__file__).parent / "output"
out.mkdir(exist_ok=True)
SEED = 42

# ---------- Assignment 1 and mini project: house price prediction ----------
housing = fetch_california_housing(as_frame=True)
X, y = housing.data, housing.target  # y is the median house value in units of $100,000
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=SEED)

models = {
    "Linear Regression": Pipeline([("scale", StandardScaler()), ("model", LinearRegression())]),
    "Decision Tree (depth 8)": DecisionTreeRegressor(max_depth=8, random_state=SEED),
    "Random Forest (100 trees)": RandomForestRegressor(n_estimators=100, random_state=SEED, n_jobs=-1),
}
print(f"HOUSE PRICES: California housing, {len(X)} districts, {X.shape[1]} features, 80/20 split (seed {SEED})")
rows, preds = [], {}
for name, m in models.items():
    m.fit(Xtr, ytr)
    p = m.predict(Xte)
    preds[name] = p
    rows.append({"model": name, "MSE": mean_squared_error(yte, p), "R2": r2_score(yte, p), "R2 on training data": r2_score(ytr, m.predict(Xtr))})
print(pd.DataFrame(rows).round(3).to_string(index=False))

lin = models["Linear Regression"]
coef = pd.Series(lin.named_steps["model"].coef_, index=X.columns).sort_values(key=abs, ascending=False).round(3)
print("\nLinear regression coefficients (on standardised features, so they are comparable):")
print(coef.to_string())

fig, ax = plt.subplots(1, 2, figsize=(11, 4.5), sharex=True, sharey=True)
for a, name in zip(ax, ["Linear Regression", "Random Forest (100 trees)"]):
    a.scatter(yte, preds[name], s=4, alpha=0.3)
    a.plot([0, 5], [0, 5], "r--", label="perfect prediction")
    a.set(title=f"{name}: R2 = {r2_score(yte, preds[name]):.3f}", xlabel="Actual value ($100k)", ylabel="Predicted ($100k)")
    a.legend()
fig.tight_layout()
fig.savefig(out / "house_pred_vs_actual.png", dpi=120)

# ---------- Assignment 2: Titanic survival with logistic regression ----------
titanic = fetch_openml("titanic", version=1, as_frame=True, parser="auto").frame
features = ["pclass", "sex", "age", "sibsp", "parch", "fare", "embarked"]  # not boat/body: they are only known after the sinking
t = titanic[features + ["survived"]].copy()
t["pclass"] = t["pclass"].astype(int)
ty = t.pop("survived").astype(int)
txtr, txte, tytr, tyte = train_test_split(t, ty, test_size=0.2, random_state=SEED, stratify=ty)
pre = ColumnTransformer([
    ("num", Pipeline([("fill", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), ["pclass", "age", "sibsp", "parch", "fare"]),
    ("cat", Pipeline([("fill", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), ["sex", "embarked"]),
])
clfs = {
    "Logistic Regression": LogisticRegression(max_iter=1000),
    "Decision Tree (depth 4)": DecisionTreeClassifier(max_depth=4, random_state=SEED),
    "Random Forest (200 trees)": RandomForestClassifier(n_estimators=200, random_state=SEED, n_jobs=-1),
}
print(f"\nTITANIC: {len(t)} passengers, survival rate {ty.mean():.1%}, test set {len(txte)} passengers")
print(f"Baseline (always predict the majority class): accuracy {max(tyte.mean(), 1 - tyte.mean()):.3f}")
fitted = {}
for name, c in clfs.items():
    pipe = Pipeline([("pre", pre), ("clf", c)]).fit(txtr, tytr)
    fitted[name] = pipe
    print(f"  {name}: test accuracy {accuracy_score(tyte, pipe.predict(txte)):.3f}")
log = fitted["Logistic Regression"]
cm = confusion_matrix(tyte, log.predict(txte))
tn, fp, fn, tp = cm.ravel()
print("\nLogistic regression confusion matrix (rows = actual, columns = predicted)")
print(f"  died:     {tn:4d} correct, {fp:4d} wrongly predicted to survive")
print(f"  survived: {tp:4d} correct, {fn:4d} wrongly predicted to die")
names = list(log.named_steps["pre"].get_feature_names_out())
odds = pd.Series(np.exp(log.named_steps["clf"].coef_[0]), index=names).sort_values(ascending=False).round(2)
print("\nOdds multipliers from logistic regression (above 1 raises survival odds):")
print(odds.to_string())
ConfusionMatrixDisplay(cm, display_labels=["died", "survived"]).plot(cmap="Blues")
plt.title("Titanic: logistic regression")
plt.savefig(out / "titanic_confusion_matrix.png", dpi=120)
