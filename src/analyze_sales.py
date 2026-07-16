from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "sales_data.csv"
OUTPUT_DIR = BASE_DIR / "output"
REQUIRED_COLUMNS = {
    "Order Date",
    "Region",
    "Product Category",
    "Product Name",
    "Sales Amount",
    "Quantity Sold",
    "Profit",
}


def load_and_clean_data(file_path: Path) -> pd.DataFrame:
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset not found: {file_path}")

    df = pd.read_csv(file_path)
    df = df.drop_duplicates().copy()
    df.columns = [column.strip() for column in df.columns]
    missing_columns = REQUIRED_COLUMNS.difference(df.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"Dataset is missing required columns: {missing_list}")

    df["Product Category"] = (
        df["Product Category"].astype(str).str.strip().str.title()
    )
    df["Product Name"] = df["Product Name"].astype(str).str.strip()
    df["Region"] = df["Region"].astype(str).str.strip().str.title()
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")

    numeric_columns = ["Sales Amount", "Quantity Sold", "Profit"]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(
        subset=[
            "Order Date",
            "Product Category",
            "Product Name",
            "Sales Amount",
            "Quantity Sold",
            "Profit",
        ]
    ).copy()

    df["Month"] = df["Order Date"].dt.to_period("M").astype(str)
    df["Month Name"] = df["Order Date"].dt.strftime("%b")
    df["Quarter"] = df["Order Date"].dt.to_period("Q").astype(str)
    df["Profit Margin %"] = (df["Profit"] / df["Sales Amount"] * 100).round(2)

    if df.empty:
        raise ValueError("No valid rows remain after cleaning the dataset.")

    return df


def build_category_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("Product Category", as_index=False)
        .agg(
            Total_Revenue=("Sales Amount", "sum"),
            Total_Quantity=("Quantity Sold", "sum"),
            Total_Profit=("Profit", "sum"),
            Average_Sale=("Sales Amount", "mean"),
            Average_Profit_Margin=("Profit Margin %", "mean"),
        )
        .sort_values("Total_Revenue", ascending=False)
    )

    summary["Revenue_Contribution_%"] = (
        summary["Total_Revenue"] / summary["Total_Revenue"].sum() * 100
    ).round(2)
    summary["Profit_Contribution_%"] = (
        summary["Total_Profit"] / summary["Total_Profit"].sum() * 100
    ).round(2)
    return summary.round(2)


def build_monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        df.groupby(["Month", "Product Category"], as_index=False)["Sales Amount"]
        .sum()
        .sort_values(["Month", "Sales Amount"], ascending=[True, False])
    )
    return monthly


def build_region_summary(df: pd.DataFrame) -> pd.DataFrame:
    region = (
        df.groupby("Region", as_index=False)
        .agg(
            Total_Revenue=("Sales Amount", "sum"),
            Total_Profit=("Profit", "sum"),
            Total_Quantity=("Quantity Sold", "sum"),
        )
        .sort_values("Total_Revenue", ascending=False)
        .round(2)
    )
    return region


