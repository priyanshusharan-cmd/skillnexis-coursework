# Machine Learning & AI — Week 2: Supervised Learning

- **Assignment 1 and mini project, house prices:** linear regression to predict house prices, scored with MSE and R², plus a predicted-versus-actual plot (`output/house_pred_vs_actual.png`). A decision tree and a random forest are included for comparison.
- **Assignment 2, Titanic survival:** logistic regression with median and most-frequent imputation, scaling and one-hot encoding in a pipeline, plus a confusion matrix, a majority-class baseline, and odds multipliers for each feature.

**Datasets differ from the brief.** The brief's Kaggle links need a login, so these use scikit-learn's California housing data (20,640 districts, prices in units of $100,000) and the OpenML copy of Titanic (1,309 passengers). Results are not comparable with the Kaggle "House Prices" file.

Results from the run: linear regression R² 0.576, decision tree 0.678, random forest 0.805. The random forest scores 0.974 on the training data, so it overfits, and the test score is the one that counts. On Titanic, logistic regression reaches 0.809 test accuracy against a 0.618 baseline. The `boat` and `body` columns are deliberately left out, because they are only known after the sinking and would leak the answer.

Run with `pip install pandas matplotlib scikit-learn` and then `python3 train.py` (the datasets download on first run).
