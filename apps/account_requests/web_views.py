from decimal import Decimal
from datetime import timedelta

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView

from apps.account_requests.models import (
    Asset,
    AssetCategoryS,
    AssetType,
    AuditLog,
    Budget,
    BudgetCategoryS,
    Configuration,
    DisposalHistory,
    ExecutedBudget,
    InventoryCycle,
    InventoryResult,
    AssetStatusTransitionMaster,
    LicenseAllocationHistory,
    LicensePool,
    UserPCAssignment,
)
from apps.account_requests.services.budget_service import create_budget, create_executed_budget
from apps.account_requests.services.configuration_service import create_configuration
from apps.account_requests.services.disposal_service import approve_disposal, reject_disposal
from apps.account_requests.services.inventory_service import create_inventory_result, update_inventory_result
from apps.account_requests.services.license_service import allocate_license, create_license_pool
from apps.account_requests.services.pc_service import assign_pc_user
from apps.account_requests.services.asset_service import create_asset, update_asset
from apps.account_requests.services.workflow_service import transition_asset_status

User = get_user_model()


def home_redirect(_request):
    return redirect('/dashboard')


class AppLoginView(LoginView):
    template_name = 'account_requests/login.html'
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True


class AppLogoutView(LogoutView):
    pass


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'account_requests/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        planned_total = Budget.objects.aggregate(total=Sum('planned_amount'))['total'] or Decimal('0')
        executed_total = ExecutedBudget.objects.aggregate(total=Sum('executed_amount'))['total'] or Decimal('0')
        if planned_total > 0:
            context['budget_consumption_rate'] = round((executed_total / planned_total) * Decimal('100'), 2)
        else:
            context['budget_consumption_rate'] = Decimal('0.00')
        threshold_date = timezone.localdate() + timedelta(days=30)
        context['maintenance_due_30_count'] = Asset.objects.filter(
            warranty_expiry_date__isnull=False,
            warranty_expiry_date__lte=threshold_date,
        ).exclude(status=Asset.AssetStatus.DISPOSED).count()
        context['unlinked_count'] = Asset.objects.filter(budget_link_status=Asset.BudgetLinkStatus.UNLINKED).count()
        context['disposal_pending_count'] = DisposalHistory.objects.filter(
            disposal_status=DisposalHistory.DisposalStatus.REQUESTED,
        ).count()
        context['inventory_diff_count'] = InventoryResult.objects.exclude(correction_status=InventoryResult.CorrectionStatus.DONE).count()
        return context


