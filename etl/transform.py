from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "raw" / "vendas.csv"
OUT_DIR = ROOT / "data" / "processed"


EXPECTED_COLUMNS = [
    "sale_id",
    "sale_date",
    "customer_id",
    "customer_name",
    "customer_segment",
    "city",
    "state",
    "region",
    "region_id",
    "product_id",
    "product_name",
    "category",
    "subcategory",
    "unit_price",
    "quantity",
    "discount_pct",
    "unit_cost",
    "seller_id",
    "seller_name",
    "seller_team",
    "channel",
    "order_status",
]


def _mode(series: pd.Series, fallback="Unknown"):
    """
    Returns the most frequent non-null/non-empty value.
    """
    values = series.dropna().astype(str).str.strip()
    values = values[values != ""]

    if values.empty:
        return fallback

    return values.mode().iloc[0]


def validate_raw(df: pd.DataFrame):
    """
    Validates the raw dataset structure and required keys.
    """
    missing_columns = [
        column for column in EXPECTED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    required_keys = [
        "sale_id",
        "customer_id",
        "product_id",
        "seller_id",
    ]

    for column in required_keys:
        if df[column].isna().any():
            raise ValueError(
                f"Column '{column}' contains null values."
            )


def clean_raw(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and enriches the raw transactional dataset.
    """

    df = df.copy()

    # ---------------------------------------------------------
    # Remove duplicated transactions
    # ---------------------------------------------------------

    df = df.drop_duplicates(
        subset=["sale_id"],
        keep="first"
    ).copy()

    # ---------------------------------------------------------
    # Dates
    # ---------------------------------------------------------

    df["sale_date"] = pd.to_datetime(
        df["sale_date"],
        errors="coerce"
    )

    if df["sale_date"].isna().any():
        raise ValueError(
            "Some sale_date values could not be converted to dates."
        )

    # ---------------------------------------------------------
    # Integer columns
    # ---------------------------------------------------------

    integer_columns = [
        "customer_id",
        "region_id",
        "product_id",
        "quantity",
        "seller_id",
    ]

    for column in integer_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="raise"
        ).astype("int64")

    # ---------------------------------------------------------
    # Numeric columns
    # ---------------------------------------------------------

    numeric_columns = [
        "unit_price",
        "discount_pct",
        "unit_cost",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="raise"
        )

    # ---------------------------------------------------------
    # Text normalization
    # ---------------------------------------------------------

    text_columns = [
        "customer_name",
        "customer_segment",
        "city",
        "state",
        "region",
        "product_name",
        "category",
        "subcategory",
        "seller_name",
        "seller_team",
        "channel",
        "order_status",
    ]

    for column in text_columns:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    # State normalization
    df["state"] = df["state"].str.upper()

    # Region normalization
    df["region"] = df["region"].str.title()

    # ---------------------------------------------------------
    # Customer segment
    # ---------------------------------------------------------

    df["customer_segment"] = (
        df["customer_segment"]
        .replace("", pd.NA)
    )

    # Missing segments become Unknown
    df["customer_segment"] = (
        df["customer_segment"]
        .fillna("Unknown")
    )

    # ---------------------------------------------------------
    # Remove cancelled transactions
    # ---------------------------------------------------------

    df = df[
        df["order_status"].str.lower() != "cancelado"
    ].copy()

    # ---------------------------------------------------------
    # Returns
    # ---------------------------------------------------------
    # Normal sale = +1
    # Return     = -1
    # ---------------------------------------------------------

    df["movement_sign"] = np.where(
        df["order_status"].str.lower() == "devolvido",
        -1,
        1,
    )

    # ---------------------------------------------------------
    # Quantities
    # ---------------------------------------------------------

    df["net_quantity"] = (
        df["quantity"] * df["movement_sign"]
    )

    # ---------------------------------------------------------
    # Revenue
    # ---------------------------------------------------------

    df["gross_revenue"] = (
        df["unit_price"]
        * df["quantity"]
        * df["movement_sign"]
    )

    # ---------------------------------------------------------
    # Discount
    # ---------------------------------------------------------

    df["discount_amount"] = (
        df["unit_price"]
        * df["quantity"]
        * df["discount_pct"]
        * df["movement_sign"]
    )

    # ---------------------------------------------------------
    # Net revenue
    # ---------------------------------------------------------

    df["net_revenue"] = (
        df["gross_revenue"]
        - df["discount_amount"]
    )

    # ---------------------------------------------------------
    # Cost
    # ---------------------------------------------------------

    df["total_cost"] = (
        df["unit_cost"]
        * df["quantity"]
        * df["movement_sign"]
    )

    # ---------------------------------------------------------
    # Gross profit
    # ---------------------------------------------------------

    df["gross_profit"] = (
        df["net_revenue"]
        - df["total_cost"]
    )

    # ---------------------------------------------------------
    # Margin
    # ---------------------------------------------------------

    df["margin_pct"] = np.where(
        df["net_revenue"] != 0,
        df["gross_profit"] / df["net_revenue"],
        0,
    )

    # ---------------------------------------------------------
    # Date ID
    # ---------------------------------------------------------

    df["date_id"] = (
        df["sale_date"]
        .dt.strftime("%Y%m%d")
        .astype(int)
    )

    return df


def build_dim_customer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the customer dimension.

    Region is intentionally NOT included here.
    Customer attributes remain independent from the
    transactional region used by FactSales.
    """

    dim_customer = (
        df.groupby("customer_id", as_index=False)
        .agg(
            customer_name=("customer_name", _mode),
            segment=("customer_segment", _mode),
            city=("city", _mode),
            state=("state", _mode),
        )
    )

    return dim_customer


def build_dim_product(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the product dimension.
    """

    dim_product = (
        df.groupby("product_id", as_index=False)
        .agg(
            product_name=("product_name", _mode),
            category=("category", _mode),
            subcategory=("subcategory", _mode),
        )
    )

    return dim_product


def build_dim_seller(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the seller dimension.
    """

    dim_seller = (
        df.groupby("seller_id", as_index=False)
        .agg(
            seller_name=("seller_name", _mode),
            seller_team=("seller_team", _mode),
        )
    )

    return dim_seller


def build_dim_region(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the region dimension.
    """

    dim_region = (
        df.groupby("region_id", as_index=False)
        .agg(
            region=("region", _mode),
            state=("state", _mode),
        )
    )

    return dim_region


def build_dim_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds a continuous date dimension covering the
    complete transaction period.
    """

    start_date = df["sale_date"].min().normalize()
    end_date = df["sale_date"].max().normalize()

    dates = pd.date_range(
        start=start_date,
        end=end_date,
        freq="D",
    )

    dim_date = pd.DataFrame({
        "date": dates
    })

    dim_date["date_id"] = (
        dim_date["date"]
        .dt.strftime("%Y%m%d")
        .astype(int)
    )

    dim_date["year"] = dim_date["date"].dt.year

    dim_date["quarter"] = (
        "Q"
        + dim_date["date"].dt.quarter.astype(str)
    )

    dim_date["month_number"] = (
        dim_date["date"].dt.month
    )

    dim_date["month_name"] = (
        dim_date["date"]
        .dt.month_name()
    )

    dim_date["year_month"] = (
        dim_date["date"]
        .dt.strftime("%Y-%m")
    )

    dim_date["day"] = (
        dim_date["date"].dt.day
    )

    dim_date["weekday_number"] = (
        dim_date["date"].dt.weekday + 1
    )

    dim_date["weekday_name"] = (
        dim_date["date"]
        .dt.day_name()
    )

    dim_date["is_weekend"] = (
        dim_date["date"]
        .dt.weekday >= 5
    )

    return dim_date[
        [
            "date_id",
            "date",
            "year",
            "quarter",
            "month_number",
            "month_name",
            "year_month",
            "day",
            "weekday_number",
            "weekday_name",
            "is_weekend",
        ]
    ]


def build_fact_sales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the sales fact table.

    Region remains in the fact table because it represents
    the region associated with the transaction.
    """

    columns = [
        "sale_id",
        "date_id",
        "customer_id",
        "product_id",
        "seller_id",
        "region_id",
        "channel",
        "order_status",
        "unit_price",
        "quantity",
        "net_quantity",
        "discount_pct",
        "gross_revenue",
        "discount_amount",
        "net_revenue",
        "unit_cost",
        "total_cost",
        "gross_profit",
        "margin_pct",
    ]

    return df[columns].copy()


def validate_model(
    fact_sales: pd.DataFrame,
    dim_customer: pd.DataFrame,
    dim_product: pd.DataFrame,
    dim_seller: pd.DataFrame,
    dim_region: pd.DataFrame,
    dim_date: pd.DataFrame,
):
    """
    Validates referential integrity between the fact
    table and dimensions.
    """

    # ---------------------------------------------------------
    # Validate dimension key uniqueness
    # ---------------------------------------------------------

    dimensions = {
        "customer_id": dim_customer,
        "product_id": dim_product,
        "seller_id": dim_seller,
        "region_id": dim_region,
        "date_id": dim_date,
    }

    for key, dimension in dimensions.items():
        if dimension[key].duplicated().any():
            raise ValueError(
                f"Duplicate keys found in dimension '{key}'."
            )

    # ---------------------------------------------------------
    # Validate fact -> customer
    # ---------------------------------------------------------

    invalid_customers = (
        ~fact_sales["customer_id"]
        .isin(dim_customer["customer_id"])
    )

    if invalid_customers.any():
        raise ValueError(
            "FactSales contains customer_id values "
            "not present in DimCustomer."
        )

    # ---------------------------------------------------------
    # Validate fact -> product
    # ---------------------------------------------------------

    invalid_products = (
        ~fact_sales["product_id"]
        .isin(dim_product["product_id"])
    )

    if invalid_products.any():
        raise ValueError(
            "FactSales contains product_id values "
            "not present in DimProduct."
        )

    # ---------------------------------------------------------
    # Validate fact -> seller
    # ---------------------------------------------------------

    invalid_sellers = (
        ~fact_sales["seller_id"]
        .isin(dim_seller["seller_id"])
    )

    if invalid_sellers.any():
        raise ValueError(
            "FactSales contains seller_id values "
            "not present in DimSeller."
        )

    # ---------------------------------------------------------
    # Validate fact -> region
    # ---------------------------------------------------------

    invalid_regions = (
        ~fact_sales["region_id"]
        .isin(dim_region["region_id"])
    )

    if invalid_regions.any():
        raise ValueError(
            "FactSales contains region_id values "
            "not present in DimRegion."
        )

    # ---------------------------------------------------------
    # Validate fact -> date
    # ---------------------------------------------------------

    invalid_dates = (
        ~fact_sales["date_id"]
        .isin(dim_date["date_id"])
    )

    if invalid_dates.any():
        raise ValueError(
            "FactSales contains date_id values "
            "not present in DimDate."
        )


def export_model(
    fact_sales: pd.DataFrame,
    dim_customer: pd.DataFrame,
    dim_product: pd.DataFrame,
    dim_seller: pd.DataFrame,
    dim_region: pd.DataFrame,
    dim_date: pd.DataFrame,
):
    """
    Clears the processed directory and exports
    the dimensional model as CSV files.
    """

    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Remove previously generated CSV files
    for file in OUT_DIR.glob("*.csv"):
        file.unlink()

    # Export dimensions
    dim_customer.to_csv(
        OUT_DIR / "dim_customer.csv",
        index=False
    )

    dim_product.to_csv(
        OUT_DIR / "dim_product.csv",
        index=False
    )

    dim_seller.to_csv(
        OUT_DIR / "dim_seller.csv",
        index=False
    )

    dim_region.to_csv(
        OUT_DIR / "dim_region.csv",
        index=False
    )

    dim_date.to_csv(
        OUT_DIR / "dim_date.csv",
        index=False
    )

    # Export fact
    fact_sales.to_csv(
        OUT_DIR / "fact_sales.csv",
        index=False
    )


def main():
    print("Starting ETL...")

    # ---------------------------------------------------------
    # Read raw data
    # ---------------------------------------------------------

    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"Raw file not found: {RAW_FILE}"
        )

    df_raw = pd.read_csv(RAW_FILE)

    print(f"Raw rows: {len(df_raw):,}")

    # ---------------------------------------------------------
    # Validate raw data
    # ---------------------------------------------------------

    validate_raw(df_raw)

    # ---------------------------------------------------------
    # Clean and transform
    # ---------------------------------------------------------

    df_clean = clean_raw(df_raw)

    print(
        f"Rows after cleaning: {len(df_clean):,}"
    )

    # ---------------------------------------------------------
    # Build dimensions
    # ---------------------------------------------------------

    dim_customer = build_dim_customer(df_clean)
    dim_product = build_dim_product(df_clean)
    dim_seller = build_dim_seller(df_clean)
    dim_region = build_dim_region(df_clean)
    dim_date = build_dim_date(df_clean)

    # ---------------------------------------------------------
    # Build fact
    # ---------------------------------------------------------

    fact_sales = build_fact_sales(df_clean)

    # ---------------------------------------------------------
    # Validate dimensional model
    # ---------------------------------------------------------

    validate_model(
        fact_sales=fact_sales,
        dim_customer=dim_customer,
        dim_product=dim_product,
        dim_seller=dim_seller,
        dim_region=dim_region,
        dim_date=dim_date,
    )

    # ---------------------------------------------------------
    # Export
    # ---------------------------------------------------------

    export_model(
        fact_sales=fact_sales,
        dim_customer=dim_customer,
        dim_product=dim_product,
        dim_seller=dim_seller,
        dim_region=dim_region,
        dim_date=dim_date,
    )

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    print("\nETL completed successfully.")
    print("\nGenerated tables:")

    print(
        f"  DimCustomer: {len(dim_customer):,} rows"
    )

    print(
        f"  DimProduct:  {len(dim_product):,} rows"
    )

    print(
        f"  DimSeller:   {len(dim_seller):,} rows"
    )

    print(
        f"  DimRegion:   {len(dim_region):,} rows"
    )

    print(
        f"  DimDate:     {len(dim_date):,} rows"
    )

    print(
        f"  FactSales:   {len(fact_sales):,} rows"
    )

    print(
        f"\nOutput directory: {OUT_DIR}"
    )


if __name__ == "__main__":
    main()