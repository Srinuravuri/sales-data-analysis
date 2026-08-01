"""Full sales data analysis: cleaning -> KPIs -> charts -> dashboard -> report.

Run from the project root:
    python scripts/analysis.py

Outputs (in output/):
    dashboard.html       - visual dashboard (open in browser)
    summary_report.md    - business insights report
    *.png                - individual charts
"""

import base64
import io
import os
import sys
from datetime import datetime

# Windows console is cp1252 by default and cannot print "₹" — force UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import pandas as pd

# ---------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------
COLORS = ["#7c6cff", "#38d9ff", "#ff6ec7", "#34d399", "#fbbf24", "#4dabf7", "#ff8787"]
plt.rcParams.update({
    "figure.facecolor": "#0f1526",
    "axes.facecolor": "#0f1526",
    "axes.edgecolor": "#2b3a5e",
    "axes.labelcolor": "#c9d2ec",
    "text.color": "#e8ecf8",
    "xtick.color": "#9aa5c3",
    "ytick.color": "#9aa5c3",
    "grid.color": "#1e2946",
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
})

OUT = "output"
DATA = "data/sales_data.csv"


def ensure_output():
    os.makedirs(OUT, exist_ok=True)


def load_and_clean() -> pd.DataFrame:
    """Load data and clean it (the 'data cleaning' stage)."""
    df = pd.read_csv(DATA)

    # 1. Parse dates
    df["order_date"] = pd.to_datetime(df["order_date"])

    # 2. Drop duplicates
    before = len(df)
    df = df.drop_duplicates(subset=["order_id"])
    print(f"Duplicates removed: {before - len(df)}")

    # 3. Handle missing values
    print(f"Missing values before: {df.isna().sum().sum()}")
    df = df.dropna(subset=["sales", "profit"])
    df = df.fillna({"discount_pct": 0})

    # 4. Sanity checks
    df = df[df["sales"] > 0]

    # 5. Derived columns
    df["year"] = df["order_date"].dt.year
    df["month"] = df["order_date"].dt.month
    df["year_month"] = df["order_date"].dt.to_period("M").astype(str)
    df["margin_pct"] = df["profit"] / df["sales"] * 100

    print(f"Final rows: {len(df):,}")
    return df


def save_chart(fig, name: str):
    path = os.path.join(OUT, name)
    fig.savefig(path, bbox_inches="tight", dpi=110)
    plt.close(fig)
    print(f"  chart -> {path}")
    return path


def charts(df: pd.DataFrame):
    """Build all charts and return {key: path}."""

    # 1. Monthly sales trend
    monthly = df.groupby("year_month")["sales"].sum()
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.plot(monthly.index, monthly.values, color=COLORS[1], linewidth=2.2, marker="o", markersize=3)
    ax.set_title("Monthly Sales Trend (2022–2024)")
    ax.set_ylabel("Sales (₹)")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(alpha=0.4)
    fig.tight_layout()
    c1 = save_chart(fig, "monthly_sales_trend.png")

    # 2. Sales by category
    cat = df.groupby("category")["sales"].sum().sort_values()
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.barh(cat.index, cat.values, color=COLORS[0])
    ax.set_title("Total Sales by Category")
    ax.set_xlabel("Sales (₹)")
    ax.grid(alpha=0.4, axis="x")
    fig.tight_layout()
    c2 = save_chart(fig, "sales_by_category.png")

    # 3. Profit margin by category
    margin = df.groupby("category")["margin_pct"].mean().sort_values()
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.barh(margin.index, margin.values, color=COLORS[2])
    ax.set_title("Average Profit Margin by Category (%)")
    ax.set_xlabel("Margin %")
    ax.grid(alpha=0.4, axis="x")
    fig.tight_layout()
    c3 = save_chart(fig, "margin_by_category.png")

    # 4. Sales by region
    reg = df.groupby("region")["sales"].sum().sort_values()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(reg.index, reg.values, color=[COLORS[3], COLORS[4], COLORS[5], COLORS[1]])
    ax.set_title("Total Sales by Region")
    ax.set_ylabel("Sales (₹)")
    ax.grid(alpha=0.4, axis="y")
    fig.tight_layout()
    c4 = save_chart(fig, "sales_by_region.png")

    # 5. Top 10 products
    top = df.groupby("product_name")["sales"].sum().nlargest(10).sort_values()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(top.index, top.values, color=COLORS[4])
    ax.set_title("Top 10 Products by Revenue")
    ax.set_xlabel("Sales (₹)")
    ax.grid(alpha=0.4, axis="x")
    fig.tight_layout()
    c5 = save_chart(fig, "top_products.png")

    return {"monthly": c1, "category": c2, "margin": c3, "region": c4, "top": c5}