class AssetListView(LoginRequiredMixin, ListView):
    template_name = 'account_requests/asset_list.html'
    context_object_name = 'assets'
    model = Asset
    paginate_by = 50

    def get_queryset(self):
        queryset = Asset.objects.select_related(
            'category_s__category_m__category_l',
            'assetattributevalue__person_attr_01',
        ).all().order_by('-updated_at')
        asset_code = self.request.GET.get('asset_code', '').strip()
        asset_name = self.request.GET.get('asset_name', '').strip()
        category_s_id = self.request.GET.get('category_s_id', '').strip()
        statuses = [status for status in self.request.GET.getlist('status') if status]
        budget_link_status = self.request.GET.get('budget_link_status', '').strip()
        person_attr_01_id = self.request.GET.get('person_attr_01_id', '').strip()

        if asset_code:
            queryset = queryset.filter(asset_code__istartswith=asset_code)
        if asset_name:
            queryset = queryset.filter(asset_name__icontains=asset_name)
        if category_s_id:
            try:
                queryset = queryset.filter(category_s_id=int(category_s_id))
            except ValueError:
                queryset = queryset.none()
        if statuses:
            queryset = queryset.filter(status__in=statuses)
        if budget_link_status:
            queryset = queryset.filter(budget_link_status=budget_link_status)
        if person_attr_01_id:
            try:
                queryset = queryset.filter(assetattributevalue__person_attr_01_id=int(person_attr_01_id))
            except ValueError:
                queryset = queryset.none()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_assets = list(context['assets'])
        category_l_ids = {asset.category_s.category_m.category_l_id for asset in page_assets}
        status_codes = {asset.status for asset in page_assets}

        transition_qs = AssetStatusTransitionMaster.objects.select_related('to_status').filter(
            category_l_id__in=category_l_ids,
            from_status__status_code__in=status_codes,
            from_status__is_active=True,
            to_status__is_active=True,
            is_active=True,
        ).order_by('to_status__sort_order')

        transition_map = {}
        for transition in transition_qs:
            key = (transition.category_l_id, transition.from_status.status_code)
            transition_map.setdefault(key, []).append(transition.to_status)

        for asset in page_assets:
            key = (asset.category_s.category_m.category_l_id, asset.status)
            asset.available_next_statuses = transition_map.get(key, [])
            attr_value = getattr(asset, 'assetattributevalue', None)
            asset.display_person_attr_01 = attr_value.person_attr_01 if attr_value else None
            asset.display_date_attr_03 = attr_value.date_attr_03 if attr_value else None

        context['assets'] = page_assets
        context['search'] = {
            'asset_code': self.request.GET.get('asset_code', '').strip(),
            'asset_name': self.request.GET.get('asset_name', '').strip(),
            'category_s_id': self.request.GET.get('category_s_id', '').strip(),
            'status': [status for status in self.request.GET.getlist('status') if status],
            'budget_link_status': self.request.GET.get('budget_link_status', '').strip(),
            'person_attr_01_id': self.request.GET.get('person_attr_01_id', '').strip(),
        }
        context['category_s_options'] = AssetCategoryS.objects.select_related('category_m__category_l').all().order_by('id')
        context['asset_type_options'] = AssetType.objects.filter(is_active=True).order_by('id')
        context['asset_kind_options'] = Asset.AssetKind.choices
        context['status_options'] = Asset.AssetStatus.choices
        context['budget_link_options'] = Asset.BudgetLinkStatus.choices
        context['person_options'] = User.objects.filter(is_active=True).order_by('username')
        context['create_form'] = kwargs.get('create_form') or {
            'asset_code': '',
            'asset_type_id': '',
            'category_s_id': '',
            'asset_name': '',
            'asset_kind': Asset.AssetKind.DEVICE,
            'status': Asset.AssetStatus.IN_USE,
            'person_attr_01': '',
            'person_attr_02': '',
            'person_attr_03': '',
            'multi_attr_01_lines': '',
            'multi_attr_02_lines': '',
            **{f'cls_attr_0{i}': '' for i in range(1, 6)},
            'location_attr_01': '',
            'location_attr_02': '',
            'date_attr_01': '',
            'date_attr_02': '',
            'date_attr_03': '',
            'free_text_attr_01': '',
            'free_text_attr_02': '',
            'free_text_attr_03': '',
            'memo_attr_01': '',
            'memo_attr_02': '',
        }
        return context

    def _build_create_payload(self, request):
        attributes = {
            f'cls_attr_0{i}': request.POST.get(f'cls_attr_0{i}', '').strip()
            for i in range(1, 6)
        }
        attributes.update(
            {
                'person_attr_01': int(request.POST['person_attr_01']) if request.POST.get('person_attr_01') else None,
                'person_attr_02': int(request.POST['person_attr_02']),
                'person_attr_03': int(request.POST['person_attr_03']) if request.POST.get('person_attr_03') else request.user.id,
                'location_attr_01': request.POST.get('location_attr_01', '').strip(),
                'location_attr_02': request.POST.get('location_attr_02', '').strip(),
                'date_attr_01': request.POST.get('date_attr_01') or None,
                'date_attr_02': request.POST.get('date_attr_02') or None,
                'date_attr_03': request.POST.get('date_attr_03') or None,
                'free_text_attr_01': request.POST.get('free_text_attr_01', '').strip(),
                'free_text_attr_02': request.POST.get('free_text_attr_02', '').strip(),
                'free_text_attr_03': request.POST.get('free_text_attr_03', '').strip(),
                'memo_attr_01': request.POST.get('memo_attr_01', '').strip(),
                'memo_attr_02': request.POST.get('memo_attr_02', '').strip(),
            }
        )

        multi_attributes = []
        for multi_attr_type, key in [('MULTI_01', 'multi_attr_01_lines'), ('MULTI_02', 'multi_attr_02_lines')]:
            lines = [line.strip() for line in request.POST.get(key, '').splitlines() if line.strip()]
            for idx, value in enumerate(lines, start=1):
                multi_attributes.append(
                    {
                        'multi_attr_type': multi_attr_type,
                        'value': value,
                        'sort_order': idx,
                    }
                )

        payload = {
            'asset_code': request.POST['asset_code'].strip(),
            'asset_type_id': int(request.POST['asset_type_id']),
            'category_s_id': int(request.POST['category_s_id']),
            'asset_name': request.POST['asset_name'].strip(),
            'asset_kind': request.POST['asset_kind'],
            'status': request.POST.get('status') or Asset.AssetStatus.IN_USE,
            'attributes': attributes,
            'multi_attributes': multi_attributes,
        }
        return payload

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')

        if action == 'create_asset':
            try:
                payload = self._build_create_payload(request)
                create_asset(payload=payload, actor=request.user)
                return HttpResponseRedirect('/assets')
            except (ValidationError, ValueError, KeyError):
                self.object_list = self.get_queryset()
                context = self.get_context_data(
                    create_form={key: request.POST.get(key, '') for key in request.POST.keys()},
                )
                context['create_error_message'] = '資産登録に失敗しました。入力値を確認してください。'
                return self.render_to_response(context)

        try:
            asset = Asset.objects.select_related('category_s__category_m__category_l').get(id=int(request.POST['asset_id']))
            transition_asset_status(asset=asset, new_status=request.POST['new_status'])
            return HttpResponseRedirect('/assets')
        except (ValueError, Asset.DoesNotExist, ValidationError):
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            context['error_message'] = '状態遷移に失敗しました。遷移可能な状態を選択してください。'
            return self.render_to_response(context)


