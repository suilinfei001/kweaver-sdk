"""E2E: Vega query operations."""
import pytest

pytestmark = pytest.mark.e2e


def test_vega_task_list_discover(vega_client):
    """List discover tasks — may return 404 if no discoverable catalog exists."""
    from kweaver._errors import NotFoundError
    try:
        tasks = vega_client.tasks.list_discover()
        assert isinstance(tasks, list)
    except NotFoundError:
        pytest.skip("No discoverable catalog configured")
