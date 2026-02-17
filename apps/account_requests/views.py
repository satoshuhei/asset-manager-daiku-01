from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone
from rest_framework.parsers import MultiPartParser
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.account_requests.models import (
	Asset,
	AuditLog,
	AuthLockout,
	Budget,
	Configuration,
	DisposalHistory,
	ExecutedBudget,
	InventoryResult,
	LoanHistory,
	LicenseAllocationHistory,
	LicensePool,
	UserPCAssignment,
)
from apps.account_requests.serializers import (
	AssetCreateSerializer,
	AssetListSerializer,
	AssetUpdateSerializer,
	AuditLogSerializer,
	BudgetCreateSerializer,
	BudgetUpdateSerializer,
	BudgetLinkSerializer,
	BudgetSerializer,
	ConfigurationCreateSerializer,
	ConfigurationSerializer,
	DisposalCreateSerializer,
	DisposalDecisionSerializer,
	DisposalSerializer,
	ExecutedBudgetCreateSerializer,
	ExecutedBudgetSerializer,
	InventoryResultSerializer,
	LoanHistoryCreateSerializer,
	LoanHistorySerializer,
	LicenseAllocationCreateSerializer,
	LicenseAllocationSerializer,
	LicensePoolCreateSerializer,
	LicensePoolSerializer,
	LoginSerializer,
	UserPCAssignmentCreateSerializer,
	UserPCAssignmentSerializer,
)
from apps.account_requests.services.asset_service import create_asset, update_asset, update_budget_link
from apps.account_requests.services.csv_service import export_assets_csv, import_assets_csv
from apps.account_requests.services.budget_service import create_budget, create_executed_budget, update_budget
from apps.account_requests.services.configuration_service import create_configuration
from apps.account_requests.services.disposal_service import approve_disposal, reject_disposal, request_disposal
from apps.account_requests.services.inventory_service import create_inventory_result, update_inventory_result
from apps.account_requests.services.license_service import allocate_license, create_license_pool
from apps.account_requests.services.loan_service import create_loan_history, return_loan_history
from apps.account_requests.services.pc_service import assign_pc_user


class IsApproverOrAdmin(permissions.BasePermission):
	def has_permission(self, request, view):
		return bool(request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser))


class LoginAPIView(APIView):
	permission_classes = [permissions.AllowAny]

	def post(self, request):
		serializer = LoginSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		username = serializer.validated_data['username']
		password = serializer.validated_data['password']

		lockout, _ = AuthLockout.objects.get_or_create(username=username)
		if lockout.locked_until and lockout.locked_until > timezone.now():
			return Response({'code': 'LOCKED', 'message': 'Account temporarily locked.'}, status=423)

		user = authenticate(request, username=username, password=password)
		if not user or not user.is_active:
			lockout.failed_count += 1
			if lockout.failed_count >= 5:
				lockout.failed_count = 0
				lockout.locked_until = timezone.now() + timedelta(minutes=15)
			lockout.save(update_fields=['failed_count', 'locked_until', 'updated_at'])
			return Response({'code': 'AUTH_FAILED', 'message': 'Invalid credentials.'}, status=401)

		lockout.failed_count = 0
		lockout.locked_until = None
		lockout.save(update_fields=['failed_count', 'locked_until', 'updated_at'])

		login(request, user)
		request.session['login_at'] = timezone.now().isoformat()
		request.session.set_expiry(getattr(settings, 'SESSION_COOKIE_AGE', 1800))
		return Response({'result': 'ok'})


class LogoutAPIView(APIView):
	def post(self, request):
		logout(request)
		return Response({'result': 'ok'})


class AssetListCreateAPIView(APIView):
	def get(self, request):
		queryset = Asset.objects.all().order_by('-updated_at')
		asset_code = request.query_params.get('asset_code')
		asset_name = request.query_params.get('asset_name')
		status_value = request.query_params.get('status')
		budget_link_status = request.query_params.get('budget_link_status')
		if asset_code:
			queryset = queryset.filter(asset_code__istartswith=asset_code)
		if asset_name:
			queryset = queryset.filter(asset_name__icontains=asset_name)
		if status_value:
			queryset = queryset.filter(status=status_value)
		if budget_link_status:
			queryset = queryset.filter(budget_link_status=budget_link_status)
		return Response(AssetListSerializer(queryset, many=True).data)

	def post(self, request):
		serializer = AssetCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		try:
			asset = create_asset(payload=serializer.validated_data, actor=request.user)
		except ValidationError as exc:
			return Response({'detail': exc.message}, status=422)
		return Response(AssetListSerializer(asset).data, status=status.HTTP_201_CREATED)


class AssetCsvExportAPIView(APIView):
	def get(self, request):
		csv_content = export_assets_csv()
		response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
		response['Content-Disposition'] = 'attachment; filename="assets.csv"'
		return response