class AssetDetailView(LoginRequiredMixin, DetailView):
    template_name = 'account_requests/asset_detail.html'
    model = Asset
    context_object_name = 'asset'

    def get_queryset(self):
        return Asset.objects.select_related(
            'category_s__category_m__category_l',
            'assetattributevalue__person_attr_01',
            'assetattributevalue__person_attr_02',
            'assetattributevalue__person_attr_03',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attr_value = getattr(self.object, 'assetattributevalue', None)
        multi_values = self.object.assetattributemultivalue_set.all().order_by('multi_attr_type', 'sort_order', 'id')
        context['attr_value'] = attr_value
        context['multi_attr_01_values'] = [item for item in multi_values if item.multi_attr_type == 'MULTI_01']
        context['multi_attr_02_values'] = [item for item in multi_values if item.multi_attr_type == 'MULTI_02']
        context['category_s_options'] = AssetCategoryS.objects.select_related('category_m__category_l').all().order_by('id')
        context['asset_kind_options'] = Asset.AssetKind.choices
        context['status_options'] = Asset.AssetStatus.choices
        context['person_options'] = User.objects.filter(is_active=True).order_by('username')
        context['edit_form'] = kwargs.get('edit_form') or {
            'asset_name': self.object.asset_name,
            'asset_kind': self.object.asset_kind,
            'category_s_id': str(self.object.category_s_id),
            'status': self.object.status,
            'person_attr_01': str(attr_value.person_attr_01_id) if attr_value and attr_value.person_attr_01_id else '',
            'person_attr_02': str(attr_value.person_attr_02_id) if attr_value and attr_value.person_attr_02_id else '',
            'person_attr_03': str(attr_value.person_attr_03_id) if attr_value and attr_value.person_attr_03_id else '',
            'multi_attr_01_lines': '\n'.join(item.value for item in context['multi_attr_01_values']),
            'multi_attr_02_lines': '\n'.join(item.value for item in context['multi_attr_02_values']),
            'cls_attr_01': attr_value.cls_attr_01 if attr_value else '',
            'cls_attr_02': attr_value.cls_attr_02 if attr_value else '',
            'cls_attr_03': attr_value.cls_attr_03 if attr_value else '',
            'cls_attr_04': attr_value.cls_attr_04 if attr_value else '',
            'cls_attr_05': attr_value.cls_attr_05 if attr_value else '',
            'location_attr_01': attr_value.location_attr_01 if attr_value else '',
            'location_attr_02': attr_value.location_attr_02 if attr_value else '',
            'date_attr_01': attr_value.date_attr_01.isoformat() if attr_value and attr_value.date_attr_01 else '',
            'date_attr_02': attr_value.date_attr_02.isoformat() if attr_value and attr_value.date_attr_02 else '',
            'date_attr_03': attr_value.date_attr_03.isoformat() if attr_value and attr_value.date_attr_03 else '',
            'free_text_attr_01': attr_value.free_text_attr_01 if attr_value else '',
            'free_text_attr_02': attr_value.free_text_attr_02 if attr_value else '',
            'free_text_attr_03': attr_value.free_text_attr_03 if attr_value else '',
            'memo_attr_01': attr_value.memo_attr_01 if attr_value else '',
            'memo_attr_02': attr_value.memo_attr_02 if attr_value else '',
        }
        return context

    def _build_update_payload(self, request):
        attributes = {
            f'cls_attr_0{i}': request.POST.get(f'cls_attr_0{i}', '').strip()
            for i in range(1, 6)
        }
        attributes.update(
            {
                'person_attr_01': int(request.POST['person_attr_01']) if request.POST.get('person_attr_01') else None,
                'person_attr_02': int(request.POST['person_attr_02']),
                'person_attr_03': int(request.POST['person_attr_03']) if request.POST.get('person_attr_03') else request.user.id,
                'location_attr_01': request.POST.get('location_attr_01', '').strip(),
                'location_attr_02': request.POST.get('location_attr_02', '').strip(),
                'date_attr_01': request.POST.get('date_attr_01') or None,
                'date_attr_02': request.POST.get('date_attr_02') or None,
                'date_attr_03': request.POST.get('date_attr_03') or None,
                'free_text_attr_01': request.POST.get('free_text_attr_01', '').strip(),
                'free_text_attr_02': request.POST.get('free_text_attr_02', '').strip(),
                'free_text_attr_03': request.POST.get('free_text_attr_03', '').strip(),
                'memo_attr_01': request.POST.get('memo_attr_01', '').strip(),
                'memo_attr_02': request.POST.get('memo_attr_02', '').strip(),
            }
        )

        multi_attributes = []
        for multi_attr_type, key in [('MULTI_01', 'multi_attr_01_lines'), ('MULTI_02', 'multi_attr_02_lines')]:
            lines = [line.strip() for line in request.POST.get(key, '').splitlines() if line.strip()]
            for idx, value in enumerate(lines, start=1):
                multi_attributes.append(
                    {
                        'multi_attr_type': multi_attr_type,
                        'value': value,
                        'sort_order': idx,
                    }
                )

        payload = {
            'asset_name': request.POST['asset_name'].strip(),
            'asset_kind': request.POST['asset_kind'],
            'category_s_id': int(request.POST['category_s_id']),
            'status': request.POST.get('status') or self.object.status,
            'attributes': attributes,
            'multi_attributes': multi_attributes,
        }
        return payload

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get('action')

        if action == 'update_asset':
            try:
                payload = self._build_update_payload(request)
                update_asset(asset=self.object, payload=payload, actor=request.user)
                return HttpResponseRedirect(f'/assets/{self.object.id}')
            except (ValidationError, ValueError, KeyError):
                context = self.get_context_data(edit_form={key: request.POST.get(key, '') for key in request.POST.keys()})
                context['update_error_message'] = '資産更新に失敗しました。入力値を確認してください。'
                return self.render_to_response(context)

        return HttpResponseRedirect(f'/assets/{self.object.id}')


class DisposalApprovalView(LoginRequiredMixin, ListView):
    template_name = 'account_requests/disposal_approval.html'
    context_object_name = 'disposals'
    model = DisposalHistory

    def get_queryset(self):
        return DisposalHistory.objects.filter(disposal_status=DisposalHistory.DisposalStatus.REQUESTED).order_by('-requested_at')

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        try:
            disposal_id = int(request.POST['disposal_id'])
            disposal = DisposalHistory.objects.get(id=disposal_id)
            if action == 'approve':
                approve_disposal(
                    disposal=disposal,
                    approved_by=request.user,
                    evidence_text=request.POST.get('evidence_text', ''),
                )
            elif action == 'reject':
                reject_disposal(
                    disposal=disposal,
                    approved_by=request.user,
                    reason=request.POST.get('reason', ''),
                )
            return HttpResponseRedirect('/disposals/approvals')
        except (ValidationError, ValueError, DisposalHistory.DoesNotExist):
            context = self.get_context_data()
            context['error_message'] = '廃棄承認の更新に失敗しました。入力値を確認してください。'
            return self.render_to_response(context)


class AuditLogView(LoginRequiredMixin, ListView):
    template_name = 'account_requests/audit_logs.html'
    context_object_name = 'logs'
    model = AuditLog
    paginate_by = 100

    def get_queryset(self):
        queryset = AuditLog.objects.select_related('changed_by').all().order_by('-changed_at')
        target_table = self.request.GET.get('target_table', '').strip()
        action = self.request.GET.get('action', '').strip()
        changed_by_id = self.request.GET.get('changed_by_id', '').strip()
        changed_at_from = self.request.GET.get('changed_at_from', '').strip()
        changed_at_to = self.request.GET.get('changed_at_to', '').strip()

        if target_table:
            queryset = queryset.filter(target_table__icontains=target_table)
        if action:
            queryset = queryset.filter(action__icontains=action)
        if changed_by_id:
            try:
                queryset = queryset.filter(changed_by_id=int(changed_by_id))
            except ValueError:
                queryset = queryset.none()
        if changed_at_from:
            queryset = queryset.filter(changed_at__date__gte=changed_at_from)
        if changed_at_to:
            queryset = queryset.filter(changed_at__date__lte=changed_at_to)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = {
            'target_table': self.request.GET.get('target_table', ''),
            'action': self.request.GET.get('action', ''),
            'changed_by_id': self.request.GET.get('changed_by_id', ''),
            'changed_at_from': self.request.GET.get('changed_at_from', ''),
            'changed_at_to': self.request.GET.get('changed_at_to', ''),
        }
        return context


class ConfigurationView(LoginRequiredMixin, TemplateView):
    template_name = 'account_requests/configuration_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['configurations'] = Configuration.objects.all().order_by('-updated_at')
        context['assets'] = Asset.objects.exclude(status=Asset.AssetStatus.DISPOSED).order_by('asset_code')[:200]
        return context

    def post(self, request, *args, **kwargs):
        asset_id = request.POST.get('asset_id')
        payload = {
            'config_code': request.POST.get('config_code'),
            'config_name': request.POST.get('config_name'),
            'status': request.POST.get('status') or 'ACTIVE',
            'items': [
                {
                    'asset_id': int(asset_id),
                    'role_type': request.POST.get('role_type') or 'MAIN',
                    'quantity': int(request.POST.get('quantity') or 1),
                }
            ]
            if asset_id
            else [],
        }
        try:
            create_configuration(payload=payload, actor=request.user)
            return HttpResponseRedirect('/configurations')
        except (ValidationError, ValueError):
            context = self.get_context_data()
            context['error_message'] = '構成の登録に失敗しました。入力値を確認してください。'
            return self.render_to_response(context)


class BudgetView(LoginRequiredMixin, TemplateView):
    template_name = 'account_requests/budget_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        budgets = Budget.objects.all().order_by('-updated_at')
        context['budget_categories_s'] = BudgetCategoryS.objects.select_related('category_m__category_l').all().order_by('id')
        context['budget_attr_indices'] = range(1, 21)
        selected_budget_id = self.request.GET.get('budget_id')
        selected_budget = None
        executions = ExecutedBudget.objects.none()
        if selected_budget_id:
            selected_budget = Budget.objects.filter(id=selected_budget_id).first()
            if selected_budget:
                executions = ExecutedBudget.objects.filter(budget=selected_budget).order_by('-executed_date', '-id')
        context['budgets'] = budgets
        context['selected_budget'] = selected_budget
        context['executions'] = executions
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        try:
            if action == 'create_budget':
                attributes = {
                    f'attr_{index:02d}': request.POST.get(f'attr_{index:02d}', '')
                    for index in range(1, 21)
                }
                multi_attributes = []
                for multi_attr_type in ['MULTI_01', 'MULTI_02']:
                    value = request.POST.get(f'multi_{multi_attr_type.lower()}_value', '').strip()
                    if value:
                        multi_attributes.append(
                            {
                                'multi_attr_type': multi_attr_type,
                                'value': value,
                                'sort_order': int(request.POST.get(f'multi_{multi_attr_type.lower()}_sort') or 1),
                            }
                        )
                payload = {
                    'fiscal_year': int(request.POST['fiscal_year']),
                    'budget_category': request.POST['budget_category'],
                    'budget_category_s_id': int(request.POST['budget_category_s_id']) if request.POST.get('budget_category_s_id') else None,
                    'project_id': int(request.POST['project_id']),
                    'planned_amount': request.POST['planned_amount'],
                    'attributes': attributes,
                    'multi_attributes': multi_attributes,
                }
                create_budget(payload=payload, actor=request.user)
                return HttpResponseRedirect('/budgets')
            if action == 'create_execution':
                budget_id = int(request.POST['budget_id'])
                payload = {
                    'executed_date': request.POST['executed_date'],
                    'executed_amount': request.POST['executed_amount'],
                    'description': request.POST.get('description', ''),
                }
                create_executed_budget(budget_id=budget_id, payload=payload, actor=request.user)
                return HttpResponseRedirect(f'/budgets?budget_id={budget_id}')
        except (ValidationError, ValueError):
            context = self.get_context_data()
            context['error_message'] = '予算データの登録に失敗しました。入力値を確認してください。'
            return self.render_to_response(context)
        return HttpResponseRedirect('/budgets')


class LicensePoolView(LoginRequiredMixin, TemplateView):
    template_name = 'account_requests/license_pool_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pools = LicensePool.objects.all().order_by('-updated_at')
        selected_pool_id = self.request.GET.get('pool_id')
        allocations = LicenseAllocationHistory.objects.none()
        if selected_pool_id:
            allocations = LicenseAllocationHistory.objects.filter(pool_id=selected_pool_id).order_by('-allocated_at', '-id')
        context['pools'] = pools
        context['assets'] = Asset.objects.all().order_by('asset_code')[:200]
        context['allocations'] = allocations
        context['selected_pool_id'] = int(selected_pool_id) if selected_pool_id else None
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        try:
            if action == 'create_pool':
                payload = {
                    'license_name': request.POST['license_name'],
                    'total_count': int(request.POST['total_count']),
                    'used_count': int(request.POST.get('used_count') or 0),
                    'contract_expiry_date': request.POST.get('contract_expiry_date') or None,
                }
                create_license_pool(payload=payload, actor=request.user)
                return HttpResponseRedirect('/license-pools')
            if action == 'allocate':
                pool_id = int(request.POST['pool_id'])
                pool = LicensePool.objects.get(id=pool_id)
                payload = {
                    'asset_id': int(request.POST['asset_id']),
                    'allocated_count': int(request.POST.get('allocated_count') or 1),
                }
                allocate_license(pool=pool, payload=payload, actor=request.user)
                return HttpResponseRedirect(f'/license-pools?pool_id={pool_id}')
        except (ValidationError, ValueError):
            context = self.get_context_data()
            context['error_message'] = 'ライセンス登録に失敗しました。入力値を確認してください。'
            return self.render_to_response(context)
        return HttpResponseRedirect('/license-pools')


class PCManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'account_requests/pc_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assignments'] = UserPCAssignment.objects.select_related('asset', 'user').order_by('-updated_at')
        context['pc_assets'] = Asset.objects.filter(asset_kind=Asset.AssetKind.PC).order_by('asset_code')[:200]
        return context

    def post(self, request, *args, **kwargs):
        try:
            payload = {
                'asset_id': int(request.POST['asset_id']),
                'user_id': int(request.POST['user_id']),
                'os_name': request.POST['os_name'],
                'spec_text': request.POST.get('spec_text', ''),
                'warranty_expiry_date': request.POST.get('warranty_expiry_date') or None,
            }
            assign_pc_user(payload=payload, actor=request.user)
            return HttpResponseRedirect('/pc-management')
        except (ValidationError, ValueError):
            context = self.get_context_data()
            context['error_message'] = 'PC割当の登録に失敗しました。入力値を確認してください。'
            return self.render_to_response(context)


