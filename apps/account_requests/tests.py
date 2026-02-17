from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connection
from django.utils import timezone
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIClient

from apps.account_requests.models import (
	Asset,
	AssetAttributeMultiValue,
	AssetAttributeValue,
	AssetCategoryL,
	AssetCategoryM,
	AssetCategoryS,
	AssetStatusMaster,
	AssetStatusTransitionMaster,
	AssetType,
	AuditLog,
	BudgetAttributeMultiValue,
	BudgetAttributeValue,
	BudgetCategoryL,
	BudgetCategoryM,
	BudgetCategoryS,
	AssetBudgetMonitorDaily,
	AuthLockout,
	Budget,
	DashboardKPIDaily,
	Configuration,
	DisposalHistory,
	ExecutedBudget,
	InventoryCycle,
	InventoryResult,
	InventoryTargetSnapshot,
	LoanHistory,
	LicenseAllocationHistory,
	LicensePool,
	NotificationQueue,
	Project,
)
from apps.account_requests.services.asset_service import create_asset, update_budget_link
from apps.account_requests.services.disposal_service import approve_disposal, request_disposal


User = get_user_model()


class BaseDomainTestCase(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = User.objects.create_user(username='editor', password='pass1234')
		cls.manager = User.objects.create_user(username='manager', password='pass1234', is_staff=True)
		cls.asset_type = AssetType.objects.create(code='PC', name='PC')
		l_cat = AssetCategoryL.objects.create(code='L1', name='L1')
		m_cat = AssetCategoryM.objects.create(code='M1', name='M1', category_l=l_cat)
		cls.s_cat = AssetCategoryS.objects.create(code='S1', name='S1', category_m=m_cat)
		status_defs = [
			('REQUESTED_FROM_IT', 'IT部依頼中（受領待ち）', 1),
			('RECEIVED_WAITING', '受領済（配備待ち）', 2),
			('WAITING_ASSIGNMENT', '利用者割当待ち', 3),
			('IN_USE', 'ユーザー利用中', 4),
			('RETURN_PENDING', '返却依頼中', 5),
			('RETURNED', '返却済', 6),
			('MAINTENANCE', '保守対応中', 7),
			('REPAIRING', '修理中', 8),
			('RETIRED_WAITING', '廃棄判定待ち', 9),
			('DISPOSED', '廃棄済', 10),
		]
		status_map = {}
		for code, name, sort_order in status_defs:
			status_map[code] = AssetStatusMaster.objects.create(
				category_l=l_cat,
				status_code=code,
				status_name=name,
				sort_order=sort_order,
			)
		for from_code, to_code in [
			('REQUESTED_FROM_IT', 'RECEIVED_WAITING'),
			('RECEIVED_WAITING', 'WAITING_ASSIGNMENT'),
			('WAITING_ASSIGNMENT', 'IN_USE'),
			('IN_USE', 'RETURN_PENDING'),
			('RETURN_PENDING', 'RETURNED'),
			('RETURNED', 'WAITING_ASSIGNMENT'),
			('IN_USE', 'MAINTENANCE'),
			('MAINTENANCE', 'IN_USE'),
			('MAINTENANCE', 'REPAIRING'),
			('REPAIRING', 'MAINTENANCE'),
			('IN_USE', 'RETIRED_WAITING'),
			('IN_USE', 'DISPOSED'),
			('RETURNED', 'RETIRED_WAITING'),
			('MAINTENANCE', 'RETIRED_WAITING'),
			('RETIRED_WAITING', 'DISPOSED'),
		]:
			AssetStatusTransitionMaster.objects.create(
				category_l=l_cat,
				from_status=status_map[from_code],
				to_status=status_map[to_code],
			)
		project = Project.objects.create(project_code='PJ1', project_name='Project1')
		cls.budget_cat_l = BudgetCategoryL.objects.create(code='BL1', name='Budget L1')
		cls.budget_cat_m = BudgetCategoryM.objects.create(category_l=cls.budget_cat_l, code='BM1', name='Budget M1')
		cls.budget_cat_s = BudgetCategoryS.objects.create(category_m=cls.budget_cat_m, code='BS1', name='Budget S1')
		cls.budget = Budget.objects.create(
			fiscal_year=2026,
			budget_category='CAT',
			budget_category_s=cls.budget_cat_s,
			project=project,
			planned_amount=1000,
		)


class AssetServiceTests(BaseDomainTestCase):
	def test_pc_requires_person_attr_01(self):
		payload = {
			'asset_code': 'AS-001',
			'asset_type_id': self.asset_type.id,
			'category_s_id': self.s_cat.id,
			'asset_name': 'PC-1',
			'asset_kind': Asset.AssetKind.PC,
			'attributes': {
				'person_attr_02': self.manager.id,
			},
		}

		with self.assertRaises(ValidationError):
			create_asset(payload=payload, actor=self.user)

	def test_budget_link_updates_status(self):
		payload = {
			'asset_code': 'AS-002',
			'asset_type_id': self.asset_type.id,
			'category_s_id': self.s_cat.id,
			'asset_name': 'Device-1',
			'asset_kind': Asset.AssetKind.DEVICE,
			'attributes': {
				'person_attr_02': self.manager.id,
			},
		}
		asset = create_asset(payload=payload, actor=self.user)
		updated = update_budget_link(asset=asset, budget_id=self.budget.id, actor=self.user)
		self.assertEqual(updated.budget_link_status, Asset.BudgetLinkStatus.LINKED)


class DisposalServiceTests(BaseDomainTestCase):
	def test_disposal_approval_requires_evidence(self):
		payload = {
			'asset_code': 'AS-003',
			'asset_type_id': self.asset_type.id,
			'category_s_id': self.s_cat.id,
			'asset_name': 'Device-2',
			'asset_kind': Asset.AssetKind.DEVICE,
			'attributes': {
				'person_attr_02': self.manager.id,
			},
		}
		asset = create_asset(payload=payload, actor=self.user)
		disposal = request_disposal(asset=asset, requested_by=self.user)

		with self.assertRaises(ValidationError):
			approve_disposal(disposal=disposal, approved_by=self.manager, evidence_text='')

	def test_disposal_approval_disposes_asset(self):
		payload = {
			'asset_code': 'AS-004',
			'asset_type_id': self.asset_type.id,
			'category_s_id': self.s_cat.id,
			'asset_name': 'Device-3',
			'asset_kind': Asset.AssetKind.DEVICE,
			'attributes': {
				'person_attr_02': self.manager.id,
			},
		}
		asset = create_asset(payload=payload, actor=self.user)
		disposal = request_disposal(asset=asset, requested_by=self.user)
		approve_disposal(disposal=disposal, approved_by=self.manager, evidence_text='WIPE-1')
		asset.refresh_from_db()
		disposal.refresh_from_db()

		self.assertEqual(asset.status, Asset.AssetStatus.DISPOSED)
		self.assertEqual(disposal.disposal_status, DisposalHistory.DisposalStatus.APPROVED)


class AuthApiTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = User.objects.create_user(username='lockuser', password='pass1234')

	def setUp(self):
		self.client = APIClient()

	def test_login_lockout_after_five_failures(self):
		for _ in range(5):
			response = self.client.post('/api/v1/auth/login', {'username': 'lockuser', 'password': 'wrong'}, format='json')
			self.assertIn(response.status_code, [401, 423])

		locked_response = self.client.post('/api/v1/auth/login', {'username': 'lockuser', 'password': 'pass1234'}, format='json')
		self.assertEqual(locked_response.status_code, 423)
		lockout = AuthLockout.objects.get(username='lockuser')
		self.assertIsNotNone(lockout.locked_until)


class WebInterfaceTests(BaseDomainTestCase):
	def setUp(self):
		self.client = APIClient()

	def test_dashboard_requires_login(self):
		response = self.client.get('/dashboard')
		self.assertEqual(response.status_code, 302)
		self.assertIn('/login', response.url)

	def test_login_and_access_dashboard(self):
		login_response = self.client.post('/login', {'username': 'editor', 'password': 'pass1234'})
		self.assertEqual(login_response.status_code, 302)
		dashboard_response = self.client.get('/dashboard')
		self.assertEqual(dashboard_response.status_code, 200)

	def test_asset_list_access_after_login(self):
		self.client.force_login(self.user)
		response = self.client.get('/assets')
		self.assertEqual(response.status_code, 200)

	def test_asset_list_displays_category_user_and_due_date(self):
		asset = create_asset(
			payload={
				'asset_code': 'AS-WEB-LIST-1',
				'asset_type_id': self.asset_type.id,
				'category_s_id': self.s_cat.id,
				'asset_name': 'List Display Asset',
				'asset_kind': Asset.AssetKind.PC,
				'attributes': {
					'person_attr_01': self.user.id,
					'person_attr_02': self.manager.id,
					'person_attr_03': self.manager.id,
					'date_attr_03': timezone.localdate(),
				},
			},
			actor=self.user,
		)

		self.client.force_login(self.user)
		response = self.client.get('/assets', {'asset_code': asset.asset_code})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'L1 / M1 / S1')
		self.assertContains(response, self.user.username)
		self.assertContains(response, timezone.localdate().strftime('%Y-%m-%d'))

	def test_asset_list_search_filters_by_name_category_status_budget_and_user(self):
		s_cat2 = AssetCategoryS.objects.create(code='S2', name='S2', category_m=self.s_cat.category_m)
		target_asset = create_asset(
			payload={
				'asset_code': 'AS-WEB-SRCH-1',
				'asset_type_id': self.asset_type.id,
				'category_s_id': self.s_cat.id,
				'asset_name': 'Target Notebook Asset',
				'asset_kind': Asset.AssetKind.PC,
				'status': Asset.AssetStatus.IN_USE,
				'budget_id': self.budget.id,
				'budget_link_status': Asset.BudgetLinkStatus.LINKED,
				'attributes': {
					'person_attr_01': self.user.id,
					'person_attr_02': self.manager.id,
					'person_attr_03': self.manager.id,
				},
			},
			actor=self.user,
		)
		create_asset(
			payload={
				'asset_code': 'AS-WEB-SRCH-2',
				'asset_type_id': self.asset_type.id,
				'category_s_id': s_cat2.id,
				'asset_name': 'Other Tablet Asset',
				'asset_kind': Asset.AssetKind.PC,
				'status': Asset.AssetStatus.MAINTENANCE,
				'budget_link_status': Asset.BudgetLinkStatus.UNLINKED,
				'attributes': {
					'person_attr_01': self.manager.id,
					'person_attr_02': self.manager.id,
					'person_attr_03': self.manager.id,
				},
			},
			actor=self.user,
		)

		self.client.force_login(self.user)
		response = self.client.get(
			'/assets',
			{
				'asset_name': 'Target',
				'category_s_id': str(self.s_cat.id),
				'status': [Asset.AssetStatus.IN_USE],
				'budget_link_status': Asset.BudgetLinkStatus.LINKED,
				'person_attr_01_id': str(self.user.id),
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, target_asset.asset_code)
		self.assertNotContains(response, 'AS-WEB-SRCH-2')

	def test_asset_list_web_create_asset_success(self):
		self.client.force_login(self.user)
		response = self.client.post(
			'/assets',
			{
				'action': 'create_asset',
				'asset_code': 'AS-WEB-CRT-1',
				'asset_type_id': str(self.asset_type.id),
				'category_s_id': str(self.s_cat.id),
				'asset_name': 'Web Created Asset',
				'asset_kind': Asset.AssetKind.PC,
				'status': Asset.AssetStatus.IN_USE,
				'person_attr_01': str(self.user.id),
				'person_attr_02': str(self.manager.id),
				'person_attr_03': str(self.manager.id),
				'cls_attr_01': 'CLS-A',
				'free_text_attr_01': 'MODEL-WEB-1',
				'memo_attr_01': 'memo-web',
				'multi_attr_01_lines': 'LINE-1\nLINE-2',
				'multi_attr_02_lines': 'REL-1',
			},
		)

		self.assertEqual(response.status_code, 302)
		asset = Asset.objects.get(asset_code='AS-WEB-CRT-1')
		attr = AssetAttributeValue.objects.get(asset=asset)
		self.assertEqual(asset.asset_name, 'Web Created Asset')
		self.assertEqual(attr.cls_attr_01, 'CLS-A')
		self.assertEqual(attr.free_text_attr_01, 'MODEL-WEB-1')
		self.assertEqual(attr.memo_attr_01, 'memo-web')
		self.assertEqual(AssetAttributeMultiValue.objects.filter(asset=asset, multi_attr_type='MULTI_01').count(), 2)
		self.assertEqual(AssetAttributeMultiValue.objects.filter(asset=asset, multi_attr_type='MULTI_02').count(), 1)

	def test_asset_list_web_create_asset_validation_error(self):
		self.client.force_login(self.user)
		response = self.client.post(
			'/assets',
			{
				'action': 'create_asset',
				'asset_code': 'AS-WEB-CRT-ERR-1',
				'asset_type_id': str(self.asset_type.id),
				'category_s_id': str(self.s_cat.id),
				'asset_name': 'Web Invalid Asset',
				'asset_kind': Asset.AssetKind.PC,
				'person_attr_02': str(self.manager.id),
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '資産登録に失敗しました')
		self.assertFalse(Asset.objects.filter(asset_code='AS-WEB-CRT-ERR-1').exists())

	def test_asset_detail_displays_category_attributes_and_multi_values(self):
		asset = create_asset(
			payload={
				'asset_code': 'AS-WEB-DETAIL-1',
				'asset_type_id': self.asset_type.id,
				'category_s_id': self.s_cat.id,
				'asset_name': 'Detail Display Asset',
				'asset_kind': Asset.AssetKind.PC,
				'attributes': {
					'cls_attr_01': 'CLS-1',
					'person_attr_01': self.user.id,
					'person_attr_02': self.manager.id,
					'person_attr_03': self.manager.id,
					'date_attr_03': timezone.localdate(),
					'free_text_attr_01': 'MODEL-001',
					'memo_attr_01': 'memo one',
					'memo_attr_02': 'memo two',
				},
				'multi_attributes': [
					{'multi_attr_type': 'MULTI_01', 'value': 'ATTACH-1', 'sort_order': 1},
					{'multi_attr_type': 'MULTI_02', 'value': 'REL-ABC', 'sort_order': 1},
				],
			},
			actor=self.user,
		)

		self.client.force_login(self.user)
		response = self.client.get(f'/assets/{asset.id}')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'L1 / M1 / S1')
		self.assertContains(response, 'CLS-1')
		self.assertContains(response, self.user.username)
		self.assertContains(response, 'MODEL-001')
		self.assertContains(response, 'memo one')
		self.assertContains(response, 'memo two')
		self.assertContains(response, 'ATTACH-1')
		self.assertContains(response, 'REL-ABC')

	def test_asset_detail_web_update_asset_success(self):
		asset = create_asset(
			payload={
				'asset_code': 'AS-WEB-UPD-1',
				'asset_type_id': self.asset_type.id,
				'category_s_id': self.s_cat.id,
				'asset_name': 'Before Update Asset',
				'asset_kind': Asset.AssetKind.PC,
				'status': Asset.AssetStatus.IN_USE,
				'attributes': {
					'person_attr_01': self.user.id,
					'person_attr_02': self.manager.id,
					'person_attr_03': self.manager.id,
					'free_text_attr_01': 'BEFORE-MODEL',
				},
				'multi_attributes': [
					{'multi_attr_type': 'MULTI_01', 'value': 'OLD-1', 'sort_order': 1},
				],
			},
			actor=self.user,
		)

		self.client.force_login(self.user)
		response = self.client.post(
			f'/assets/{asset.id}',
			{
				'action': 'update_asset',
				'asset_name': 'After Update Asset',
				'category_s_id': str(self.s_cat.id),
				'asset_kind': Asset.AssetKind.PC,
				'status': Asset.AssetStatus.MAINTENANCE,
				'person_attr_01': str(self.user.id),
				'person_attr_02': str(self.manager.id),
				'person_attr_03': str(self.manager.id),
				'free_text_attr_01': 'AFTER-MODEL',
				'memo_attr_01': 'updated memo',
				'multi_attr_01_lines': 'NEW-1\nNEW-2',
				'multi_attr_02_lines': 'REL-2',
			},
		)

		self.assertEqual(response.status_code, 302)
		asset.refresh_from_db()
		attr = AssetAttributeValue.objects.get(asset=asset)
		self.assertEqual(asset.asset_name, 'After Update Asset')
		self.assertEqual(asset.status, Asset.AssetStatus.MAINTENANCE)
		self.assertEqual(attr.free_text_attr_01, 'AFTER-MODEL')
		self.assertEqual(attr.memo_attr_01, 'updated memo')
		self.assertEqual(AssetAttributeMultiValue.objects.filter(asset=asset, multi_attr_type='MULTI_01').count(), 2)
		self.assertEqual(AssetAttributeMultiValue.objects.filter(asset=asset, multi_attr_type='MULTI_02').count(), 1)

	def test_asset_detail_web_update_asset_invalid_transition(self):
		asset = create_asset(
			payload={
				'asset_code': 'AS-WEB-UPD-ERR-1',
				'asset_type_id': self.asset_type.id,
				'category_s_id': self.s_cat.id,
				'asset_name': 'Invalid Update Asset',
				'asset_kind': Asset.AssetKind.PC,
				'status': Asset.AssetStatus.IN_USE,
				'attributes': {
					'person_attr_01': self.user.id,
					'person_attr_02': self.manager.id,
					'person_attr_03': self.manager.id,
				},
			},
			actor=self.user,
		)

		self.client.force_login(self.user)
		response = self.client.post(
			f'/assets/{asset.id}',
			{
				'action': 'update_asset',
				'asset_name': 'Invalid Update Asset',
				'category_s_id': str(self.s_cat.id),
				'asset_kind': Asset.AssetKind.PC,
				'status': Asset.AssetStatus.REQUESTED_FROM_IT,
				'person_attr_01': str(self.user.id),
				'person_attr_02': str(self.manager.id),
				'person_attr_03': str(self.manager.id),
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '資産更新に失敗しました')
		asset.refresh_from_db()
		self.assertEqual(asset.status, Asset.AssetStatus.IN_USE)

	def test_extended_web_screens_access_after_login(self):
		self.client.force_login(self.user)
		for path in ['/configurations', '/budgets', '/license-pools', '/pc-management', '/inventories']:
			response = self.client.get(path)
			self.assertEqual(response.status_code, 200)

	def test_disposal_approval_web_action_approve(self):
		asset = create_asset(
			payload={
				'asset_code': 'AS-WEB-DP-1',
				'asset_type_id': self.asset_type.id,
				'category_s_id': self.s_cat.id,
				'asset_name': 'Web Disposal Asset',
				'asset_kind': Asset.AssetKind.DEVICE,
				'attributes': {'person_attr_02': self.manager.id},
			},
			actor=self.user,
		)
		disposal = request_disposal(asset=asset, requested_by=self.user)

		self.client.force_login(self.manager)
		response = self.client.post(
			'/disposals/approvals',
			{
				'action': 'approve',
				'disposal_id': disposal.id,
				'evidence_text': 'approved evidence',
			},
		)

		self.assertEqual(response.status_code, 302)
		disposal.refresh_from_db()
		asset.refresh_from_db()
		self.assertEqual(disposal.disposal_status, DisposalHistory.DisposalStatus.APPROVED)
		self.assertEqual(asset.status, Asset.AssetStatus.DISPOSED)

	def test_inventory_web_create_and_update_result(self):
		asset = create_asset(
			payload={
				'asset_code': 'AS-WEB-IV-1',
				'asset_type_id': self.asset_type.id,
				'category_s_id': self.s_cat.id,
				'asset_name': 'Web Inventory Asset',
				'asset_kind': Asset.AssetKind.DEVICE,
				'attributes': {'person_attr_02': self.manager.id},
			},
			actor=self.user,
		)
		cycle = InventoryCycle.objects.create(cycle_code='2026-03', cycle_year=2026, cycle_month=3, status=InventoryCycle.CycleStatus.OPEN)

		self.client.force_login(self.user)
		create_response = self.client.post(
			'/inventories',
			{
				'action': 'create_result',
				'cycle_id': cycle.id,
				'asset_id': asset.id,
				'difference_type': InventoryResult.DifferenceType.MISSING,
				'correction_status': InventoryResult.CorrectionStatus.OPEN,
				'correction_note': 'initial note',
			},
		)
		self.assertEqual(create_response.status_code, 302)

		result = InventoryResult.objects.get(cycle=cycle, asset=asset)
		update_response = self.client.post(
			'/inventories',
			{
				'action': 'update_result',
				'result_id': result.id,
				'difference_type': InventoryResult.DifferenceType.STATUS_DIFF,
				'correction_status': InventoryResult.CorrectionStatus.DONE,
				'correction_note': 'fixed',
			},
		)
		self.assertEqual(update_response.status_code, 302)

		result.refresh_from_db()
		self.assertEqual(result.difference_type, InventoryResult.DifferenceType.STATUS_DIFF)
		self.assertEqual(result.correction_status, InventoryResult.CorrectionStatus.DONE)
		self.assertEqual(result.correction_note, 'fixed')

	def test_audit_log_web_filter_by_target_and_action(self):
		AuditLog.objects.create(
			target_table='asset',
			target_id=1,
			action='UPDATE',
			changed_by=self.user,
			change_summary='asset updated',
		)
		AuditLog.objects.create(
			target_table='budget',
			target_id=2,
			action='CREATE',
			changed_by=self.user,
			change_summary='budget created',
		)

		self.client.force_login(self.user)
		response = self.client.get('/audit-logs', {'target_table': 'asset', 'action': 'UPDATE'})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'asset updated')
		self.assertNotContains(response, 'budget created')

	def test_dashboard_displays_budget_rate_and_maintenance_due_count(self):
		asset = create_asset(
			payload={
				'asset_code': 'AS-WEB-DS-1',
				'asset_type_id': self.asset_type.id,
				'category_s_id': self.s_cat.id,
				'asset_name': 'Dashboard Asset',
				'asset_kind': Asset.AssetKind.DEVICE,
				'attributes': {'person_attr_02': self.manager.id},
			},
			actor=self.user,
		)
		asset.warranty_expiry_date = timezone.localdate()
		asset.save(update_fields=['warranty_expiry_date'])

		ExecutedBudget.objects.create(
			budget=self.budget,
			executed_date=timezone.localdate(),
			executed_amount='250.00',
			description='dashboard test',
		)

		self.client.force_login(self.user)
		response = self.client.get('/dashboard')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '予算消化率')
		self.assertContains(response, '保守期限30日以内件数')

	def test_asset_list_web_status_transition_success(self):
		asset = create_asset(
			payload={
				'asset_code': 'AS-WEB-ST-1',
				'asset_type_id': self.asset_type.id,
				'category_s_id': self.s_cat.id,
				'asset_name': 'Status Transition Asset',
				'asset_kind': Asset.AssetKind.DEVICE,
				'attributes': {'person_attr_02': self.manager.id},
			},
			actor=self.user,
		)

		self.client.force_login(self.user)
		response = self.client.post('/assets', {'asset_id': asset.id, 'new_status': Asset.AssetStatus.MAINTENANCE})

		self.assertEqual(response.status_code, 302)
		asset.refresh_from_db()
		self.assertEqual(asset.status, Asset.AssetStatus.MAINTENANCE)

	def test_asset_list_web_status_transition_invalid(self):
		asset = create_asset(
			payload={
				'asset_code': 'AS-WEB-ST-2',
				'asset_type_id': self.asset_type.id,
				'category_s_id': self.s_cat.id,
				'asset_name': 'Invalid Transition Asset',
				'asset_kind': Asset.AssetKind.DEVICE,
				'attributes': {'person_attr_02': self.manager.id},
			},
			actor=self.user,
		)

		self.client.force_login(self.user)
		response = self.client.post('/assets', {'asset_id': asset.id, 'new_status': Asset.AssetStatus.REQUESTED_FROM_IT})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '状態遷移に失敗しました')
		asset.refresh_from_db()
		self.assertEqual(asset.status, Asset.AssetStatus.IN_USE)