class AssetCsvImportAPIView(APIView):
	parser_classes = [MultiPartParser]

	def post(self, request):
		if 'file' not in request.FILES:
			return Response({'detail': 'file is required'}, status=400)
		file_obj = request.FILES['file']
		content = file_obj.read().decode('utf-8-sig')
		result = import_assets_csv(content=content, actor=request.user)
		status_code = 201 if not result['errors'] else 207
		return Response(result, status=status_code)


class AssetDetailAPIView(APIView):
	def get(self, request, asset_id: int):
		asset = Asset.objects.get(id=asset_id)
		return Response(AssetListSerializer(asset).data)

	def put(self, request, asset_id: int):
		asset = Asset.objects.get(id=asset_id)
		serializer = AssetUpdateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		try:
			updated = update_asset(asset=asset, payload=serializer.validated_data, actor=request.user)
		except ValidationError as exc:
			return Response({'detail': exc.message}, status=422)
		return Response(AssetListSerializer(updated).data)


class BudgetLinkAPIView(APIView):
	def patch(self, request, asset_id: int):
		serializer = BudgetLinkSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		asset = Asset.objects.get(id=asset_id)
		try:
			updated = update_budget_link(asset=asset, budget_id=serializer.validated_data.get('budget_id'), actor=request.user)
		except ValidationError as exc:
			return Response({'detail': exc.message}, status=422)
		return Response(AssetListSerializer(updated).data)


class ConfigurationListCreateAPIView(APIView):
	def get(self, request):
		queryset = Configuration.objects.all().order_by('-updated_at')
		return Response(ConfigurationSerializer(queryset, many=True).data)

	def post(self, request):
		serializer = ConfigurationCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		try:
			configuration = create_configuration(payload=serializer.validated_data, actor=request.user)
		except ValidationError as exc:
			return Response({'detail': exc.message}, status=422)
		return Response(ConfigurationSerializer(configuration).data, status=status.HTTP_201_CREATED)


class BudgetListCreateAPIView(APIView):
	def get(self, request):
		queryset = Budget.objects.all().order_by('-updated_at')
		return Response(BudgetSerializer(queryset, many=True).data)

	def post(self, request):
		serializer = BudgetCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		try:
			budget = create_budget(payload=serializer.validated_data, actor=request.user)
		except ValueError as exc:
			return Response({'detail': str(exc)}, status=422)
		return Response(BudgetSerializer(budget).data, status=status.HTTP_201_CREATED)


class BudgetDetailAPIView(APIView):
	def put(self, request, budget_id: int):
		serializer = BudgetUpdateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		budget = Budget.objects.get(id=budget_id)
		try:
			updated = update_budget(budget=budget, payload=serializer.validated_data, actor=request.user)
		except ValueError as exc:
			return Response({'detail': str(exc)}, status=422)
		return Response(BudgetSerializer(updated).data)


class ExecutedBudgetListCreateAPIView(APIView):
	def get(self, request, budget_id: int):
		queryset = ExecutedBudget.objects.filter(budget_id=budget_id).order_by('-executed_date', '-id')
		return Response(ExecutedBudgetSerializer(queryset, many=True).data)

	def post(self, request, budget_id: int):
		serializer = ExecutedBudgetCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		execution = create_executed_budget(budget_id=budget_id, payload=serializer.validated_data, actor=request.user)
		return Response(ExecutedBudgetSerializer(execution).data, status=status.HTTP_201_CREATED)


class LicensePoolListCreateAPIView(APIView):
	def get(self, request):
		queryset = LicensePool.objects.all().order_by('-updated_at')
		return Response(LicensePoolSerializer(queryset, many=True).data)

	def post(self, request):
		serializer = LicensePoolCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		pool = create_license_pool(payload=serializer.validated_data, actor=request.user)
		return Response(LicensePoolSerializer(pool).data, status=status.HTTP_201_CREATED)


class LicenseAllocationListCreateAPIView(APIView):
	def get(self, request, pool_id: int):
		queryset = LicenseAllocationHistory.objects.filter(pool_id=pool_id).order_by('-allocated_at', '-id')
		return Response(LicenseAllocationSerializer(queryset, many=True).data)

	def post(self, request, pool_id: int):
		serializer = LicenseAllocationCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		pool = LicensePool.objects.get(id=pool_id)
		try:
			history = allocate_license(pool=pool, payload=serializer.validated_data, actor=request.user)
		except ValidationError as exc:
			return Response({'detail': exc.message}, status=422)
		return Response(LicenseAllocationSerializer(history).data, status=status.HTTP_201_CREATED)


