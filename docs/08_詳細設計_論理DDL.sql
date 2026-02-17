-- 資産管理システム 論理DDL草案
-- version: v0.3
-- date: 2026-02-17

-- NOTE:
-- 本DDLは Django 標準 `auth_user(id)` テーブルの存在を前提とする。

create table asset_type_mst (
    id bigint primary key,
    code varchar(20) not null unique,
    name varchar(100) not null,
    is_active boolean not null default true
);

create table asset_category_l_mst (
    id bigint primary key,
    code varchar(20) not null unique,
    name varchar(100) not null,
    is_active boolean not null default true
);

create table asset_category_m_mst (
    id bigint primary key,
    category_l_id bigint not null references asset_category_l_mst(id),
    code varchar(20) not null,
    name varchar(100) not null,
    is_active boolean not null default true,
    unique (category_l_id, code)
);

create table asset_category_s_mst (
    id bigint primary key,
    category_m_id bigint not null references asset_category_m_mst(id),
    code varchar(20) not null,
    name varchar(100) not null,
    is_active boolean not null default true,
    unique (category_m_id, code)
);

create table asset_status_mst (
    id bigint primary key,
    category_l_id bigint not null references asset_category_l_mst(id),
    status_code varchar(40) not null,
    status_name varchar(100) not null,
    sort_order int not null default 1,
    is_active boolean not null default true,
    unique (category_l_id, status_code)
);

create table asset_status_transition_mst (
    id bigint primary key,
    category_l_id bigint not null references asset_category_l_mst(id),
    from_status_id bigint not null references asset_status_mst(id),
    to_status_id bigint not null references asset_status_mst(id),
    is_active boolean not null default true,
    unique (category_l_id, from_status_id, to_status_id)
);

create table project_mst (
    id bigint primary key,
    project_code varchar(30) not null unique,
    project_name varchar(200) not null,
    is_active boolean not null default true
);

create table budget_category_l_mst (
    id bigint primary key,
    code varchar(20) not null unique,
    name varchar(100) not null,
    is_active boolean not null default true
);

create table budget_category_m_mst (
    id bigint primary key,
    category_l_id bigint not null references budget_category_l_mst(id),
    code varchar(20) not null,
    name varchar(100) not null,
    is_active boolean not null default true,
    unique (category_l_id, code)
);

create table budget_category_s_mst (
    id bigint primary key,
    category_m_id bigint not null references budget_category_m_mst(id),
    code varchar(20) not null,
    name varchar(100) not null,
    is_active boolean not null default true,
    unique (category_m_id, code)
);

create table budget (
    id bigint primary key,
    fiscal_year int not null,
    budget_category varchar(100) not null,
    budget_category_s_id bigint not null references budget_category_s_mst(id),
    project_id bigint not null references project_mst(id),
    planned_amount numeric(18,2) not null check (planned_amount >= 0),
    created_at timestamp not null,
    updated_at timestamp not null
);

create index idx_budget_year_project on budget(fiscal_year, project_id);

create index idx_budget_category_s on budget(budget_category_s_id);

create table budget_attribute_value (
    id bigint primary key,
    budget_id bigint not null unique references budget(id),
    cls_attr_01 varchar(50),
    cls_attr_02 varchar(50),
    cls_attr_03 varchar(50),
    cls_attr_04 varchar(50),
    cls_attr_05 varchar(50),
    person_attr_01 bigint,
    person_attr_02 bigint,
    person_attr_03 bigint,
    location_attr_01 varchar(100),
    location_attr_02 varchar(100),
    date_attr_01 date,
    date_attr_02 date,
    date_attr_03 date,
    free_text_attr_01 varchar(200),
    free_text_attr_02 varchar(200),
    free_text_attr_03 varchar(500),
    memo_attr_01 text,
    memo_attr_02 text,
    updated_at timestamp not null,
    check (date_attr_03 is null or date_attr_01 is null or date_attr_03 >= date_attr_01)
);

create table budget_attribute_multi_value (
    id bigint primary key,
    budget_id bigint not null references budget(id),
    multi_attr_type varchar(20) not null,
    value varchar(500) not null,
    sort_order int not null default 1,
    created_at timestamp not null,
    check (multi_attr_type in ('MULTI_01','MULTI_02'))
);

