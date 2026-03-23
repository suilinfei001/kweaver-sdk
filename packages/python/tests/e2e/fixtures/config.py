"""E2E test data configuration — centralized schema knowledge.

All test-data-related configuration lives here:
- Resource naming prefix
- PK/display key hints per table
- Known OT names for KN discovery
- Agent configuration template
"""
from __future__ import annotations

from typing import Any

# All e2e-created resources use this prefix for easy identification and cleanup
PREFIX = "e2e_agentpipe_"

# PK and display key hints per table name.
# Avoids float/text PK errors when creating OTs.
# Format: {table_name: (pk_field, display_field)}
PK_HINTS: dict[str, tuple[str, str]] = {
    # nexus supply chain
    "e2e_nexus_物料": ("material_code", "material_name"),
    "e2e_nexus_库存": ("material_code", "material_name"),
    "e2e_nexus_供应商": ("supplier_code", "provided_material_name"),
    "e2e_nexus_产品BOM": ("bom_number", "child_name"),
    "e2e_nexus_销售订单": ("id", "product_name"),
    "e2e_nexus_产品": ("product_code", "product_name"),
    "e2e_nexus_工厂生产计划": ("order_number", "code"),
    "e2e_nexus_需求计划": ("id", "product_code"),
    # acme product demand
    "e2e_acme_CRM需求工单": ("workorder_number", "subject"),
    "e2e_acme_客户需求": ("workitemsid", "title"),
    "e2e_acme_员工": ("userid", "username"),
    "e2e_acme_部门": ("dept_code", "name"),
    "e2e_acme_研发项目": ("projectsk", "projectname"),
    "e2e_acme_产品": ("productname", "productname"),
}

# OT names recognized by the question builder and KN discovery.
# KNs containing these OTs are preferred in default (non-build) mode.
KNOWN_OT_NAMES: set[str] = {
    "物料", "库存", "供应商", "产品BOM", "销售订单",
    "CRM需求工单", "客户需求", "员工", "部门",
}

# BKN retrieval advanced config defaults for agent creation.
# The agent-factory API uses legacy field name "kg" to bind agents to BKNs
# (Business Knowledge Networks).
BKN_ADVANCED_CONFIG: dict[str, Any] = {
    "text_match_entity_nums": 60,
    "vector_match_entity_nums": 60,
    "graph_rag_topk": 25,
    "long_text_length": 256,
    "reranker_sim_threshold": -5.5,
    "retrieval_max_length": 20480,
}

# Agent system prompt
AGENT_SYSTEM_PROMPT = (
    "你是一个数据分析助手。"
    "你可以访问知识网络中的供应链数据和产品需求数据。"
    "请基于知识网络中的实际数据准确回答问题，引用具体编码或数值。"
)
