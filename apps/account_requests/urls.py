from django.urls import path

from apps.account_requests import views


urlpatterns = [
    path('auth/login', views.LoginAPIView.as_view()),
    path('auth/logout', views.LogoutAPIView.as_view()),
    path('assets', views.AssetListCreateAPIView.as_view()),
    path('assets/export-csv', views.AssetCsvExportAPIView.as_view()),
    path('assets/import-csv', views.AssetCsvImportAPIView.as_view()),
    path('assets/<int:asset_id>', views.AssetDetailAPIView.as_view()),
    path('assets/<int:asset_id>/budget-link', views.BudgetLinkAPIView.as_view()),
    path('configurations', views.ConfigurationListCreateAPIView.as_view()),
    path('budgets', views.BudgetListCreateAPIView.as_view()),
    path('budgets/<int:budget_id>', views.BudgetDetailAPIView.as_view()),
    path('budgets/<int:budget_id>/executions', views.ExecutedBudgetListCreateAPIView.as_view()),
    path('license-pools', views.LicensePoolListCreateAPIView.as_view()),
    path('license-pools/<int:pool_id>/allocations', views.LicenseAllocationListCreateAPIView.as_view()),
    path('pc-assignments', views.PCAssignmentListCreateAPIView.as_view()),
    path('loan-histories', views.LoanHistoryListCreateAPIView.as_view()),
    path('loan-histories/<int:history_id>/return', views.LoanHistoryReturnAPIView.as_view()),
    path('disposals', views.DisposalListCreateAPIView.as_view()),
    path('disposals/<int:disposal_id>/approve', views.DisposalApproveAPIView.as_view()),
    path('disposals/<int:disposal_id>/reject', views.DisposalRejectAPIView.as_view()),
    path('inventories/<int:inventory_id>/results', views.InventoryResultCreateAPIView.as_view()),
    path('inventories/<int:inventory_id>/results/<int:result_id>', views.InventoryResultUpdateAPIView.as_view()),
    path('audit-logs', views.AuditLogListAPIView.as_view()),
    path('audit-logs/<int:log_id>', views.AuditLogDetailAPIView.as_view()),
]