create unique index uq_budget_multi_02_value
    on budget_attribute_multi_value(budget_id, multi_attr_type, value)
    where multi_attr_type = 'MULTI_02';

create index idx_budget_multi_sort
    on budget_attribute_multi_value(budget_id, multi_attr_type, sort_order);

create table executed_budget (
    id bigint primary key,
    budget_id bigint not null references budget(id),
    executed_date date not null,
    executed_amount numeric(18,2) not null check (executed_amount >= 0),
    description varchar(500),
    created_at timestamp not null
);

create table vendor_mst (
    id bigint primary key,
    vendor_code varchar(30) not null unique,
    vendor_name varchar(200) not null,
    is_active boolean not null default true
);

create table asset (
    id bigint primary key,
    asset_code varchar(50) not null unique,
    asset_type_id bigint not null references asset_type_mst(id),
    category_s_id bigint not null references asset_category_s_mst(id),
    asset_name varchar(200) not null,
    asset_kind varchar(20) not null,
    status varchar(40) not null,
    vendor_id bigint references vendor_mst(id),
    budget_id bigint references budget(id),
    budget_link_status varchar(20) not null,
    purchase_date date,
    warranty_expiry_date date,
    created_at timestamp not null,
    updated_at timestamp not null,
    check (budget_link_status in ('UNLINKED','LINKED'))
);

create index idx_asset_status_budget_category on asset(status, budget_link_status, category_s_id);

create table asset_attribute_value (
    id bigint primary key,
    asset_id bigint not null unique references asset(id),
    cls_attr_01 varchar(50),
    cls_attr_02 varchar(50),
    cls_attr_03 varchar(50),
    cls_attr_04 varchar(50),
    cls_attr_05 varchar(50),
    person_attr_01 bigint,
    person_attr_02 bigint not null,
    person_attr_03 bigint not null,
    location_attr_01 varchar(100),
    location_attr_02 varchar(100),
    date_attr_01 date,
    date_attr_02 date,
    date_attr_03 date,
    free_text_attr_01 varchar(200),
    free_text_attr_02 varchar(200),
    free_text_attr_03 varchar(500),
    memo_attr_01 text,
    memo_attr_02 text,
    updated_at timestamp not null,
    check (date_attr_03 is null or date_attr_01 is null or date_attr_03 >= date_attr_01)
);

create table asset_attribute_multi_value (
    id bigint primary key,
    asset_id bigint not null references asset(id),
    multi_attr_type varchar(20) not null,
    value varchar(500) not null,
    sort_order int not null default 1,
    created_at timestamp not null,
    check (multi_attr_type in ('MULTI_01','MULTI_02'))
);

create unique index uq_asset_multi_02_value
    on asset_attribute_multi_value(asset_id, multi_attr_type, value)
    where multi_attr_type = 'MULTI_02';

create index idx_asset_multi_sort
    on asset_attribute_multi_value(asset_id, multi_attr_type, sort_order);

create table configuration (
    id bigint primary key,
    config_code varchar(50) not null unique,
    config_name varchar(200) not null,
    status varchar(20) not null,
    created_at timestamp not null,
    updated_at timestamp not null
);

create table configuration_item (
    id bigint primary key,
    configuration_id bigint not null references configuration(id),
    asset_id bigint not null references asset(id),
    role_type varchar(20) not null,
    quantity int not null check (quantity > 0),
    created_at timestamp not null
);

create index idx_configuration_item_conf_asset
    on configuration_item(configuration_id, asset_id);

create table license_pool (
    id bigint primary key,
    license_name varchar(200) not null,
    total_count int not null check (total_count >= 0),
    used_count int not null check (used_count >= 0),
    remaining_count int not null,
    contract_expiry_date date,
    created_at timestamp not null,
    updated_at timestamp not null,
    check (used_count <= total_count),
    check (remaining_count = total_count - used_count)
);

