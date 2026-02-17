from django.db import transaction

from apps.account_requests.models import Budget, BudgetAttributeMultiValue, BudgetAttributeValue, BudgetCategoryS, ExecutedBudget
from apps.account_requests.services.audit_service import record_audit


@transaction.atomic
def create_budget(*, payload: dict, actor):
    budget_category_s_id = payload.get('budget_category_s_id')
    if budget_category_s_id is not None and not BudgetCategoryS.objects.filter(id=budget_category_s_id).exists():
        raise ValueError('budget_category_s_id is invalid.')

    budget = Budget.objects.create(
        fiscal_year=payload['fiscal_year'],
        budget_category=payload['budget_category'],
        budget_category_s_id=budget_category_s_id,
        project_id=payload['project_id'],
        planned_amount=payload['planned_amount'],
    )

    attributes = payload.get('attributes', {})
    BudgetAttributeValue.objects.create(
        budget=budget,
        attr_01=attributes.get('attr_01', ''),
        attr_02=attributes.get('attr_02', ''),
        attr_03=attributes.get('attr_03', ''),
        attr_04=attributes.get('attr_04', ''),
        attr_05=attributes.get('attr_05', ''),
        attr_06=attributes.get('attr_06', ''),
        attr_07=attributes.get('attr_07', ''),
        attr_08=attributes.get('attr_08', ''),
        attr_09=attributes.get('attr_09', ''),
        attr_10=attributes.get('attr_10', ''),
        attr_11=attributes.get('attr_11', ''),
        attr_12=attributes.get('attr_12', ''),
        attr_13=attributes.get('attr_13', ''),
        attr_14=attributes.get('attr_14', ''),
        attr_15=attributes.get('attr_15', ''),
        attr_16=attributes.get('attr_16', ''),
        attr_17=attributes.get('attr_17', ''),
        attr_18=attributes.get('attr_18', ''),
        attr_19=attributes.get('attr_19', ''),
        attr_20=attributes.get('attr_20', ''),
    )

    for item in payload.get('multi_attributes', []):
        BudgetAttributeMultiValue.objects.create(
            budget=budget,
            multi_attr_type=item['multi_attr_type'],
            value=item['value'],
            sort_order=item.get('sort_order', 1),
        )

    record_audit(
        target_table='budget',
        target_id=budget.id,
        action='CREATE',
        changed_by=actor,
        summary='Budget created',
    )
    return budget


@transaction.atomic
def update_budget(*, budget: Budget, payload: dict, actor):
    budget_category_s_id = payload.get('budget_category_s_id')
    if budget_category_s_id is not None and not BudgetCategoryS.objects.filter(id=budget_category_s_id).exists():
        raise ValueError('budget_category_s_id is invalid.')

    for field in ['fiscal_year', 'budget_category', 'planned_amount']:
        if field in payload:
            setattr(budget, field, payload[field])
    if 'budget_category_s_id' in payload:
        budget.budget_category_s_id = budget_category_s_id
    budget.save()

    if 'attributes' in payload:
        attrs, _ = BudgetAttributeValue.objects.get_or_create(budget=budget)
        for index in range(1, 21):
            key = f'attr_{index:02d}'
            if key in payload['attributes']:
                setattr(attrs, key, payload['attributes'][key] or '')
        attrs.save()

    if 'multi_attributes' in payload:
        BudgetAttributeMultiValue.objects.filter(budget=budget).delete()
        for item in payload['multi_attributes']:
            BudgetAttributeMultiValue.objects.create(
                budget=budget,
                multi_attr_type=item['multi_attr_type'],
                value=item['value'],
                sort_order=item.get('sort_order', 1),
            )

    record_audit(
        target_table='budget',
        target_id=budget.id,
        action='UPDATE',
        changed_by=actor,
        summary='Budget updated',
    )
    return budget


@transaction.atomic
def create_executed_budget(*, budget_id: int, payload: dict, actor):
    execution = ExecutedBudget.objects.create(
        budget_id=budget_id,
        executed_date=payload['executed_date'],
        executed_amount=payload['executed_amount'],
        description=payload.get('description', ''),
    )
    record_audit(
        target_table='executed_budget',
        target_id=execution.id,
        action='CREATE',
        changed_by=actor,
        summary='Executed budget created',
    )
    return execution