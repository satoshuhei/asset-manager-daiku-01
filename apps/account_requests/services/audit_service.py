from apps.account_requests.models import AuditLog


def record_audit(*, target_table: str, target_id: int, action: str, changed_by, summary: str = '') -> AuditLog:
    return AuditLog.objects.create(
        target_table=target_table,
        target_id=target_id,
        action=action,
        changed_by=changed_by,
        change_summary=summary,
    )