class PCAssignmentListCreateAPIView(APIView):
	def get(self, request):
		queryset = UserPCAssignment.objects.all().order_by('-updated_at')
		return Response(UserPCAssignmentSerializer(queryset, many=True).data)

	def post(self, request):
		serializer = UserPCAssignmentCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		try:
			assignment = assign_pc_user(payload=serializer.validated_data, actor=request.user)
		except ValidationError as exc:
			return Response({'detail': exc.message}, status=422)
		return Response(UserPCAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)


class LoanHistoryListCreateAPIView(APIView):
	def get(self, request):
		queryset = LoanHistory.objects.all().order_by('-loaned_at', '-id')
		asset_id = request.query_params.get('asset_id')
		borrower_id = request.query_params.get('borrower_id')
		if asset_id:
			queryset = queryset.filter(asset_id=asset_id)
		if borrower_id:
			queryset = queryset.filter(borrower_id=borrower_id)
		return Response(LoanHistorySerializer(queryset, many=True).data)

	def post(self, request):
		serializer = LoanHistoryCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		try:
			history = create_loan_history(payload=serializer.validated_data, actor=request.user)
		except ValidationError as exc:
			return Response({'detail': exc.message}, status=422)
		return Response(LoanHistorySerializer(history).data, status=status.HTTP_201_CREATED)


class LoanHistoryReturnAPIView(APIView):
	def patch(self, request, history_id: int):
		history = LoanHistory.objects.get(id=history_id)
		try:
			history = return_loan_history(history=history, actor=request.user)
		except ValidationError as exc:
			return Response({'detail': exc.message}, status=422)
		return Response(LoanHistorySerializer(history).data)


class DisposalListCreateAPIView(APIView):
	def get(self, request):
		queryset = DisposalHistory.objects.all().order_by('-requested_at')
		return Response(DisposalSerializer(queryset, many=True).data)

	def post(self, request):
		serializer = DisposalCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		asset = Asset.objects.get(id=serializer.validated_data['asset_id'])
		disposal = request_disposal(asset=asset, requested_by=request.user)
		return Response(DisposalSerializer(disposal).data, status=201)


class DisposalApproveAPIView(APIView):
	permission_classes = [IsApproverOrAdmin]

	def patch(self, request, disposal_id: int):
		serializer = DisposalDecisionSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		disposal = DisposalHistory.objects.get(id=disposal_id)
		try:
			disposal = approve_disposal(
				disposal=disposal,
				approved_by=request.user,
				evidence_text=serializer.validated_data.get('evidence_text', ''),
			)
		except ValidationError as exc:
			return Response({'detail': exc.message}, status=422)
		return Response(DisposalSerializer(disposal).data)


class DisposalRejectAPIView(APIView):
	permission_classes = [IsApproverOrAdmin]

	def patch(self, request, disposal_id: int):
		serializer = DisposalDecisionSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		disposal = DisposalHistory.objects.get(id=disposal_id)
		try:
			disposal = reject_disposal(
				disposal=disposal,
				approved_by=request.user,
				reason=serializer.validated_data.get('reason', ''),
			)
		except ValidationError as exc:
			return Response({'detail': exc.message}, status=422)
		return Response(DisposalSerializer(disposal).data)


class InventoryResultCreateAPIView(APIView):
	def post(self, request, inventory_id: int):
		data = request.data.copy()
		data['cycle_id'] = inventory_id
		serializer = InventoryResultSerializer(data=data)
		serializer.is_valid(raise_exception=True)
		result = create_inventory_result(payload=serializer.validated_data, actor=request.user)
		return Response(InventoryResultSerializer(result).data, status=201)


class InventoryResultUpdateAPIView(APIView):
	def patch(self, request, inventory_id: int, result_id: int):
		instance = InventoryResult.objects.get(id=result_id, cycle_id=inventory_id)
		serializer = InventoryResultSerializer(instance, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		result = update_inventory_result(instance=instance, payload=serializer.validated_data, actor=request.user)
		return Response(InventoryResultSerializer(result).data)


class AuditLogListAPIView(APIView):
	permission_classes = [IsApproverOrAdmin]

	def get(self, request):
		queryset = AuditLog.objects.all().order_by('-changed_at')
		target_table = request.query_params.get('target_table')
		action = request.query_params.get('action')
		changed_by = request.query_params.get('changed_by')
		from_date = request.query_params.get('from')
		to_date = request.query_params.get('to')
		if target_table:
			queryset = queryset.filter(target_table=target_table)
		if action:
			queryset = queryset.filter(action=action)
		if changed_by:
			queryset = queryset.filter(changed_by_id=changed_by)
		if from_date and to_date:
			queryset = queryset.filter(changed_at__range=[from_date, to_date])
		return Response(AuditLogSerializer(queryset, many=True).data)


class AuditLogDetailAPIView(APIView):
	permission_classes = [IsApproverOrAdmin]

	def get(self, request, log_id: int):
		log = AuditLog.objects.get(id=log_id)
		return Response(AuditLogSerializer(log).data)
