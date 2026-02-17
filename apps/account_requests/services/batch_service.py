from datetime import timedelta

from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from apps.account_requests.models import (
    Asset,
    AssetBudgetMonitorDaily,
    DashboardKPIDaily,
    InventoryCycle,
    InventoryResult,
    InventoryTargetSnapshot,
    NotificationQueue,
)


@transaction.atomic
def run_maintenance_notification_batch():
    today = timezone.localdate()
    near_date = today + timedelta(days=30)
    targets = Asset.objects.filter(warranty_expiry_date__isnull=False, warranty_expiry_date__lte=near_date)
    count = 0
    for asset in targets:
        NotificationQueue.objects.create(
            notification_type='MAINTENANCE_ALERT',
            title='保守期限通知',
            body=f'{asset.asset_code} の期限日 {asset.warranty_expiry_date}',
            status=NotificationQueue.QueueStatus.PENDING,
            scheduled_at=timezone.now(),
        )
        count += 1
    return count


@transaction.atomic
def run_unlinked_asset_monitor_batch(*, threshold: int = 10):
    today = timezone.localdate()
    grouped = (
        Asset.objects.filter(budget_link_status=Asset.BudgetLinkStatus.UNLINKED)
        .values('category_s_id')
        .annotate(count=Count('id'))
    )
    created = 0
    for item in grouped:
        AssetBudgetMonitorDaily.objects.update_or_create(
            monitor_date=today,
            dept_code='',
            category_s_id=item['category_s_id'],
            defaults={
                'unlinked_count': item['count'],
                'threshold_count': threshold,
                'is_threshold_exceeded': item['count'] >= threshold,
            },
        )
        created += 1
    return created


@transaction.atomic
def run_dashboard_kpi_batch():
    today = timezone.localdate()
    unlinked_count = Asset.objects.filter(budget_link_status=Asset.BudgetLinkStatus.UNLINKED).count()
    maintenance_overdue_count = Asset.objects.filter(warranty_expiry_date__lt=today).count()
    inventory_diff_count = InventoryResult.objects.exclude(correction_status=InventoryResult.CorrectionStatus.DONE).count()
    total_assets = Asset.objects.count()
    linked_assets = Asset.objects.filter(budget_link_status=Asset.BudgetLinkStatus.LINKED).count()
    completeness = round((linked_assets / total_assets) * 100, 2) if total_assets else 0

    DashboardKPIDaily.objects.update_or_create(
        kpi_date=today,
        defaults={
            'budget_consumption_rate': 0,
            'unlinked_asset_count': unlinked_count,
            'maintenance_overdue_count': maintenance_overdue_count,
            'inventory_diff_count': inventory_diff_count,
            'configuration_completeness_rate': completeness,
        },
    )
    return True


@transaction.atomic
def run_inventory_target_snapshot_batch(*, cycle_id: int):
    cycle = InventoryCycle.objects.get(id=cycle_id)
    created = 0
    for asset in Asset.objects.exclude(status=Asset.AssetStatus.DISPOSED):
        _, is_created = InventoryTargetSnapshot.objects.update_or_create(
            cycle=cycle,
            asset=asset,
            defaults={
                'status_at_snapshot': asset.status,
                'budget_link_status_at_snapshot': asset.budget_link_status,
            },
        )
        if is_created:
            created += 1
    return created
