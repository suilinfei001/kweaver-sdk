# Integration Tests

End-to-end integration tests that validate complete user scenarios against a real KWeaver environment.

## Scenarios

| File | Scenario | What it validates |
|------|----------|-------------------|
| `test_data_pipeline.py` | Data Pipeline | DS → DV → KN → OT → Build → REST query |
| `test_context_loader.py` | Context Loader | kn_search + query_object_instance + REST↔MCP consistency |
| `test_agent_pipeline.py` | Agent Pipeline | Data → BKN → Context Loader → Agent → Conversation (14 questions) |

## Modes

### Default mode (fast, ~1 min)

```bash
pytest tests/e2e/integration/test_agent_pipeline.py --run-destructive -v -s
```

Uses existing BKNs in the environment. Discovers the best BKN with known object types, collects ground truth via REST, tests Context Loader, creates a temporary agent, runs questions. Only the agent is created and cleaned up.

### Build mode (full lifecycle, ~15 min)

```bash
pytest tests/e2e/integration/test_agent_pipeline.py --run-destructive --build -v -s
```

Full end-to-end from CSV import:
1. Import CSV fixtures via dataflow API → MySQL tables
2. Create datasource → discover tables → create dataviews
3. Create BKN → object types → build and index
4. Test Context Loader (kn_search, query, REST↔CL consistency)
5. Create agent with BKN binding → publish → conversation tests
6. Cleanup everything (agent → BKN → datasource)

### Data pipeline + Context Loader (existing tests)

```bash
pytest tests/e2e/integration/test_data_pipeline.py tests/e2e/integration/test_context_loader.py --run-destructive -v
```

These use `lifecycle_env` fixture (always builds from scratch).

## Configuration

| Source | What | Committed |
|--------|------|-----------|
| `.env.e2e` | `KWEAVER_BASE_URL`, DB connection | No |
| `~/.env.secrets` | `KWEAVER_USERNAME`, `KWEAVER_PASSWORD` | No |
| `fixtures/config.py` | PK hints, known OT names, agent config | Yes |
| `fixtures/questions.py` | Question generation + ground truth | Yes |
| `fixtures/db.py` | Dataflow CSV import tool | Yes |
| `fixtures/data/*.csv` | Anonymized test data (31K rows) | No (gitignored) |

## Test Data

Two datasets (~31,000 records total):

**Supply chain (nexus_\*, ~1,400 records):**
物料(242), 产品BOM(531), 销售订单(452), 库存(70), 供应商(69), 产品(4), 生产计划(4), 需求计划(12)

**Product demand (acme_\*, ~30,000 records):**
CRM需求工单(16,028), 客户需求(7,977), 员工(4,322), 部门(1,478), 研发项目(44), 产品(3)

## Test Questions (14)

Dynamically generated from ground truth at runtime:

| ID | Category | Tests |
|----|----------|-------|
| exact_material_lookup | Supply chain | 按编码精确查找物料 |
| most_expensive | Supply chain | 极值查询（最贵物料） |
| zero_stock | Supply chain | 零库存边界检测 |
| inventory_alert | Supply chain | 可用量 < 安全库存比较 |
| order_lookup | Supply chain | 按合同号查订单 |
| product_bom | Supply chain | 跨表查询（产品→BOM） |
| supplier_lookup | Supply chain | 跨表查找（物料→供应商） |
| material_count | Supply chain | 统计查询 |
| workorder_lookup | CRM | 按工单号查CRM工单 |
| workorder_count | CRM | CRM工单统计 |
| demand_lookup | CRM | 按需求ID查客户需求 |
| employee_lookup | CRM | 按姓名查员工 |
| org_stats | CRM | 部门+员工统计 |
| demand_priority | CRM | 按优先级过滤+聚合 |

## Context Loader Tests (5)

| Test | What |
|------|------|
| cl_kn_search_schema | kn_search discovers OTs in each BKN |
| cl_kn_search_only_schema | only_schema returns schema without instances |
| cl_query_instance_eq | == condition returns exact match |
| cl_query_instance_in | in operator matches multiple values |
| cl_rest_consistency | REST and Context Loader return consistent data |
