import pandas as pd

df = pd.read_parquet("C:/Users/Admin/Downloads/00000-1-bc7c51b6-7ae7-4697-8830-a7e736b2ea95-0-00001.parquet")
print(df.describe())