def save_outputs(
    category_summary: pd.DataFrame,
    monthly_summary: pd.DataFrame,
    region_summary: pd.DataFrame,
    output_dir: Path = OUTPUT_DIR,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    category_summary.to_csv(output_dir / "category_summary.csv", index=False)
    monthly_summary.to_csv(output_dir / "monthly_sales_trend.csv", index=False)
    region_summary.to_csv(output_dir / "region_summary.csv", index=False)


def create_visualizations(
    category_summary: pd.DataFrame,
    monthly_summary: pd.DataFrame,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, str]:
    sns.set_theme(style="whitegrid", palette="deep")
    output_dir.mkdir(parents=True, exist_ok=True)

    bar_chart = output_dir / "sales_by_category_bar.png"
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(
        data=category_summary,
        x="Product Category",
        y="Total_Revenue",
        hue="Product Category",
        dodge=False,
        legend=False,
    )
    ax.set_title("Total Revenue by Category")
    ax.set_xlabel("Product Category")
    ax.set_ylabel("Revenue")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(bar_chart, dpi=200)
    plt.close()

    pie_chart = output_dir / "sales_contribution_pie.png"
    plt.figure(figsize=(8, 8))
    plt.pie(
        category_summary["Total_Revenue"],
        labels=category_summary["Product Category"],
        autopct="%1.1f%%",
        startangle=140,
    )
    plt.title("Revenue Contribution by Category")
    plt.tight_layout()
    plt.savefig(pie_chart, dpi=200)
    plt.close()

    trend_chart = output_dir / "monthly_category_trend.png"
    plt.figure(figsize=(12, 6))
    sns.lineplot(
        data=monthly_summary,
        x="Month",
        y="Sales Amount",
        hue="Product Category",
        marker="o",
    )
    plt.title("Monthly Sales Trend by Category")
    plt.xlabel("Month")
    plt.ylabel("Sales Amount")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(trend_chart, dpi=200)
    plt.close()

    return {
        "bar_chart": bar_chart.name,
        "pie_chart": pie_chart.name,
        "trend_chart": trend_chart.name,
    }


def write_key_findings(
    category_summary: pd.DataFrame,
    monthly_summary: pd.DataFrame,
    region_summary: pd.DataFrame,
) -> list[str]:
    top_category = category_summary.iloc[0]
    low_category = category_summary.iloc[-1]
    top_month = (
        monthly_summary.groupby("Month", as_index=False)["Sales Amount"]
        .sum()
        .sort_values("Sales Amount", ascending=False)
        .iloc[0]
    )
    top_region = region_summary.iloc[0]

    findings = [
        "Sales by Category Analysis - Key Findings",
        "",
        f"Top performing category: {top_category['Product Category']}",
        f"Total revenue: {top_category['Total_Revenue']}",
        f"Total profit: {top_category['Total_Profit']}",
        "",
        f"Lowest performing category by revenue: {low_category['Product Category']}",
        f"Total revenue: {low_category['Total_Revenue']}",
        f"Total profit: {low_category['Total_Profit']}",
        "",
        f"Best sales month overall: {top_month['Month']}",
        f"Monthly revenue: {round(top_month['Sales Amount'], 2)}",
        "",
        f"Top revenue region: {top_region['Region']}",
        f"Regional revenue: {top_region['Total_Revenue']}",
        "",
        "Business recommendation:",
        "Invest more in the strongest categories, review pricing and promotions for weaker categories, and prepare inventory for peak seasonal months.",
    ]

    return findings


def write_key_findings_file(findings: list[str], output_dir: Path = OUTPUT_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "key_findings.txt").write_text("\n".join(findings), encoding="utf-8")


def build_overview_metrics(
    df: pd.DataFrame,
    category_summary: pd.DataFrame,
    monthly_summary: pd.DataFrame,
) -> dict[str, Any]:
    monthly_totals = (
        monthly_summary.groupby("Month", as_index=False)["Sales Amount"]
        .sum()
        .sort_values("Sales Amount", ascending=False)
    )
    top_category = category_summary.iloc[0]
    lowest_category = category_summary.iloc[-1]
    best_month = monthly_totals.iloc[0]

    return {
        "total_revenue": float(round(df["Sales Amount"].sum(), 2)),
        "total_profit": float(round(df["Profit"].sum(), 2)),
        "total_quantity": int(df["Quantity Sold"].sum()),
        "category_count": int(df["Product Category"].nunique()),
        "record_count": int(len(df)),
        "top_category": str(top_category["Product Category"]),
        "lowest_category": str(lowest_category["Product Category"]),
        "best_month": str(best_month["Month"]),
        "best_month_revenue": round(float(best_month["Sales Amount"]), 2),
    }


def analyze_sales_file(file_path: Path, output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    df = load_and_clean_data(file_path)
    category_summary = build_category_summary(df)
    monthly_summary = build_monthly_summary(df)
    region_summary = build_region_summary(df)
    save_outputs(category_summary, monthly_summary, region_summary, output_dir=output_dir)
    charts = create_visualizations(
        category_summary, monthly_summary, output_dir=output_dir
    )
    findings = write_key_findings(category_summary, monthly_summary, region_summary)
    write_key_findings_file(findings, output_dir=output_dir)

    return {
        "clean_data": df,
        "category_summary": category_summary,
        "monthly_summary": monthly_summary,
        "region_summary": region_summary,
        "charts": charts,
        "findings": findings,
        "overview": build_overview_metrics(df, category_summary, monthly_summary),
    }


def main() -> None:
    try:
        result = analyze_sales_file(DATA_FILE, output_dir=OUTPUT_DIR)
    except Exception as exc:
        print(f"Analysis failed: {exc}")
        raise SystemExit(1) from exc

    print("Analysis complete.")
    print(f"Processed records: {len(result['clean_data'])}")
    print(f"Top category: {result['overview']['top_category']}")
    print(f"Output folder: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
