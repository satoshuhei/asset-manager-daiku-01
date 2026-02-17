# 資産管理システム 詳細設計書（API）

## 0. 文書情報
- 文書名: 資産管理システム 詳細設計書（API）
- 版数: v0.3（ドラフト）
- 作成日: 2026-02-17
- 前提: Django + 認証済セッション

## 1. 共通仕様
- ベースパス: `/api/v1`
- 形式: `application/json`
- 認可: ロールベース（閲覧者/編集者/承認者/管理者）
- 日付形式: `YYYY-MM-DD`
- ページング: `page`, `page_size`（既定50）
- ソート: `sort`（例: `-updated_at`）

## 1.1 認証方針
- 認証方式は Django Session Authentication を利用する
- ログインAPIは `/api/v1/auth/login` を提供し、内部で Django 標準認証（`authenticate`/`login`）を呼び出す
- ログアウトAPIは `/api/v1/auth/logout` を提供し、内部で Django 標準 `logout` を呼び出す
- ユーザ登録/変更/無効化は Django 管理画面のみで実施する
- 業務APIとしてユーザ自己登録エンドポイントは提供しない

## 2. エラー仕様
| HTTP | コード | 意味 |
|---|---|---|
| 400 | VALIDATION_ERROR | 入力不正 |
| 401 | UNAUTHORIZED | 未認証 |
| 403 | FORBIDDEN | 権限不足 |
| 404 | NOT_FOUND | 対象なし |
| 409 | CONFLICT | 整合性違反 |
| 422 | DOMAIN_RULE_VIOLATION | 業務ルール違反 |

## 2.1 認証API
### 2.1.1 ログイン
- `POST /auth/login`
- Request:
```json
{
  "username": "admin01",
  "password": "********"
}
```
- Response（成功時）:
```json
{
  "result": "ok"
}
```
- Response（失敗時）:
```json
{
  "code": "AUTH_FAILED",
  "message": "ユーザIDまたはパスワードが不正です"
}
```
- 備考:
  - 連続失敗5回で15分ロック（`423 LOCKED`）

### 2.1.2 ログアウト
- `POST /auth/logout`

### 2.1.3 禁止事項
- `POST /auth/register` は提供しない

## 2.2 監査ログAPI
### 2.2.1 監査ログ一覧取得
- `GET /audit-logs`
- Query: `target_table`, `action`, `changed_by`, `from`, `to`, `page`, `page_size`
- 権限: 承認者/管理者

### 2.2.2 監査ログ詳細取得
- `GET /audit-logs/{log_id}`
- 権限: 承認者/管理者

## 3. 資産API
### 3.1 資産一覧取得
- `GET /assets`
- Query: `asset_code`, `asset_name`, `category_s_id`, `status`, `budget_link_status`, `person_attr_01`, `page`, `page_size`
- Response（抜粋）:
```json
{
  "count": 120,
  "results": [
    {
      "id": 101,
      "asset_code": "AS-0001",
      "asset_name": "開発PC-01",
      "status": "IN_USE",
      "budget_link_status": "UNLINKED"
    }
  ]
}
```

### 3.2 資産詳細取得
- `GET /assets/{asset_id}`
- Response: 基本情報 + 属性20 + 1:n属性 + 予算紐付け

### 3.3 資産登録
- `POST /assets`
- Request（抜粋）:
```json
{
  "asset_code": "AS-0002",
  "asset_name": "デバッガA",
  "asset_type_id": 2,
  "category_s_id": 31,
  "status": "IN_USE",
  "budget_id": null,
  "budget_link_status": "UNLINKED",
  "attributes": {
    "cls_attr_01": "HW",
    "person_attr_02": 501,
    "date_attr_01": "2026-02-01",
    "memo_attr_01": "初期導入"
  },
  "multi_attributes": [
    {"multi_attr_type": "MULTI_01", "value": "保守オプションA", "sort_order": 1}
  ]
}
```
- バリデーション:
  - `asset_code` 一意
  - `category_s_id` 必須
  - PC種別時は `person_attr_01` 必須

### 3.4 資産更新
- `PUT /assets/{asset_id}`
- 備考: ステータス変更は `workflow_service` 経由の内部処理で更新

### 3.5 予算後付け紐付け
- `PATCH /assets/{asset_id}/budget-link`
- Request:
```json
{
  "budget_id": 9001,
  "budget_link_status": "LINKED"
}
```

## 4. 構成API
### 4.1 構成一覧
- `GET /configurations`

### 4.2 構成登録
- `POST /configurations`
- Request（抜粋）:
```json
{
  "config_code": "CFG-001",
  "config_name": "開発セットA",
  "items": [
    {"asset_id": 101, "role_type": "device", "quantity": 1},
    {"asset_id": 205, "role_type": "license", "quantity": 1}
  ]
}
```
- バリデーション: 廃棄済資産は追加不可

