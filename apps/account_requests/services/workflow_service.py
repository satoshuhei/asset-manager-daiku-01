from django.core.exceptions import ValidationError

from apps.account_requests.models import Asset, AssetStatusMaster, AssetStatusTransitionMaster


def validate_asset_status_for_category(*, asset: Asset, status_code: str) -> None:
    category_l_id = asset.category_s.category_m.category_l_id
    exists = AssetStatusMaster.objects.filter(
        category_l_id=category_l_id,
        status_code=status_code,
        is_active=True,
    ).exists()
    if not exists:
        raise ValidationError(f'Invalid status for category: {status_code}')


def get_transitionable_statuses(asset: Asset):
    category_l_id = asset.category_s.category_m.category_l_id
    return AssetStatusTransitionMaster.objects.select_related('to_status').filter(
        category_l_id=category_l_id,
        from_status__status_code=asset.status,
        from_status__is_active=True,
        to_status__is_active=True,
        is_active=True,
    ).order_by('to_status__sort_order')


def transition_asset_status(asset: Asset, new_status: str) -> Asset:
    category_l_id = asset.category_s.category_m.category_l_id
    exists = AssetStatusTransitionMaster.objects.filter(
        category_l_id=category_l_id,
        from_status__status_code=asset.status,
        to_status__status_code=new_status,
        from_status__is_active=True,
        to_status__is_active=True,
        is_active=True,
    ).exists()
    if not exists:
        raise ValidationError(f'Invalid status transition: {asset.status} -> {new_status}')
    asset.status = new_status
    asset.save(update_fields=['status', 'updated_at'])
    return asset