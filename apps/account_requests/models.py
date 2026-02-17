from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class TimeStampedModel(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True


class AssetType(TimeStampedModel):
	code = models.CharField(max_length=20, unique=True)
	name = models.CharField(max_length=100)
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return f'{self.code}:{self.name}'


class AssetCategoryL(TimeStampedModel):
	code = models.CharField(max_length=20, unique=True)
	name = models.CharField(max_length=100)
	is_active = models.BooleanField(default=True)


class AssetCategoryM(TimeStampedModel):
	category_l = models.ForeignKey(AssetCategoryL, on_delete=models.PROTECT)
	code = models.CharField(max_length=20)
	name = models.CharField(max_length=100)
	is_active = models.BooleanField(default=True)

	class Meta:
		unique_together = ('category_l', 'code')


class AssetCategoryS(TimeStampedModel):
	category_m = models.ForeignKey(AssetCategoryM, on_delete=models.PROTECT)
	code = models.CharField(max_length=20)
	name = models.CharField(max_length=100)
	is_active = models.BooleanField(default=True)

	class Meta:
		unique_together = ('category_m', 'code')


class AssetStatusMaster(TimeStampedModel):
	category_l = models.ForeignKey(AssetCategoryL, on_delete=models.PROTECT)
	status_code = models.CharField(max_length=40)
	status_name = models.CharField(max_length=100)
	sort_order = models.IntegerField(default=1)
	is_active = models.BooleanField(default=True)

	class Meta:
		unique_together = ('category_l', 'status_code')


class AssetStatusTransitionMaster(TimeStampedModel):
	category_l = models.ForeignKey(AssetCategoryL, on_delete=models.PROTECT)
	from_status = models.ForeignKey(AssetStatusMaster, related_name='transition_from', on_delete=models.PROTECT)
	to_status = models.ForeignKey(AssetStatusMaster, related_name='transition_to', on_delete=models.PROTECT)
	is_active = models.BooleanField(default=True)

	class Meta:
		unique_together = ('category_l', 'from_status', 'to_status')


class BudgetCategoryL(TimeStampedModel):
	code = models.CharField(max_length=20, unique=True)
	name = models.CharField(max_length=100)
	is_active = models.BooleanField(default=True)


class BudgetCategoryM(TimeStampedModel):
	category_l = models.ForeignKey(BudgetCategoryL, on_delete=models.PROTECT)
	code = models.CharField(max_length=20)
	name = models.CharField(max_length=100)
	is_active = models.BooleanField(default=True)

	class Meta:
		unique_together = ('category_l', 'code')


class BudgetCategoryS(TimeStampedModel):
	category_m = models.ForeignKey(BudgetCategoryM, on_delete=models.PROTECT)
	code = models.CharField(max_length=20)
	name = models.CharField(max_length=100)
	is_active = models.BooleanField(default=True)

	class Meta:
		unique_together = ('category_m', 'code')


class Project(TimeStampedModel):
	project_code = models.CharField(max_length=30, unique=True)
	project_name = models.CharField(max_length=200)
	is_active = models.BooleanField(default=True)


class Budget(TimeStampedModel):
	fiscal_year = models.IntegerField()
	budget_category = models.CharField(max_length=100)
	budget_category_s = models.ForeignKey(BudgetCategoryS, null=True, blank=True, on_delete=models.PROTECT)
	project = models.ForeignKey(Project, on_delete=models.PROTECT)
	planned_amount = models.DecimalField(max_digits=18, decimal_places=2)


class ExecutedBudget(models.Model):
	budget = models.ForeignKey(Budget, on_delete=models.CASCADE)
	executed_date = models.DateField()
	executed_amount = models.DecimalField(max_digits=18, decimal_places=2)
	description = models.CharField(max_length=500, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)


class BudgetAttributeValue(TimeStampedModel):
	budget = models.OneToOneField(Budget, on_delete=models.CASCADE)
	attr_01 = models.CharField(max_length=200, blank=True)
	attr_02 = models.CharField(max_length=200, blank=True)
	attr_03 = models.CharField(max_length=200, blank=True)
	attr_04 = models.CharField(max_length=200, blank=True)
	attr_05 = models.CharField(max_length=200, blank=True)
	attr_06 = models.CharField(max_length=200, blank=True)
	attr_07 = models.CharField(max_length=200, blank=True)
	attr_08 = models.CharField(max_length=200, blank=True)
	attr_09 = models.CharField(max_length=200, blank=True)
	attr_10 = models.CharField(max_length=200, blank=True)
	attr_11 = models.CharField(max_length=200, blank=True)
	attr_12 = models.CharField(max_length=200, blank=True)
	attr_13 = models.CharField(max_length=200, blank=True)
	attr_14 = models.CharField(max_length=200, blank=True)
	attr_15 = models.CharField(max_length=200, blank=True)
	attr_16 = models.CharField(max_length=500, blank=True)
	attr_17 = models.CharField(max_length=500, blank=True)
	attr_18 = models.CharField(max_length=500, blank=True)
	attr_19 = models.TextField(blank=True)
	attr_20 = models.TextField(blank=True)


class BudgetAttributeMultiValue(models.Model):
	class MultiAttrType(models.TextChoices):
		MULTI_01 = 'MULTI_01', 'MULTI_01'
		MULTI_02 = 'MULTI_02', 'MULTI_02'

	budget = models.ForeignKey(Budget, on_delete=models.CASCADE)
	multi_attr_type = models.CharField(max_length=20, choices=MultiAttrType.choices)
	value = models.CharField(max_length=500)
	sort_order = models.IntegerField(default=1)
	created_at = models.DateTimeField(auto_now_add=True)


class Vendor(TimeStampedModel):
	vendor_code = models.CharField(max_length=30, unique=True)
	vendor_name = models.CharField(max_length=200)
	is_active = models.BooleanField(default=True)


class Asset(TimeStampedModel):
	class AssetKind(models.TextChoices):
		PC = 'PC', 'PC'
		DEVICE = 'DEVICE', 'DEVICE'
		LICENSE = 'LICENSE', 'LICENSE'
		OTHER = 'OTHER', 'OTHER'

	class AssetStatus(models.TextChoices):
		REQUESTED_FROM_IT = 'REQUESTED_FROM_IT', 'REQUESTED_FROM_IT'
		RECEIVED_WAITING = 'RECEIVED_WAITING', 'RECEIVED_WAITING'
		WAITING_ASSIGNMENT = 'WAITING_ASSIGNMENT', 'WAITING_ASSIGNMENT'
		IN_USE = 'IN_USE', 'IN_USE'
		RETURN_PENDING = 'RETURN_PENDING', 'RETURN_PENDING'
		RETURNED = 'RETURNED', 'RETURNED'
		MAINTENANCE = 'MAINTENANCE', 'MAINTENANCE'
		REPAIRING = 'REPAIRING', 'REPAIRING'
		RETIRED_WAITING = 'RETIRED_WAITING', 'RETIRED_WAITING'
		DISPOSED = 'DISPOSED', 'DISPOSED'

	class BudgetLinkStatus(models.TextChoices):
		UNLINKED = 'UNLINKED', 'UNLINKED'
		LINKED = 'LINKED', 'LINKED'

	asset_code = models.CharField(max_length=50, unique=True)
	asset_type = models.ForeignKey(AssetType, on_delete=models.PROTECT)
	category_s = models.ForeignKey(AssetCategoryS, on_delete=models.PROTECT)
	asset_name = models.CharField(max_length=200)
	asset_kind = models.CharField(max_length=20, choices=AssetKind.choices)
	status = models.CharField(max_length=40, default=AssetStatus.IN_USE)
	vendor = models.ForeignKey(Vendor, null=True, blank=True, on_delete=models.PROTECT)
	budget = models.ForeignKey(Budget, null=True, blank=True, on_delete=models.PROTECT)
	budget_link_status = models.CharField(
		max_length=20,
		choices=BudgetLinkStatus.choices,
		default=BudgetLinkStatus.UNLINKED,
	)
	purchase_date = models.DateField(null=True, blank=True)
	warranty_expiry_date = models.DateField(null=True, blank=True)


class AssetAttributeValue(TimeStampedModel):
	asset = models.OneToOneField(Asset, on_delete=models.CASCADE)
	cls_attr_01 = models.CharField(max_length=50, blank=True)
	cls_attr_02 = models.CharField(max_length=50, blank=True)
	cls_attr_03 = models.CharField(max_length=50, blank=True)
	cls_attr_04 = models.CharField(max_length=50, blank=True)
	cls_attr_05 = models.CharField(max_length=50, blank=True)
	person_attr_01 = models.ForeignKey(User, null=True, blank=True, related_name='+', on_delete=models.PROTECT)
	person_attr_02 = models.ForeignKey(User, related_name='+', on_delete=models.PROTECT)
	person_attr_03 = models.ForeignKey(User, related_name='+', on_delete=models.PROTECT)
	location_attr_01 = models.CharField(max_length=100, blank=True)
	location_attr_02 = models.CharField(max_length=100, blank=True)
	date_attr_01 = models.DateField(null=True, blank=True)
	date_attr_02 = models.DateField(null=True, blank=True)
	date_attr_03 = models.DateField(null=True, blank=True)
	free_text_attr_01 = models.CharField(max_length=200, blank=True)
	free_text_attr_02 = models.CharField(max_length=200, blank=True)
	free_text_attr_03 = models.CharField(max_length=500, blank=True)
	memo_attr_01 = models.TextField(blank=True)
	memo_attr_02 = models.TextField(blank=True)


class AssetAttributeMultiValue(models.Model):
	class MultiAttrType(models.TextChoices):
		MULTI_01 = 'MULTI_01', 'MULTI_01'
		MULTI_02 = 'MULTI_02', 'MULTI_02'

	asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
	multi_attr_type = models.CharField(max_length=20, choices=MultiAttrType.choices)
	value = models.CharField(max_length=500)
	sort_order = models.IntegerField(default=1)
	created_at = models.DateTimeField(auto_now_add=True)


class Configuration(TimeStampedModel):
	config_code = models.CharField(max_length=50, unique=True)
	config_name = models.CharField(max_length=200)
	status = models.CharField(max_length=20)


class ConfigurationItem(models.Model):
	configuration = models.ForeignKey(Configuration, on_delete=models.CASCADE)
	asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
	role_type = models.CharField(max_length=20)
	quantity = models.IntegerField()
	created_at = models.DateTimeField(auto_now_add=True)


class LicensePool(TimeStampedModel):
	license_name = models.CharField(max_length=200)
	total_count = models.IntegerField(default=0)
	used_count = models.IntegerField(default=0)
	remaining_count = models.IntegerField(default=0)
	contract_expiry_date = models.DateField(null=True, blank=True)

	def save(self, *args, **kwargs):
		self.remaining_count = max(0, self.total_count - self.used_count)
		super().save(*args, **kwargs)


class LicenseAllocationHistory(models.Model):
	pool = models.ForeignKey(LicensePool, on_delete=models.CASCADE)
	asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
	allocated_count = models.IntegerField(default=1)
	allocated_at = models.DateTimeField(auto_now_add=True)
	released_at = models.DateTimeField(null=True, blank=True)


class UserPCAssignment(TimeStampedModel):
	asset = models.OneToOneField(Asset, on_delete=models.PROTECT)
	user = models.ForeignKey(User, on_delete=models.PROTECT)
	os_name = models.CharField(max_length=100)
	spec_text = models.CharField(max_length=500, blank=True)
	warranty_expiry_date = models.DateField(null=True, blank=True)


class LoanHistory(TimeStampedModel):
	asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
	borrower = models.ForeignKey(User, on_delete=models.PROTECT)
	loaned_at = models.DateTimeField(auto_now_add=True)
	returned_at = models.DateTimeField(null=True, blank=True)


class DisposalHistory(models.Model):
	class DisposalStatus(models.TextChoices):
		REQUESTED = 'REQUESTED', 'REQUESTED'
		APPROVED = 'APPROVED', 'APPROVED'
		REJECTED = 'REJECTED', 'REJECTED'

	asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
	requested_by = models.ForeignKey(User, related_name='disposal_requests', on_delete=models.PROTECT)
	approved_by = models.ForeignKey(User, null=True, blank=True, related_name='disposal_approvals', on_delete=models.PROTECT)
	requested_at = models.DateTimeField(auto_now_add=True)
	approved_at = models.DateTimeField(null=True, blank=True)
	evidence_text = models.TextField(blank=True)
	reject_reason = models.TextField(blank=True)
	disposal_status = models.CharField(max_length=20, choices=DisposalStatus.choices, default=DisposalStatus.REQUESTED)


class InventoryCycle(TimeStampedModel):
	class CycleStatus(models.TextChoices):
		PLANNED = 'PLANNED', 'PLANNED'
		OPEN = 'OPEN', 'OPEN'
		CLOSED = 'CLOSED', 'CLOSED'

	cycle_code = models.CharField(max_length=20, unique=True)
	cycle_year = models.IntegerField()
	cycle_month = models.IntegerField()
	status = models.CharField(max_length=20, choices=CycleStatus.choices, default=CycleStatus.PLANNED)
	started_at = models.DateTimeField(null=True, blank=True)
	ended_at = models.DateTimeField(null=True, blank=True)


class InventoryResult(TimeStampedModel):
	class DifferenceType(models.TextChoices):
		MISSING = 'MISSING', 'MISSING'
		EXCESS = 'EXCESS', 'EXCESS'
		STATUS_DIFF = 'STATUS_DIFF', 'STATUS_DIFF'

	class CorrectionStatus(models.TextChoices):
		OPEN = 'OPEN', 'OPEN'
		IN_PROGRESS = 'IN_PROGRESS', 'IN_PROGRESS'
		DONE = 'DONE', 'DONE'

	cycle = models.ForeignKey(InventoryCycle, on_delete=models.CASCADE)
	asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
	difference_type = models.CharField(max_length=20, choices=DifferenceType.choices)
	correction_status = models.CharField(max_length=20, choices=CorrectionStatus.choices, default=CorrectionStatus.OPEN)
	correction_note = models.TextField(blank=True)
	registered_by = models.ForeignKey(User, related_name='inventory_registered', on_delete=models.PROTECT)
	updated_by = models.ForeignKey(User, null=True, blank=True, related_name='inventory_updated', on_delete=models.PROTECT)

	class Meta:
		unique_together = ('cycle', 'asset')


class AuditLog(models.Model):
	target_table = models.CharField(max_length=100)
	target_id = models.BigIntegerField()
	action = models.CharField(max_length=30)
	changed_by = models.ForeignKey(User, on_delete=models.PROTECT)
	changed_at = models.DateTimeField(auto_now_add=True)
	change_summary = models.TextField(blank=True)


class AuthLockout(models.Model):
	username = models.CharField(max_length=150, unique=True)
	failed_count = models.IntegerField(default=0)
	locked_until = models.DateTimeField(null=True, blank=True)
	updated_at = models.DateTimeField(auto_now=True)


class NotificationQueue(TimeStampedModel):
	class QueueStatus(models.TextChoices):
		PENDING = 'PENDING', 'PENDING'
		SENT = 'SENT', 'SENT'
		FAILED = 'FAILED', 'FAILED'

	notification_type = models.CharField(max_length=50)
	target_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT)
	title = models.CharField(max_length=200)
	body = models.TextField()
	status = models.CharField(max_length=20, choices=QueueStatus.choices, default=QueueStatus.PENDING)
	scheduled_at = models.DateTimeField(null=True, blank=True)
	sent_at = models.DateTimeField(null=True, blank=True)


