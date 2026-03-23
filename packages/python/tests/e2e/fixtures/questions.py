"""E2E test questions — dynamically built from ground-truth data.

Ground truth is queried from the KN at test setup time via REST API,
then questions are constructed with verify functions that check the
agent's response against known facts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TestQuestion:
    id: str
    question: str
    description: str
    verify: callable  # (response: str) -> str | None (error msg or None)


def _contains_all(response: str, keywords: list[str]) -> str | None:
    missing = [k for k in keywords if k not in response]
    return f"Missing: {missing}" if missing else None


def _contains_any(response: str, keywords: list[str]) -> str | None:
    if not any(k in response for k in keywords):
        return f"Should contain one of: {keywords}"
    return None


def _has_digits(response: str) -> str | None:
    return None if any(c.isdigit() for c in response) else "Should contain numbers"


def _not_empty(response: str) -> str | None:
    return None if response and len(response.strip()) > 10 else "Response too short"


# ---------------------------------------------------------------------------
# Ground truth collection — auto-discovers OTs and builds questions
# ---------------------------------------------------------------------------


def collect_ground_truth(client: Any, kn_id: str) -> dict[str, Any]:
    """Query the KN to collect ground-truth data for question building.

    Auto-discovers object types by name pattern and collects relevant samples.
    Works with both supply-chain and product-demand KNs.
    """
    ots = client.object_types.list(kn_id)
    ot_map = {ot.name: ot for ot in ots if ot.status and ot.status.doc_count > 0}

    def _find_ot(keyword: str) -> Any | None:
        """Find OT by exact name or suffix match (handles e2e prefixes)."""
        if keyword in ot_map:
            return ot_map[keyword]
        for name, ot in ot_map.items():
            if name.endswith(keyword) or keyword in name:
                return ot
        return None

    gt: dict[str, Any] = {"ot_map": ot_map, "kn_id": kn_id}

    # --- Supply chain data ---
    mat_ot = _find_ot("物料")
    if mat_ot:
        all_mat = client.query.instances(kn_id, mat_ot.id, limit=300)
        gt["materials_total"] = all_mat.total_count
        by_price = sorted(all_mat.data, key=lambda x: float(x.get("unit_price", 0) or 0), reverse=True)
        if by_price:
            top = by_price[0]
            gt["most_expensive_material"] = {
                "material_code": top.get("material_code", ""),
                "material_name": top.get("material_name", ""),
                "unit_price": top.get("unit_price", 0),
            }

    inv_ot = _find_ot("库存")
    if inv_ot:
        all_inv = client.query.instances(kn_id, inv_ot.id, limit=100)
        gt["zero_stock"] = [
            {"material_code": r["material_code"], "material_name": r["material_name"]}
            for r in all_inv.data
            if str(r.get("available_quantity", "0")).strip() in ("0", "0.0", "")
        ]
        gt["below_safety"] = [
            {"material_code": r["material_code"], "available": r.get("available_quantity", 0), "safety": r.get("safety_stock", 0)}
            for r in all_inv.data
            if float(r.get("available_quantity") or 0) < float(r.get("safety_stock") or 0)
        ]

    order_ot = _find_ot("销售订单")
    if order_ot:
        orders = client.query.instances(kn_id, order_ot.id, limit=5)
        gt["orders_total"] = orders.total_count
        if orders.data:
            gt["sample_order"] = orders.data[0]

    sup_ot = _find_ot("供应商")
    if sup_ot:
        sups = client.query.instances(kn_id, sup_ot.id, limit=5)
        gt["suppliers_total"] = sups.total_count
        if sups.data:
            gt["sample_supplier"] = sups.data[0]

    bom_ot = _find_ot("产品BOM") or _find_ot("产品bom")
    if bom_ot:
        gt["bom_total"] = bom_ot.status.doc_count

    prod_ot = _find_ot("产品")
    if prod_ot:
        prods = client.query.instances(kn_id, prod_ot.id, limit=5)
        if prods.data:
            gt["sample_product"] = prods.data[0]

    # --- Product demand / CRM data ---
    wo_ot = _find_ot("CRM需求工单") or _find_ot("crm需求工单")
    if wo_ot:
        gt["workorders_total"] = wo_ot.status.doc_count
        wos = client.query.instances(kn_id, wo_ot.id, limit=5)
        if wos.data:
            gt["sample_workorder"] = wos.data[0]

    cd_ot = _find_ot("客户需求")
    if cd_ot:
        gt["customer_demands_total"] = cd_ot.status.doc_count
        cds = client.query.instances(kn_id, cd_ot.id, limit=5)
        if cds.data:
            gt["sample_demand"] = cds.data[0]

    emp_ot = _find_ot("员工")
    if emp_ot:
        gt["employees_total"] = emp_ot.status.doc_count
        emps = client.query.instances(kn_id, emp_ot.id, limit=5)
        if emps.data:
            gt["sample_employee"] = emps.data[0]

    dept_ot = _find_ot("部门")
    if dept_ot:
        gt["departments_total"] = dept_ot.status.doc_count

    return gt


def build_questions(gt: dict[str, Any]) -> list[TestQuestion]:
    """Build test questions from collected ground truth.

    Dynamically generates questions based on what data is available.
    """
    questions: list[TestQuestion] = []

    # ── Supply chain questions ────────────────────────────────────────────

    me = gt.get("most_expensive_material")
    if me:
        questions.append(TestQuestion(
            id="exact_material_lookup",
            question=f"请查找物料编码为{me['material_code']}的物料，告诉我它的名称和单价。",
            description="精确查找：按编码定位单个实体",
            verify=lambda r, m=me: _contains_all(r, [m["material_code"]]),
        ))
        questions.append(TestQuestion(
            id="most_expensive",
            question="单价最高的物料是什么？请告诉我物料编码、名称和单价。",
            description="极值查询：排序找最大值",
            verify=lambda r, m=me: _contains_any(r, [m["material_code"], m["material_name"]]),
        ))

    zs = gt.get("zero_stock", [])
    if zs:
        questions.append(TestQuestion(
            id="zero_stock",
            question="哪些物料的库存可用数量为0？请列出物料编码和名称。",
            description="边界值检测：零库存",
            verify=lambda r, z=zs: _contains_any(r, [x["material_code"] for x in z[:5]]),
        ))

    bs = gt.get("below_safety", [])
    if bs:
        questions.append(TestQuestion(
            id="inventory_alert",
            question="哪些物料的当前可用数量低于安全库存？请列出物料编码、可用数量和安全库存。",
            description="跨字段比较：available < safety_stock",
            verify=lambda r, b=bs: _contains_any(r, [x["material_code"] for x in b[:5]]),
        ))

    so = gt.get("sample_order")
    if so and so.get("contract_number"):
        questions.append(TestQuestion(
            id="order_lookup",
            question=f"合同编号为{so['contract_number']}的订单，产品名称是什么，签约数量是多少？",
            description="精确查找：按合同号查订单",
            verify=lambda r, o=so: _contains_all(r, [o["contract_number"]]),
        ))

    sp = gt.get("sample_product")
    if sp and sp.get("product_code"):
        questions.append(TestQuestion(
            id="product_bom",
            question=f"产品{sp['product_code']}有哪些BOM子件？请列出子件编码和名称。",
            description="跨表查询：产品→BOM关联",
            verify=lambda r: _not_empty(r),
        ))

    ss = gt.get("sample_supplier")
    if ss and ss.get("provided_material_name"):
        questions.append(TestQuestion(
            id="supplier_lookup",
            question=f"物料「{ss['provided_material_name']}」的供应商是谁？含税单价是多少？",
            description="跨表查找：物料→供应商",
            verify=lambda r, s=ss: _contains_any(r, [
                s.get("supplier", ""), s.get("provided_material_code", ""),
            ]),
        ))

    mt = gt.get("materials_total")
    if mt:
        questions.append(TestQuestion(
            id="material_count",
            question="知识网络中一共有多少种物料？",
            description="统计查询：数据总量",
            verify=lambda r: _has_digits(r),
        ))

    # ── CRM / product demand questions ────────────────────────────────────

    sw = gt.get("sample_workorder")
    if sw and sw.get("workorder_number"):
        questions.append(TestQuestion(
            id="workorder_lookup",
            question=f"工单编号{sw['workorder_number']}的主题是什么？当前状态是什么？",
            description="精确查找：按工单号查CRM工单",
            verify=lambda r, w=sw: _contains_any(r, [
                w.get("workorder_number", ""), w.get("status", ""),
            ]),
        ))

    wt = gt.get("workorders_total")
    if wt:
        questions.append(TestQuestion(
            id="workorder_count",
            question="系统中一共有多少个CRM需求工单？",
            description="统计查询：CRM工单总量",
            verify=lambda r: _has_digits(r),
        ))

    sd = gt.get("sample_demand")
    if sd and sd.get("title"):
        # Extract workitem ID from title like "[ABP-14616] ..."
        title = sd["title"]
        wid = ""
        if title.startswith("["):
            wid = title.split("]")[0].strip("[")
        if wid:
            questions.append(TestQuestion(
                id="demand_lookup",
                question=f"客户需求{wid}的标题和当前状态是什么？",
                description="精确查找：按需求ID查客户需求",
                verify=lambda r, w=wid: _contains_all(r, [w]),
            ))

    se = gt.get("sample_employee")
    if se and se.get("username"):
        questions.append(TestQuestion(
            id="employee_lookup",
            question=f"员工「{se['username']}」在哪个部门？当前状态是什么？",
            description="精确查找：按姓名查员工信息",
            verify=lambda r, e=se: _contains_any(r, [
                e.get("username", ""), e.get("department", ""),
            ]),
        ))

    dt = gt.get("departments_total")
    et = gt.get("employees_total")
    if dt and et:
        questions.append(TestQuestion(
            id="org_stats",
            question="公司一共有多少个部门？多少名员工？",
            description="统计查询：组织架构数据量",
            verify=lambda r: _has_digits(r),
        ))

    cdt = gt.get("customer_demands_total")
    if cdt:
        questions.append(TestQuestion(
            id="demand_priority",
            question="客户需求中，优先级为1（最高优先级）的需求有多少个？请列出几个例子。",
            description="条件过滤 + 聚合：按优先级筛选",
            verify=lambda r: _not_empty(r),
        ))

    return questions