create table license_allocation_history (
    id bigint primary key,
    pool_id bigint not null references license_pool(id),
    asset_id bigint not null references asset(id),
    allocated_count int not null check (allocated_count > 0),
    allocated_at timestamp not null,
    released_at timestamp
);

create index idx_license_allocation_asset on license_allocation_history(asset_id);

create table loan_history (
    id bigint primary key,
    asset_id bigint not null references asset(id),
    borrower_id bigint not null references auth_user(id),
    loaned_at timestamp not null,
    returned_at timestamp
);

create table user_pc_assignment (
    id bigint primary key,
    asset_id bigint not null unique references asset(id),
    user_id bigint not null references auth_user(id),
    os_name varchar(100) not null,
    spec_text varchar(500),
    warranty_expiry_date date,
    updated_at timestamp not null
);

create table maintenance_contract (
    id bigint primary key,
    asset_id bigint not null unique references asset(id),
    vendor_id bigint references vendor_mst(id),
    contract_start_date date,
    contract_end_date date,
    support_level varchar(100),
    updated_at timestamp not null,
    check (contract_end_date is null or contract_start_date is null or contract_end_date >= contract_start_date)
);

create table disposal_history (
    id bigint primary key,
    asset_id bigint not null references asset(id),
    requested_by bigint not null references auth_user(id),
    approved_by bigint references auth_user(id),
    requested_at timestamp not null,
    approved_at timestamp,
    evidence_text text,
    disposal_status varchar(20) not null
);

create table audit_log (
    id bigint primary key,
    target_table varchar(100) not null,
    target_id bigint not null,
    action varchar(30) not null,
    changed_by bigint not null references auth_user(id),
    changed_at timestamp not null,
    change_summary text
);

create table notification_queue (
    id bigint primary key,
    notification_type varchar(50) not null,
    target_user_id bigint references auth_user(id),
    title varchar(200) not null,
    body text not null,
    status varchar(20) not null default 'PENDING',
    scheduled_at timestamp,
    sent_at timestamp,
    created_at timestamp not null,
    check (status in ('PENDING','SENT','FAILED'))
);

create table asset_budget_monitor_daily (
    id bigint primary key,
    monitor_date date not null,
    dept_code varchar(30),
    category_s_id bigint references asset_category_s_mst(id),
    unlinked_count int not null default 0,
    threshold_count int not null default 0,
    is_threshold_exceeded boolean not null default false,
    created_at timestamp not null,
    unique (monitor_date, dept_code, category_s_id)
);

create table dashboard_kpi_daily (
    id bigint primary key,
    kpi_date date not null unique,
    budget_consumption_rate numeric(7,2) not null default 0,
    unlinked_asset_count int not null default 0,
    maintenance_overdue_count int not null default 0,
    inventory_diff_count int not null default 0,
    configuration_completeness_rate numeric(7,2) not null default 0,
    created_at timestamp not null
);

create table inventory_cycle (
    id bigint primary key,
    cycle_code varchar(20) not null unique,
    cycle_year int not null,
    cycle_month int not null,
    status varchar(20) not null,
    started_at timestamp,
    ended_at timestamp,
    created_at timestamp not null,
    check (cycle_month between 1 and 12),
    check (status in ('PLANNED','OPEN','CLOSED'))
);

create table inventory_target_snapshot (
    id bigint primary key,
    cycle_id bigint not null references inventory_cycle(id),
    asset_id bigint not null references asset(id),
    status_at_snapshot varchar(20) not null,
    budget_link_status_at_snapshot varchar(20) not null,
    created_at timestamp not null,
    unique (cycle_id, asset_id)
);

create table inventory_result (
    id bigint primary key,
    cycle_id bigint not null references inventory_cycle(id),
    asset_id bigint not null references asset(id),
    difference_type varchar(20) not null,
    correction_status varchar(20) not null,
    correction_note text,
    registered_by bigint not null references auth_user(id),
    registered_at timestamp not null,
    updated_by bigint references auth_user(id),
    updated_at timestamp,
    check (difference_type in ('MISSING','EXCESS','STATUS_DIFF')),
    check (correction_status in ('OPEN','IN_PROGRESS','DONE')),
    unique (cycle_id, asset_id)
);
