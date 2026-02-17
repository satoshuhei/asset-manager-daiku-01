from django.urls import path

from apps.account_requests import web_views


urlpatterns = [
    path('', web_views.home_redirect),
    path('login', web_views.AppLoginView.as_view()),
    path('logout', web_views.AppLogoutView.as_view()),
    path('dashboard', web_views.DashboardView.as_view()),
    path('assets', web_views.AssetListView.as_view()),
    path('assets/<int:pk>', web_views.AssetDetailView.as_view()),
    path('configurations', web_views.ConfigurationView.as_view()),
    path('budgets', web_views.BudgetView.as_view()),
    path('license-pools', web_views.LicensePoolView.as_view()),
    path('pc-management', web_views.PCManagementView.as_view()),
    path('inventories', web_views.InventoryView.as_view()),
    path('disposals/approvals', web_views.DisposalApprovalView.as_view()),
    path('audit-logs', web_views.AuditLogView.as_view()),
]