# AI/BI Dashboards & Genie Spaces

A hands-on lab for learning how to build **AI/BI (Lakeview) dashboards** and **Genie spaces** in Databricks using a supply chain operations dataset.

## What You'll Build

By the end of this lab you will have:
- **4 supply chain tables** in Unity Catalog — suppliers, products, purchase orders, and inventory snapshots
- An **AI/BI dashboard** with KPI counters, charts, a data table, interactive filters, and cross-filtering
- A **tuned Genie space** with descriptions, synonyms, joins, SQL expressions, instructions, and SQL queries and functions
- A **benchmark suite** of 10 evaluation questions with a feedback review workflow

## Prerequisites

- A Databricks workspace (free tier works!)
- Unity Catalog enabled (enabled by default on all Databricks workspaces)
- Access to a SQL warehouse (Serverless or Pro)

## Getting Started

### 1. Clone this repo as a Git Folder in your Databricks workspace

1. In your Databricks workspace, go to **Workspace** in the left sidebar
2. Click **Create** → **Git folder**
3. Paste this repository's URL
4. Click **Create Git folder**

### 2. Open the lab notebook

Navigate to `lab_notebook.py` in the cloned folder and open it. All lab instructions are inside.

---

## Repository Structure

```
ai-bi-dashboards-and-genie/
├── README.md                              # This file
├── lab_notebook.py                        # Central lab notebook — START HERE
│
├── data/
│   └── setup_tables.py                    # Generates all 4 supply chain tables
│
└── solutions/
    ├── sample_dashboard_queries.py        # Reference SQL queries for dashboard widgets
    └── genie_instructions.md              # Reference Genie tuning content
```

## Lab Outline

| Part | Topic | Time |
|------|-------|------|
| **Setup** | Generate supply chain data (suppliers, products, orders, inventory) | ~3 min |
| **Part 1** | Explore the data with guided SQL queries | ~3 min |
| **Part 2** | Build an AI/BI dashboard with KPIs, charts, filters, and cross-filtering | ~18 min |
| **Part 3** | Create a Genie space, ask questions, and try Agent mode | ~10 min |
| **Part 4** | Tune the Genie space — descriptions, synonyms, joins, SQL expressions, instructions, and SQL queries and functions | ~14 min |
| **Part 5** | Benchmark, iterate, and use the feedback loop | ~8 min |

**Total: ~56 minutes**

## Data Model

```
suppliers ──┐
            ├──> purchase_orders
products ───┘
                 inventory_snapshots (weekly stock levels per warehouse)
```
