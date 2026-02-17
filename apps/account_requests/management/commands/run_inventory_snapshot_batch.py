from django.core.management.base import BaseCommand

from apps.account_requests.services.batch_service import run_inventory_target_snapshot_batch


class Command(BaseCommand):
    help = '棚卸対象スナップショット生成バッチを実行する'

    def add_arguments(self, parser):
        parser.add_argument('cycle_id', type=int)

    def handle(self, *args, **options):
        count = run_inventory_target_snapshot_batch(cycle_id=options['cycle_id'])
        self.stdout.write(self.style.SUCCESS(f'inventory snapshots generated: {count}'))
