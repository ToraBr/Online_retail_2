import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]   # src/ → prosjektmappa
RAW = ROOT / "Data" / "raw" / "online_retail_II.xlsx"
PROCESSED = ROOT / "Data" / "processed"

sheet = pd.read_excel(RAW, sheet_name=None)
df = pd.concat(sheet.values(), ignore_index=True)
df = df.drop_duplicates()   # the sheets overlap 1-9 Dec 2010


df["StockCode"] = df["StockCode"].astype(str)
df["Invoice"] = df["Invoice"].astype(str)
df["Revenue"] = df["Quantity"] * df["Price"]

#keeping seperate file with cancellations
cancellations = df[df["Invoice"].str.startswith("C")]


#removes cancellations
df = df[(df["Quantity"] > 0) & (df["Price"] > 0)].copy() #remove returns

#non-product stock codes to remove
codes_to_remove = [
    "POST", "DOT", "C2",               
    "BANK CHARGES", "AMAZONFEE",       
    "M", "m", "ADJUST", "ADJUST2",     
    "B", "D", "S",                     
    "PADS", "TEST001", "TEST002",      
]

remove = df["StockCode"].isin(codes_to_remove) | df["StockCode"].str.startswith("gift_")
df = df[~remove]

#the two giant mistake orders, that were later cancelled
orders_to_remove = ["581483", "541431"]
df = df[~df["Invoice"].astype(str).isin(orders_to_remove)]

df["Country"] = df["Country"].replace({
    "EIRE": "Ireland",
    "RSA": "South Africa",
    "Unspecified": "Unknown",
    "European Community": "Unknown",
})

df['Weekday'] = df['InvoiceDate'].dt.day_name()
df['Hour'] = df['InvoiceDate'].dt.hour

PROCESSED.mkdir(parents=True, exist_ok=True)
df.to_parquet(PROCESSED /"online_retail_clean.parquet", index=False)
cancellations.to_parquet(PROCESSED / "cancellations.parquet", index=False)
