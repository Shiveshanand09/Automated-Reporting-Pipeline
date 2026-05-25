"""
reports/weekly_report.py
Generates the automated weekly Excel + chart report.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

logger = logging.getLogger(__name__)

PALETTE = ["#2563EB", "#7C3AED", "#059669", "#D97706", "#DC2626"]


def generate_weekly_report(conn, output_dir: Path) -> Path:
    today      = datetime.utcnow().date()
    week_start = today - timedelta(days=today.weekday() + 7)
    week_end   = week_start + timedelta(days=6)

    logger.info(f"  Week: {week_start} → {week_end}")

    # ── Pull data ─────────────────────────────────────────────────────────────
    sales_df = pd.read_sql_query(
        """
        SELECT region, product, SUM(revenue) AS revenue, SUM(units_sold) AS units
        FROM   sales
        WHERE  sale_date BETWEEN ? AND ?
        GROUP  BY region, product
        ORDER  BY revenue DESC
        """,
        conn,
        params=(str(week_start), str(week_end)),
    )

    daily_df = pd.read_sql_query(
        """
        SELECT sale_date AS date, SUM(revenue) AS revenue
        FROM   sales
        WHERE  sale_date BETWEEN ? AND ?
        GROUP  BY sale_date
        ORDER  BY sale_date
        """,
        conn,
        params=(str(week_start), str(week_end)),
    )

    tickets_df = pd.read_sql_query(
        """
        SELECT category, status, COUNT(*) AS count
        FROM   support_tickets
        WHERE  created_date BETWEEN ? AND ?
        GROUP  BY category, status
        """,
        conn,
        params=(str(week_start), str(week_end)),
    )

    # ── Build charts ──────────────────────────────────────────────────────────
    chart_path = _build_weekly_chart(sales_df, daily_df, tickets_df, week_start, week_end, output_dir)

    # ── Write Excel ───────────────────────────────────────────────────────────
    file_name  = f"weekly_report_{week_start}.xlsx"
    file_path  = output_dir / file_name

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        sales_df.to_excel(writer, sheet_name="Sales by Region-Product", index=False)
        daily_df.to_excel(writer, sheet_name="Daily Revenue", index=False)
        tickets_df.to_excel(writer, sheet_name="Support Tickets", index=False)

        summary = pd.DataFrame({
            "Metric": ["Total Revenue", "Units Sold", "Avg Daily Revenue", "Open Tickets"],
            "Value": [
                f"${sales_df['revenue'].sum():,.2f}",
                f"{sales_df['units'].sum():,}",
                f"${daily_df['revenue'].mean():,.2f}" if len(daily_df) else "N/A",
                str(tickets_df[tickets_df["status"] == "open"]["count"].sum()) if len(tickets_df) else "0",
            ],
        })
        summary.to_excel(writer, sheet_name="Summary", index=False)

    logger.info(f"  Excel report: {file_path}")
    return file_path


def _build_weekly_chart(sales_df, daily_df, tickets_df, week_start, week_end, output_dir):
    sns.set_style("whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(
        f"Weekly Report  |  {week_start} – {week_end}",
        fontsize=16, fontweight="bold", y=0.98
    )

    # 1. Revenue by Region
    if not sales_df.empty:
        region_rev = sales_df.groupby("region")["revenue"].sum().sort_values(ascending=False)
        axes[0, 0].bar(region_rev.index, region_rev.values, color=PALETTE)
        axes[0, 0].set_title("Revenue by Region", fontweight="bold")
        axes[0, 0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        axes[0, 0].tick_params(axis="x", rotation=30)
    else:
        axes[0, 0].text(0.5, 0.5, "No data", ha="center", va="center")

    # 2. Daily revenue trend
    if not daily_df.empty:
        axes[0, 1].plot(daily_df["date"], daily_df["revenue"], marker="o", color=PALETTE[0], linewidth=2)
        axes[0, 1].fill_between(daily_df["date"], daily_df["revenue"], alpha=0.15, color=PALETTE[0])
        axes[0, 1].set_title("Daily Revenue Trend", fontweight="bold")
        axes[0, 1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        axes[0, 1].tick_params(axis="x", rotation=30)
    else:
        axes[0, 1].text(0.5, 0.5, "No data", ha="center", va="center")

    # 3. Product mix
    if not sales_df.empty:
        prod_rev = sales_df.groupby("product")["revenue"].sum()
        axes[1, 0].pie(prod_rev.values, labels=prod_rev.index, colors=PALETTE,
                       autopct="%1.1f%%", startangle=140)
        axes[1, 0].set_title("Product Revenue Mix", fontweight="bold")
    else:
        axes[1, 0].text(0.5, 0.5, "No data", ha="center", va="center")

    # 4. Support tickets by status
    if not tickets_df.empty:
        status_counts = tickets_df.groupby("status")["count"].sum()
        axes[1, 1].bar(status_counts.index, status_counts.values, color=PALETTE[2:])
        axes[1, 1].set_title("Support Tickets by Status", fontweight="bold")
    else:
        axes[1, 1].text(0.5, 0.5, "No data", ha="center", va="center")

    plt.tight_layout()
    chart_path = output_dir / f"weekly_chart_{week_start}.png"
    fig.savefig(chart_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return chart_path
