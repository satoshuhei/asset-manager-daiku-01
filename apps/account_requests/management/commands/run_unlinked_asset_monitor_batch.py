from django.core.management.base import BaseCommand

from apps.account_requests.services.batch_service import run_unlinked_asset_monitor_batch


class Command(BaseCommand):
    help = '未紐付け資産監視バッチを実行する'

    def add_arguments(self, parser):
        parser.add_argument('--threshold', type=int, default=10)

    def handle(self, *args, **options):
        count = run_unlinked_asset_monitor_batch(threshold=options['threshold'])
        self.stdout.write(self.style.SUCCESS(f'unlinked monitor rows updated: {count}'))
