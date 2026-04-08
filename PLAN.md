# AI/BI Dashboards & Genie Lab — Build Plan

## Overview

A **40-45 minute**, fully standalone, hands-on lab that teaches students how to build AI/BI (Lakeview) dashboards and Genie spaces in Databricks. Follows the same structural patterns as the Lakeflow Jobs & CI/CD lab: a central lab notebook that walks students through everything, with inline markdown instructions and executable code cells.

**Domain**: Supply chain & operations
**Time split**: ~18 min dashboards / ~22 min Genie

---

## Dataset Design

### Domain: Supply Chain & Operations

Four tables modeling a mid-size company's supply chain:

| Table | Description | ~Rows | Key Columns |
|-------|-------------|-------|-------------|
| `suppliers` | Supplier directory | ~15 | `supplier_id`, `supplier_name`, `region`, `country`, `lead_time_days`, `reliability_rating` |
| `products` | Product catalog with cost info | ~30 | `product_id`, `product_name`, `category`, `unit_cost`, `supplier_id`, `weight_kg` |
| `purchase_orders` | Orders placed to suppliers | ~800 | `order_id`, `product_id`, `supplier_id`, `order_date`, `expected_delivery_date`, `actual_delivery_date`, `quantity`, `unit_cost`, `status` |
| `inventory_snapshots` | Daily warehouse stock levels | ~2,000 | `snapshot_date`, `product_id`, `warehouse`, `quantity_on_hand`, `reorder_point`, `quantity_on_order` |

**Data characteristics** (designed to produce interesting dashboard/Genie results):
- 3 product categories: Electronics Components, Raw Materials, Packaging
- 4 warehouses: Chicago, Atlanta, Seattle, Dallas
- 5 supplier regions: North America, Europe, Asia-Pacific, South America, Africa
- Statuses: delivered (65%), in_transit (20%), delayed (10%), cancelled (5%)
- Deliberate patterns: Asia-Pacific suppliers have longer lead times but lower cost; some products frequently dip below reorder point; seasonal ordering spikes
- Date range: 6 months (Oct 2024 - Mar 2025)
- Deterministic generation via `random.seed(42)`

---

## Lab Structure

### Directory Layout

```
ai-bi-dashboards-and-genie/
├── README.md                        # Setup guide & lab overview
├── lab_notebook.py                  # Central lab notebook (START HERE)
├── data/
│   └── setup_tables.py              # Generates all 4 tables into Unity Catalog
└── solutions/
    ├── sample_dashboard_queries.py   # Reference queries for dashboard widgets
    └── genie_instructions.md         # Reference Genie tuning instructions & sample Qs
```

**Design choice**: Unlike the lakeflow lab (which had separate pipeline notebooks), this lab keeps things simpler since students build dashboards and Genie spaces entirely through the UI. The `data/setup_tables.py` notebook is the only supporting notebook — it generates and writes all 4 tables. The `solutions/` folder provides reference material students can peek at if stuck.

---

### Lab Notebook Outline (`lab_notebook.py`)

The central notebook is organized into **6 parts** plus setup and wrap-up:

---

#### Setup (~3 min)
- **What happens**: Create a Unity Catalog schema (`ai_bi_lab`), generate all 4 tables via `data/setup_tables.py`, verify row counts
- **Student action**: Run the setup cell(s), confirm tables appear in Catalog Explorer
- **Implementation**: Single `%run ./data/setup_tables` call after setting up widgets for `catalog` (default: `workspace`)

---

#### Part 1: Explore the Data (~3 min)
- **What happens**: Guided SQL queries to understand the dataset — preview each table, key relationships, interesting patterns
- **Student action**: Run provided SQL cells, observe results
- **Content**:
  - `SELECT * FROM suppliers LIMIT 10` — see supplier regions and ratings
  - `SELECT category, COUNT(*) ... GROUP BY category` — understand product categories
  - `SELECT status, COUNT(*), ROUND(AVG(quantity), 0) FROM purchase_orders GROUP BY status` — see order distribution
  - Quick join: orders with delayed deliveries by supplier region
- **Purpose**: Build mental model of the data before building visuals

---