class AssetBudgetMonitorDaily(TimeStampedModel):
	monitor_date = models.DateField()
	dept_code = models.CharField(max_length=30, blank=True)
	category_s = models.ForeignKey(AssetCategoryS, null=True, blank=True, on_delete=models.PROTECT)
	unlinked_count = models.IntegerField(default=0)
	threshold_count = models.IntegerField(default=0)
	is_threshold_exceeded = models.BooleanField(default=False)

	class Meta:
		unique_together = ('monitor_date', 'dept_code', 'category_s')


class DashboardKPIDaily(TimeStampedModel):
	kpi_date = models.DateField(unique=True)
	budget_consumption_rate = models.DecimalField(max_digits=7, decimal_places=2, default=0)
	unlinked_asset_count = models.IntegerField(default=0)
	maintenance_overdue_count = models.IntegerField(default=0)
	inventory_diff_count = models.IntegerField(default=0)
	configuration_completeness_rate = models.DecimalField(max_digits=7, decimal_places=2, default=0)


class InventoryTargetSnapshot(TimeStampedModel):
	cycle = models.ForeignKey(InventoryCycle, on_delete=models.CASCADE)
	asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
	status_at_snapshot = models.CharField(max_length=20)
	budget_link_status_at_snapshot = models.CharField(max_length=20)

	class Meta:
		unique_together = ('cycle', 'asset')

# Create your models here.
