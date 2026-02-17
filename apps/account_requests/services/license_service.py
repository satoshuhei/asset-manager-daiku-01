from django.core.exceptions import ValidationError
from django.db import transaction

from apps.account_requests.models import LicenseAllocationHistory, LicensePool
from apps.account_requests.services.audit_service import record_audit


@transaction.atomic
def create_license_pool(*, payload: dict, actor):
    pool = LicensePool.objects.create(
        license_name=payload['license_name'],
        total_count=payload['total_count'],
        used_count=payload.get('used_count', 0),
        contract_expiry_date=payload.get('contract_expiry_date'),
    )
    record_audit(
        target_table='license_pool',
        target_id=pool.id,
        action='CREATE',
        changed_by=actor,
        summary='License pool created',
    )
    return pool


@transaction.atomic
def allocate_license(*, pool: LicensePool, payload: dict, actor):
    allocate_count = payload.get('allocated_count', 1)
    if pool.used_count + allocate_count > pool.total_count:
        raise ValidationError('License allocation exceeds total_count.')

    history = LicenseAllocationHistory.objects.create(
        pool=pool,
        asset_id=payload['asset_id'],
        allocated_count=allocate_count,
    )
    pool.used_count += allocate_count
    pool.save(update_fields=['used_count', 'remaining_count', 'updated_at'])

    record_audit(
        target_table='license_allocation_history',
        target_id=history.id,
        action='CREATE',
        changed_by=actor,
        summary='License allocated',
    )
    return history