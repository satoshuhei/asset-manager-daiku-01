from rest_framework import serializers

from apps.account_requests.models import (
    Asset,
    AssetAttributeMultiValue,
    AuditLog,
    Budget,
    BudgetAttributeMultiValue,
    Configuration,
    DisposalHistory,
    ExecutedBudget,
    InventoryResult,
    LoanHistory,
    LicenseAllocationHistory,
    LicensePool,
    UserPCAssignment,
)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128)


class AssetListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ['id', 'asset_code', 'asset_name', 'status', 'budget_link_status']


class AssetCreateSerializer(serializers.Serializer):
    asset_code = serializers.CharField(max_length=50)
    asset_type_id = serializers.IntegerField()
    category_s_id = serializers.IntegerField()
    asset_name = serializers.CharField(max_length=200)
    asset_kind = serializers.ChoiceField(choices=Asset.AssetKind.choices)
    status = serializers.CharField(max_length=40, required=False)
    vendor_id = serializers.IntegerField(required=False, allow_null=True)
    budget_id = serializers.IntegerField(required=False, allow_null=True)
    budget_link_status = serializers.ChoiceField(
        choices=Asset.BudgetLinkStatus.choices,
        required=False,
    )
    purchase_date = serializers.DateField(required=False, allow_null=True)
    warranty_expiry_date = serializers.DateField(required=False, allow_null=True)
    attributes = serializers.DictField()
    multi_attributes = serializers.ListField(required=False)


class AssetAttributeMultiValueItemSerializer(serializers.Serializer):
    multi_attr_type = serializers.ChoiceField(choices=AssetAttributeMultiValue.MultiAttrType.choices)
    value = serializers.CharField(max_length=500)
    sort_order = serializers.IntegerField(required=False)


class AssetUpdateSerializer(serializers.Serializer):
    category_s_id = serializers.IntegerField(required=False)
    asset_name = serializers.CharField(max_length=200, required=False)
    asset_kind = serializers.ChoiceField(choices=Asset.AssetKind.choices, required=False)
    status = serializers.CharField(max_length=40, required=False)
    vendor_id = serializers.IntegerField(required=False, allow_null=True)
    purchase_date = serializers.DateField(required=False, allow_null=True)
    warranty_expiry_date = serializers.DateField(required=False, allow_null=True)
    attributes = serializers.DictField(required=False)
    multi_attributes = AssetAttributeMultiValueItemSerializer(many=True, required=False)


class BudgetLinkSerializer(serializers.Serializer):
    budget_id = serializers.IntegerField(required=False, allow_null=True)


class DisposalCreateSerializer(serializers.Serializer):
    asset_id = serializers.IntegerField()


class DisposalDecisionSerializer(serializers.Serializer):
    evidence_text = serializers.CharField(required=False, allow_blank=True)
    reason = serializers.CharField(required=False, allow_blank=True)


class DisposalSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisposalHistory
        fields = [
            'id',
            'asset_id',
            'requested_by_id',
            'approved_by_id',
            'requested_at',
            'approved_at',
            'evidence_text',
            'reject_reason',
            'disposal_status',
        ]


class InventoryResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryResult
        fields = [
            'id',
            'cycle_id',
            'asset_id',
            'difference_type',
            'correction_status',
            'correction_note',
            'registered_by_id',
            'updated_by_id',
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['id', 'target_table', 'target_id', 'action', 'changed_by_id', 'changed_at', 'change_summary']


class ConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Configuration
        fields = ['id', 'config_code', 'config_name', 'status']


class ConfigurationCreateSerializer(serializers.Serializer):
    config_code = serializers.CharField(max_length=50)
    config_name = serializers.CharField(max_length=200)
    status = serializers.CharField(max_length=20, required=False)
    items = serializers.ListField(required=False)


class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['id', 'fiscal_year', 'budget_category', 'budget_category_s_id', 'project_id', 'planned_amount']


class BudgetAttributeMultiValueItemSerializer(serializers.Serializer):
    multi_attr_type = serializers.ChoiceField(choices=BudgetAttributeMultiValue.MultiAttrType.choices)
    value = serializers.CharField(max_length=500)
    sort_order = serializers.IntegerField(required=False)


class BudgetCreateSerializer(serializers.Serializer):
    fiscal_year = serializers.IntegerField()
    budget_category = serializers.CharField(max_length=100)
    budget_category_s_id = serializers.IntegerField(required=False, allow_null=True)
    project_id = serializers.IntegerField()
    planned_amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    attributes = serializers.DictField(required=False)
    multi_attributes = BudgetAttributeMultiValueItemSerializer(many=True, required=False)


class BudgetUpdateSerializer(serializers.Serializer):
    fiscal_year = serializers.IntegerField(required=False)
    budget_category = serializers.CharField(max_length=100, required=False)
    budget_category_s_id = serializers.IntegerField(required=False, allow_null=True)
    planned_amount = serializers.DecimalField(max_digits=18, decimal_places=2, required=False)
    attributes = serializers.DictField(required=False)
    multi_attributes = BudgetAttributeMultiValueItemSerializer(many=True, required=False)


class ExecutedBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutedBudget
        fields = ['id', 'budget_id', 'executed_date', 'executed_amount', 'description']


class ExecutedBudgetCreateSerializer(serializers.Serializer):
    executed_date = serializers.DateField()
    executed_amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)


class LicensePoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = LicensePool
        fields = ['id', 'license_name', 'total_count', 'used_count', 'remaining_count', 'contract_expiry_date']


class LicensePoolCreateSerializer(serializers.Serializer):
    license_name = serializers.CharField(max_length=200)
    total_count = serializers.IntegerField()
    used_count = serializers.IntegerField(required=False)
    contract_expiry_date = serializers.DateField(required=False, allow_null=True)


class LicenseAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LicenseAllocationHistory
        fields = ['id', 'pool_id', 'asset_id', 'allocated_count', 'allocated_at', 'released_at']


class LicenseAllocationCreateSerializer(serializers.Serializer):
    asset_id = serializers.IntegerField()
    allocated_count = serializers.IntegerField(required=False)


class UserPCAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPCAssignment
        fields = ['id', 'asset_id', 'user_id', 'os_name', 'spec_text', 'warranty_expiry_date']


class UserPCAssignmentCreateSerializer(serializers.Serializer):
    asset_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    os_name = serializers.CharField(max_length=100)
    spec_text = serializers.CharField(max_length=500, required=False, allow_blank=True)
    warranty_expiry_date = serializers.DateField(required=False, allow_null=True)


class LoanHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanHistory
        fields = ['id', 'asset_id', 'borrower_id', 'loaned_at', 'returned_at']


class LoanHistoryCreateSerializer(serializers.Serializer):
    asset_id = serializers.IntegerField()
    borrower_id = serializers.IntegerField()