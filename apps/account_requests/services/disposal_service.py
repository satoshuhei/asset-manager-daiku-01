from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.account_requests.models import Asset, DisposalHistory
from apps.account_requests.services.audit_service import record_audit
from apps.account_requests.services.workflow_service import transition_asset_status


@transaction.atomic
def request_disposal(*, asset: Asset, requested_by):
    disposal = DisposalHistory.objects.create(asset=asset, requested_by=requested_by)
    record_audit(
        target_table='disposal_history',
        target_id=disposal.id,
        action='REQUEST',
        changed_by=requested_by,
        summary='Disposal requested',
    )
    return disposal


@transaction.atomic
def approve_disposal(*, disposal: DisposalHistory, approved_by, evidence_text: str):
    if not evidence_text:
        raise ValidationError('evidence_text is required to approve disposal.')

    disposal.approved_by = approved_by
    disposal.approved_at = timezone.now()
    disposal.evidence_text = evidence_text
    disposal.disposal_status = DisposalHistory.DisposalStatus.APPROVED
    disposal.save(update_fields=['approved_by', 'approved_at', 'evidence_text', 'disposal_status'])

    transition_asset_status(disposal.asset, Asset.AssetStatus.DISPOSED)

    record_audit(
        target_table='disposal_history',
        target_id=disposal.id,
        action='APPROVE',
        changed_by=approved_by,
        summary='Disposal approved',
    )
    return disposal


@transaction.atomic
def reject_disposal(*, disposal: DisposalHistory, approved_by, reason: str):
    if not reason:
        raise ValidationError('reason is required to reject disposal.')

    disposal.approved_by = approved_by
    disposal.approved_at = timezone.now()
    disposal.reject_reason = reason
    disposal.disposal_status = DisposalHistory.DisposalStatus.REJECTED
    disposal.save(update_fields=['approved_by', 'approved_at', 'reject_reason', 'disposal_status'])

    record_audit(
        target_table='disposal_history',
        target_id=disposal.id,
        action='REJECT',
        changed_by=approved_by,
        summary='Disposal rejected',
    )
    return disposal