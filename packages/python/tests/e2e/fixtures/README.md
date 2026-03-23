# E2E Test Fixtures

Controlled test data for integration tests. CSV files define the test data, `db.py` imports them into MySQL.

## Data Design

A small supply-chain scenario with 3 related tables:

```
e2e_products ──< e2e_orders
     │
     └──< e2e_inventory
```

- **e2e_products** — 6 products with known attributes (price, category, status)
- **e2e_orders** — 8 orders referencing products, with dates and quantities
- **e2e_inventory** — 5 inventory records with safety stock, available quantity

## Design Principles

- **Small & precise** — few rows, every value known, assertions can be exact
- **Covers edge cases** — null values, zero quantity, Chinese characters, large numbers
- **Cross-table relations** — product_code links all 3 tables
- **Known answers** — e.g., "most expensive product is P005 (¥9999.99)", "total orders = 8"

## Known Answers (Ground Truth)

Use these in test assertions:

| Question | Answer |
|----------|--------|
| Most expensive product | P005 工业级伺服电机 ¥9999.99 |
| Cheapest product | P004 不锈钢法兰盘 ¥45.80 |
| Discontinued product | P004 (status=停产) |
| Out of stock (available=0) | P003 控制主板 v2.1 |
| Below safety stock | P002 (available=12, safety=20), P003 (0, 30), P005 (3, 5) |
| Cancelled order | ORD-2024-008 (quantity=0, status=已取消) |
| Repeat customer | 上海自动化仪表有限公司 (ORD-001, ORD-004) |
| Product with no orders | P003 |
| Total products | 6 |
| Total orders | 8 |

## Setup

CSV data must be imported into the test MySQL before tests run. Since the test
runner may not have direct MySQL connectivity (internal network), import is done
separately:

```bash
# From a machine that can reach the MySQL server:
python -m tests.e2e.fixtures.db --setup \
  --host <DB_HOST> --port 3306 \
  --user root --password 'xxx' --database nexus_supply

# Teardown (drop tables):
python -m tests.e2e.fixtures.db --teardown \
  --host <DB_HOST> --port 3306 \
  --user root --password 'xxx' --database nexus_supply
```

Tests check if the `e2e_*` tables exist via KWeaver SDK's `datasources.list_tables()`.
If tables are missing, the agent pipeline test will skip with a clear message.
