from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
import re
import string


class TextPreprocessor(BaseEstimator, TransformerMixin):

    def __init__(self):
        self.stop_words = set(ENGLISH_STOP_WORDS)

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

            # Remove numbers (optional)
            text = re.sub(r"\d+", "", text)

            # Remove extra spaces
            text = re.sub(r"\s+", " ", text).strip()

            # Remove stopwords
            tokens = [
                word for word in text.split()
                if word not in self.stop_words
            ]

            processed_texts.append(" ".join(tokens))

        return processed_texts