def kpis(df: pd.DataFrame) -> dict:
    return {
        "revenue": df["sales"].sum(),
        "profit": df["profit"].sum(),
        "orders": len(df),
        "units": df["units"].sum(),
        "avg_order": df["sales"].mean(),
        "margin": df["profit"].sum() / df["sales"].sum() * 100,
    }


def insights(df: pd.DataFrame, k: dict) -> list:
    lines = []

    # Growth
    by_year = df.groupby("year")["sales"].sum()
    if len(by_year) >= 2:
        y1, y2 = by_year.iloc[-2], by_year.iloc[-1]
        growth = (y2 - y1) / y1 * 100
        lines.append(f"Revenue **grew {growth:.1f}%** from {by_year.index[-2]} to {by_year.index[-1]} "
                     f"(₹{y1/1e5:.2f}L → ₹{y2/1e5:.2f}L).")

    # Best month
    monthly = df.groupby(df["order_date"].dt.to_period("M"))["sales"].sum()
    best = monthly.idxmax()
    lines.append(f"The **strongest sales month** was {best} — consistent with Indian festival-season "
                 f"demand (Diwali ~ Oct/Nov).")

    # Top category & margin laggard
    cat_sales = df.groupby("category")["sales"].sum()
    cat_margin = df.groupby("category")["margin_pct"].mean()
    lines.append(f"**{cat_sales.idxmax()}** is the top revenue category "
                 f"(₹{cat_sales.max()/1e5:.2f}L), but it runs the **thinnest margin** "
                 f"({cat_margin.min():.1f}%) — volume with pressure on profitability.")
    laggard = cat_margin.idxmin()
    best = cat_margin.idxmax()
    lines.append(f"**{best}** earns the healthiest margin ({cat_margin.max():.1f}%) — "
                 f"its pricing/discount playbook is worth extending to other categories.")

    # Region
    reg = df.groupby("region")["sales"].sum()
    lines.append(f"**{reg.idxmax()} India** leads regional sales (₹{reg.max()/1e5:.2f}L); "
                 f"**{reg.idxmin()}** lags (₹{reg.min()/1e5:.2f}L) — expansion opportunity.")

    # Top product
    top_prod = df.groupby("product_name")["sales"].sum().idxmax()
    lines.append(f"**{top_prod}** is the single best-selling product by revenue.")

    # Discount effect
    disc = df.groupby(pd.cut(df["discount_pct"], [0, 5, 15, 30, 50]))[["sales", "profit"]].sum()
    disc.columns = ["sales", "profit"]
    disc["margin"] = disc["profit"] / disc["sales"] * 100
    deep = disc["margin"].idxmin()
    lines.append(f"Orders with **{deep} discounts (i.e. 15–30% off)** earn the lowest margin "
                 f"({disc['margin'].min():.1f}%) — check whether those discounts are worth the volume.")

    return lines


