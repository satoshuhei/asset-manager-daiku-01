from django.core.management.base import BaseCommand

from apps.account_requests.services.batch_service import run_maintenance_notification_batch


class Command(BaseCommand):
    help = '保守期限通知バッチを実行する'

    def handle(self, *args, **options):
        count = run_maintenance_notification_batch()
        self.stdout.write(self.style.SUCCESS(f'maintenance notifications queued: {count}'))
