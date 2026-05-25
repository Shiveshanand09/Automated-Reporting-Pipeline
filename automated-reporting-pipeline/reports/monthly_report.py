"""
reports/monthly_report.py
Generates the automated monthly Excel + chart report.
"""

import logging
from datetime import datetime
from pathlib import Path
import calendar

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

logger = logging.getLogger(__name__)

PALETTE = ["#2563EB", "#7C3AED", "#059669", "#D97706", "#DC2626",
           "#0891B2", "#BE185D", "#65A30D"]


def generate_monthly_report(conn, output_dir: Path) -> Path:
    today = datetime.utcnow().date()
    # Use previous full month
    if today.month == 1:
        year, month = today.year - 1, 12
    else:
        year, month = today.year, today.month - 1

    _, last_day = calendar.monthrange(year, month)
    month_start = f"{year}-{month:02d}-01"
    month_end   = f"{year}-{month:02d}-{last_day:02d}"
    month_label = f"{year}-{month:02d}"

    logger.info(f"  Month: {month_start} → {month_end}")

    # ── Sales summary ─────────────────────────────────────────────────────────
    sales_df = pd.read_sql_query(
        """
        SELECT region, product,
               SUM(revenue)    AS revenue,
               SUM(units_sold) AS units,
               COUNT(*)        AS transactions
        FROM   sales
        WHERE  sale_date BETWEEN ? AND ?
        GROUP  BY region, product
        ORDER  BY revenue DESC
        """,
        conn, params=(month_start, month_end),
    )

    weekly_trend = pd.read_sql_query(
        """
        SELECT strftime('%W', sale_date) AS week,
               SUM(revenue)             AS revenue
        FROM   sales
        WHERE  sale_date BETWEEN ? AND ?
        GROUP  BY week
        ORDER  BY week
        """,
        conn, params=(month_start, month_end),
    )

    marketing_df = pd.read_sql_query(
        """
        SELECT channel,
               SUM(spend)       AS spend,
               SUM(impressions) AS impressions,
               SUM(clicks)      AS clicks
        FROM   marketing_spend
        WHERE  spend_date BETWEEN ? AND ?
        GROUP  BY channel
        ORDER  BY spend DESC
        """,
        conn, params=(month_start, month_end),
    )

    tickets_df = pd.read_sql_query(
        """
        SELECT category, status, COUNT(*) AS count
        FROM   support_tickets
        WHERE  created_date BETWEEN ? AND ?
        GROUP  BY category, status
        """,
        conn, params=(month_start, month_end),
    )

    # ── KPI summary ───────────────────────────────────────────────────────────
    total_rev   = sales_df["revenue"].sum() if not sales_df.empty else 0
    total_units = sales_df["units"].sum() if not sales_df.empty else 0
    total_spend = marketing_df["spend"].sum() if not marketing_df.empty else 0
    roas        = total_rev / total_spend if total_spend > 0 else 0

    kpi_df = pd.DataFrame({
        "KPI":   ["Total Revenue", "Units Sold", "Marketing Spend", "ROAS"],
        "Value": [f"${total_rev:,.2f}", f"{total_units:,}", f"${total_spend:,.2f}", f"{roas:.2f}x"],
    })

    # ── Charts ────────────────────────────────────────────────────────────────
    _build_monthly_chart(sales_df, weekly_trend, marketing_df, tickets_df, month_label, output_dir)

    # ── Excel ─────────────────────────────────────────────────────────────────
    file_name = f"monthly_report_{month_label}.xlsx"
    file_path = output_dir / file_name

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        kpi_df.to_excel(writer, sheet_name="KPI Summary", index=False)
        sales_df.to_excel(writer, sheet_name="Sales Detail", index=False)
        weekly_trend.to_excel(writer, sheet_name="Weekly Trend", index=False)
        marketing_df.to_excel(writer, sheet_name="Marketing Performance", index=False)
        tickets_df.to_excel(writer, sheet_name="Support Tickets", index=False)

    logger.info(f"  Excel report: {file_path}")
    return file_path


def _build_monthly_chart(sales_df, weekly_trend, marketing_df, tickets_df, month_label, output_dir):
    sns.set_style("whitegrid")
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle(f"Monthly Executive Report  |  {month_label}",
                 fontsize=17, fontweight="bold", y=0.99)

    # 1. Revenue by region (horizontal bar)
    if not sales_df.empty:
        region_rev = sales_df.groupby("region")["revenue"].sum().sort_values()
        axes[0, 0].barh(region_rev.index, region_rev.values, color=PALETTE)
        axes[0, 0].set_title("Revenue by Region", fontweight="bold")
        axes[0, 0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e3:.0f}K"))

    # 2. Weekly revenue inside month
    if not weekly_trend.empty:
        axes[0, 1].bar(weekly_trend["week"], weekly_trend["revenue"], color=PALETTE[0])
        axes[0, 1].set_title("Weekly Revenue Trend", fontweight="bold")
        axes[0, 1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e3:.0f}K"))
        axes[0, 1].set_xlabel("Week #")

    # 3. Product mix pie
    if not sales_df.empty:
        prod_rev = sales_df.groupby("product")["revenue"].sum()
        axes[0, 2].pie(prod_rev.values, labels=prod_rev.index, colors=PALETTE,
                       autopct="%1.1f%%", startangle=140, textprops={"fontsize": 9})
        axes[0, 2].set_title("Product Revenue Mix", fontweight="bold")

    # 4. Marketing spend by channel
    if not marketing_df.empty:
        axes[1, 0].bar(marketing_df["channel"], marketing_df["spend"], color=PALETTE[2:])
        axes[1, 0].set_title("Marketing Spend by Channel", fontweight="bold")
        axes[1, 0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e3:.0f}K"))
        axes[1, 0].tick_params(axis="x", rotation=30)

    # 5. CTR by channel
    if not marketing_df.empty:
        marketing_df["ctr"] = marketing_df["clicks"] / marketing_df["impressions"] * 100
        axes[1, 1].bar(marketing_df["channel"], marketing_df["ctr"], color=PALETTE[4:])
        axes[1, 1].set_title("Click-Through Rate by Channel (%)", fontweight="bold")
        axes[1, 1].set_ylabel("CTR (%)")
        axes[1, 1].tick_params(axis="x", rotation=30)

    # 6. Support tickets by category
    if not tickets_df.empty:
        cat_counts = tickets_df.groupby("category")["count"].sum()
        axes[1, 2].bar(cat_counts.index, cat_counts.values, color=PALETTE)
        axes[1, 2].set_title("Support Tickets by Category", fontweight="bold")
        axes[1, 2].tick_params(axis="x", rotation=30)

    plt.tight_layout()
    chart_path = output_dir / f"monthly_chart_{month_label}.png"
    fig.savefig(chart_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return chart_path
