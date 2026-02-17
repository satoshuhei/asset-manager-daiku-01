from django.contrib import admin

from .models import (
	AssetBudgetMonitorDaily,
	Asset,
		DashboardKPIDaily,
		InventoryTargetSnapshot,
		LicenseAllocationHistory,
		LicensePool,
		NotificationQueue,
		UserPCAssignment,
	AssetAttributeMultiValue,
	AssetAttributeValue,
	AssetCategoryL,
	AssetCategoryM,
	AssetCategoryS,
	AssetStatusMaster,
	AssetStatusTransitionMaster,
	AssetType,
	AuditLog,
	AuthLockout,
	Budget,
	Configuration,
	ConfigurationItem,
	DisposalHistory,
	ExecutedBudget,
	InventoryCycle,
	InventoryResult,
	Project,
	Vendor,
)


admin.site.register(AssetType)
admin.site.register(AssetCategoryL)
admin.site.register(AssetCategoryM)
admin.site.register(AssetCategoryS)
admin.site.register(AssetStatusMaster)
admin.site.register(AssetStatusTransitionMaster)
admin.site.register(Project)
admin.site.register(Budget)
admin.site.register(ExecutedBudget)
admin.site.register(Vendor)
admin.site.register(Asset)
admin.site.register(AssetAttributeValue)
admin.site.register(AssetAttributeMultiValue)
admin.site.register(AssetBudgetMonitorDaily)
admin.site.register(Configuration)
admin.site.register(ConfigurationItem)
admin.site.register(LicensePool)
admin.site.register(LicenseAllocationHistory)
admin.site.register(UserPCAssignment)
admin.site.register(DisposalHistory)
admin.site.register(InventoryCycle)
admin.site.register(InventoryResult)
admin.site.register(InventoryTargetSnapshot)
admin.site.register(AuditLog)
admin.site.register(AuthLockout)
admin.site.register(NotificationQueue)
admin.site.register(DashboardKPIDaily)

# Register your models here.
