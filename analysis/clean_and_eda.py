
import os
import json
import pandas as pd


# ---------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------

orders = pd.read_csv("data/orders.csv")
customers = pd.read_csv("data/customers.csv")
products = pd.read_csv("data/products.csv")

print("Orders shape before cleaning:", orders.shape)
print("Customers shape:", customers.shape)
print("Products shape:", products.shape)


# ---------------------------------------------------------
# 2. Standardize payment_method
# ---------------------------------------------------------

orders["payment_method"] = (
    orders["payment_method"]
    .astype(str)
    .str.strip()
    .str.upper()
)

print("\nPayment method counts:")
print(orders["payment_method"].value_counts())


# ---------------------------------------------------------
# 3. Detect and remove duplicate orders
# Natural key excludes order_id
# ---------------------------------------------------------

natural_key = [
    "customer_id",
    "product_id",
    "order_date",
    "quantity",
    "discount_pct",
    "rating",
    "returned",
    "payment_method"
]

duplicate_mask = orders.duplicated(
    subset=natural_key,
    keep="first"
)

duplicate_orders = orders.loc[duplicate_mask].copy()

print("\nDuplicate orders detected:")
print(duplicate_orders["order_id"].tolist())

orders_clean = orders.loc[~duplicate_mask].copy()

print("Shape after duplicate removal:", orders_clean.shape)


# ---------------------------------------------------------
# 4. Impute missing values
# ---------------------------------------------------------

discount_missing = orders_clean["discount_pct"].isna().sum()
rating_missing = orders_clean["rating"].isna().sum()

orders_clean["discount_pct"] = (
    orders_clean["discount_pct"].fillna(0)
)

rating_median = orders_clean["rating"].median()

orders_clean["rating"] = (
    orders_clean["rating"].fillna(rating_median)
)

print("\nMissing discount_pct values filled:", discount_missing)
print("Missing rating values filled:", rating_missing)
print("Rating median used:", rating_median)

print("\nRemaining missing values:")
print(orders_clean.isna().sum())


# ---------------------------------------------------------
# 5. Merge products and customers
# ---------------------------------------------------------

merged = orders_clean.merge(
    products[["product_id", "price"]],
    on="product_id",
    how="left"
)

merged = merged.merge(
    customers[["customer_id", "city", "city_tier"]],
    on="customer_id",
    how="left"
)

# Calculate order value
merged["order_value"] = (
    merged["quantity"]
    * merged["price"]
    * (1 - merged["discount_pct"] / 100)
)

cleaned_total_revenue = merged["order_value"].sum()

print("\nCleaned rows:", len(merged))
print("Cleaned total revenue:", round(cleaned_total_revenue, 2))


# ---------------------------------------------------------
# 6. Raw revenue for reconciliation
# ---------------------------------------------------------

raw_with_products = orders.merge(
    products[["product_id", "price"]],
    on="product_id",
    how="left"
)

raw_with_products["order_value"] = (
    raw_with_products["quantity"]
    * raw_with_products["price"]
    * (1 - raw_with_products["discount_pct"].fillna(0) / 100)
)

raw_total_revenue = raw_with_products["order_value"].sum()

duplicate_reconciliation_delta = (
    raw_total_revenue - cleaned_total_revenue
)

print("Raw total revenue:", round(raw_total_revenue, 2))
print(
    "Duplicate reconciliation delta:",
    round(duplicate_reconciliation_delta, 2)
)


# ---------------------------------------------------------
# 7. IQR outlier detection on quantity
# ---------------------------------------------------------

q1 = merged["quantity"].quantile(0.25)
q3 = merged["quantity"].quantile(0.75)

iqr = q3 - q1

lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

quantity_outliers = merged[
    (merged["quantity"] < lower_bound)
    | (merged["quantity"] > upper_bound)
].copy()

print("\nQuantity IQR:")
print("Q1:", q1)
print("Q3:", q3)
print("IQR:", iqr)
print("Lower bound:", lower_bound)
print("Upper bound:", upper_bound)

print("Quantity outliers:")
print(
    quantity_outliers[
        ["order_id", "quantity"]
    ].to_string(index=False)
)


# ---------------------------------------------------------
# 8. Return rate by payment method
# ---------------------------------------------------------

payment_return_rate = (
    merged.groupby("payment_method")["returned"]
    .mean()
    .mul(100)
)

print("\nReturn rate by payment method:")
print(payment_return_rate.round(1))


# ---------------------------------------------------------
# 9. Multi-level segmentation
# ---------------------------------------------------------

segment = (
    merged
    .groupby(["payment_method", "city_tier"])
    .agg(
        orders=("order_id", "count"),
        returned_orders=("returned", "sum"),
        return_rate_pct=("returned", lambda x: x.mean() * 100)
    )
)

print("\nPayment method + city tier segmentation:")
print(segment.round(1))


# ---------------------------------------------------------
# 10. Correlation analysis
# ---------------------------------------------------------

correlation_columns = [
    "rating",
    "returned",
    "discount_pct",
    "quantity"
]

correlation_matrix = merged[correlation_columns].corr()

print("\nCorrelation matrix:")
print(correlation_matrix.round(3))


# ---------------------------------------------------------
# 11. Monthly revenue analysis
# ---------------------------------------------------------

merged["order_date"] = pd.to_datetime(
    merged["order_date"]
)

merged["year_month"] = (
    merged["order_date"]
    .dt.to_period("M")
    .astype(str)
)

monthly_revenue_all = (
    merged.groupby("year_month")["order_value"]
    .sum()
)

outlier_order_ids = quantity_outliers["order_id"].tolist()

monthly_revenue_corrected = (
    merged[
        ~merged["order_id"].isin(outlier_order_ids)
    ]
    .groupby("year_month")["order_value"]
    .sum()
)

print("\nMonthly revenue including quantity outliers:")
print(monthly_revenue_all.round(2))

print("\nMonthly revenue excluding quantity outliers:")
print(monthly_revenue_corrected.round(2))


# ---------------------------------------------------------
# 12. Generate findings.json
# ---------------------------------------------------------

os.makedirs("narrator", exist_ok=True)

true_peak_month = monthly_revenue_corrected.idxmax()

findings = {
    "cleaned_total_revenue_inr": round(
        cleaned_total_revenue, 2
    ),

    "raw_total_revenue_inr": round(
        raw_total_revenue, 2
    ),

    "duplicate_reconciliation_delta_inr": round(
        duplicate_reconciliation_delta, 2
    ),

    "return_rate_by_payment": {
        payment: round(rate, 1)
        for payment, rate in payment_return_rate.items()
    },

    "highest_risk_segment": {
        "payment_method": "COD",
        "city_tier": 2,
        "return_rate_pct": round(
            segment.loc[
                ("COD", 2),
                "return_rate_pct"
            ],
            1
        )
    },

    "true_peak_month": {
        "month": true_peak_month,
        "revenue_inr": round(
            monthly_revenue_corrected.max(),
            2
        )
    },

    "outlier_inflated_month": {
        "month": "2026-01",
        "apparent_revenue_inr": round(
            monthly_revenue_all.loc["2026-01"],
            2
        ),
        "corrected_revenue_inr": round(
            monthly_revenue_corrected.loc["2026-01"],
            2
        )
    }
}

with open(
    "narrator/findings.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(findings, f, indent=4)

print("\nfindings.json created successfully.")
print(json.dumps(findings, indent=4))
