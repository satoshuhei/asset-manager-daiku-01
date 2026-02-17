import csv
from io import StringIO

from django.core.exceptions import ValidationError

from apps.account_requests.models import Asset
from apps.account_requests.services.asset_service import create_asset


ASSET_EXPORT_FIELDS = [
    'asset_code',
    'asset_name',
    'asset_kind',
    'status',
    'budget_link_status',
    'budget_id',
]


def export_assets_csv() -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=ASSET_EXPORT_FIELDS)
    writer.writeheader()
    for asset in Asset.objects.all().order_by('id'):
        writer.writerow(
            {
                'asset_code': asset.asset_code,
                'asset_name': asset.asset_name,
                'asset_kind': asset.asset_kind,
                'status': asset.status,
                'budget_link_status': asset.budget_link_status,
                'budget_id': asset.budget_id or '',
            }
        )
    return output.getvalue()


def import_assets_csv(*, content: str, actor):
    reader = csv.DictReader(StringIO(content))
    imported = 0
    errors = []
    for index, row in enumerate(reader, start=2):
        try:
            payload = {
                'asset_code': row['asset_code'],
                'asset_type_id': int(row['asset_type_id']),
                'category_s_id': int(row['category_s_id']),
                'asset_name': row['asset_name'],
                'asset_kind': row['asset_kind'],
                'status': row.get('status') or Asset.AssetStatus.IN_USE,
                'budget_id': int(row['budget_id']) if row.get('budget_id') else None,
                'budget_link_status': row.get('budget_link_status') or Asset.BudgetLinkStatus.UNLINKED,
                'attributes': {
                    'person_attr_01': int(row['person_attr_01']) if row.get('person_attr_01') else None,
                    'person_attr_02': int(row['person_attr_02']) if row.get('person_attr_02') else None,
                },
                'multi_attributes': [],
            }
            create_asset(payload=payload, actor=actor)
            imported += 1
        except (KeyError, ValueError, ValidationError) as exc:
            message = exc.message if hasattr(exc, 'message') else str(exc)
            errors.append({'line': index, 'message': message})

    return {'imported': imported, 'errors': errors}
