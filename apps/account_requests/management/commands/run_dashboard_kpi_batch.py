from django.core.management.base import BaseCommand

from apps.account_requests.services.batch_service import run_dashboard_kpi_batch


class Command(BaseCommand):
    help = 'ダッシュボードKPI集計バッチを実行する'

    def handle(self, *args, **options):
        run_dashboard_kpi_batch()
        self.stdout.write(self.style.SUCCESS('dashboard kpi updated'))
