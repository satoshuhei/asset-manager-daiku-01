from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.account_requests.models import Asset, LoanHistory
from apps.account_requests.services.audit_service import record_audit


@transaction.atomic
def create_loan_history(*, payload: dict, actor):
    asset = Asset.objects.get(id=payload['asset_id'])
    if asset.status == Asset.AssetStatus.DISPOSED:
        raise ValidationError('Disposed assets cannot be loaned.')

    if LoanHistory.objects.filter(asset=asset, returned_at__isnull=True).exists():
        raise ValidationError('Asset is already loaned and not yet returned.')

    history = LoanHistory.objects.create(
        asset=asset,
        borrower_id=payload['borrower_id'],
    )

    record_audit(
        target_table='loan_history',
        target_id=history.id,
        action='CREATE',
        changed_by=actor,
        summary='Loan history created',
    )
    return history


@transaction.atomic
def return_loan_history(*, history: LoanHistory, actor):
    if history.returned_at is not None:
        raise ValidationError('Loan already returned.')

    history.returned_at = timezone.now()
    history.save(update_fields=['returned_at'])

    record_audit(
        target_table='loan_history',
        target_id=history.id,
        action='RETURN',
        changed_by=actor,
        summary='Loan returned',
    )
    return history
