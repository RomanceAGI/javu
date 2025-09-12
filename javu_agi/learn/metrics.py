import numpy as np


def brier_score(probs, outcomes):
    return np.mean((np.array(probs) - np.array(outcomes)) ** 2)


def coverage(predictions, threshold=0.8):
    return np.mean([p >= threshold for p in predictions])
