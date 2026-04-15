import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit_log import AuditLogEntry


async def log_access(
    db: AsyncSession,
    actor_type: str,
    actor_id: uuid.UUID,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID,
    clearance_check_result: str | None = None,
    metadata: dict | None = None,
) -> AuditLogEntry:
    entry = AuditLogEntry(
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        clearance_check_result=clearance_check_result,
        metadata_=metadata,
    )
    db.add(entry)
    await db.flush()

    # Async SLS shipping (fire-and-forget in production)
    await _ship_to_sls(entry)

    return entry


async def _ship_to_sls(entry: AuditLogEntry) -> None:
    """Ship audit log entry to Alibaba Cloud SLS for long-term compliance retention.

    In production, this uses the Alibaba Cloud Log Service SDK (aliyun-log-python-sdk)
    to push logs to a configured logstore. Currently a placeholder that formats the
    log record for future integration.
    """
    try:
        from src.config import get_settings
        get_settings()

        log_record = {
            "id": str(entry.id),
            "actor_type": entry.actor_type,
            "actor_id": str(entry.actor_id) if entry.actor_id else None,
            "action": entry.action,
            "resource_type": entry.resource_type,
            "resource_id": str(entry.resource_id) if entry.resource_id else None,
            "clearance_check_result": entry.clearance_check_result,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Production: use aliyun.log.PutLogsRequest to ship to SLS logstore
        # from aliyun.log import LogClient, LogItem, PutLogsRequest
        # client = LogClient(settings.sls_endpoint, settings.alibaba_access_key_id, settings.alibaba_access_key_secret)
        # log_item = LogItem(contents=list(log_record.items()))
        # request = PutLogsRequest(settings.sls_project, settings.sls_logstore, "", "", [log_item])
        # client.put_logs(request)
        _ = log_record  # Placeholder: record formatted, ready for SLS SDK integration

    except Exception:
        # SLS shipping failure must never break the main flow
        logging.getLogger(__name__).exception("SLS audit shipping failed")
