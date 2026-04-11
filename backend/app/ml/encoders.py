"""
Shared encoder classes — must live in a stable import path so joblib
can deserialise artifacts saved during training.
"""
import pandas as pd


class SmoothedTargetEncoder:
    """
    Encode categorical columns with their smoothed mean target value.

      encoded = (n_cat * mean_cat + k * global_mean) / (n_cat + k)

    Sparse categories collapse toward global mean.
    Per-column smoothing supported via smoothing_per_col dict.
    """

    def __init__(self, smoothing: float = 10.0,
                 smoothing_per_col: dict | None = None):
        self.smoothing = smoothing
        self.smoothing_per_col = smoothing_per_col or {}
        self._maps: dict[str, dict] = {}
        self._global_mean: float = 0.0

    def fit(self, X: pd.DataFrame, y: pd.Series, cols: list[str]) -> "SmoothedTargetEncoder":
        self._global_mean = float(y.mean())
        self._maps = {}
        for col in cols:
            k  = self.smoothing_per_col.get(col, self.smoothing)
            gm = self._global_mean
            stats = y.groupby(X[col]).agg(["mean", "count"])
            encoded = (stats["count"] * stats["mean"] + k * gm) / (stats["count"] + k)
            self._maps[col] = encoded.to_dict()
        return self

    def transform(self, X: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        X = X.copy()
        for col in cols:
            X[col] = X[col].map(self._maps[col]).fillna(self._global_mean)
        return X

    def fit_transform(self, X: pd.DataFrame, y: pd.Series, cols: list[str]) -> pd.DataFrame:
        return self.fit(X, y, cols).transform(X, cols)