def write_report(df: pd.DataFrame, k: dict, ins: list, chart_paths: dict):
    md = []
    md.append("# Sales Data Analysis — Summary Report\n")
    md.append(f"*Generated {datetime.now().strftime('%d %b %Y %H:%M')} · "
              f"{len(df):,} transactions · 2022–2024 · Indian retail*\n")

    md.append("## 📊 Key Metrics\n")
    md.append("| Metric | Value |")
    md.append("|--------|-------|")
    md.append(f"| Total Revenue | ₹{k['revenue']:,.0f} |")
    md.append(f"| Total Profit | ₹{k['profit']:,.0f} |")
    md.append(f"| Profit Margin | {k['margin']:.1f}% |")
    md.append(f"| Orders | {k['orders']:,} |")
    md.append(f"| Units Sold | {k['units']:,} |")
    md.append(f"| Avg Order Value | ₹{k['avg_order']:,.0f} |")

    md.append("\n## 💡 Key Insights\n")
    for i, line in enumerate(ins, 1):
        md.append(f"{i}. {line}")

    md.append("\n## 🎯 Recommendations\n")
    md.append("1. **Lean into festival season**: stock and promote top categories (especially "
              "electronics) before Oct–Nov to capture peak demand.")
    md.append("2. **Fix the margin drag**: renegotiate or reprice the lowest-margin category and "
              "tighten deep-discount thresholds.")
    md.append("3. **Expand the lagging region**: targeted campaigns and logistics investment in the "
              "weakest region mirroring the leader's playbook.")
    md.append("4. **Double down on best sellers**: feature the top products in bundles and "
              "cross-sells to lift average order value.")

    md.append("\n## 📈 Charts\n")
    for label, path in chart_paths.items():
        md.append(f"- `{label}`: {os.path.basename(path)}")

    path = os.path.join(OUT, "summary_report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"report -> {path}")


def write_dashboard(k: dict, ins: list, chart_paths: dict):
    def img_b64(path):
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()

    cards = [
        ("Total Revenue", f"₹{k['revenue']/1e5:.2f} L", "💰"),
        ("Total Profit", f"₹{k['profit']/1e5:.2f} L", "📈"),
        ("Profit Margin", f"{k['margin']:.1f}%", "🎯"),
        ("Orders", f"{k['orders']:,}", "🧾"),
        ("Avg Order Value", f"₹{k['avg_order']:,.0f}", "🛒"),
        ("Units Sold", f"{k['units']:,}", "📦"),
    ]

    card_html = "".join(
        f'<div class="card"><div class="ico">{i}</div><div class="val">{v}</div>'
        f'<div class="lbl">{l}</div></div>'
        for l, v, i in cards
    )

    ins_html = "".join(f"<li>{t}</li>" for t in ins[:5])

    chart_html = ""
    layout = [
        ("monthly", "Monthly Sales Trend"),
        ("category", "Sales by Category"),
        ("margin", "Profit Margin by Category"),
        ("region", "Sales by Region"),
        ("top", "Top 10 Products"),
    ]
    for key, title in layout:
        chart_html += f'<div class="panel"><h3>{title}</h3><img src="{img_b64(chart_paths[key])}" alt="{title}"></div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sales Dashboard — Srinu Ravuri</title>
<style>
  :root {{ --bg:#0a0e1a; --card:#131b30; --border:#1e2946; --text:#e8ecf8; --muted:#9aa5c3; }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:var(--bg); color:var(--text); font-family:'Segoe UI',Arial,sans-serif; padding:32px 20px; }}
  .wrap {{ max-width:1080px; margin:0 auto; }}
  h1 {{ font-size:1.8rem; margin-bottom:4px; }}
  .sub {{ color:var(--muted); margin-bottom:24px; }}
  .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:14px; margin-bottom:24px; }}
  .card {{ background:var(--card); border:1px solid var(--border); border-radius:14px; padding:18px; text-align:center; }}
  .card .ico {{ font-size:1.5rem; }}
  .card .val {{ font-size:1.35rem; font-weight:800; margin:6px 0 2px; }}
  .card .lbl {{ color:var(--muted); font-size:.82rem; }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
  .panel {{ background:var(--card); border:1px solid var(--border); border-radius:14px; padding:16px; }}
  .panel.full {{ grid-column:1/-1; }}
  .panel h3 {{ font-size:1rem; margin-bottom:10px; }}
  .panel img {{ width:100%; height:auto; border-radius:8px; }}
  .insights {{ background:var(--card); border:1px solid var(--border); border-radius:14px; padding:18px; margin-top:16px; }}
  .insights h2 {{ font-size:1.1rem; margin-bottom:10px; }}
  .insights li {{ color:var(--muted); margin:6px 0 6px 18px; font-size:.95rem; }}
  footer {{ margin-top:24px; color:var(--muted); font-size:.82rem; text-align:center; }}
  @media (max-width:800px) {{ .grid {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<div class="wrap">
  <h1>📊 Indian Retail Sales Dashboard</h1>
  <div class="sub">2022–2024 · Analysis by Srinu Ravuri · Aspiring Data Analyst</div>
  <div class="cards">{card_html}</div>
  <div class="grid">{chart_html}</div>
  <div class="insights">
    <h2>💡 Key Insights</h2>
    <ol>{ins_html}</ol>
  </div>
  <footer>Generated by scripts/analysis.py · pandas + matplotlib</footer>
</div>
</body>
</html>"""

    path = os.path.join(OUT, "dashboard.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"dashboard -> {path}")


def main():
    ensure_output()
    print("Loading & cleaning data...")
    df = load_and_clean()

    print("\nBuilding charts...")
    chart_paths = charts(df)

    print("\nComputing KPIs & insights...")
    k = kpis(df)
    print(f"  revenue=₹{k['revenue']:,.0f}  profit=₹{k['profit']:,.0f}  margin={k['margin']:.1f}%")
    ins = insights(df, k)

    print("\nWriting report & dashboard...")
    write_report(df, k, ins, chart_paths)
    write_dashboard(k, ins, chart_paths)

    print("\n✅ Done! Open output/dashboard.html in your browser.")


if __name__ == "__main__":
    main()
