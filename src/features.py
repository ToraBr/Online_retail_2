import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "Data" / "processed"

CUTOFF = pd.Timestamp("2011-09-01")
WINDOW_DAYS = 90


def build_customer_table(df, cutoff, window_days=WINDOW_DAYS):
    past = df[df["InvoiceDate"] < cutoff]
    future = df[(df["InvoiceDate"] >= cutoff) &
                (df["InvoiceDate"] < cutoff + pd.Timedelta(days=window_days))]

    customers = past.groupby("Customer ID").agg(
        recency=("InvoiceDate", lambda x: (cutoff - x.max()).days),
        frequency=("Invoice", "nunique"),
        monetary=("Revenue", "sum"),
        tenure=("InvoiceDate", lambda x: (cutoff - x.min()).days),
        n_products=("StockCode", "nunique"),
    )

    # ratios
    customers["avg_order_value"] = customers["monetary"] / customers["frequency"]
    customers["orders_per_month"] = customers["frequency"] / (customers["tenure"] / 30 + 1)

    # bought in the same season last year (christmas customers)
    q4_start = cutoff - pd.DateOffset(years=1)
    q4_end = q4_start + pd.Timedelta(days=window_days)
    last_q4 = past[(past["InvoiceDate"] >= q4_start) & (past["InvoiceDate"] < q4_end)]
    customers["bought_last_q4"] = customers.index.isin(last_q4["Customer ID"]).astype(int)

    # target: did the customer buy again within the window?
    customers["target"] = customers.index.isin(future["Customer ID"]).astype(int)
    return customers


if __name__ == "__main__":
    df = pd.read_parquet(PROCESSED / "online_retail_clean.parquet")
    df = df.dropna(subset=["Customer ID"])
    df["Customer ID"] = df["Customer ID"].astype(int)

    customers = build_customer_table(df, CUTOFF, WINDOW_DAYS)
    customers.to_parquet(PROCESSED / "customers.parquet")   # keep index = Customer ID
    print(f"Saved {len(customers):,} customers, {customers['target'].mean():.0%} returned")
