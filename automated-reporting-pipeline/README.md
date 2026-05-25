# 📊 Automated Reporting Pipeline

> **Eliminates ~40% of manual analyst hours** by automating weekly and monthly report generation using Python scripts and SQL stored procedures.

[![CI Pipeline](https://github.com/YOUR_USERNAME/automated-reporting-pipeline/actions/workflows/pipeline.yml/badge.svg)](https://github.com/YOUR_USERNAME/automated-reporting-pipeline/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🚀 What It Does

| Before | After |
|--------|-------|
| Analysts manually pulled data from multiple sources every week | Fully automated — runs on schedule via GitHub Actions |
| Copy-pasting figures into Excel reports (error-prone) | Python generates consistent, formatted Excel + charts |
| ~40% of analyst time spent on recurring reports | Zero manual effort for standard report cycles |
| No audit trail | Every run logged in `report_run_log` table |

---

## 🏗️ Architecture

```
automated-reporting-pipeline/
│
├── pipeline.py              ← Main entry point (CLI + orchestrator)
├── db.py                    ← DB connection factory (PostgreSQL / SQLite)
├── utils.py                 ← Email dispatch, formatting helpers
│
├── reports/
│   ├── weekly_report.py     ← Weekly Excel + 4-panel chart generator
│   └── monthly_report.py    ← Monthly Excel + 6-panel chart generator
│
├── sql/
│   ├── schema.sql           ← Database schema (PostgreSQL)
│   ├── sp_weekly_report.sql ← Stored procedure: weekly summary
│   └── sp_monthly_report.sql← Stored procedure: monthly executive summary
│
├── dashboard/
│   └── dashboard.html       ← Power BI-style executive dashboard (HTML)
│
├── tests/
│   └── test_pipeline.py     ← pytest unit tests
│
├── reports/output/          ← Generated report files (git-ignored)
│
└── .github/workflows/
    └── pipeline.yml         ← GitHub Actions CI/CD (scheduled + manual)
```

---

## ⚡ Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/automated-reporting-pipeline.git
cd automated-reporting-pipeline
pip install -r requirements.txt
```

### 2. Run Locally (SQLite dev mode)

```bash
# Generate all reports (weekly + monthly)
python pipeline.py --type all --dry-run

# Weekly only
python pipeline.py --type weekly --dry-run

# Monthly only
python pipeline.py --type monthly --dry-run
```

Reports saved to `reports/output/`.

### 3. Run Tests

```bash
pytest tests/ -v
```

### 4. Open Dashboard

Open `dashboard/dashboard.html` in any browser — no server needed.

---

## 🔧 Configuration

Create a `.env` file (never commit this):

```env
# Database
DB_TYPE=postgres          # 'postgres' or 'sqlite'
DB_HOST=your-db-host
DB_PORT=5432
DB_NAME=reporting_db
DB_USER=analyst
DB_PASSWORD=your_password

# Email delivery
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASS=your_app_password
REPORT_FROM=reports@yourcompany.com
REPORT_TO=analyst1@co.com,analyst2@co.com
```

---

## 🚦 GitHub Actions Deployment

### Automated Schedule

| Report   | Trigger                        |
|----------|-------------------------------|
| Weekly   | Every Monday at 07:00 UTC      |
| Monthly  | 1st of every month at 06:00 UTC |

### Manual Trigger

Go to **Actions → Automated Reporting Pipeline → Run workflow** and choose:
- Report type: `weekly` / `monthly` / `all`
- Dry run: `true` (skips email) / `false`

### Required Secrets

Add these in **Settings → Secrets and variables → Actions**:

| Secret         | Description                      |
|----------------|----------------------------------|
| `DB_TYPE`      | `postgres` or `sqlite`           |
| `DB_HOST`      | Database hostname                |
| `DB_NAME`      | Database name                    |
| `DB_USER`      | Database user                    |
| `DB_PASSWORD`  | Database password                |
| `SMTP_HOST`    | SMTP server                      |
| `SMTP_USER`    | SMTP login                       |
| `SMTP_PASS`    | SMTP password / app password     |
| `REPORT_FROM`  | Sender email                     |
| `REPORT_TO`    | Comma-separated recipient emails |

---

## 📁 Output Files

Each pipeline run produces:

```
reports/output/
├── weekly_report_2025-05-19.xlsx    ← Excel: 4 sheets (Summary, Sales, Tickets, …)
├── weekly_chart_2025-05-19.png      ← 4-panel chart (Revenue, Trend, Mix, Support)
├── monthly_report_2025-05.xlsx      ← Excel: 5 sheets (KPIs, Sales, Marketing, …)
└── monthly_chart_2025-05.png        ← 6-panel executive chart
```

GitHub Actions archives these as **build artifacts** retained for 30 days.

---

## 🗄️ SQL Stored Procedures

```sql
-- Run weekly report for last week (PostgreSQL)
CALL sp_generate_weekly_report(
    DATE_TRUNC('week', CURRENT_DATE)::DATE - 7,
    DATE_TRUNC('week', CURRENT_DATE)::DATE - 1
);

-- Run monthly report for last month
CALL sp_generate_monthly_report(
    EXTRACT(YEAR  FROM CURRENT_DATE - INTERVAL '1 month')::INT,
    EXTRACT(MONTH FROM CURRENT_DATE - INTERVAL '1 month')::INT
);
```

---

## 🛠️ Tech Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| Language    | Python 3.11                         |
| Data        | pandas, openpyxl                    |
| Charts      | matplotlib, seaborn                 |
| Database    | PostgreSQL (prod) · SQLite (dev)     |
| SQL         | Stored procedures (PL/pgSQL)        |
| Scheduling  | GitHub Actions (cron)               |
| Email       | Python smtplib                      |
| Testing     | pytest                              |
| Dashboard   | HTML + Chart.js                     |

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

*Built by [Shivesh Anand](https://linkedin.com/in/shiveshanand)*
