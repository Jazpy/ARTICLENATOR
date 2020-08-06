import warnings
from snorkel.utils                   import probs_to_preds
from snorkel.labeling                import PandasLFApplier
from snorkel.labeling                import LFAnalysis
from snorkel.labeling                import filter_unlabeled_dataframe
from snorkel.labeling.model          import LabelModel
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model            import LogisticRegression

class Classifier:
  def __init__(self, lfs, name):
    self.lfs        = lfs
    self.model      = None
    self.vectorizer = None
    self.name       = name

  def get_name(self):
    return self.name

  def train(self, dataset):
    # Apply labeler functions to training set
    lfs_applier = PandasLFApplier(lfs=self.lfs)
    with warnings.catch_warnings():
      warnings.filterwarnings('ignore')
      lfs_train = lfs_applier.apply(df=dataset)

    # Build probabilistic label model
    label_model = LabelModel(cardinality=3, verbose=True)
    label_model.fit(L_train=lfs_train, n_epochs=500, log_freq=100, seed=42)
    label_probs = label_model.predict_proba(lfs_train)

    # Filter unlabeled data points
    df_filtered, probs_filtered = filter_unlabeled_dataframe(
      X=dataset, y=label_probs, L=lfs_train)

    # Featurize data using scikit
    self.vectorizer = CountVectorizer(ngram_range=(1, 5))
    dataset_train   = self.vectorizer.fit_transform(
                        df_filtered.sentence.tolist())

    # Replace probabilistic labels with most likely label
    preds_filtered = probs_to_preds(probs=probs_filtered)

    # Train scikit model
    self.model = LogisticRegression(C=1e3, solver="liblinear",
      multi_class='auto')
    self.model.fit(X=dataset_train, y=preds_filtered)

  def classify(self, dataset):
    if not self.model or not self.vectorizer:
      raise RuntimeError('Classifier has not been trained')

    # Featurize data
    dataset_feat = self.vectorizer.transform(dataset.sentence.tolist())

    # Run model on featurized data
    return self.model.predict(dataset_feat)
