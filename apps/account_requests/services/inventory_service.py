from django.db import transaction

from apps.account_requests.models import InventoryResult
from apps.account_requests.services.audit_service import record_audit


@transaction.atomic
def create_inventory_result(*, payload: dict, actor):
    result = InventoryResult.objects.create(
        cycle_id=payload['cycle_id'],
        asset_id=payload['asset_id'],
        difference_type=payload['difference_type'],
        correction_status=payload.get('correction_status', InventoryResult.CorrectionStatus.OPEN),
        correction_note=payload.get('correction_note', ''),
        registered_by=actor,
    )
    record_audit(
        target_table='inventory_result',
        target_id=result.id,
        action='CREATE',
        changed_by=actor,
        summary='Inventory result created',
    )
    return result


@transaction.atomic
def update_inventory_result(*, instance: InventoryResult, payload: dict, actor):
    for field in ['difference_type', 'correction_status', 'correction_note']:
        if field in payload:
            setattr(instance, field, payload[field])
    instance.updated_by = actor
    instance.save()
    record_audit(
        target_table='inventory_result',
        target_id=instance.id,
        action='UPDATE',
        changed_by=actor,
        summary='Inventory result updated',
    )
    return instance