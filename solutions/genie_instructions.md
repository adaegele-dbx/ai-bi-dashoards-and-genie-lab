## Column Descriptions

### purchase_orders
| Column | Description |
|--------|-------------|
| `order_date` | Date the purchase order was placed |
| `expected_delivery_date` | Date the supplier committed to deliver by |
| `actual_delivery_date` | Date the order was actually received; NULL if not yet delivered |
| `quantity` | Number of units ordered |
| `unit_cost` | Price per unit at time of order |
| `status` | Order status: delivered, in_transit, delayed, or cancelled |

### inventory_snapshots
| Column | Description |
|--------|-------------|
| `snapshot_date` | Date of the weekly inventory count |
| `quantity_on_hand` | Current stock level in this warehouse |
| `reorder_point` | Minimum stock threshold; below this triggers replenishment |
| `quantity_on_order` | Units currently on order from suppliers |

## Synonyms

| Business term | Maps to |
|---------------|---------|
| cost | `unit_cost` |
| price | `unit_cost` |
| ETA | `expected_delivery_date` |
| received date | `actual_delivery_date` |
| order value | `quantity * unit_cost` |
| stock level | `quantity_on_hand` |

## Join Relationships

| Left table | Right table | Join condition |
|-----------|------------|----------------|
| `purchase_orders` | `suppliers` | `purchase_orders.supplier_id = suppliers.supplier_id` |
| `purchase_orders` | `products` | `purchase_orders.product_id = products.product_id` |
| `inventory_snapshots` | `products` | `inventory_snapshots.product_id = products.product_id` |
| `products` | `suppliers` | `products.supplier_id = suppliers.supplier_id` |

## SQL Expressions

### Measure: total_spend
- **Expression:** `SUM(purchase_orders.quantity * purchase_orders.unit_cost)`
- **Description:** Total spend across purchase orders, excluding cancelled orders
- **Filter:** `purchase_orders.status != 'cancelled'`

### Measure: on_time_delivery_rate
- **Expression:** `COUNT(CASE WHEN purchase_orders.actual_delivery_date <= purchase_orders.expected_delivery_date THEN 1 END) * 100.0 / NULLIF(COUNT(purchase_orders.actual_delivery_date), 0)`
- **Description:** Percentage of delivered orders that arrived on or before the expected date
- **Filter:** `purchase_orders.actual_delivery_date IS NOT NULL`

### Filter: latest_snapshot
- **Expression:** `inventory_snapshots.snapshot_date = (SELECT MAX(snapshot_date) FROM workspace.ai_bi_lab.inventory_snapshots)`
- **Description:** Restricts inventory queries to the most recent weekly snapshot

### Filter: low_stock
- **Expression:** `inventory_snapshots.quantity_on_hand < inventory_snapshots.reorder_point`
- **Description:** Items below their reorder threshold

## General Instructions (for Genie space)

These are the business context instructions to add to the Genie space settings:

- On-time delivery means actual_delivery_date <= expected_delivery_date. Orders where actual_delivery_date IS NULL should not be included in on-time calculations.
- Spend or total spend is calculated as quantity * unit_cost. Exclude cancelled orders from spend calculations unless explicitly asked.
- When asked about "current" inventory, use the most recent snapshot_date in the inventory_snapshots table.
- Lead time is measured in calendar days. For actual lead time, use DATEDIFF(actual_delivery_date, order_date). For expected lead time, use the lead_time_days column from the suppliers table.
- A "low-stock" or "at-risk" item is one where quantity_on_hand < reorder_point in the latest inventory snapshot.
- "Best" or "top" suppliers should be ranked by a combination of on-time delivery rate and reliability_rating, unless the user specifies a different metric.
- When asked about trends over time, group by month using DATE_TRUNC('month', order_date) unless a different granularity is specified.
- The four warehouses are Chicago, Atlanta, Seattle, and Dallas. When asked about warehouse performance, include all four.
- Product categories are: Electronics Components, Raw Materials, and Packaging.
- Supplier regions are: North America, Europe, Asia-Pacific, South America, and Africa.

## Sample Questions

These are curated sample questions to add to the Genie space:

1. What is our overall on-time delivery rate?
2. Which supplier region has the highest total spend?
3. Show me products that are currently below their reorder point
4. What are the monthly spend trends by product category?
5. Which suppliers have the worst delivery performance?

## Certified SQL Queries

### Supplier Scorecard
```sql
SELECT 
  s.supplier_name,
  s.region,
  s.reliability_rating,
  s.lead_time_days AS expected_lead_time,
  COUNT(po.order_id) AS total_orders,
  ROUND(AVG(CASE WHEN po.actual_delivery_date IS NOT NULL 
    THEN DATEDIFF(po.actual_delivery_date, po.order_date) END), 1) AS avg_actual_lead_time,
  ROUND(
    COUNT(CASE WHEN po.actual_delivery_date <= po.expected_delivery_date THEN 1 END) * 100.0 
    / NULLIF(COUNT(po.actual_delivery_date), 0), 1
  ) AS on_time_pct,
  ROUND(SUM(CASE WHEN po.status != 'cancelled' THEN po.quantity * po.unit_cost ELSE 0 END), 2) AS total_spend
FROM workspace.ai_bi_lab.suppliers s
LEFT JOIN workspace.ai_bi_lab.purchase_orders po ON s.supplier_id = po.supplier_id
GROUP BY s.supplier_name, s.region, s.reliability_rating, s.lead_time_days
ORDER BY on_time_pct DESC
```

### Inventory Risk Report
```sql
SELECT 
  p.product_name,
  p.category,
  i.warehouse,
  i.quantity_on_hand,
  i.reorder_point,
  i.reorder_point - i.quantity_on_hand AS units_below_threshold,
  i.quantity_on_order,
  CASE 
    WHEN i.quantity_on_order > 0 THEN 'Replenishment Ordered'
    ELSE 'Action Required'
  END AS risk_status
FROM workspace.ai_bi_lab.inventory_snapshots i
JOIN workspace.ai_bi_lab.products p ON i.product_id = p.product_id
WHERE i.snapshot_date = (SELECT MAX(snapshot_date) FROM workspace.ai_bi_lab.inventory_snapshots)
  AND i.quantity_on_hand < i.reorder_point
ORDER BY units_below_threshold DESC
```

## Benchmark Questions

A table with columns: Question, Category, Expected Behavior

| Question | Category | Expected Behavior |
|----------|----------|-------------------|
| How many suppliers are in Asia-Pacific? | Simple lookup | Should return count of suppliers where region = 'Asia-Pacific' |
| What is the average order value? | Calculation | Should compute AVG(quantity * unit_cost), exclude cancelled |
| Which warehouse has the most low-stock items? | Join | Should join inventory_snapshots with products, filter latest date, count where qty < reorder |
| How has spend changed month over month? | Time-based | Should show monthly spend trend with DATE_TRUNC |
| Who are our best suppliers? | Ambiguous | Should use on-time rate + reliability_rating per instructions |
| What percentage of orders are delayed? | Calculation | Should count delayed status / total orders |
| Compare Electronics Components vs Raw Materials spend | Comparison | Should group by category, sum spend |
| Which products have never been below reorder point? | Negation | Should find products NOT in low-stock snapshots |
| Show me supplier performance for Q1 2025 | Time-filtered | Should filter Jan-Mar 2025, show supplier metrics |
| What is the total quantity on order across all warehouses? | Aggregation | Should sum quantity_on_order from latest snapshot |