#### Part 2: Build an AI/BI Dashboard (~15 min)
- **What happens**: Step-by-step instructions for building a supply chain operations dashboard in the Databricks UI
- **Student action**: Follow instructions in the Databricks Dashboard editor (UI-based, no code)
- **Sections**:

  **2a. Create the Dashboard (~2 min)**
  - Navigate to Dashboards > Create Dashboard
  - Name it "Supply Chain Operations - Dev"
  - Select the SQL warehouse

  **2b. Add KPI Counter Widgets (~3 min)**
  - Total Purchase Orders (count)
  - On-Time Delivery Rate (% of orders where `actual_delivery_date <= expected_delivery_date`)
  - Total Spend (sum of `quantity * unit_cost`)
  - Current Low-Stock Items (count where `quantity_on_hand < reorder_point`)
  - Each widget: provide the SQL query, explain the visualization type, walk through config

  **2c. Add Chart Widgets (~5 min)**
  - **Spend by Supplier Region** — bar chart from `purchase_orders` joined to `suppliers`
  - **Orders Over Time** — line chart showing monthly order volume, colored by status
  - **Delivery Performance by Supplier** — bar chart of avg days late/early per supplier
  - **Inventory Levels vs. Reorder Points** — grouped bar chart from latest `inventory_snapshots`
  - Each widget: SQL query provided, chart type selection, axis/color configuration explained

  **2d. Add a Table Widget (~2 min)**
  - Top 10 products by total spend with supplier name, category, total quantity, total cost
  - Configure column formatting (currency, numbers)

  **2e. Layout & Polish (~3 min)**
  - Rearrange widgets into a logical layout (KPIs on top row, charts below, table at bottom)
  - Add text/header widgets to create sections ("Key Metrics", "Spend Analysis", "Delivery Performance", "Inventory Health")
  - Add a date range filter on `order_date`
  - Publish the dashboard

---

#### Part 3: Genie Space Fundamentals (~8 min)
- **What happens**: Create a Genie space, add tables, ask natural language questions, review SQL
- **Student action**: Build and interact with a Genie space in the UI

  **3a. Create the Genie Space (~2 min)**
  - Navigate to Genie > New Genie Space
  - Name: "Supply Chain Analyst"
  - Add all 4 tables
  - Select SQL warehouse

  **3b. Ask Questions & Review SQL (~6 min)**
  - Walk through 5-6 progressively complex questions:
    1. "How many purchase orders do we have?" (simple count)
    2. "What is our on-time delivery rate?" (calculated metric)
    3. "Which supplier has the most delayed orders?" (join + aggregation)
    4. "Show me monthly spend trends by product category" (time series + grouping)
    5. "Which products are currently below their reorder point?" (inventory query)
    6. "Compare average lead time and delivery performance across supplier regions" (multi-metric)
  - For each: observe the generated SQL, check if the result is correct, note where Genie gets it right vs. where it needs help
  - Discuss: how Genie infers table joins, handles ambiguity, chooses visualizations

---

#### Part 4: Tune the Genie Space (~8 min)
- **What happens**: Improve Genie's accuracy with instructions, sample questions, and certified queries
- **Student action**: Add tuning artifacts in the Genie space settings

  **4a. Add General Instructions (~2 min)**
  - Add business context instructions, e.g.:
    - "On-time delivery means actual_delivery_date <= expected_delivery_date"
    - "Spend is calculated as quantity * unit_cost"
    - "When asked about 'current' inventory, use the most recent snapshot_date"
    - "Lead time is measured in days from order_date to actual_delivery_date"
  - Re-ask a question that was previously ambiguous — observe improvement

  **4b. Add Sample Questions (~2 min)**
  - Add 4-5 curated sample questions that represent common business queries
  - These appear as suggestions for end users and help Genie understand question patterns

  **4c. Add Certified SQL Queries (~4 min)**
  - Create 2-3 certified queries for business-critical metrics:
    1. "Supplier Scorecard" — reliability rating, avg lead time, on-time %, total orders per supplier
    2. "Inventory Risk Report" — products below reorder point with days-of-supply estimate
  - Explain: certified queries are trusted, curated SQL that Genie will prefer over generating its own
  - Re-ask related questions — observe Genie now uses certified queries

---

#### Part 5: Benchmark & Iterate (~6 min)
- **What happens**: Run evaluation questions, assess Genie quality, iterate on tuning
- **Student action**: Systematic benchmarking workflow

  **5a. Define Benchmark Questions (~2 min)**
  - Create a set of 8-10 benchmark questions spanning:
    - Simple lookups ("How many suppliers are in Asia-Pacific?")
    - Calculations ("What is the average order value?")
    - Joins ("Which warehouse has the most low-stock items?")
    - Time-based ("How has spend changed month over month?")
    - Ambiguous ("Who are our best suppliers?" — tests whether instructions guide interpretation)
  - For each, write down the expected correct answer/SQL pattern

  **5b. Run the Benchmark (~2 min)**
  - Ask each question in the Genie space
  - Record: correct, partially correct, or incorrect for each
  - Identify patterns in failures (missing context? wrong join? ambiguous term?)

  **5c. Iterate & Re-test (~2 min)**
  - Based on failures, add/refine instructions or certified queries
  - Re-run the failed questions
  - Observe improvement (or identify remaining gaps)
  - Discuss: this iterative loop is the real-world workflow for Genie space curation

