import pandas as pd

df = pd.read_csv("sqldata.csv")

print(df.dtypes)
print(df.info())