class ExtendedApiTests(BaseDomainTestCase):
	def setUp(self):
		self.client = APIClient()
		self.client.force_login(self.user)

	def _create_asset(self, code: str):
		return create_asset(
			payload={
				'asset_code': code,
				'asset_type_id': self.asset_type.id,
				'category_s_id': self.s_cat.id,
				'asset_name': f'Asset-{code}',
				'asset_kind': Asset.AssetKind.DEVICE,
				'attributes': {
					'person_attr_02': self.manager.id,
				},
			},
			actor=self.user,
		)

	def test_configuration_create_rejects_disposed_asset(self):
		asset = self._create_asset('AS-CFG-1')
		asset.status = Asset.AssetStatus.DISPOSED
		asset.save(update_fields=['status'])

		response = self.client.post(
			'/api/v1/configurations',
			{
				'config_code': 'CFG-001',
				'config_name': 'PCセット',
				'items': [{'asset_id': asset.id, 'role_type': 'MAIN', 'quantity': 1}],
			},
			format='json',
		)

		self.assertEqual(response.status_code, 422)
		self.assertEqual(Configuration.objects.count(), 0)

	def test_budget_execution_create_success(self):
		response = self.client.post(
			f'/api/v1/budgets/{self.budget.id}/executions',
			{
				'executed_date': '2026-02-01',
				'executed_amount': '350.00',
				'description': 'PC購入',
			},
			format='json',
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(ExecutedBudget.objects.filter(budget=self.budget).count(), 1)

	def test_budget_create_with_category_attributes_and_multi_attributes(self):
		response = self.client.post(
			'/api/v1/budgets',
			{
				'fiscal_year': 2027,
				'budget_category': 'CAPEX',
				'budget_category_s_id': self.budget_cat_s.id,
				'project_id': self.budget.project_id,
				'planned_amount': '1200.00',
				'attributes': {
					'attr_01': 'A01',
					'attr_02': 'A02',
					'attr_20': 'A20',
				},
				'multi_attributes': [
					{'multi_attr_type': 'MULTI_01', 'value': 'multi-1', 'sort_order': 1},
				],
			},
			format='json',
		)

		self.assertEqual(response.status_code, 201)
		budget_id = response.data['id']
		attrs = BudgetAttributeValue.objects.get(budget_id=budget_id)
		self.assertEqual(attrs.attr_01, 'A01')
		self.assertEqual(attrs.attr_20, 'A20')
		self.assertEqual(BudgetAttributeMultiValue.objects.filter(budget_id=budget_id).count(), 1)

	def test_budget_update_updates_attributes_and_multi_attributes(self):
		BudgetAttributeValue.objects.create(budget=self.budget)
		response = self.client.put(
			f'/api/v1/budgets/{self.budget.id}',
			{
				'budget_category_s_id': self.budget_cat_s.id,
				'attributes': {
					'attr_05': 'UPDATED-05',
					'attr_19': 'UPDATED-19',
				},
				'multi_attributes': [
					{'multi_attr_type': 'MULTI_02', 'value': 'multi-updated', 'sort_order': 2},
				],
			},
			format='json',
		)

		self.assertEqual(response.status_code, 200)
		attrs = BudgetAttributeValue.objects.get(budget=self.budget)
		self.assertEqual(attrs.attr_05, 'UPDATED-05')
		self.assertEqual(attrs.attr_19, 'UPDATED-19')
		self.assertEqual(BudgetAttributeMultiValue.objects.filter(budget=self.budget).count(), 1)

	def test_license_allocation_exceeds_total_count(self):
		asset = self._create_asset('AS-LIC-1')
		pool = LicensePool.objects.create(license_name='Office', total_count=1, used_count=1)

		response = self.client.post(
			f'/api/v1/license-pools/{pool.id}/allocations',
			{
				'asset_id': asset.id,
				'allocated_count': 1,
			},
			format='json',
		)

		self.assertEqual(response.status_code, 422)
		self.assertEqual(LicenseAllocationHistory.objects.filter(pool=pool).count(), 0)

	def test_assets_csv_export_and_import(self):
		self._create_asset('AS-CSV-1')
		export_response = self.client.get('/api/v1/assets/export-csv')
		self.assertEqual(export_response.status_code, 200)
		self.assertIn('asset_code', export_response.content.decode('utf-8'))

		csv_content = (
			'asset_code,asset_type_id,category_s_id,asset_name,asset_kind,status,budget_id,budget_link_status,person_attr_01,person_attr_02\n'
			f'AS-CSV-2,{self.asset_type.id},{self.s_cat.id},CSV Asset,DEVICE,IN_USE,,UNLINKED,,{self.manager.id}\n'
		)
		file_obj = SimpleUploadedFile('assets.csv', csv_content.encode('utf-8'), content_type='text/csv')
		import_response = self.client.post('/api/v1/assets/import-csv', {'file': file_obj}, format='multipart')
		self.assertIn(import_response.status_code, [201, 207])
		self.assertTrue(Asset.objects.filter(asset_code='AS-CSV-2').exists())

	def test_asset_update_updates_attributes_and_multi_attributes(self):
		asset = self._create_asset('AS-UPD-1')

		response = self.client.put(
			f'/api/v1/assets/{asset.id}',
			{
				'asset_name': 'Updated Asset Name',
				'status': Asset.AssetStatus.MAINTENANCE,
				'attributes': {
					'person_attr_01': self.user.id,
					'person_attr_02': self.manager.id,
					'free_text_attr_01': 'MODEL-XYZ',
					'memo_attr_01': 'updated memo',
				},
				'multi_attributes': [
					{'multi_attr_type': 'MULTI_01', 'value': 'sub-item-1', 'sort_order': 1},
					{'multi_attr_type': 'MULTI_02', 'value': 'sub-item-2', 'sort_order': 2},
				],
			},
			format='json',
		)

		self.assertEqual(response.status_code, 200)
		asset.refresh_from_db()
		attrs = AssetAttributeValue.objects.get(asset=asset)
		self.assertEqual(asset.asset_name, 'Updated Asset Name')
		self.assertEqual(asset.status, Asset.AssetStatus.MAINTENANCE)
		self.assertEqual(attrs.person_attr_01_id, self.user.id)
		self.assertEqual(attrs.free_text_attr_01, 'MODEL-XYZ')
		self.assertEqual(attrs.memo_attr_01, 'updated memo')
		self.assertEqual(AssetAttributeMultiValue.objects.filter(asset=asset).count(), 2)

	def test_asset_update_rejects_pc_without_person_attr_01(self):
		asset = self._create_asset('AS-UPD-2')

		response = self.client.put(
			f'/api/v1/assets/{asset.id}',
			{
				'asset_kind': Asset.AssetKind.PC,
			},
			format='json',
		)

		self.assertEqual(response.status_code, 422)
		self.assertIn('person_attr_01', response.data.get('detail', ''))

	def test_loan_history_create_success(self):
		asset = self._create_asset('AS-LOAN-1')

		response = self.client.post(
			'/api/v1/loan-histories',
			{
				'asset_id': asset.id,
				'borrower_id': self.user.id,
			},
			format='json',
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(LoanHistory.objects.filter(asset=asset, borrower=self.user, returned_at__isnull=True).count(), 1)

	def test_loan_history_create_rejects_disposed_asset(self):
		asset = self._create_asset('AS-LOAN-2')
		asset.status = Asset.AssetStatus.DISPOSED
		asset.save(update_fields=['status'])

		response = self.client.post(
			'/api/v1/loan-histories',
			{
				'asset_id': asset.id,
				'borrower_id': self.user.id,
			},
			format='json',
		)

		self.assertEqual(response.status_code, 422)
		self.assertEqual(LoanHistory.objects.filter(asset=asset).count(), 0)

	def test_loan_history_create_rejects_duplicate_open_loan(self):
		asset = self._create_asset('AS-LOAN-3')
		first = self.client.post(
			'/api/v1/loan-histories',
			{
				'asset_id': asset.id,
				'borrower_id': self.user.id,
			},
			format='json',
		)
		self.assertEqual(first.status_code, 201)

		second = self.client.post(
			'/api/v1/loan-histories',
			{
				'asset_id': asset.id,
				'borrower_id': self.manager.id,
			},
			format='json',
		)

		self.assertEqual(second.status_code, 422)
		self.assertEqual(LoanHistory.objects.filter(asset=asset).count(), 1)

	def test_loan_history_return_rejects_double_return(self):
		asset = self._create_asset('AS-LOAN-4')
		create_response = self.client.post(
			'/api/v1/loan-histories',
			{
				'asset_id': asset.id,
				'borrower_id': self.user.id,
			},
			format='json',
		)
		self.assertEqual(create_response.status_code, 201)
		history_id = create_response.data['id']

		first_return = self.client.patch(f'/api/v1/loan-histories/{history_id}/return', {}, format='json')
		self.assertEqual(first_return.status_code, 200)

		second_return = self.client.patch(f'/api/v1/loan-histories/{history_id}/return', {}, format='json')
		self.assertEqual(second_return.status_code, 422)


class BatchCommandTests(BaseDomainTestCase):
	def test_batch_commands_create_outputs(self):
		create_asset(
			payload={
				'asset_code': 'AS-BAT-1',
				'asset_type_id': self.asset_type.id,
				'category_s_id': self.s_cat.id,
				'asset_name': 'Batch Asset',
				'asset_kind': Asset.AssetKind.DEVICE,
				'attributes': {'person_attr_02': self.manager.id},
			},
			actor=self.user,
		)
		cycle = InventoryCycle.objects.create(cycle_code='2026-02', cycle_year=2026, cycle_month=2, status=InventoryCycle.CycleStatus.OPEN)

		call_command('run_maintenance_notification_batch')
		call_command('run_unlinked_asset_monitor_batch', '--threshold', '1')
		call_command('run_dashboard_kpi_batch')
		call_command('run_inventory_snapshot_batch', str(cycle.id))

		self.assertGreaterEqual(NotificationQueue.objects.count(), 0)
		self.assertGreaterEqual(AssetBudgetMonitorDaily.objects.count(), 1)
		self.assertEqual(DashboardKPIDaily.objects.count(), 1)
		self.assertGreaterEqual(InventoryTargetSnapshot.objects.filter(cycle=cycle).count(), 1)


class PerformanceGovernanceTests(BaseDomainTestCase):
	@classmethod
	def setUpTestData(cls):
		super().setUpTestData()
		for i in range(60):
			create_asset(
				payload={
					'asset_code': f'AS-PERF-{i:03d}',
					'asset_type_id': cls.asset_type.id,
					'category_s_id': cls.s_cat.id,
					'asset_name': f'Perf Asset {i:03d}',
					'asset_kind': Asset.AssetKind.DEVICE,
					'attributes': {
						'person_attr_02': cls.manager.id,
					},
				},
				actor=cls.user,
			)

	def setUp(self):
		self.client = APIClient()
		self.client.force_login(self.user)

	def test_query_budget_asset_list_web(self):
		"""
		測定条件:
		- データ件数: Asset 60件
		- ページサイズ: 50（view固定）
		- フィルタ: asset_code前方一致 `AS-PERF-`
		クエリ予算: 16件以内
		"""
		with CaptureQueriesContext(connection) as ctx:
			response = self.client.get('/assets', {'asset_code': 'AS-PERF-'})
		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(ctx), 16)

	def test_query_budget_asset_list_api(self):
		"""
		測定条件:
		- データ件数: Asset 60件
		- ページサイズ: なし（現行API仕様）
		- フィルタ: asset_code前方一致 `AS-PERF-`
		クエリ予算: 8件以内
		"""
		with CaptureQueriesContext(connection) as ctx:
			response = self.client.get('/api/v1/assets', {'asset_code': 'AS-PERF-'}, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(ctx), 8)

	def test_query_budget_audit_log_list_web(self):
		"""
		測定条件:
		- データ件数: 監査ログは資産作成により生成済
		- ページサイズ: 100（view固定）
		- フィルタ: なし
		クエリ予算: 10件以内
		"""
		with CaptureQueriesContext(connection) as ctx:
			response = self.client.get('/audit-logs')
		self.assertEqual(response.status_code, 200)
		self.assertLessEqual(len(ctx), 10)
