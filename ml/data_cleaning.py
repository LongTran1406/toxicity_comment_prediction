import pandas as pd

class DataCleaning:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def run(self):
        df = self.df.copy()

        # Remove null rows
        df = df.dropna(subset=["comment_text", "toxicity"])

        # Remove duplicates
        df = df.drop_duplicates()

        # Ensure correct datatype
        df["comment_text"] = df["comment_text"].astype(str)

        return df