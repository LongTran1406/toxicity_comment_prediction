from sklearn.base import BaseEstimator, TransformerMixin
import re
import string


class TextPreprocessor(BaseEstimator, TransformerMixin):

    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        processed_texts = []

        for text in X:
            # Ensure string
            text = str(text)

            # Lowercase
            text = text.lower()

            # Remove punctuation
            text = text.translate(str.maketrans("", "", string.punctuation))

            # Remove numbers
            text = re.sub(r"\d+", "", text)

            # Remove extra spaces
            text = re.sub(r"\s+", " ", text).strip()

            processed_texts.append(text)

        return processed_texts