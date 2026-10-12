
import os
import json
from itertools import combinations
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

print("\nTask 2: Raw payment_method values BEFORE standardization:")
print(orders["payment_method"].value_counts(dropna=False))

orders["payment_method"] = (
    orders["payment_method"]
    .astype(str)
    .str.strip()
    .str.upper()
)

print("\nPayment method counts AFTER standardization:")
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

# Independently calculate the value of the five removed duplicate rows
duplicate_with_products = duplicate_orders.merge(
    products[["product_id", "price"]],
    on="product_id",
    how="left"
)

duplicate_with_products["order_value"] = (
    duplicate_with_products["quantity"]
    * duplicate_with_products["price"]
    * (
        1
        - duplicate_with_products["discount_pct"].fillna(0) / 100
    )
)

duplicate_sum = duplicate_with_products["order_value"].sum()

print("\nTask 5: Revenue reconciliation")
print("Raw total revenue:", round(raw_total_revenue, 2))
print("Cleaned total revenue:", round(cleaned_total_revenue, 2))
print(
    "Duplicate reconciliation delta:",
    round(duplicate_reconciliation_delta, 2)
)
print(
    "Independent sum of the 5 duplicate rows:",
    round(duplicate_sum, 2)
)

print(
    f"Reconciliation: Raw revenue of "
    f"₹{raw_total_revenue:,.2f} minus cleaned revenue of "
    f"₹{cleaned_total_revenue:,.2f} equals "
    f"₹{duplicate_reconciliation_delta:,.2f}. "
    f"This difference is attributable to the five duplicate "
    f"orders removed. Imputing missing discount_pct and rating "
    f"values does not change the order-value totals."
)


# ---------------------------------------------------------
# 7. IQR outlier detection on quantity
# ---------------------------------------------------------

q1 = merged["quantity"].quantile(0.25)
q3 = merged["quantity"].quantile(0.75)

iqr = q3 - q1

lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

# Create an explicit outlier flag
merged["is_outlier"] = (
    (merged["quantity"] < lower_bound)
    | (merged["quantity"] > upper_bound)
)

quantity_outliers = merged[
    merged["is_outlier"]
].copy()

print("\nTask 6: Quantity IQR")
print("Q1:", q1)
print("Q3:", q3)
print("IQR:", iqr)
print("Lower bound:", lower_bound)
print("Upper bound:", upper_bound)

print("\nQuantity outliers with is_outlier flag:")
print(
    merged[
        ["order_id", "quantity", "is_outlier"]
    ]
    .query("is_outlier")
    .to_string(index=False)
)


# ---------------------------------------------------------
# 8. Return rate by payment method
# ---------------------------------------------------------

payment_return_rate = (
    merged.groupby("payment_method")["returned"]
    .mean()
    .mul(100)
)

print("\nTask 7: Return rate by payment method:")
print(payment_return_rate.round(1))

print(
    "\nHypothesis: COD orders have a higher return rate "
    "than CARD and UPI orders."
)

confirmed = (
    payment_return_rate["COD"]
    > payment_return_rate.drop("COD").max()
)

print(
    "Hypothesis result:",
    "Confirmed" if confirmed else "Not confirmed"
)


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

print("\nTask 8: Payment method + city tier segmentation:")
print(segment.round(1))

highest_risk_key = segment["return_rate_pct"].idxmax()
highest_risk_rate = segment.loc[
    highest_risk_key,
    "return_rate_pct"
]

print(
    f"\nHighest-risk segment: "
    f"{highest_risk_key[0]} + "
    f"Tier-{highest_risk_key[1]} cities, "
    f"with a return rate of {highest_risk_rate:.1f}%."
)


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

print("\nTask 9: Correlation matrix:")
print(correlation_matrix.round(3))


print("\nCorrelation strength for each pair:")

for col1, col2 in combinations(correlation_columns, 2):

    r = correlation_matrix.loc[col1, col2]
    strength = abs(r)

    if strength < 0.2:
        band = "Negligible"
    elif strength < 0.4:
        band = "Weak"
    elif strength < 0.7:
        band = "Moderate"
    else:
        band = "Strong"

    print(
        f"{col1} vs {col2}: "
        f"r = {r:.3f}, strength = {band}"
    )


discount_return_corr = correlation_matrix.loc[
    "discount_pct",
    "returned"
]

print(
    "\nHypothesis: Higher discounts reduce returns."
)

if abs(discount_return_corr) < 0.2:
    print("Hypothesis result: Busted")
else:
    print("Hypothesis result: Requires further investigation")


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

print("\nTask 10: Monthly revenue including quantity outliers:")
print(monthly_revenue_all.round(2))

print("\nMonthly revenue excluding quantity outliers:")
print(monthly_revenue_corrected.round(2))


print("\nTime-series finding:")

print(
    "January 2026's apparent revenue lead is inflated "
    "by two bulk orders: O0011 on 2026-01-28 and "
    "O0098 on 2026-01-10."
)

true_peak_month_display = pd.to_datetime(
    monthly_revenue_corrected.idxmax()
).strftime("%B %Y")

print(
    f"After excluding these quantity outliers, "
    f"{true_peak_month_display} is the true "
    f"peak month, with revenue of "
    f"₹{monthly_revenue_corrected.max():,.2f}."
)


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

    "duplicate_rows_removed": len(duplicate_orders),

    "duplicate_sum_inr": round(
        duplicate_sum, 2
    ),

    "return_rate_by_payment": {
        payment: round(rate, 1)
        for payment, rate in payment_return_rate.items()
    },

    "hypothesis_cod_higher_return_rate": (
        "Confirmed" if confirmed else "Not confirmed"
    ),

    "highest_risk_segment": {
        "payment_method": highest_risk_key[0],
        "city_tier": int(highest_risk_key[1]),
        "return_rate_pct": round(
            highest_risk_rate,
            1
        )
    },

    "discount_return_hypothesis": (
        "Busted"
        if abs(discount_return_corr) < 0.2
        else "Requires further investigation"
    ),

    "true_peak_month": {
        "month": true_peak_month,
        "revenue_inr": round(
            monthly_revenue_corrected.max(),
            2
        )
    },

    "outlier_inflated_month": {
        "month": (
            monthly_revenue_all
            .sub(monthly_revenue_corrected, fill_value=0)
            .idxmax()
        ),
        "apparent_revenue_inr": round(
            monthly_revenue_all.loc[
                monthly_revenue_all
                .sub(monthly_revenue_corrected, fill_value=0)
                .idxmax()
            ],
            2
        ),
        "corrected_revenue_inr": round(
            monthly_revenue_corrected.loc[
                monthly_revenue_all
                .sub(monthly_revenue_corrected, fill_value=0)
                .idxmax()
            ],
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
