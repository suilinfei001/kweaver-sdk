"""VegaNamespace -- all Vega resources under one namespace."""
from __future__ import annotations
from typing import TYPE_CHECKING
from kweaver.resources.vega.models import (
    VegaMetricModelsResource, VegaEventModelsResource, VegaTraceModelsResource,
    VegaDataViewsResource, VegaDataDictsResource, VegaObjectiveModelsResource,
)
from kweaver.resources.vega.query import VegaQueryResource
from kweaver.resources.vega.catalogs import VegaCatalogsResource
from kweaver.resources.vega.resources import VegaResourcesResource
from kweaver.resources.vega.connector_types import VegaConnectorTypesResource
from kweaver.resources.vega.tasks import VegaTasksResource
from kweaver.types import (
    VegaServerInfo, VegaPlatformStats, VegaInspectReport, VegaHealthReport,
)

if TYPE_CHECKING:
    from kweaver._http import HttpClient


class VegaNamespace:
    def __init__(self, http: HttpClient) -> None:
        self._http = http
        self.metric_models = VegaMetricModelsResource(http)
        self.event_models = VegaEventModelsResource(http)
        self.trace_models = VegaTraceModelsResource(http)
        self.data_views = VegaDataViewsResource(http)
        self.data_dicts = VegaDataDictsResource(http)
        self.objective_models = VegaObjectiveModelsResource(http)
        self.query = VegaQueryResource(http)
        self.catalogs = VegaCatalogsResource(http)
        self.resources = VegaResourcesResource(http)
        self.connector_types = VegaConnectorTypesResource(http)
        self.tasks = VegaTasksResource(http)

    def health(self) -> VegaServerInfo:
        """Return Vega server info from the /health endpoint."""
        data = self._http.get("/health")
        return VegaServerInfo(**data)

    def stats(self) -> VegaPlatformStats:
        """Return composite platform statistics (best-effort; partial on failure)."""
        s = VegaPlatformStats()
        try:
            cats = self.catalogs.list(limit=1000)
            s.catalog_count = len(cats)
        except Exception:
            pass
        try:
            s.metric_model_count = len(self.metric_models.list(limit=1000))
        except Exception:
            pass
        try:
            s.event_model_count = len(self.event_models.list(limit=1000))
        except Exception:
            pass
        try:
            s.trace_model_count = len(self.trace_models.list(limit=1000))
        except Exception:
            pass
        try:
            s.data_view_count = len(self.data_views.list(limit=1000))
        except Exception:
            pass
        try:
            s.data_dict_count = len(self.data_dicts.list(limit=1000))
        except Exception:
            pass
        try:
            s.objective_model_count = len(self.objective_models.list(limit=1000))
        except Exception:
            pass
        return s

    def inspect(self, *, full: bool = False) -> VegaInspectReport:
        """Return a one-shot health + catalog + tasks report (partial on failure)."""
        server_info: VegaServerInfo | None = None
        try:
            server_info = self.health()
        except Exception:
            pass

        catalog_health = VegaHealthReport()
        try:
            cats = self.catalogs.list(limit=1000)
            catalog_health.catalogs = [c.model_dump() for c in cats]
            catalog_health.healthy = sum(1 for c in cats if c.health_status == "healthy")
            catalog_health.unhealthy = sum(1 for c in cats if c.health_status == "unhealthy")
            catalog_health.unknown = sum(
                1 for c in cats if c.health_status not in ("healthy", "unhealthy")
            )
        except Exception:
            pass

        active_tasks = []
        try:
            active_tasks = self.tasks.list_discover(status="running")
        except Exception:
            pass

        return VegaInspectReport(
            server_info=server_info,
            catalog_health=catalog_health,
            active_tasks=active_tasks,
        )
