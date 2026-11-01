# Machine Learning & AI — Week 3: Unsupervised Learning

- **K-Means on Iris:** features are standardised, K is chosen with the elbow method and silhouette scores, and k = 3 is fitted as the brief asks. (The silhouette score actually prefers k = 2, because two species overlap; k = 3 is used because there are three known species.)
- **Clusters versus true labels:** the labels are only used afterwards to check the clusters. Setosa is separated perfectly, and versicolor and virginica overlap, so 83.3% of flowers land with their own species (adjusted Rand index 0.620).
- **PCA:** two components keep 95.8% of the variance, with the loadings printed. K-Means on the two components gives the same agreement as on all four features.
- **Model saving:** the scaler, K-Means model and cluster-to-species mapping are saved and reloaded with `joblib`.
- Plots are in `output/iris_clusters.png` (elbow curve, clusters, true species).

The Iris data comes bundled with scikit-learn, so no download is needed.

Run with `pip install pandas matplotlib scikit-learn joblib` and then `python3 cluster.py`.
