
import os
import pandas as pd
import matplotlib.pyplot as plt


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

orders = pd.read_csv("data/orders.csv")
customers = pd.read_csv("data/customers.csv")
products = pd.read_csv("data/products.csv")


# ---------------------------------------------------------
# Clean payment method
# ---------------------------------------------------------

orders["payment_method"] = (
    orders["payment_method"]
    .astype(str)
    .str.strip()
    .str.upper()
)


# ---------------------------------------------------------
# Remove duplicate orders
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

orders_clean = orders.loc[~duplicate_mask].copy()


# ---------------------------------------------------------
# Fill missing values
# ---------------------------------------------------------

orders_clean["discount_pct"] = (
    orders_clean["discount_pct"].fillna(0)
)

orders_clean["rating"] = (
    orders_clean["rating"]
    .fillna(orders_clean["rating"].median())
)


# ---------------------------------------------------------
# Merge product and customer information
# ---------------------------------------------------------

merged = orders_clean.merge(
    products[["product_id", "price"]],
    on="product_id",
    how="left"
)

merged = merged.merge(
    customers[["customer_id", "city_tier"]],
    on="customer_id",
    how="left"
)


# ---------------------------------------------------------
# Calculate order value
# ---------------------------------------------------------

merged["order_value"] = (
    merged["quantity"]
    * merged["price"]
    * (1 - merged["discount_pct"] / 100)
)


# ---------------------------------------------------------
# Create visualization folder
# ---------------------------------------------------------

os.makedirs("visualizations", exist_ok=True)


# ---------------------------------------------------------
# Visualization 1 — Return rate by payment method
# ---------------------------------------------------------

payment_return_rate = (
    merged.groupby("payment_method")["returned"]
    .mean()
    .mul(100)
    .sort_values(ascending=False)
)

plt.figure(figsize=(8, 5))

bars = plt.bar(
    payment_return_rate.index,
    payment_return_rate.values
)

plt.title("Return Rate by Payment Method")
plt.xlabel("Payment Method")
plt.ylabel("Return Rate (%)")

for bar, value in zip(
    bars,
    payment_return_rate.values
):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height(),
        f"{value:.1f}%",
        ha="center",
        va="bottom"
    )

plt.tight_layout()

plt.savefig(
    "visualizations/return_rate_by_payment.png",
    dpi=150
)

plt.close()


# ---------------------------------------------------------
# Visualization 2 — Monthly revenue trend
# Exclude quantity outliers
# ---------------------------------------------------------

q1 = merged["quantity"].quantile(0.25)
q3 = merged["quantity"].quantile(0.75)

iqr = q3 - q1

lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

outlier_mask = (
    (merged["quantity"] < lower_bound)
    | (merged["quantity"] > upper_bound)
)

corrected = merged.loc[~outlier_mask].copy()

corrected["order_date"] = pd.to_datetime(
    corrected["order_date"]
)

corrected["year_month"] = (
    corrected["order_date"]
    .dt.to_period("M")
    .astype(str)
)

monthly_revenue = (
    corrected
    .groupby("year_month")["order_value"]
    .sum()
)


plt.figure(figsize=(9, 5))

plt.plot(
    monthly_revenue.index,
    monthly_revenue.values,
    marker="o"
)

plt.title("Monthly Revenue Trend (Outlier Corrected)")
plt.xlabel("Month")
plt.ylabel("Revenue (INR)")
plt.xticks(rotation=45)

for month, value in monthly_revenue.items():
    plt.text(
        month,
        value,
        f"{value:,.0f}",
        ha="center",
        va="bottom"
    )

plt.tight_layout()

plt.savefig(
    "visualizations/monthly_revenue_trend.png",
    dpi=150
)

plt.close()


print("Visualization files created successfully.")
print("1. visualizations/return_rate_by_payment.png")
print("2. visualizations/monthly_revenue_trend.png")