---

#### Lab Complete (~1 min)
- Summary of what was built:
  - 4 supply chain tables in Unity Catalog
  - An AI/BI dashboard with KPIs, charts, tables, and filters
  - A tuned Genie space with instructions, sample questions, certified queries, and benchmarks
- Next steps / further exploration:
  - Add dashboard to a Lakeflow Job for scheduled refresh
  - Share the Genie space with team members and monitor usage
  - Explore Genie space conversation history and feedback
  - Connect dashboards to alerts for threshold-based notifications
  - Version-control dashboard JSON via Databricks Asset Bundles

---

## File-by-File Build Plan

### 1. `README.md`
- What you'll build (1-paragraph overview)
- Prerequisites (Databricks workspace with Unity Catalog, SQL warehouse, permissions)
- Getting started (clone as Git Folder, open `lab_notebook.py`)
- Repository structure (tree diagram)
- Lab outline (table with parts, timing, description)

### 2. `lab_notebook.py`
- ~500-600 lines
- Databricks notebook format using `# MAGIC %md` for markdown and `# COMMAND` separators
- Setup section with `%run ./data/setup_tables` and verification queries
- Parts 1-5 with inline markdown instructions and SQL/Python cells
- All dashboard and Genie instructions as rich markdown (step-by-step with bold action items)
- SQL queries provided inline for dashboard widgets (students copy-paste into dashboard editor)
- Benchmark question table provided as markdown

### 3. `data/setup_tables.py`
- ~200-250 lines
- Accepts `catalog` widget (default: `workspace`)
- Schema name: `ai_bi_lab`
- Generates all 4 tables using Python (random + seed for determinism)
- Writes to Unity Catalog as managed tables
- Prints summary with row counts

### 4. `solutions/sample_dashboard_queries.py`
- ~80-100 lines
- All SQL queries used in the dashboard, labeled with widget name
- Students can reference this if they get stuck on a query

### 5. `solutions/genie_instructions.md`
- ~50-60 lines
- Reference copy of Genie instructions, sample questions, and certified queries
- Useful for students who want to compare their tuning with a reference

---

## Key Design Decisions

1. **UI-first approach**: Dashboard building and Genie space creation are done entirely through the Databricks UI. The lab notebook provides queries and instructions but doesn't programmatically create dashboards. This is more accessible and mirrors how most users will actually work.

2. **Standalone data setup**: A separate `data/setup_tables.py` notebook generates all tables. This keeps the lab notebook clean and focused on teaching, while making setup a single `%run` call.

3. **Solutions folder**: Provides reference material without giving away the answers upfront. Students are encouraged to try on their own first.

4. **Supply chain domain**: Rich enough for interesting queries (joins across 4 tables, time series, inventory thresholds) but intuitive enough that students don't need domain expertise.

5. **Benchmark-driven Genie tuning**: The benchmark/iterate loop in Part 5 teaches students the real-world workflow — not just "add instructions" but "measure, adjust, re-measure."

6. **No programmatic dashboard creation**: Keeps the lab focused on the user experience and saves time. The lakeflow lab already covers JSON dashboards and DABs.

---

## Timing Breakdown

| Section | Minutes | Cumulative |
|---------|---------|------------|
| Setup | 3 | 3 |
| Part 1: Explore the Data | 3 | 6 |
| Part 2: Build Dashboard | 15 | 21 |
| Part 3: Genie Fundamentals | 8 | 29 |
| Part 4: Tune the Genie Space | 8 | 37 |
| Part 5: Benchmark & Iterate | 6 | 43 |
| Wrap-up | 1 | 44 |

**Total: ~44 minutes** (within the 40-45 min target)

---

## Build Order

1. `data/setup_tables.py` — data generation first (everything depends on this)
2. `solutions/sample_dashboard_queries.py` — write the queries that will be used in the dashboard
3. `solutions/genie_instructions.md` — write the reference Genie tuning content
4. `lab_notebook.py` — the main deliverable, references queries from step 2
5. `README.md` — final, once structure is locked in
