"""Alerts through Amazon SNS with de-duplication; dry-run when SNS is not configured."""
import logging
import time

from . import config as C
from .advisories import get_advisory

log = logging.getLogger("heatwatch.alerts")
_seen: dict = {}      # alert_id -> record (used when no DynamoDB table is configured)
LOG: list = []        # recent alerts for the dashboard / demo


def _first_time(alert_id: str, record: dict) -> bool:
    """True if this alert was not sent before. Uses DynamoDB when configured."""
    if C.ALERTS_TABLE:
        try:
            import boto3
            from botocore.exceptions import ClientError
            table = boto3.resource("dynamodb").Table(C.ALERTS_TABLE)
            try:
                table.put_item(Item={"alert_id": alert_id, **{k: str(v) for k, v in record.items()}},
                               ConditionExpression="attribute_not_exists(alert_id)")
                return True
            except ClientError as e:
                if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                    return False
                raise
        except Exception as exc:
            log.warning("DynamoDB unavailable (%s); using in-memory de-dupe", exc)
    if alert_id in _seen:
        return False
    _seen[alert_id] = record
    return True


def send_alert(row: dict, day: int, resources: list, force: bool = False) -> dict:
    """Publish an English + Hindi alert for one ward. Returns a status record."""
    alert_id = f"{row['id']}#{row['date']}#{row['band']}"
    record = {"ward": row["name"], "band": row["band"], "priority": row["priority"],
              "date": row["date"], "ts": int(time.time())}
    if not force and not _first_time(alert_id, record):
        return {**record, "alert_id": alert_id, "status": "skipped-duplicate"}
    en = get_advisory(row, "en", day, resources)["text"]
    hi = get_advisory(row, "hi", day, resources)["text"]
    message = f"{en}\n\n{hi}"
    status = "dry-run"
    if C.ALERT_TOPIC_ARN:
        try:
            import boto3
            boto3.client("sns").publish(TopicArn=C.ALERT_TOPIC_ARN, Message=message,
                                        Subject=f"HeatWatch: {row['name']} {row['band']} heat risk"[:100])
            status = "sent"
        except Exception as exc:
            log.error("SNS publish failed: %s", exc)
            status = "failed"
    out = {**record, "alert_id": alert_id, "status": status, "message": message}
    LOG.append(out)
    del LOG[:-50]
    return out


def check_and_alert(rows: list, day: int, resources: list, min_priority: float | None = None) -> list:
    """Alert every ward at or above the threshold (scheduled job + manual trigger)."""
    limit = C.ALERT_MIN_PRIORITY if min_priority is None else min_priority
    return [send_alert(r, day, resources) for r in sorted(rows, key=lambda r: -r["priority"])
            if r["priority"] >= limit]
