from django.core.exceptions import ValidationError
from django.db import transaction

from apps.account_requests.models import Asset, AssetAttributeMultiValue, AssetAttributeValue, Budget
from apps.account_requests.services.audit_service import record_audit
from apps.account_requests.services.workflow_service import transition_asset_status, validate_asset_status_for_category


@transaction.atomic
def create_asset(*, payload: dict, actor):
    attributes = payload.get('attributes', {})
    multi_attributes = payload.get('multi_attributes', [])

    if payload.get('asset_kind') == Asset.AssetKind.PC and not attributes.get('person_attr_01'):
        raise ValidationError('PC asset requires person_attr_01.')

    status = payload.get('status', Asset.AssetStatus.IN_USE)
    asset = Asset.objects.create(
        asset_code=payload['asset_code'],
        asset_type_id=payload['asset_type_id'],
        category_s_id=payload['category_s_id'],
        asset_name=payload['asset_name'],
        asset_kind=payload['asset_kind'],
        status=status,
        vendor_id=payload.get('vendor_id'),
        budget_id=payload.get('budget_id'),
        budget_link_status=payload.get('budget_link_status', Asset.BudgetLinkStatus.UNLINKED),
        purchase_date=payload.get('purchase_date'),
        warranty_expiry_date=payload.get('warranty_expiry_date'),
    )
    validate_asset_status_for_category(asset=asset, status_code=status)

    AssetAttributeValue.objects.create(
        asset=asset,
        cls_attr_01=attributes.get('cls_attr_01', ''),
        cls_attr_02=attributes.get('cls_attr_02', ''),
        cls_attr_03=attributes.get('cls_attr_03', ''),
        cls_attr_04=attributes.get('cls_attr_04', ''),
        cls_attr_05=attributes.get('cls_attr_05', ''),
        person_attr_01_id=attributes.get('person_attr_01'),
        person_attr_02_id=attributes['person_attr_02'],
        person_attr_03_id=attributes.get('person_attr_03', actor.id),
        location_attr_01=attributes.get('location_attr_01', ''),
        location_attr_02=attributes.get('location_attr_02', ''),
        date_attr_01=attributes.get('date_attr_01'),
        date_attr_02=attributes.get('date_attr_02'),
        date_attr_03=attributes.get('date_attr_03'),
        free_text_attr_01=attributes.get('free_text_attr_01', ''),
        free_text_attr_02=attributes.get('free_text_attr_02', ''),
        free_text_attr_03=attributes.get('free_text_attr_03', ''),
        memo_attr_01=attributes.get('memo_attr_01', ''),
        memo_attr_02=attributes.get('memo_attr_02', ''),
    )

    for item in multi_attributes:
        AssetAttributeMultiValue.objects.create(
            asset=asset,
            multi_attr_type=item['multi_attr_type'],
            value=item['value'],
            sort_order=item.get('sort_order', 1),
        )

    record_audit(
        target_table='asset',
        target_id=asset.id,
        action='CREATE',
        changed_by=actor,
        summary='Asset created via service',
    )
    return asset


@transaction.atomic
def update_budget_link(*, asset: Asset, budget_id: int | None, actor):
    if budget_id is not None and not Budget.objects.filter(id=budget_id).exists():
        raise ValidationError('Budget not found.')

    asset.budget_id = budget_id
    asset.budget_link_status = Asset.BudgetLinkStatus.LINKED if budget_id else Asset.BudgetLinkStatus.UNLINKED
    asset.save(update_fields=['budget_id', 'budget_link_status', 'updated_at'])

    record_audit(
        target_table='asset',
        target_id=asset.id,
        action='BUDGET_LINK',
        changed_by=actor,
        summary=f'budget_id={budget_id}',
    )
    return asset


@transaction.atomic
def update_asset(*, asset: Asset, payload: dict, actor):
    requested_status = payload.get('status')
    if 'asset_name' in payload:
        asset.asset_name = payload['asset_name']
    if 'asset_kind' in payload:
        asset.asset_kind = payload['asset_kind']
    if 'category_s_id' in payload:
        asset.category_s_id = payload['category_s_id']
    if 'vendor_id' in payload:
        asset.vendor_id = payload['vendor_id']
    if 'purchase_date' in payload:
        asset.purchase_date = payload['purchase_date']
    if 'warranty_expiry_date' in payload:
        asset.warranty_expiry_date = payload['warranty_expiry_date']
    asset.save()

    if requested_status and requested_status != asset.status:
        transition_asset_status(asset=asset, new_status=requested_status)

    attributes_payload = payload.get('attributes')
    attribute_value = AssetAttributeValue.objects.filter(asset=asset).first()
    if attributes_payload is not None:
        if attribute_value is None:
            if 'person_attr_02' not in attributes_payload:
                raise ValidationError('person_attr_02 is required for attribute initialization.')
            attribute_value = AssetAttributeValue(asset=asset, person_attr_02_id=attributes_payload['person_attr_02'])

        for field in ['cls_attr_01', 'cls_attr_02', 'cls_attr_03', 'cls_attr_04', 'cls_attr_05']:
            if field in attributes_payload:
                setattr(attribute_value, field, attributes_payload[field] or '')

        for field in ['person_attr_01', 'person_attr_02', 'person_attr_03']:
            if field in attributes_payload:
                setattr(attribute_value, f'{field}_id', attributes_payload[field])

        for field in ['location_attr_01', 'location_attr_02']:
            if field in attributes_payload:
                setattr(attribute_value, field, attributes_payload[field] or '')

        for field in ['date_attr_01', 'date_attr_02', 'date_attr_03']:
            if field in attributes_payload:
                setattr(attribute_value, field, attributes_payload[field])

        for field in ['free_text_attr_01', 'free_text_attr_02', 'free_text_attr_03', 'memo_attr_01', 'memo_attr_02']:
            if field in attributes_payload:
                setattr(attribute_value, field, attributes_payload[field] or '')

        if 'person_attr_03' not in attributes_payload:
            attribute_value.person_attr_03_id = actor.id

        if not attribute_value.person_attr_02_id:
            raise ValidationError('person_attr_02 is required.')

        attribute_value.save()

    effective_attr = attribute_value or AssetAttributeValue.objects.filter(asset=asset).first()
    if asset.asset_kind == Asset.AssetKind.PC and not (effective_attr and effective_attr.person_attr_01_id):
        raise ValidationError('PC asset requires person_attr_01.')

    if 'multi_attributes' in payload:
        AssetAttributeMultiValue.objects.filter(asset=asset).delete()
        for item in payload['multi_attributes']:
            AssetAttributeMultiValue.objects.create(
                asset=asset,
                multi_attr_type=item['multi_attr_type'],
                value=item['value'],
                sort_order=item.get('sort_order', 1),
            )

    record_audit(
        target_table='asset',
        target_id=asset.id,
        action='UPDATE',
        changed_by=actor,
        summary='Asset updated via service',
    )
    return asset