from django.core.exceptions import ValidationError
from django.db import transaction

from apps.account_requests.models import Asset, UserPCAssignment
from apps.account_requests.services.audit_service import record_audit


@transaction.atomic
def assign_pc_user(*, payload: dict, actor):
    asset = Asset.objects.get(id=payload['asset_id'])
    if asset.asset_kind != Asset.AssetKind.PC:
        raise ValidationError('Only PC assets can be assigned in PC management.')

    assignment, _ = UserPCAssignment.objects.update_or_create(
        asset=asset,
        defaults={
            'user_id': payload['user_id'],
            'os_name': payload['os_name'],
            'spec_text': payload.get('spec_text', ''),
            'warranty_expiry_date': payload.get('warranty_expiry_date'),
        },
    )
    record_audit(
        target_table='user_pc_assignment',
        target_id=assignment.id,
        action='UPSERT',
        changed_by=actor,
        summary='PC assignment updated',
    )
    return assignment
