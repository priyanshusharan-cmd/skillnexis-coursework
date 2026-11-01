"""Week 3: unsupervised learning. K-Means and PCA on the Iris dataset, with model saving."""
import warnings
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
out = Path(__file__).parent / "output"
out.mkdir(exist_ok=True)
SEED = 42

iris = load_iris(as_frame=True)
X, truth = iris.data, iris.target
species = np.array(iris.target_names)
Xs = StandardScaler().fit_transform(X)
print(f"IRIS: {len(X)} flowers, features {list(X.columns)}")

# ---------- Elbow method and silhouette score for choosing K ----------
ks = range(2, 9)
inertia = [KMeans(n_clusters=k, n_init=10, random_state=SEED).fit(Xs).inertia_ for k in ks]
sil = [silhouette_score(Xs, KMeans(n_clusters=k, n_init=10, random_state=SEED).fit_predict(Xs)) for k in ks]
print("\nChoosing K (standardised features)")
print(pd.DataFrame({"k": list(ks), "inertia": np.round(inertia, 1), "silhouette": np.round(sil, 3)}).to_string(index=False))

# ---------- Assignment 1 / mini project: K-Means with k = 3 ----------
km = KMeans(n_clusters=3, n_init=10, random_state=SEED).fit(Xs)
labels = km.labels_
print(f"\nK-Means k=3: inertia {km.inertia_:.1f}, silhouette {silhouette_score(Xs, labels):.3f}")
table = pd.crosstab(pd.Series(species[truth], name="true species"), pd.Series(labels, name="cluster"))
print("\nClusters vs true species (rows = species):")
print(table.to_string())
# Cluster numbers are arbitrary, so map each cluster to the species most common inside it.
mapping = {c: table[c].idxmax() for c in table.columns}
mapped = np.array([mapping[c] for c in labels])
acc = (mapped == species[truth]).mean()
print(f"\nIf each cluster is named after its most common species, {acc:.1%} of flowers are grouped with their own species.")
print(f"Adjusted Rand index (1 = perfect agreement, 0 = chance): {adjusted_rand_score(truth, labels):.3f}")
print("Note: the labels were not used to build the clusters; they are only used here to check them.")

# ---------- Assignment 2: PCA ----------
pca = PCA().fit(Xs)
ratio = pca.explained_variance_ratio_
print("\nPCA explained variance ratio:", np.round(ratio, 3), "| cumulative:", np.round(np.cumsum(ratio), 3))
pca2 = PCA(n_components=2).fit(Xs)
Z = pca2.transform(Xs)
print(f"Reducing 4 dimensions to 2 keeps {pca2.explained_variance_ratio_.sum():.1%} of the variance.")
print("Component loadings (which original features each component mixes):")
print(pd.DataFrame(pca2.components_.T, index=X.columns, columns=["PC1", "PC2"]).round(3).to_string())
km_pca = KMeans(n_clusters=3, n_init=10, random_state=SEED).fit(Z)
print(f"K-Means on the 2 PCA components: adjusted Rand index {adjusted_rand_score(truth, km_pca.labels_):.3f} (4 features gave {adjusted_rand_score(truth, labels):.3f})")

# ---------- Plots ----------
fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))
ax[0].plot(list(ks), inertia, "o-")
ax[0].axvline(3, color="r", ls="--", label="k = 3")
ax[0].set(title="Elbow method", xlabel="k", ylabel="inertia")
ax[0].legend()
ax[1].scatter(Z[:, 0], Z[:, 1], c=labels, cmap="viridis", s=30)
cent = pca2.transform(km.cluster_centers_)
ax[1].scatter(cent[:, 0], cent[:, 1], c="red", marker="X", s=200, label="centroids")
ax[1].set(title="K-Means clusters (shown on PCA axes)", xlabel="PC1", ylabel="PC2")
ax[1].legend()
for i, name in enumerate(species):
    ax[2].scatter(Z[truth == i, 0], Z[truth == i, 1], s=30, label=name)
ax[2].set(title="True species (same axes)", xlabel="PC1", ylabel="PC2")
ax[2].legend()
fig.tight_layout()
fig.savefig(out / "iris_clusters.png", dpi=120)

# ---------- Model saving and loading ----------
joblib.dump({"scaler": StandardScaler().fit(X), "kmeans": km, "cluster_to_species": mapping}, out / "iris_kmeans.joblib")
loaded = joblib.load(out / "iris_kmeans.joblib")
sample = X.iloc[[0, 60, 120]]
cl = loaded["kmeans"].predict(loaded["scaler"].transform(sample))
print("\nSaved and reloaded the model with joblib. Predictions for 3 flowers:", [loaded["cluster_to_species"][c] for c in cl], "| true:", [str(s) for s in species[truth.iloc[[0, 60, 120]]]])
