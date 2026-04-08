# Databricks notebook source

# MAGIC %md
# MAGIC # Supply Chain Operations Lab - Data Setup
# MAGIC This notebook generates synthetic supply chain data for the AI/BI dashboards and Genie lab.

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace", "Catalog Name")
catalog = dbutils.widgets.get("catalog")
schema = "ai_bi_lab"
print(f"Using catalog: {catalog}, schema: {schema}")

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
print(f"Schema {catalog}.{schema} is ready.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Suppliers Table (~15 rows)

# COMMAND ----------

import random
from datetime import date, timedelta
from pyspark.sql.types import *

random.seed(42)

# Region config: (countries, lead_time_range, reliability_range)
region_config = {
    "North America": (["US", "Canada", "Mexico"], (3, 14), (3.5, 5.0)),
    "Europe": (["Germany", "UK", "France"], (3, 14), (3.5, 5.0)),
    "Asia-Pacific": (["China", "Japan", "South Korea"], (14, 30), (2.5, 4.5)),
    "South America": (["Brazil", "Argentina", "Chile"], (10, 25), (2.5, 4.5)),
    "Africa": (["South Africa", "Nigeria", "Kenya"], (12, 28), (2.0, 4.0)),
}

suppliers = []
sup_id = 1
for region, (countries, lt_range, rel_range) in region_config.items():
    for country in countries:
        suppliers.append({
            "supplier_id": f"SUP-{sup_id:03d}",
            "supplier_name": f"{country} Supply Co {sup_id}",
            "region": region,
            "country": country,
            "lead_time_days": random.randint(lt_range[0], lt_range[1]),
            "reliability_rating": round(random.uniform(rel_range[0], rel_range[1]), 1),
        })
        sup_id += 1

suppliers_schema = StructType([
    StructField("supplier_id", StringType()),
    StructField("supplier_name", StringType()),
    StructField("region", StringType()),
    StructField("country", StringType()),
    StructField("lead_time_days", IntegerType()),
    StructField("reliability_rating", FloatType()),
])

df_suppliers = spark.createDataFrame(suppliers, schema=suppliers_schema)
df_suppliers.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{catalog}.{schema}.suppliers")
print(f"suppliers: {df_suppliers.count()} rows written.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Products Table (~30 rows)

# COMMAND ----------

random.seed(42)

electronics = [
    "Circuit Board A1", "Resistor Pack 1K", "LED Display Module",
    "Microcontroller Unit", "Capacitor Set", "Power Supply Unit",
    "Connector Cable Kit", "Sensor Array Module", "Memory Chip 8GB", "Transistor Pack",
]
raw_materials = [
    "Aluminum Sheet 4x8", "Copper Wire Spool", "Steel Rod Bundle",
    "Plastic Pellets 25kg", "Rubber Gasket Set", "Glass Panel 2x3",
    "Carbon Fiber Sheet", "Titanium Bar Stock", "Silicone Tubing 100ft", "Ceramic Substrate",
]
packaging = [
    "Cardboard Box Large", "Foam Insert Custom", "Shrink Wrap Roll",
    "Bubble Wrap 100ft", "Packing Tape Case", "Anti-Static Bag Pack",
    "Wooden Crate 3x3", "Label Roll 5000ct", "Pallet Standard 48x40", "Desiccant Pack Box",
]

# Cost ranges and weight ranges per category
cat_config = {
    "Electronics Components": (electronics, (5.0, 150.0), (0.1, 5.0)),
    "Raw Materials": (raw_materials, (10.0, 200.0), (1.0, 50.0)),
    "Packaging": (packaging, (2.0, 50.0), (0.5, 15.0)),
}

supplier_ids = [s["supplier_id"] for s in suppliers]
products = []
prod_id = 1
for category, (names, cost_range, weight_range) in cat_config.items():
    for name in names:
        products.append({
            "product_id": f"PROD-{prod_id:03d}",
            "product_name": name,
            "category": category,
            "unit_cost": round(random.uniform(cost_range[0], cost_range[1]), 2),
            "supplier_id": random.choice(supplier_ids),
            "weight_kg": round(random.uniform(weight_range[0], weight_range[1]), 2),
        })
        prod_id += 1

products_schema = StructType([
    StructField("product_id", StringType()),
    StructField("product_name", StringType()),
    StructField("category", StringType()),
    StructField("unit_cost", FloatType()),
    StructField("supplier_id", StringType()),
    StructField("weight_kg", FloatType()),
])

df_products = spark.createDataFrame(products, schema=products_schema)
df_products.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{catalog}.{schema}.products")
print(f"products: {df_products.count()} rows written.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Purchase Orders Table (~800 rows)

# COMMAND ----------

random.seed(42)

# Build lookup maps
supplier_lead = {s["supplier_id"]: s["lead_time_days"] for s in suppliers}
product_map = {p["product_id"]: p for p in products}

# Quantity ranges by category
qty_ranges = {
    "Electronics Components": (10, 200),
    "Raw Materials": (50, 500),
    "Packaging": (100, 500),
}

# Monthly weights for seasonal pattern (Oct 2024 - Mar 2025)
month_weights = {10: 1.0, 11: 1.4, 12: 1.5, 1: 0.9, 2: 1.2, 3: 1.3}

start_date = date(2024, 10, 1)
end_date = date(2025, 3, 31)
total_days = (end_date - start_date).days

purchase_orders = []
po_id = 1

# Generate ~800 orders, distributed by monthly weights
target_orders = 800
for _ in range(target_orders):
    # Pick a random day, weighted by month
    while True:
        day_offset = random.randint(0, total_days)
        order_date = start_date + timedelta(days=day_offset)
        weight = month_weights.get(order_date.month, 1.0)
        if random.random() < weight / 1.5:
            break

    prod = random.choice(products)
    sup_id = prod["supplier_id"]
    lead = supplier_lead[sup_id]
    expected_delivery = order_date + timedelta(days=lead + random.randint(-2, 5))

    # Determine status
    roll = random.random()
    if roll < 0.65:
        status = "delivered"
        offset = random.randint(-3, 10)
        actual_delivery = expected_delivery + timedelta(days=offset)
    elif roll < 0.85:
        status = "in_transit"
        actual_delivery = None
    elif roll < 0.95:
        status = "delayed"
        actual_delivery = None
    else:
        status = "cancelled"
        actual_delivery = None

    qty_range = qty_ranges[prod["category"]]
    quantity = random.randint(qty_range[0], qty_range[1])
    unit_cost = round(prod["unit_cost"] * random.uniform(0.95, 1.05), 2)

    purchase_orders.append({
        "order_id": f"PO-{po_id:05d}",
        "product_id": prod["product_id"],
        "supplier_id": sup_id,
        "order_date": order_date,
        "expected_delivery_date": expected_delivery,
        "actual_delivery_date": actual_delivery,
        "quantity": quantity,
        "unit_cost": unit_cost,
        "status": status,
    })
    po_id += 1

po_schema = StructType([
    StructField("order_id", StringType()),
    StructField("product_id", StringType()),
    StructField("supplier_id", StringType()),
    StructField("order_date", DateType()),
    StructField("expected_delivery_date", DateType()),
    StructField("actual_delivery_date", DateType()),
    StructField("quantity", IntegerType()),
    StructField("unit_cost", FloatType()),
    StructField("status", StringType()),
])

df_orders = spark.createDataFrame(purchase_orders, schema=po_schema)
df_orders.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{catalog}.{schema}.purchase_orders")
print(f"purchase_orders: {df_orders.count()} rows written.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Inventory Snapshots Table (~2000 rows)

# COMMAND ----------

random.seed(42)

warehouses = ["Chicago", "Atlanta", "Seattle", "Dallas"]

# All 30 products are stocked in all 4 warehouses
product_warehouse_map = {}
for prod in products:
    product_warehouse_map[prod["product_id"]] = warehouses

# Reorder points by category
reorder_points = {
    "Electronics Components": 50,
    "Raw Materials": 100,
    "Packaging": 200,
}

# Products that will consistently be below reorder point (interesting dashboard data)
low_stock_products = set(random.sample(list(product_warehouse_map.keys()), k=5))

# Weekly snapshots: 17 weeks (~4 months) from Nov 2024 to Mar 2025
snapshot_start = date(2024, 11, 4)
snapshot_dates = [snapshot_start + timedelta(weeks=w) for w in range(17)]

inventory_snapshots = []
for snap_date in snapshot_dates:
    for prod_id, wh_list in product_warehouse_map.items():
        prod = product_map[prod_id]
        reorder_pt = reorder_points[prod["category"]]
        for wh in wh_list:
            if prod_id in low_stock_products:
                qty_on_hand = random.randint(0, int(reorder_pt * 0.6))
            else:
                qty_on_hand = random.randint(int(reorder_pt * 0.5), 500)

            qty_on_order = 0
            if qty_on_hand < reorder_pt:
                qty_on_order = random.randint(reorder_pt, reorder_pt * 3)

            inventory_snapshots.append({
                "snapshot_date": snap_date,
                "product_id": prod_id,
                "warehouse": wh,
                "quantity_on_hand": qty_on_hand,
                "reorder_point": reorder_pt,
                "quantity_on_order": qty_on_order,
            })

inv_schema = StructType([
    StructField("snapshot_date", DateType()),
    StructField("product_id", StringType()),
    StructField("warehouse", StringType()),
    StructField("quantity_on_hand", IntegerType()),
    StructField("reorder_point", IntegerType()),
    StructField("quantity_on_order", IntegerType()),
])

df_inventory = spark.createDataFrame(inventory_snapshots, schema=inv_schema)
df_inventory.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable(f"{catalog}.{schema}.inventory_snapshots")
print(f"inventory_snapshots: {df_inventory.count()} rows written.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verification - Sample Data from Each Table

# COMMAND ----------

for table in ["suppliers", "products", "purchase_orders", "inventory_snapshots"]:
    print(f"\n--- {catalog}.{schema}.{table} ---")
    display(spark.table(f"{catalog}.{schema}.{table}").limit(5))
    count = spark.table(f"{catalog}.{schema}.{table}").count()
    print(f"Total rows: {count}")
