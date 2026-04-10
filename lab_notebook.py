# Databricks notebook source

# MAGIC %md
# MAGIC # AI/BI Dashboards & Genie Spaces
# MAGIC ### Hands-On Lab
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## What you'll build
# MAGIC
# MAGIC In this lab you will build an AI/BI dashboard and a tuned Genie space on top of a
# MAGIC supply chain operations dataset:
# MAGIC
# MAGIC | Step | What you'll do |
# MAGIC |------|----------------|
# MAGIC | **Setup** | Generate supply chain data — suppliers, products, purchase orders, and inventory snapshots |
# MAGIC | **Part 1** | Explore the four tables with guided SQL queries |
# MAGIC | **Part 2** | Build an **AI/BI (Lakeview) dashboard** with KPI counters, charts, filters, and **cross-filtering** |
# MAGIC | **Part 3** | Create a **Genie space**, ask natural language questions, try **Agent mode**, and review generated SQL |
# MAGIC | **Part 4** | Tune the Genie space with **descriptions**, **instructions**, **SQL expressions**, and **SQL queries and functions** |
# MAGIC | **Part 5** | Define **benchmark questions**, run them, iterate on tuning, and use the **feedback loop** |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Prerequisites
# MAGIC
# MAGIC - This notebook is running in a Databricks workspace with **Unity Catalog** enabled
# MAGIC   (all free-tier workspaces have UC by default)
# MAGIC - This repository has been cloned as a **Git Folder** in your workspace
# MAGIC   (`Workspace` → `Create` → `Git folder`)
# MAGIC - You have access to a **SQL warehouse** (Serverless or Pro)
# MAGIC
# MAGIC > **Tip:** Run each cell with `Shift + Enter` and read the markdown cells between
# MAGIC > them — they contain the lab instructions.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Setup — Generate Supply Chain Data
# MAGIC
# MAGIC The cell below creates a Unity Catalog schema and populates it with four tables:
# MAGIC
# MAGIC | Table | Description | Rows |
# MAGIC |-------|-------------|------|
# MAGIC | `suppliers` | Supplier directory with regions, countries, lead times, and reliability ratings | ~15 |
# MAGIC | `products` | Product catalog across three categories with cost and weight info | ~30 |
# MAGIC | `purchase_orders` | Six months of purchase orders with delivery tracking | ~800 |
# MAGIC | `inventory_snapshots` | 17 weeks of warehouse stock levels across four locations | ~2,000 |
# MAGIC
# MAGIC Run this cell once before proceeding.

# COMMAND ----------

# MAGIC %run ./data/setup_tables

# COMMAND ----------

