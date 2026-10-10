"""EventBridge entry point: score tomorrow's risk and alert wards above the threshold."""
from .alerts import check_and_alert
from .service import get_resource_list, ward_rows


def scheduled_handler(event=None, context=None) -> dict:
    rows, _, source = ward_rows(1)
    resources, _ = get_resource_list()
    results = check_and_alert(rows, 1, resources)
    return {"forecast_source": source, "alerts": [
        {k: a[k] for k in ("ward", "band", "priority", "status")} for a in results]}