class InventoryView(LoginRequiredMixin, TemplateView):
    template_name = 'account_requests/inventory_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cycles'] = InventoryCycle.objects.all().order_by('-cycle_year', '-cycle_month')
        context['results'] = InventoryResult.objects.select_related('asset', 'cycle').order_by('-updated_at')[:200]
        context['assets'] = Asset.objects.exclude(status=Asset.AssetStatus.DISPOSED).order_by('asset_code')[:200]
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        try:
            if action == 'create_result':
                payload = {
                    'cycle_id': int(request.POST['cycle_id']),
                    'asset_id': int(request.POST['asset_id']),
                    'difference_type': request.POST['difference_type'],
                    'correction_status': request.POST.get('correction_status') or InventoryResult.CorrectionStatus.OPEN,
                    'correction_note': request.POST.get('correction_note', ''),
                }
                create_inventory_result(payload=payload, actor=request.user)
                return HttpResponseRedirect('/inventories')

            if action == 'update_result':
                result = InventoryResult.objects.get(id=int(request.POST['result_id']))
                payload = {
                    'difference_type': request.POST.get('difference_type') or result.difference_type,
                    'correction_status': request.POST.get('correction_status') or result.correction_status,
                    'correction_note': request.POST.get('correction_note', ''),
                }
                update_inventory_result(instance=result, payload=payload, actor=request.user)
                return HttpResponseRedirect('/inventories')
        except (ValidationError, ValueError, InventoryResult.DoesNotExist):
            context = self.get_context_data()
            context['error_message'] = '棚卸差異の更新に失敗しました。入力値を確認してください。'
            return self.render_to_response(context)
        return HttpResponseRedirect('/inventories')