# MAGIC %md
# MAGIC ### Verify the setup
# MAGIC
# MAGIC The queries below confirm the tables were created successfully.  You should see
# MAGIC row counts matching the table above.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 'suppliers' AS table_name, COUNT(*) AS row_count FROM workspace.ai_bi_lab.suppliers
# MAGIC UNION ALL
# MAGIC SELECT 'products', COUNT(*) FROM workspace.ai_bi_lab.products
# MAGIC UNION ALL
# MAGIC SELECT 'purchase_orders', COUNT(*) FROM workspace.ai_bi_lab.purchase_orders
# MAGIC UNION ALL
# MAGIC SELECT 'inventory_snapshots', COUNT(*) FROM workspace.ai_bi_lab.inventory_snapshots

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Part 1 — Explore the Data
# MAGIC
# MAGIC Before building dashboards and Genie spaces, let's understand what we're working with.
# MAGIC Run each query below and observe the results.
# MAGIC
# MAGIC ### 1a. Suppliers
# MAGIC
# MAGIC Our supply chain spans **5 regions** and **15 suppliers**.  Notice that lead times
# MAGIC and reliability ratings vary significantly by region.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM workspace.ai_bi_lab.suppliers ORDER BY region, supplier_name

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1b. Products by category
# MAGIC
# MAGIC Products fall into three categories.  Each category has different cost profiles
# MAGIC and ordering patterns.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT category, COUNT(*) AS product_count,
# MAGIC        ROUND(AVG(unit_cost), 2) AS avg_unit_cost,
# MAGIC        ROUND(MIN(unit_cost), 2) AS min_cost,
# MAGIC        ROUND(MAX(unit_cost), 2) AS max_cost
# MAGIC FROM workspace.ai_bi_lab.products
# MAGIC GROUP BY category
# MAGIC ORDER BY category

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1c. Purchase order distribution
# MAGIC
# MAGIC ~800 purchase orders over 6 months with four statuses.  Note the distribution —
# MAGIC most orders are delivered, but delayed and cancelled orders create interesting
# MAGIC analytical questions.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT status, COUNT(*) AS order_count,
# MAGIC        ROUND(AVG(quantity), 0) AS avg_quantity,
# MAGIC        ROUND(SUM(quantity * unit_cost), 2) AS total_spend
# MAGIC FROM workspace.ai_bi_lab.purchase_orders
# MAGIC GROUP BY status
# MAGIC ORDER BY order_count DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1d. Delayed deliveries by supplier region
# MAGIC
# MAGIC Which regions have the most delivery issues?  This join across `purchase_orders`
# MAGIC and `suppliers` is the kind of question we'll later ask Genie in natural language.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT s.region,
# MAGIC        COUNT(*) AS delayed_orders,
# MAGIC        ROUND(AVG(DATEDIFF(po.actual_delivery_date, po.expected_delivery_date)), 1) AS avg_days_late
# MAGIC FROM workspace.ai_bi_lab.purchase_orders po
# MAGIC JOIN workspace.ai_bi_lab.suppliers s ON po.supplier_id = s.supplier_id
# MAGIC WHERE po.status = 'delivered'
# MAGIC   AND po.actual_delivery_date > po.expected_delivery_date
# MAGIC GROUP BY s.region
# MAGIC ORDER BY delayed_orders DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Part 2 — Build an AI/BI Dashboard
# MAGIC
# MAGIC In this section you'll build a **Supply Chain Operations** dashboard using the
# MAGIC Databricks AI/BI dashboard editor.  The dashboard will have:
# MAGIC
# MAGIC - **4 KPI counters** across the top
# MAGIC - **3 charts** for visual analysis
# MAGIC - **1 table widget** showing top products
# MAGIC - **A region filter** for interactive exploration
# MAGIC
# MAGIC > **Important:** All of the work in Part 2 happens in the **dashboard editor UI** —
# MAGIC > not in this notebook.  The SQL queries are provided below for you to copy-paste
# MAGIC > into the dashboard's dataset editor.
# MAGIC >
# MAGIC > If you get stuck on any query, check `solutions/sample_dashboard_queries.py` for
# MAGIC > a complete reference.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2a. Create the dashboard
# MAGIC
# MAGIC 1. In the left sidebar, click **Dashboards**
# MAGIC 2. Click the blue **Create dashboard** button
# MAGIC 3. Name your dashboard: **Supply Chain Operations**
# MAGIC 4. You're now in the dashboard canvas editor
# MAGIC
# MAGIC > **What is an AI/BI dashboard?**  AI/BI dashboards (formerly Lakeview dashboards)
# MAGIC > are Databricks' built-in visualization layer.  Each widget is backed by a SQL query
# MAGIC > (called a **dataset**) that runs against your SQL warehouse.  Dashboards can be
# MAGIC > scheduled for refresh, embedded, and shared with your team.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2b. Add KPI counter widgets
# MAGIC
# MAGIC Add four counter widgets across the top of your dashboard.  For each one, you'll
# MAGIC first create a dataset, then add a widget and configure the visualization.
# MAGIC
# MAGIC **Create the dataset:**
# MAGIC 1. Click the **Data** tab in the right-hand sidebar
# MAGIC 2. Click **Add SQL dataset**
# MAGIC 3. Paste the SQL query into the query editor
# MAGIC 4. Click **Run** to verify the query returns results
# MAGIC 5. Give the dataset a descriptive name (e.g., "Total Purchase Orders")
# MAGIC
# MAGIC **Add and configure the counter widget:**
# MAGIC 1. Back on the canvas, click the **Add a visualization** button to add a widget
# MAGIC 2. In the right-hand sidebar, select the dataset you just created from the **Dataset** dropdown
# MAGIC 3. Under **Visualization type**, select **Counter**
# MAGIC 4. In the **Value** dropdown, choose the column to display (details below for each KPI)
# MAGIC 5. Optionally configure formatting options like prefix, suffix, or label text in the
# MAGIC    sections below the value selector
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC #### KPI 1: Total Purchase Orders
# MAGIC
# MAGIC ```sql
# MAGIC SELECT s.region, COUNT(*) AS total_orders
# MAGIC FROM workspace.ai_bi_lab.purchase_orders po
# MAGIC JOIN workspace.ai_bi_lab.suppliers s ON po.supplier_id = s.supplier_id
# MAGIC GROUP BY s.region
# MAGIC ```
# MAGIC
# MAGIC - **Visualization type:** Counter
# MAGIC - **Value column:** `total_orders`
# MAGIC - **Configuration:** In the right-hand sidebar, set **Value** to `total_orders`.
# MAGIC   Optionally add a label like "Total POs" in the **Label** field.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC #### KPI 2: On-Time Delivery Rate
# MAGIC
# MAGIC ```sql
# MAGIC SELECT s.region, ROUND(
# MAGIC   COUNT(CASE WHEN po.actual_delivery_date <= po.expected_delivery_date THEN 1 END) * 1.0
# MAGIC   / COUNT(po.actual_delivery_date), 3
# MAGIC ) AS on_time_pct
# MAGIC FROM workspace.ai_bi_lab.purchase_orders po
# MAGIC JOIN workspace.ai_bi_lab.suppliers s ON po.supplier_id = s.supplier_id
# MAGIC WHERE po.actual_delivery_date IS NOT NULL
# MAGIC GROUP BY s.region
# MAGIC ```
# MAGIC
# MAGIC - **Visualization type:** Counter
# MAGIC - **Value column:** `on_time_pct`
# MAGIC - **Configuration:** In the right-hand sidebar, set **Value** to `on_time_pct`.
# MAGIC   Then set the **Type** to **Percentage** — the counter will automatically format
# MAGIC   the decimal value as a percent (e.g., 0.853 displays as "85.3%").
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC #### KPI 3: Total Spend
# MAGIC
# MAGIC ```sql
# MAGIC SELECT s.region, ROUND(SUM(po.quantity * po.unit_cost), 2) AS total_spend
# MAGIC FROM workspace.ai_bi_lab.purchase_orders po
# MAGIC JOIN workspace.ai_bi_lab.suppliers s ON po.supplier_id = s.supplier_id
# MAGIC WHERE po.status != 'cancelled'
# MAGIC GROUP BY s.region
# MAGIC ```
# MAGIC
# MAGIC - **Visualization type:** Counter
# MAGIC - **Value column:** `total_spend`
# MAGIC - **Configuration:** In the right-hand sidebar, set **Value** to `total_spend`.
# MAGIC   Then scroll down to the formatting section and add `$` in the **Prefix** field.
# MAGIC   This displays the value as e.g. "$1,234,567.89".
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC #### KPI 4: Current Low-Stock Items
# MAGIC
# MAGIC ```sql
# MAGIC SELECT s.region, COUNT(*) AS low_stock_count
# MAGIC FROM workspace.ai_bi_lab.inventory_snapshots i
# MAGIC JOIN workspace.ai_bi_lab.products p ON i.product_id = p.product_id
# MAGIC JOIN workspace.ai_bi_lab.suppliers s ON p.supplier_id = s.supplier_id
# MAGIC WHERE i.snapshot_date = (SELECT MAX(snapshot_date) FROM workspace.ai_bi_lab.inventory_snapshots)
# MAGIC   AND i.quantity_on_hand < i.reorder_point
# MAGIC GROUP BY s.region
# MAGIC ```
# MAGIC
# MAGIC - **Visualization type:** Counter
# MAGIC - **Value column:** `low_stock_count`
# MAGIC - **Configuration:** In the right-hand sidebar, set **Value** to `low_stock_count`.
# MAGIC   Optionally add a label like "Low-Stock Items" in the **Label** field.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2c. Add chart widgets
# MAGIC
# MAGIC Now add three charts below the KPI row.  Same process — create a dataset with the
# MAGIC SQL query, then add the visualization.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC #### Chart 1: Spend by Supplier Region
# MAGIC
# MAGIC ```sql
# MAGIC SELECT s.region, ROUND(SUM(po.quantity * po.unit_cost), 2) AS total_spend
# MAGIC FROM workspace.ai_bi_lab.purchase_orders po
# MAGIC JOIN workspace.ai_bi_lab.suppliers s ON po.supplier_id = s.supplier_id
# MAGIC WHERE po.status != 'cancelled'
# MAGIC GROUP BY s.region
# MAGIC ORDER BY total_spend DESC
# MAGIC ```
# MAGIC
# MAGIC - **Visualization type:** Bar chart
# MAGIC - **X-axis:** `region`
# MAGIC - **Y-axis:** `total_spend`
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC #### Chart 2: Orders Over Time
# MAGIC
# MAGIC ```sql
# MAGIC SELECT s.region,
# MAGIC        DATE_TRUNC('month', po.order_date) AS order_month,
# MAGIC        po.status,
# MAGIC        COUNT(*) AS order_count
# MAGIC FROM workspace.ai_bi_lab.purchase_orders po
# MAGIC JOIN workspace.ai_bi_lab.suppliers s ON po.supplier_id = s.supplier_id
# MAGIC GROUP BY s.region, order_month, po.status
# MAGIC ORDER BY order_month, po.status
# MAGIC ```
# MAGIC
# MAGIC - **Visualization type:** Line chart
# MAGIC - **X-axis:** `order_month`
# MAGIC - **Y-axis:** `order_count`
# MAGIC - **Color / Group by:** `status`
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC #### Chart 3: Delivery Performance by Supplier
# MAGIC
# MAGIC ```sql
# MAGIC SELECT s.region, s.supplier_name,
# MAGIC        ROUND(AVG(DATEDIFF(po.actual_delivery_date, po.expected_delivery_date)), 1) AS avg_days_variance
# MAGIC FROM workspace.ai_bi_lab.purchase_orders po
# MAGIC JOIN workspace.ai_bi_lab.suppliers s ON po.supplier_id = s.supplier_id
# MAGIC WHERE po.actual_delivery_date IS NOT NULL
# MAGIC GROUP BY s.region, s.supplier_name
# MAGIC ORDER BY avg_days_variance
# MAGIC ```
# MAGIC
# MAGIC - **Visualization type:** Bar chart
# MAGIC - **X-axis:** `supplier_name`
# MAGIC - **Y-axis:** `avg_days_variance`
# MAGIC - **Note:** Negative values = early delivery, positive = late.  This chart quickly
# MAGIC   reveals which suppliers consistently miss or beat their expected delivery dates.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2d. Add a table widget
# MAGIC
# MAGIC #### Top 10 Products by Spend
# MAGIC
# MAGIC **Step 1 — Create the dataset:**
# MAGIC
# MAGIC 1. Click the **Data** tab in the right-hand sidebar
# MAGIC 2. Click **Add SQL dataset**
# MAGIC 3. Paste the following query into the query editor:
# MAGIC
# MAGIC ```sql
# MAGIC SELECT s.region, p.product_name, p.category, s.supplier_name,
# MAGIC        SUM(po.quantity) AS total_quantity,
# MAGIC        ROUND(SUM(po.quantity * po.unit_cost), 2) AS total_spend
# MAGIC FROM workspace.ai_bi_lab.purchase_orders po
# MAGIC JOIN workspace.ai_bi_lab.products p ON po.product_id = p.product_id
# MAGIC JOIN workspace.ai_bi_lab.suppliers s ON po.supplier_id = s.supplier_id
# MAGIC WHERE po.status != 'cancelled'
# MAGIC GROUP BY s.region, p.product_name, p.category, s.supplier_name
# MAGIC ORDER BY total_spend DESC
# MAGIC LIMIT 10
# MAGIC ```
# MAGIC
# MAGIC 4. Click **Run** to verify the query returns results
# MAGIC 5. Name the dataset "Top 10 Products by Spend"
# MAGIC
# MAGIC **Step 2 — Use the AI assistant to create the widget:**
# MAGIC
# MAGIC Instead of manually configuring this widget, let's try the dashboard authoring
# MAGIC assistant.  Click the **AI assistant** icon (sparkle icon) at the top of the canvas
# MAGIC and type a prompt like:
# MAGIC
# MAGIC > Create a table widget using the "Top 10 Products by Spend" dataset.
# MAGIC > Format total_spend as currency and total_quantity with a thousands separator.
# MAGIC
# MAGIC Review what the assistant generates — it should produce a table widget with the
# MAGIC formatting applied.
# MAGIC
# MAGIC **Fallback — configure manually if needed:**
# MAGIC
# MAGIC If the assistant doesn't get it right, you can configure the widget yourself:
# MAGIC 1. Click the **+** button on the canvas to add a widget
# MAGIC 2. In the right-hand sidebar, select the "Top 10 Products by Spend" dataset from
# MAGIC    the **Dataset** dropdown
# MAGIC 3. Under **Visualization type**, select **Table**
# MAGIC 4. Format `total_spend` as currency
# MAGIC 5. Format `total_quantity` with a thousands separator

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2e. Layout and polish
# MAGIC
# MAGIC Now arrange your dashboard into a clean, readable layout:
# MAGIC
# MAGIC 1. **Top row:** Place the 4 KPI counters side by side
# MAGIC 2. **Second row:** "Spend by Supplier Region" and "Orders Over Time" side by side
# MAGIC 3. **Third row:** "Delivery Performance by Supplier" (full width)
# MAGIC 4. **Bottom:** "Top 10 Products by Spend" table (full width)
# MAGIC
# MAGIC **Add section headers:**
# MAGIC - Add a **Text** widget above the KPIs: "Key Metrics"
# MAGIC - Add a **Text** widget above the second row: "Spend & Order Analysis"
# MAGIC - Add a **Text** widget above the third row: "Delivery Performance"
# MAGIC
# MAGIC **Add a region filter:**
# MAGIC 1. Click **Add a filter** at the top of the canvas
# MAGIC 2. Set the filter field to `region`
# MAGIC 3. Choose **Multi-select** as the filter type
# MAGIC 4. Because every dataset now includes a `region` column, this single filter
# MAGIC    controls all widgets on the dashboard — KPI counters, charts, and the table
# MAGIC
# MAGIC **Publish:**
# MAGIC - Click **Publish** in the top-right corner to make the dashboard available for sharing
# MAGIC
# MAGIC ### 2f. Try the global filter and understand cross-filtering
# MAGIC
# MAGIC **Try the global region filter:**
# MAGIC
# MAGIC 1. Use the **Region** filter at the top of the dashboard to select one or more
# MAGIC    regions (e.g., select "Asia-Pacific")
# MAGIC 2. Observe how **every widget** updates — KPI counters, charts, and the table all
# MAGIC    filter to show only data for the selected region(s)
# MAGIC 3. Clear the filter and try selecting multiple regions to compare
# MAGIC
# MAGIC This works because every dataset includes a `region` column, and the global filter
# MAGIC is explicitly bound to that column across all datasets.  This is the primary way
# MAGIC users will interactively explore the dashboard.
# MAGIC
# MAGIC > **A note on cross-filtering:** AI/BI dashboards also support **cross-filtering** —
# MAGIC > clicking an element in one chart (e.g., a bar or slice) automatically filters
# MAGIC > other widgets.  However, cross-filtering only works between widgets that share
# MAGIC > the **same dataset**.  In our dashboard, each widget has its own dataset, so
# MAGIC > clicking a bar in "Spend by Supplier Region" won't filter the other widgets.
# MAGIC >
# MAGIC > If you wanted cross-filtering to work, you would need multiple widgets to
# MAGIC > reference a single shared dataset.  For example, if two charts both pointed to
# MAGIC > the same dataset, clicking a value in one would filter the other.  This is a
# MAGIC > useful technique when designing dashboards with tightly related visualizations.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Part 3 — Genie Space Fundamentals
# MAGIC
# MAGIC **Genie** is Databricks' natural language interface for data.  You describe what you
# MAGIC want in plain English, and Genie writes and runs the SQL for you.
# MAGIC
# MAGIC A **Genie space** is a curated environment where you specify which tables are
# MAGIC available, add business context, and provide trusted queries — making Genie
# MAGIC accurate enough for production use by business teams.
# MAGIC
# MAGIC In this section you'll create a Genie space, ask questions, and see how well it
# MAGIC performs out of the box before tuning.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3a. Create the Genie space
# MAGIC
# MAGIC 1. In the left sidebar, click **Genie**
# MAGIC 2. Click **New** in the top-right corner
# MAGIC 3. Configure the space:
# MAGIC    - **Title:** Supply Chain Analyst
# MAGIC    - **Description (optional):** Natural language analytics for supply chain operations — suppliers, orders, inventory, and delivery performance
# MAGIC    - **SQL Warehouse:** Select your SQL warehouse
# MAGIC    - **Tables:** Add all four tables:
# MAGIC      - `workspace.ai_bi_lab.suppliers`
# MAGIC      - `workspace.ai_bi_lab.products`
# MAGIC      - `workspace.ai_bi_lab.purchase_orders`
# MAGIC      - `workspace.ai_bi_lab.inventory_snapshots`
# MAGIC 4. Click **Save**
# MAGIC
# MAGIC You now have a Genie space connected to your supply chain data.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3b. Ask questions and review the SQL
# MAGIC
# MAGIC Try each of the following questions in your Genie space.  After each answer:
# MAGIC - **Review the generated SQL** — click "View query" or the SQL tab to see what Genie wrote
# MAGIC - **Check the result** — is the answer correct?  Does it match what you'd expect from
# MAGIC   the data you explored in Part 1?
# MAGIC - **Note any issues** — we'll address these in Parts 4 and 5
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Question 1 (simple count):**
# MAGIC > How many purchase orders do we have?
# MAGIC
# MAGIC *Expected: A count of all rows in `purchase_orders` (~800)*
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Question 2 (calculated metric):**
# MAGIC > What is our on-time delivery rate?
# MAGIC
# MAGIC *Expected: Percentage of delivered orders where `actual_delivery_date <= expected_delivery_date`.
# MAGIC Pay attention — does Genie know to exclude orders without an actual delivery date?*
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Question 3 (join + aggregation):**
# MAGIC > Which supplier has the most delayed orders?
# MAGIC
# MAGIC *Expected: Joins `purchase_orders` to `suppliers`, filters for `status = 'delayed'`,
# MAGIC groups by supplier name, orders by count descending*
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Question 4 (time series):**
# MAGIC > Show me monthly spend trends by product category
# MAGIC
# MAGIC *Expected: Joins `purchase_orders` to `products`, groups by month and category,
# MAGIC sums `quantity * unit_cost`*
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Question 5 (inventory query):**
# MAGIC > Which products are currently below their reorder point?
# MAGIC
# MAGIC *Expected: Filters `inventory_snapshots` to the most recent `snapshot_date`, joins
# MAGIC to `products`, filters where `quantity_on_hand < reorder_point`*
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Question 6 (multi-metric):**
# MAGIC > Compare average lead time and delivery performance across supplier regions
# MAGIC
# MAGIC *Expected: Joins `purchase_orders` to `suppliers`, groups by region, computes avg
# MAGIC lead time (from `lead_time_days` or actual dates) and some delivery performance metric*
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Question 7 (Agent mode — multi-step reasoning):**
# MAGIC > Why did our spend increase in November and December compared to October?
# MAGIC > Break down the drivers.
# MAGIC
# MAGIC *This question triggers **Agent mode** — Genie's multi-step reasoning capability.
# MAGIC Instead of writing a single query, Genie will:*
# MAGIC 1. *Run multiple queries in sequence (or in parallel) to gather evidence*
# MAGIC 2. *Stream its "thinking" so you can follow the reasoning*
# MAGIC 3. *Synthesize findings into a narrative answer with supporting data*
# MAGIC
# MAGIC *Watch for the thinking traces that appear inline — they show how Genie decomposes
# MAGIC a complex business question into analytical steps.  Agent mode activates automatically
# MAGIC when a question requires multi-step reasoning.*
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC > **Reflection:** How did Genie do?  Most likely it handled Questions 1 and 3 well,
# MAGIC > but may have struggled with nuance on Questions 2, 5, and 6.  Common issues:
# MAGIC > - Not knowing which date columns to compare for "on-time"
# MAGIC > - Not knowing to filter for the latest snapshot date for "current" inventory
# MAGIC > - Choosing arbitrary metrics for "performance"
# MAGIC >
# MAGIC > Question 7 (Agent mode) should have produced a richer, multi-step analysis —
# MAGIC > but even Agent mode benefits from the tuning we'll do next.
# MAGIC >
# MAGIC > These are exactly the kinds of issues that **tuning** addresses in the next part.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Part 4 — Tune the Genie Space
# MAGIC
# MAGIC Out-of-the-box Genie understands your table schemas but not your **business logic**.
# MAGIC Tuning bridges this gap through the Genie space **Settings** panel, where you
# MAGIC configure metadata, rules, and trusted SQL that teach Genie how your business works.
# MAGIC
# MAGIC | Mechanism | Where to find it | What it does |
# MAGIC |-----------|-----------------|-------------|
# MAGIC | **Table & column descriptions** | Settings → Tables | Human-readable context for each table and column |
# MAGIC | **Synonyms** | Settings → Tables (per column) | Map business terms to actual column names |
# MAGIC | **Join relationships** | Settings → Tables | Explicitly define how tables connect |
# MAGIC | **SQL expressions** | Settings → SQL expressions | Reusable measures, filters, and dimensions (the semantic layer) |
# MAGIC | **General instructions** | Settings → Instructions | Business rules and definitions |
# MAGIC | **Common questions** | Settings → Common questions | Curated examples that appear as suggestions |
# MAGIC | **SQL queries and functions** | Settings → SQL queries and functions | Trusted, pre-written SQL for critical metrics |
# MAGIC
# MAGIC > If you get stuck on what to add, check `solutions/genie_instructions.md` for
# MAGIC > reference content.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4a. Add table and column descriptions with synonyms
# MAGIC
# MAGIC Genie reads Unity Catalog metadata, so table and column descriptions in
# MAGIC Unity Catalog are automatically available to Genie.  The setup script already
# MAGIC added descriptions for the `suppliers`, `products`, and `inventory_snapshots`
# MAGIC tables — but we intentionally left **`purchase_orders`** undescribed so you
# MAGIC can practice adding them yourself.
# MAGIC
# MAGIC 1. In your Genie space, open **Settings** (gear icon) and go to the **Tables**
# MAGIC    section
# MAGIC 2. Click on the **`purchase_orders`** table and add a **table description**:
# MAGIC
# MAGIC > Six months of purchase orders (Oct 2024 – Mar 2025) tracking the full order
# MAGIC > lifecycle from placement through delivery. Each order links to a product and
# MAGIC > supplier, with dates for expected and actual delivery. Use this table to
# MAGIC > analyze spend, delivery performance, and order volume trends.
# MAGIC
# MAGIC 3. Then add these **column descriptions**:
# MAGIC
# MAGIC | Column | Description |
# MAGIC |--------|-------------|
# MAGIC | `order_id` | Unique purchase order identifier (e.g. PO-00001) |
# MAGIC | `product_id` | Foreign key to the products table |
# MAGIC | `supplier_id` | Foreign key to the suppliers table |
# MAGIC | `order_date` | Date the purchase order was placed |
# MAGIC | `expected_delivery_date` | Date the supplier committed to deliver by |
# MAGIC | `actual_delivery_date` | Date the order was actually received; NULL if not yet delivered |
# MAGIC | `quantity` | Number of units ordered |
# MAGIC | `unit_cost` | Price per unit at time of order |
# MAGIC | `status` | Order status: delivered, in_transit, delayed, or cancelled |
# MAGIC
# MAGIC 4. Add these **synonyms** (these map business terms to column names):
# MAGIC
# MAGIC | Business term | Maps to |
# MAGIC |---------------|---------|
# MAGIC | cost | `unit_cost` |
# MAGIC | price | `unit_cost` |
# MAGIC | ETA | `expected_delivery_date` |
# MAGIC | received date | `actual_delivery_date` |
# MAGIC | order value | `quantity * unit_cost` |
# MAGIC
# MAGIC 5. **Save** the changes
# MAGIC 6. Re-ask: **"What is the total order value for orders with an ETA in January 2025?"**
# MAGIC    — Genie should now correctly map "order value" to `quantity * unit_cost` and
# MAGIC    "ETA" to `expected_delivery_date`.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4b. Define join relationships
# MAGIC
# MAGIC Genie can often infer joins from matching column names, but **explicitly defining
# MAGIC join relationships** eliminates guesswork — especially when column names don't
# MAGIC match across tables or when there are multiple possible join paths.
# MAGIC
# MAGIC 1. In **Settings → Tables**, find the **Join relationships** section
# MAGIC 2. Add the following relationships:
# MAGIC
# MAGIC | Left table | Right table | Join type | Join condition |
# MAGIC |-----------|------------|-----------|----------------|
# MAGIC | `purchase_orders` | `suppliers` | Inner | `purchase_orders.supplier_id = suppliers.supplier_id` |
# MAGIC | `purchase_orders` | `products` | Inner | `purchase_orders.product_id = products.product_id` |
# MAGIC | `inventory_snapshots` | `products` | Inner | `inventory_snapshots.product_id = products.product_id` |
# MAGIC | `products` | `suppliers` | Inner | `products.supplier_id = suppliers.supplier_id` |
# MAGIC
# MAGIC 3. **Save** the changes
# MAGIC
# MAGIC > **Why this matters:** Without explicit joins, Genie might join
# MAGIC > `purchase_orders` to `suppliers` through `products` (two hops) instead of
# MAGIC > directly — producing correct but slower SQL.  Or worse, it might pick the
# MAGIC > wrong join path entirely.  Explicit joins remove this ambiguity.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4c. Add SQL expressions
# MAGIC
# MAGIC **SQL expressions** are reusable building blocks — measures, filters, and
# MAGIC dimensions that capture your business definitions once and let Genie use them
# MAGIC everywhere.  Think of them as the **semantic layer** for your Genie space.
# MAGIC
# MAGIC 1. In **Settings**, go to the **SQL expressions** section
# MAGIC 2. Add the following expressions:
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Expression 1 — Measure: `total_spend`**
# MAGIC - **Type:** Measure
# MAGIC - **Expression:** `SUM(purchase_orders.quantity * purchase_orders.unit_cost)`
# MAGIC - **Synonyms:** spend, total cost
# MAGIC - **Instructions:** Exclude cancelled orders when calculating total spend
# MAGIC
# MAGIC **Expression 2 — Measure: `on_time_delivery_rate`**
# MAGIC - **Type:** Measure
# MAGIC - **Expression:** `COUNT(CASE WHEN purchase_orders.actual_delivery_date <= purchase_orders.expected_delivery_date THEN 1 END) * 100.0 / NULLIF(COUNT(purchase_orders.actual_delivery_date), 0)`
# MAGIC - **Synonyms:** on-time rate, OTD rate, delivery performance
# MAGIC - **Instructions:** Only include orders where actual_delivery_date is not null
# MAGIC
# MAGIC **Expression 3 — Filter: `latest_snapshot`**
# MAGIC - **Type:** Filter
# MAGIC - **Expression:** `inventory_snapshots.snapshot_date = (SELECT MAX(snapshot_date) FROM workspace.ai_bi_lab.inventory_snapshots)`
# MAGIC - **Synonyms:** current inventory, latest inventory
# MAGIC - **Instructions:** Use this filter when the user asks about "current" or "latest" inventory levels
# MAGIC
# MAGIC **Expression 4 — Filter: `low_stock`**
# MAGIC - **Type:** Filter
# MAGIC - **Expression:** `inventory_snapshots.quantity_on_hand < inventory_snapshots.reorder_point`
# MAGIC - **Synonyms:** at-risk items, below reorder point
# MAGIC - **Instructions:** Use this filter when the user asks about low-stock or at-risk inventory items
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC 3. **Save** the expressions
# MAGIC 4. Re-ask: **"What is our total spend by supplier region?"**
# MAGIC    — Genie should now use the `total_spend` expression, automatically excluding
# MAGIC    cancelled orders without needing a text instruction to remind it.
# MAGIC
# MAGIC > **SQL expressions vs. text instructions:** Both can define "total spend."  The
# MAGIC > difference: a text instruction says *"spend means quantity * unit_cost, exclude
# MAGIC > cancelled"* and hopes Genie follows it.  A SQL expression provides the exact
# MAGIC > formula and filter — it's deterministic and reusable.  Use SQL expressions for
# MAGIC > quantitative definitions; use text instructions for qualitative guidance.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4d. Add SQL queries and functions
# MAGIC
# MAGIC SQL queries and functions are the most powerful tuning tool.  They're pre-written,
# MAGIC **trusted** SQL that Genie will use instead of generating its own when a user
# MAGIC asks a related question.
# MAGIC
# MAGIC 1. In the Genie space settings, find the **SQL queries and functions** section
# MAGIC 2. Add the following two queries:
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC #### Query 1: Total spend by supplier region
# MAGIC
# MAGIC **Question:** What is the total spend by supplier region?
# MAGIC
# MAGIC ```sql
# MAGIC SELECT s.region,
# MAGIC        ROUND(SUM(po.quantity * po.unit_cost), 2) AS total_spend
# MAGIC FROM workspace.ai_bi_lab.purchase_orders po
# MAGIC JOIN workspace.ai_bi_lab.suppliers s ON po.supplier_id = s.supplier_id
# MAGIC WHERE po.status != 'cancelled'
# MAGIC GROUP BY s.region
# MAGIC ORDER BY total_spend DESC
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC #### Query 2: Monthly order counts by status
# MAGIC
# MAGIC **Question:** How many orders do we have each month by status?
# MAGIC
# MAGIC ```sql
# MAGIC SELECT DATE_TRUNC('month', order_date) AS order_month,
# MAGIC        status,
# MAGIC        COUNT(*) AS order_count
# MAGIC FROM workspace.ai_bi_lab.purchase_orders
# MAGIC GROUP BY order_month, status
# MAGIC ORDER BY order_month, status
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC 3. **Save** the queries
# MAGIC 4. Now test them — ask Genie:
# MAGIC    > What is the total spend by region?
# MAGIC
# MAGIC    And:
# MAGIC    > Show me monthly order counts by status
# MAGIC
# MAGIC    Genie should use your saved queries directly.  Check the SQL tab to confirm.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4e. Add general instructions
# MAGIC
# MAGIC General instructions provide qualitative business context that doesn't fit into
# MAGIC SQL expressions, descriptions, or SQL queries and functions.  Use them for things like
# MAGIC abbreviations, formatting preferences, business processes, and domain terminology.
# MAGIC
# MAGIC 1. In your Genie space, click the **gear icon** (Settings) in the top-right
# MAGIC 2. Find the **General instructions** section
# MAGIC 3. Paste the following as a hyphen-separated list:
# MAGIC
# MAGIC > - The four order statuses are: in_transit, delayed, delivered, and cancelled. The typical lifecycle is in_transit → delivered, but orders can be marked as delayed or cancelled at any point.
# MAGIC > - "PO" is short for purchase order. "OTD" stands for on-time delivery. "MOQ" means minimum order quantity.
# MAGIC > - When displaying monetary values, round to 2 decimal places and use USD.
# MAGIC > - When displaying percentages, round to 1 decimal place.
# MAGIC > - Supplier regions are: North America, Europe, Asia-Pacific, South America, and Africa.
# MAGIC > - Product categories are: Electronics Components, Raw Materials, and Packaging.
# MAGIC > - The four warehouses are Chicago, Atlanta, Seattle, and Dallas. When asked about warehouse performance, include all four.
# MAGIC > - When asked about trends over time, group by month using DATE_TRUNC('month', order_date) unless a different granularity is specified.
# MAGIC > - "Best" or "top" suppliers should be ranked by on-time delivery rate and reliability_rating, unless the user specifies a different metric.
# MAGIC
# MAGIC 4. **Save** the instructions
# MAGIC 5. Now ask Genie: **"What does OTD stand for and what's our current rate?"**
# MAGIC
# MAGIC    Genie should recognize the abbreviation from the instructions and calculate
# MAGIC    the on-time delivery rate using the SQL expression defined in step 4c.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4f. Add common questions
# MAGIC
# MAGIC Common questions serve two purposes:
# MAGIC - They appear as **suggestions** when users open the Genie space (better onboarding)
# MAGIC - They help Genie **learn question patterns** for your domain
# MAGIC
# MAGIC 1. In the Genie space settings, find the **Common questions** section
# MAGIC 2. Add the following questions:
# MAGIC
# MAGIC | # | Common question |
# MAGIC |---|----------------|
# MAGIC | 1 | What is our overall on-time delivery rate? |
# MAGIC | 2 | Which supplier region has the highest total spend? |
# MAGIC | 3 | Show me products that are currently below their reorder point |
# MAGIC | 4 | What are the monthly spend trends by product category? |
# MAGIC | 5 | Which suppliers have the worst delivery performance? |
# MAGIC | 6 | Why did our spend increase in November and December compared to October? Break down the drivers by region and category. |
# MAGIC
# MAGIC Question 6 is a good example of a question that triggers **Agent mode** —
# MAGIC Genie's multi-step reasoning capability.  Instead of writing a single query,
# MAGIC Genie will run multiple queries, stream its thinking, and synthesize the
# MAGIC findings into a narrative answer.  Including it as a common question shows
# MAGIC users that the space supports this kind of exploratory analysis.
# MAGIC
# MAGIC 3. **Save** the changes

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Part 5 — Benchmark & Iterate
# MAGIC
# MAGIC Tuning a Genie space is an iterative process — you define what "correct" looks
# MAGIC like, test against it, and refine.  This mirrors how production Genie spaces are
# MAGIC maintained.
# MAGIC
# MAGIC In this section you'll:
# MAGIC 1. Define a set of benchmark questions with expected answers
# MAGIC 2. Run them through the Genie space
# MAGIC 3. Identify failures and iterate on your tuning

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5a. Define benchmark questions
# MAGIC
# MAGIC Here are 5 benchmark questions that span different query patterns.  For each,
# MAGIC the "Expected Behavior" column describes what correct SQL should look like.
# MAGIC
# MAGIC | # | Question | Category | Expected Behavior |
# MAGIC |---|----------|----------|-------------------|
# MAGIC | 1 | How many suppliers are in Asia-Pacific? | Simple lookup | Count suppliers where `region = 'Asia-Pacific'` |
# MAGIC | 2 | What is the average order value? | Calculation | `AVG(quantity * unit_cost)`, exclude cancelled |
# MAGIC | 3 | Which warehouse has the most low-stock items? | Join | Join `inventory_snapshots` to `products`, filter latest date, count where qty < reorder, group by warehouse |
# MAGIC | 4 | How has spend changed month over month? | Time-based | Monthly spend trend using `DATE_TRUNC`, exclude cancelled |
# MAGIC | 5 | Who are our best suppliers? | Ambiguous | Should use on-time rate + reliability per instructions |

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5b. Run the benchmark
# MAGIC
# MAGIC Ask each question in your Genie space and record the results.  You can use a
# MAGIC simple scoring system:
# MAGIC
# MAGIC | Score | Meaning |
# MAGIC |-------|---------|
# MAGIC | **Correct** | SQL is right, result is accurate |
# MAGIC | **Partial** | Right approach but minor issue (e.g., didn't exclude cancelled orders) |
# MAGIC | **Incorrect** | Wrong SQL logic or missing joins |
# MAGIC
# MAGIC **Tips for efficient benchmarking:**
# MAGIC - Work through the questions in order — they progress in difficulty
# MAGIC - After each question, click **"View query"** to see the SQL
# MAGIC - Compare the SQL against the "Expected Behavior" column above
# MAGIC - Jot down notes on what went wrong for any Partial or Incorrect results

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5c. Iterate and re-test
# MAGIC
# MAGIC Based on your benchmark results, improve the Genie space:
# MAGIC
# MAGIC 1. **Identify patterns in failures:**
# MAGIC    - Did Genie miss the same business rule multiple times? → Add or refine an instruction
# MAGIC    - Did a complex query type consistently fail? → Add a SQL query or function for it
# MAGIC    - Did Genie misinterpret a term? → Add a definition to instructions
# MAGIC
# MAGIC 2. **Make targeted improvements:**
# MAGIC    - Go back to Settings and add/edit instructions or SQL queries and functions
# MAGIC    - Be specific — vague instructions don't help
# MAGIC
# MAGIC 3. **Re-run the failed questions:**
# MAGIC    - Test only the questions that scored Partial or Incorrect
# MAGIC    - Did the score improve?  If not, try a different approach to the instruction
# MAGIC
# MAGIC > **Key insight:** This benchmark → tune → re-test loop is the same workflow
# MAGIC > that data teams use to maintain production Genie spaces.  The goal isn't
# MAGIC > perfection on day one — it's building a systematic process for continuous
# MAGIC > improvement.
# MAGIC >
# MAGIC > In practice, teams often start with 10-20 benchmark questions and grow the
# MAGIC > set over time as users ask new types of questions.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5d. Use the feedback loop
# MAGIC
# MAGIC In production, end users provide feedback on Genie's answers using **thumbs up /
# MAGIC thumbs down** buttons.  As a space manager, you can review this feedback and use
# MAGIC it to improve the space over time.
# MAGIC
# MAGIC Let's simulate the feedback workflow:
# MAGIC
# MAGIC **1. Generate feedback as an end user:**
# MAGIC - Go back to your Genie space conversation from Part 3
# MAGIC - For each question you asked, click **thumbs up** if the answer was correct, or
# MAGIC   **thumbs down** if it was wrong or incomplete
# MAGIC - When clicking thumbs down, add a brief comment explaining what was wrong
# MAGIC   (e.g., "Didn't exclude cancelled orders" or "Used wrong date column")
# MAGIC
# MAGIC **2. Review feedback as a space manager:**
# MAGIC - In the Genie space settings, find the **Feedback** or **Review conversations** section
# MAGIC - You'll see a list of conversations with user feedback
# MAGIC - For each thumbs-down response:
# MAGIC   - Click to expand and see the user's question, Genie's SQL, and the feedback comment
# MAGIC   - Use **Re-run query** to execute the query with your credentials (useful for
# MAGIC     debugging permission issues vs. logic issues)
# MAGIC   - Decide the right fix: add an instruction, refine a SQL expression, or add a
# MAGIC     SQL query or function
# MAGIC
# MAGIC **3. Close the loop:**
# MAGIC - After making improvements, mark the feedback as **reviewed**
# MAGIC - Re-ask the question to verify the fix
# MAGIC
# MAGIC > **Production workflow:** In a real deployment, this feedback loop runs continuously.
# MAGIC > Space managers review feedback weekly, prioritize the most common failure patterns,
# MAGIC > and incrementally improve the space settings.  Over time, this drives accuracy
# MAGIC > from an initial ~60-70% to 80%+ (the recommended threshold for user acceptance
# MAGIC > testing).

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Lab Complete
# MAGIC
# MAGIC ### What you built
# MAGIC
# MAGIC | Asset | Description |
# MAGIC |-------|-------------|
# MAGIC | **4 supply chain tables** | Suppliers, products, purchase orders, and inventory snapshots in Unity Catalog |
# MAGIC | **AI/BI dashboard** | KPI counters, charts, a table widget, date filters, and cross-filtering — all built through the UI |
# MAGIC | **Tuned Genie space** | Descriptions, synonyms, joins, SQL expressions, instructions, common questions, and SQL queries and functions configured through space settings |
# MAGIC | **Benchmark suite** | 10 questions with expected behavior, scoring, and a feedback review workflow |
# MAGIC
# MAGIC ### Next steps
# MAGIC
# MAGIC - **Schedule dashboard refresh** — Add the dashboard to a Lakeflow Job so it updates
# MAGIC   automatically on new data
# MAGIC - **Share the Genie space** — Invite team members and see what questions they ask
# MAGIC - **Monitor Genie conversations** — Review the conversation history to find new question
# MAGIC   patterns and add more SQL queries and functions
# MAGIC - **Set up alerts** — Connect dashboard widgets to alerts for threshold-based notifications
# MAGIC   (e.g., alert when low-stock count exceeds 10)
# MAGIC - **Version-control dashboards** — Export dashboard JSON and manage it in a Databricks
# MAGIC   Asset Bundle for CI/CD (see the Lakeflow Jobs & CI/CD lab for this pattern)
