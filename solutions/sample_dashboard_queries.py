# Databricks notebook source

# MAGIC %md
# MAGIC # AI/BI Dashboard Queries - Supply Chain Operations
# MAGIC Reference SQL queries for each dashboard widget.

# COMMAND ----------

# MAGIC %md
# MAGIC ## KPI: Total Purchase Orders (Counter)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT s.region, COUNT(*) AS total_orders
# MAGIC FROM workspace.ai_bi_lab.purchase_orders po
# MAGIC JOIN workspace.ai_bi_lab.suppliers s ON po.supplier_id = s.supplier_id
# MAGIC GROUP BY s.region

# COMMAND ----------

# MAGIC %md
# MAGIC ## KPI: On-Time Delivery Rate (Counter)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT s.region, ROUND(
# MAGIC   COUNT(CASE WHEN po.actual_delivery_date <= po.expected_delivery_date THEN 1 END) * 1.0
# MAGIC   / COUNT(po.actual_delivery_date), 3
# MAGIC ) AS on_time_pct
# MAGIC FROM workspace.ai_bi_lab.purchase_orders po
# MAGIC JOIN workspace.ai_bi_lab.suppliers s ON po.supplier_id = s.supplier_id
# MAGIC WHERE po.actual_delivery_date IS NOT NULL
# MAGIC GROUP BY s.region

# COMMAND ----------

# MAGIC %md
# MAGIC ## KPI: Total Spend (Counter)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT s.region, ROUND(SUM(po.quantity * po.unit_cost), 2) AS total_spend
# MAGIC FROM workspace.ai_bi_lab.purchase_orders po
# MAGIC JOIN workspace.ai_bi_lab.suppliers s ON po.supplier_id = s.supplier_id
# MAGIC WHERE po.status != 'cancelled'
# MAGIC GROUP BY s.region

# COMMAND ----------

# MAGIC %md
# MAGIC ## KPI: Current Low-Stock Items (Counter)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT s.region, COUNT(*) AS low_stock_count
# MAGIC FROM workspace.ai_bi_lab.inventory_snapshots i
# MAGIC JOIN workspace.ai_bi_lab.products p ON i.product_id = p.product_id
# MAGIC JOIN workspace.ai_bi_lab.suppliers s ON p.supplier_id = s.supplier_id
# MAGIC WHERE i.snapshot_date = (SELECT MAX(snapshot_date) FROM workspace.ai_bi_lab.inventory_snapshots)
# MAGIC   AND i.quantity_on_hand < i.reorder_point
# MAGIC GROUP BY s.region

# COMMAND ----------

# MAGIC %md
# MAGIC ## Spend by Supplier Region (Bar Chart)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT s.region, ROUND(SUM(po.quantity * po.unit_cost), 2) AS total_spend
# MAGIC FROM workspace.ai_bi_lab.purchase_orders po
# MAGIC JOIN workspace.ai_bi_lab.suppliers s ON po.supplier_id = s.supplier_id
# MAGIC WHERE po.status != 'cancelled'
# MAGIC GROUP BY s.region
# MAGIC ORDER BY total_spend DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ## Orders Over Time (Line Chart - by month and status)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT s.region,
# MAGIC        DATE_TRUNC('month', po.order_date) AS order_month,
# MAGIC        po.status,
# MAGIC        COUNT(*) AS order_count
# MAGIC FROM workspace.ai_bi_lab.purchase_orders po
# MAGIC JOIN workspace.ai_bi_lab.suppliers s ON po.supplier_id = s.supplier_id
# MAGIC GROUP BY s.region, order_month, po.status
# MAGIC ORDER BY order_month, po.status

# COMMAND ----------

# MAGIC %md
# MAGIC ## Delivery Performance by Supplier (Bar Chart - avg days late/early)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT s.region, s.supplier_name,
# MAGIC        ROUND(AVG(DATEDIFF(po.actual_delivery_date, po.expected_delivery_date)), 1) AS avg_days_variance
# MAGIC FROM workspace.ai_bi_lab.purchase_orders po
# MAGIC JOIN workspace.ai_bi_lab.suppliers s ON po.supplier_id = s.supplier_id
# MAGIC WHERE po.actual_delivery_date IS NOT NULL
# MAGIC GROUP BY s.region, s.supplier_name
# MAGIC ORDER BY avg_days_variance

# COMMAND ----------

# MAGIC %md
# MAGIC ## Top 10 Products by Spend (Table)

# COMMAND ----------

# MAGIC %sql
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
