"""E2E: Job read operations."""
import pytest
from kweaver import KWeaverClient
from kweaver._errors import AuthorizationError

pytestmark = pytest.mark.e2e


def test_job_list(kweaver_client: KWeaverClient, kn_with_data):
    """SDK: list jobs (may be empty)."""
    kn = kn_with_data["kn"]
    try:
        jobs = kweaver_client.jobs.list(kn.id)
    except AuthorizationError:
        pytest.skip("insufficient permissions for task_manage")
    assert isinstance(jobs, list)