## 5. 予算API
### 5.1 予算一覧
- `GET /budgets`

### 5.2 予算登録
- `POST /budgets`
- Request（抜粋）:
```json
{
  "fiscal_year": 2026,
  "budget_category": "開発投資",
  "budget_category_l_id": 10,
  "budget_category_m_id": 101,
  "budget_category_s_id": 1011,
  "planned_amount": 1200000.00,
  "attributes": {
    "cls_attr_01": "HW",
    "person_attr_02": 501,
    "date_attr_01": "2026-04-01",
    "memo_attr_01": "年度初回登録"
  },
  "multi_attributes": [
    {"multi_attr_type": "MULTI_01", "value": "補足情報A", "sort_order": 1},
    {"multi_attr_type": "MULTI_02", "value": "関連識別子-001", "sort_order": 1}
  ]
}
```
- バリデーション:
  - 予算分類は `大分類/中分類/小分類` の3階層を必須入力
  - 属性情報は20属性（カテゴリ内訳付き）を定義し、`attributes` で受領
  - 1:n情報（2項目）は別テーブル管理とし、`multi_attributes` で複数行を許容

### 5.3 執行済予算登録
- `POST /budgets/{budget_id}/executions`

### 5.4 予算属性（1:n）更新
- `PUT /budgets/{budget_id}`
- 備考:
  - `multi_attributes` は全置換または差分更新で複数行保持する
  - `multi_attr_type='MULTI_02'` は同一予算内で重複不可

## 6. ライセンスAPI
### 6.1 ライセンスプール一覧
- `GET /license-pools`

### 6.2 割当登録
- `POST /license-pools/{pool_id}/allocations`
- バリデーション: `used_count <= total_count`

## 6.5 PC管理API
### 6.5.1 PC割当一覧
- `GET /pc-assignments`

### 6.5.2 PC割当登録
- `POST /pc-assignments`
- バリデーション:
  - PC種別資産のみ登録可
  - `asset_id` は同時に1利用者のみ割当可

## 7. 棚卸API
### 7.1 棚卸結果登録
- `POST /inventories/{inventory_id}/results`

### 7.2 差異是正更新
- `PATCH /inventories/{inventory_id}/results/{result_id}`

## 7.5 CSV API
### 7.5.1 資産CSVエクスポート
- `GET /assets/export-csv`

### 7.5.2 資産CSVインポート
- `POST /assets/import-csv`
- Request: `multipart/form-data`（`file` 必須）
- Response: `imported`, `errors`（行番号・項目・メッセージ）

## 7.1 廃棄API
### 7.1.1 廃棄申請登録
- `POST /disposals`

### 7.1.2 廃棄申請一覧
- `GET /disposals`

### 7.1.3 廃棄承認
- `PATCH /disposals/{disposal_id}/approve`
- Request:
```json
{
  "approved": true,
  "evidence_text": "データ消去証跡ID: WIPE-2026-001"
}
```
- バリデーション: `approved=true` の場合 `evidence_text` 必須

### 7.1.4 廃棄差戻し
- `PATCH /disposals/{disposal_id}/reject`
- Request:
```json
{
  "reason": "証跡不足のため差戻し"
}
```

## 8. 監査・ログ
- 主要更新APIは監査イベントを記録する
- 対象: 資産登録/更新、予算紐付け、構成更新、廃棄承認

## 9. 将来拡張
- 外部連携API（会計、ID管理）は `/api/v2` で分離予定

## 10. 機能・画面・API対応
| 機能ID | 画面ID | 主API |
|---|---|---|
| F-00 | SCR-000 | `POST /auth/login`, `POST /auth/logout` |
| F-01 | SCR-001 | `GET /budgets`, `GET /audit-logs`, `GET /assets`（集計表示用） |
| F-02 | SCR-010, SCR-011 | `GET /assets`, `GET /assets/{asset_id}`, `POST /assets`, `PUT /assets/{asset_id}`, `PATCH /assets/{asset_id}/budget-link` |
| F-03 | SCR-020 | `GET /configurations`, `POST /configurations` |
| F-04 | SCR-030 | `GET /budgets`, `POST /budgets`, `POST /budgets/{budget_id}/executions` |
| F-05 | SCR-040 | `GET /license-pools`, `POST /license-pools/{pool_id}/allocations` |
| F-06 | SCR-050 | `GET /pc-assignments`, `POST /pc-assignments` |
| F-07 | SCR-060 | `POST /inventories/{inventory_id}/results`, `PATCH /inventories/{inventory_id}/results/{result_id}` |
| F-08 | SCR-070 | `POST /disposals`, `GET /disposals`, `PATCH /disposals/{disposal_id}/approve`, `PATCH /disposals/{disposal_id}/reject` |
| F-09 | SCR-080 | `GET /audit-logs`, `GET /audit-logs/{log_id}` |
