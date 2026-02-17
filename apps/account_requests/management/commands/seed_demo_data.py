from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.account_requests.models import (
    Asset,
    AssetCategoryL,
    AssetCategoryM,
    AssetCategoryS,
    AssetStatusMaster,
    AssetStatusTransitionMaster,
    AssetType,
    Budget,
    BudgetCategoryL,
    BudgetCategoryM,
    BudgetCategoryS,
    InventoryCycle,
    Project,
)
from apps.account_requests.services.asset_service import create_asset


class Command(BaseCommand):
    help = 'ローカル動作確認用のデモデータを投入する'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bulk-size',
            type=int,
            default=300,
            help='追加投入するサンプル資産件数（既定: 300）',
        )

    def handle(self, *args, **options):
        bulk_size = max(0, int(options.get('bulk_size') or 0))
        user_model = get_user_model()

        admin_user, created = user_model.objects.get_or_create(
            username='admin',
            defaults={'is_staff': True, 'is_superuser': True, 'is_active': True},
        )
        if created or not admin_user.check_password('admin1234'):
            admin_user.set_password('admin1234')
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.is_active = True
            admin_user.save()

        editor_user, created = user_model.objects.get_or_create(
            username='editor',
            defaults={'is_staff': False, 'is_superuser': False, 'is_active': True},
        )
        if created or not editor_user.check_password('pass1234'):
            editor_user.set_password('pass1234')
            editor_user.is_active = True
            editor_user.save()

        approver_user, created = user_model.objects.get_or_create(
            username='approver',
            defaults={'is_staff': True, 'is_superuser': False, 'is_active': True},
        )
        if created or not approver_user.check_password('pass1234'):
            approver_user.set_password('pass1234')
            approver_user.is_staff = True
            approver_user.is_active = True
            approver_user.save()

        asset_type, _ = AssetType.objects.get_or_create(code='PC', defaults={'name': 'PC'})
        category_l, _ = AssetCategoryL.objects.get_or_create(code='L1', defaults={'name': '大分類1'})
        category_m, _ = AssetCategoryM.objects.get_or_create(category_l=category_l, code='M1', defaults={'name': '中分類1'})
        category_s, _ = AssetCategoryS.objects.get_or_create(category_m=category_m, code='S1', defaults={'name': '小分類1'})

        status_defs = [
            ('REQUESTED_FROM_IT', 'IT部依頼中（受領待ち）', 1),
            ('RECEIVED_WAITING', '受領済（配備待ち）', 2),
            ('WAITING_ASSIGNMENT', '利用者割当待ち', 3),
            ('IN_USE', 'ユーザー利用中', 4),
            ('RETURN_PENDING', '返却依頼中', 5),
            ('RETURNED', '返却済', 6),
            ('MAINTENANCE', '保守対応中', 7),
            ('REPAIRING', '修理中', 8),
            ('RETIRED_WAITING', '廃棄判定待ち', 9),
            ('DISPOSED', '廃棄済', 10),
        ]
        transition_defs = [
            ('REQUESTED_FROM_IT', 'RECEIVED_WAITING'),
            ('RECEIVED_WAITING', 'WAITING_ASSIGNMENT'),
            ('WAITING_ASSIGNMENT', 'IN_USE'),
            ('IN_USE', 'RETURN_PENDING'),
            ('RETURN_PENDING', 'RETURNED'),
            ('RETURNED', 'WAITING_ASSIGNMENT'),
            ('IN_USE', 'MAINTENANCE'),
            ('MAINTENANCE', 'IN_USE'),
            ('MAINTENANCE', 'REPAIRING'),
            ('REPAIRING', 'MAINTENANCE'),
            ('IN_USE', 'RETIRED_WAITING'),
            ('IN_USE', 'DISPOSED'),
            ('RETURNED', 'RETIRED_WAITING'),
            ('MAINTENANCE', 'RETIRED_WAITING'),
            ('RETIRED_WAITING', 'DISPOSED'),
        ]
        status_map = {}
        for code, name, sort_order in status_defs:
            status, _ = AssetStatusMaster.objects.get_or_create(
                category_l=category_l,
                status_code=code,
                defaults={'status_name': name, 'sort_order': sort_order, 'is_active': True},
            )
            status_map[code] = status
        for from_code, to_code in transition_defs:
            AssetStatusTransitionMaster.objects.get_or_create(
                category_l=category_l,
                from_status=status_map[from_code],
                to_status=status_map[to_code],
                defaults={'is_active': True},
            )
        budget_l, _ = BudgetCategoryL.objects.get_or_create(code='BL1', defaults={'name': '予算大分類1'})
        budget_m, _ = BudgetCategoryM.objects.get_or_create(category_l=budget_l, code='BM1', defaults={'name': '予算中分類1'})
        budget_s, _ = BudgetCategoryS.objects.get_or_create(category_m=budget_m, code='BS1', defaults={'name': '予算小分類1'})
        project, _ = Project.objects.get_or_create(project_code='PJ-DEMO', defaults={'project_name': 'Demo Project'})
        budget, _ = Budget.objects.get_or_create(
            fiscal_year=2026,
            budget_category='CAPEX',
            project=project,
            defaults={'planned_amount': 1000000, 'budget_category_s': budget_s},
        )
        if budget.budget_category_s_id is None:
            budget.budget_category_s = budget_s
            budget.save(update_fields=['budget_category_s', 'updated_at'])

        if not Asset.objects.filter(asset_code='AS-DEMO-001').exists():
            create_asset(
                payload={
                    'asset_code': 'AS-DEMO-001',
                    'asset_type_id': asset_type.id,
                    'category_s_id': category_s.id,
                    'asset_name': 'Demo PC 01',
                    'asset_kind': Asset.AssetKind.PC,
                    'status': Asset.AssetStatus.IN_USE,
                    'budget_id': budget.id,
                    'budget_link_status': Asset.BudgetLinkStatus.LINKED,
                    'attributes': {
                        'person_attr_01': editor_user.id,
                        'person_attr_02': approver_user.id,
                    },
                },
                actor=editor_user,
            )

        if not InventoryCycle.objects.filter(cycle_code='2026-02').exists():
            InventoryCycle.objects.create(cycle_code='2026-02', cycle_year=2026, cycle_month=2, status=InventoryCycle.CycleStatus.OPEN)

        created_count = 0
        status_cycle = [
            Asset.AssetStatus.REQUESTED_FROM_IT,
            Asset.AssetStatus.RECEIVED_WAITING,
            Asset.AssetStatus.WAITING_ASSIGNMENT,
            Asset.AssetStatus.IN_USE,
            Asset.AssetStatus.RETURN_PENDING,
            Asset.AssetStatus.RETURNED,
            Asset.AssetStatus.MAINTENANCE,
            Asset.AssetStatus.REPAIRING,
            Asset.AssetStatus.RETIRED_WAITING,
        ]
        kind_cycle = [
            Asset.AssetKind.PC,
            Asset.AssetKind.DEVICE,
            Asset.AssetKind.LICENSE,
            Asset.AssetKind.OTHER,
        ]
        for index in range(1, bulk_size + 1):
            asset_code = f'AS-BULK-{index:04d}'
            if Asset.objects.filter(asset_code=asset_code).exists():
                continue

            asset_kind = kind_cycle[(index - 1) % len(kind_cycle)]
            status = status_cycle[(index - 1) % len(status_cycle)]
            payload = {
                'asset_code': asset_code,
                'asset_type_id': asset_type.id,
                'category_s_id': category_s.id,
                'asset_name': f'Bulk Demo Asset {index:04d}',
                'asset_kind': asset_kind,
                'status': status,
                'budget_id': budget.id if index % 3 != 0 else None,
                'budget_link_status': Asset.BudgetLinkStatus.LINKED if index % 3 != 0 else Asset.BudgetLinkStatus.UNLINKED,
                'attributes': {
                    'person_attr_01': editor_user.id if asset_kind == Asset.AssetKind.PC else None,
                    'person_attr_02': approver_user.id,
                    'free_text_attr_01': f'MODEL-{index:04d}',
                    'location_attr_01': f'FLOOR-{(index % 5) + 1}',
                },
            }
            create_asset(payload=payload, actor=editor_user)
            created_count += 1

        self.stdout.write(self.style.SUCCESS('Demo users and data are ready.'))
        self.stdout.write(f'bulk assets created: {created_count}')
        self.stdout.write('admin / admin1234')
        self.stdout.write('editor / pass1234')
        self.stdout.write('approver / pass1234')
