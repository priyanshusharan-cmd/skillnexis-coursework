# Machine Learning & AI — Week 4: Capstone (Option 1, Heart Disease Prediction)

Full pipeline: load, check and clean, scale and encode features, train logistic regression and a decision tree, then evaluate with accuracy, precision, recall, a confusion matrix and an ROC curve (`output/heart_disease_evaluation.png`). The fitted pipeline is saved in `output/heart_model.joblib`.

**The dataset differs from the brief.** The Kaggle "Heart Disease UCI" file needs a login, so this uses the UCI Statlog Heart dataset from OpenML: 270 patients, 13 features, no missing values.

Results on a 68-patient test set: logistic regression has 0.897 accuracy, 0.848 precision, 0.933 recall and 0.936 ROC AUC, against a 0.559 baseline. It finds 28 of 30 patients with heart disease and misses 2. Five-fold cross-validation gives 0.836 ± 0.052, a better guide than one small split, so expect real performance nearer that figure. The depth-3 decision tree is weaker (0.779).

This is a classroom exercise on a small dataset. It is **not** a medical tool and must not be used to judge anyone's health.

Run with `pip install pandas matplotlib scikit-learn joblib` and then `python3 heart_disease.py`.
