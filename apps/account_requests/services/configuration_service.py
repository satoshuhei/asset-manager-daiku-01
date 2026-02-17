from django.core.exceptions import ValidationError
from django.db import transaction

from apps.account_requests.models import Asset, Configuration, ConfigurationItem
from apps.account_requests.services.audit_service import record_audit


@transaction.atomic
def create_configuration(*, payload: dict, actor):
    config = Configuration.objects.create(
        config_code=payload['config_code'],
        config_name=payload['config_name'],
        status=payload.get('status', 'ACTIVE'),
    )

    for item in payload.get('items', []):
        asset = Asset.objects.get(id=item['asset_id'])
        if asset.status == Asset.AssetStatus.DISPOSED:
            raise ValidationError('Disposed asset cannot be added to configuration.')
        ConfigurationItem.objects.create(
            configuration=config,
            asset=asset,
            role_type=item['role_type'],
            quantity=item.get('quantity', 1),
        )

    record_audit(
        target_table='configuration',
        target_id=config.id,
        action='CREATE',
        changed_by=actor,
        summary='Configuration created',
    )
    return config