"""Tests for Vega SDK resources."""
from __future__ import annotations
import httpx
import pytest
from kweaver._auth import TokenAuth
from kweaver._http import HttpClient
from kweaver.types import (
    VegaMetricModel, VegaEventModel, VegaTraceModel,
    VegaDataView, VegaDataDict, VegaObjectiveModel,
    VegaQueryResult, VegaDslResult, VegaPromqlResult,
    VegaCatalog, VegaResource, VegaConnectorType,
    VegaDiscoverTask, VegaServerInfo, VegaInspectReport,
)

def _make_vega_http(handler):
    transport = httpx.MockTransport(handler)
    return HttpClient(base_url="http://vega-mock:13014", auth=TokenAuth("tok"), transport=transport)


# -- Parameterized model tests -----------------------------------------------

MODEL_RESOURCES = [
    ("metric_models",    "/api/mdl-data-model/v1/metric-models",    VegaMetricModel,    {"id": "mm-1", "name": "cpu"}),
    ("event_models",     "/api/mdl-data-model/v1/event-models",     VegaEventModel,     {"id": "em-1", "name": "alert"}),
    ("trace_models",     "/api/mdl-data-model/v1/trace-models",     VegaTraceModel,     {"id": "tm-1", "name": "traces"}),
    ("data_views",       "/api/mdl-data-model/v1/data-views",       VegaDataView,       {"id": "dv-1", "name": "view1"}),
    ("data_dicts",       "/api/mdl-data-model/v1/data-dicts",       VegaDataDict,       {"id": "dd-1", "name": "codes"}),
    ("objective_models", "/api/mdl-data-model/v1/objective-models",  VegaObjectiveModel, {"id": "om-1", "name": "sla"}),
]


@pytest.mark.parametrize("attr,path,model_cls,sample", MODEL_RESOURCES)
def test_model_list(attr, path, model_cls, sample):
    def handler(req):
        return httpx.Response(200, json={"entries": [sample]})
    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    result = getattr(ns, attr).list()
    assert len(result) == 1
    assert isinstance(result[0], model_cls)


@pytest.mark.parametrize("attr,path,model_cls,sample", MODEL_RESOURCES)
def test_model_list_data_format(attr, path, model_cls, sample):
    """list() should also handle {"data": [...]} response format."""
    def handler(req):
        return httpx.Response(200, json={"data": [sample]})
    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    result = getattr(ns, attr).list()
    assert len(result) == 1
    assert isinstance(result[0], model_cls)


@pytest.mark.parametrize("attr,path,model_cls,sample", MODEL_RESOURCES)
def test_model_get(attr, path, model_cls, sample):
    def handler(req):
        return httpx.Response(200, json=sample)
    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    result = getattr(ns, attr).get(sample["id"])
    assert isinstance(result, model_cls)
    assert result.id == sample["id"]


@pytest.mark.parametrize("attr,path,model_cls,sample", MODEL_RESOURCES)
def test_model_get_entries_wrapper(attr, path, model_cls, sample):
    """get() should unwrap {"entries": [obj]} response format."""
    def handler(req):
        return httpx.Response(200, json={"entries": [sample]})
    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    result = getattr(ns, attr).get(sample["id"])
    assert isinstance(result, model_cls)
    assert result.id == sample["id"]


# -- VegaQueryResource tests -------------------------------------------------


def test_query_execute_basic():
    """execute() posts to the correct endpoint and returns VegaQueryResult."""
    def handler(req):
        assert req.url.path == "/api/vega-backend/v1/query/execute"
        return httpx.Response(200, json={"entries": [{"id": "row1"}], "total_count": 1})

    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    result = ns.query.execute(tables=["cpu"], limit=10)
    assert isinstance(result, VegaQueryResult)
    assert result.total_count == 1
    assert result.entries[0]["id"] == "row1"


def test_query_execute_empty_response():
    """execute() returns empty VegaQueryResult when API returns empty dict."""
    def handler(req):
        return httpx.Response(200, json={})

    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    result = ns.query.execute()
    assert isinstance(result, VegaQueryResult)
    assert result.entries == []
    assert result.total_count == 0


def test_query_dsl_with_index():
    """dsl() posts to index-specific endpoint when index is provided."""
    def handler(req):
        assert req.url.path == "/api/mdl-uniquery/v1/dsl/my-index/_search"
        return httpx.Response(200, json={"hits": [{"_id": "doc1"}], "total": 1, "took_ms": 5})

    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    result = ns.query.dsl(index="my-index", body={"query": {"match_all": {}}})
    assert isinstance(result, VegaDslResult)
    assert result.total == 1
    assert result.hits[0]["_id"] == "doc1"


def test_query_dsl_without_index():
    """dsl() posts to generic endpoint when index is not provided."""
    def handler(req):
        assert req.url.path == "/api/mdl-uniquery/v1/dsl/_search"
        return httpx.Response(200, json={"hits": [], "total": 0, "took_ms": 2})

    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    result = ns.query.dsl(body={"query": {"match_all": {}}})
    assert isinstance(result, VegaDslResult)
    assert result.total == 0


def test_query_dsl_count_with_index():
    """dsl_count() posts to index-specific count endpoint."""
    def handler(req):
        assert req.url.path == "/api/mdl-uniquery/v1/dsl/events/_count"
        return httpx.Response(200, json={"count": 42})

    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    count = ns.query.dsl_count(index="events", body={"query": {"match_all": {}}})
    assert count == 42


def test_query_dsl_count_without_index():
    """dsl_count() posts to generic count endpoint when index is not provided."""
    def handler(req):
        assert req.url.path == "/api/mdl-uniquery/v1/dsl/_count"
        return httpx.Response(200, json={"count": 7})

    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    count = ns.query.dsl_count(body={})
    assert count == 7


def test_query_promql():
    """promql() posts to query_range endpoint and returns VegaPromqlResult."""
    def handler(req):
        assert req.url.path == "/api/mdl-uniquery/v1/promql/query_range"
        return httpx.Response(200, json={
            "data": {"status": "success", "result_type": "matrix", "result": []}
        })

    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    result = ns.query.promql(
        query="up",
        start="2026-01-01T00:00:00Z",
        end="2026-01-01T01:00:00Z",
        step="60s",
    )
    assert isinstance(result, VegaPromqlResult)
    assert result.status == "success"
    assert result.result_type == "matrix"


def test_query_promql_instant():
    """promql_instant() posts to instant query endpoint and returns VegaPromqlResult."""
    def handler(req):
        assert req.url.path == "/api/mdl-uniquery/v1/promql/query"
        return httpx.Response(200, json={
            "data": {
                "status": "success",
                "result_type": "vector",
                "result": [{"metric": {}, "value": [1, "1"]}],
            }
        })

    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    result = ns.query.promql_instant(query="up")
    assert isinstance(result, VegaPromqlResult)
    assert result.status == "success"
    assert result.result_type == "vector"


def test_query_events():
    """events() posts to events endpoint and returns VegaDslResult."""
    def handler(req):
        assert req.url.path == "/api/mdl-uniquery/v1/events"
        return httpx.Response(200, json={"hits": [{"event": "login"}], "total": 1, "took_ms": 3})

    from kweaver.resources.vega import VegaNamespace
    ns = VegaNamespace(_make_vega_http(handler))
    result = ns.query.events(body={"filter": {"type": "login"}})
    assert isinstance(result, VegaDslResult)
    assert result.total == 1
    assert result.hits[0]["event"] == "login"
