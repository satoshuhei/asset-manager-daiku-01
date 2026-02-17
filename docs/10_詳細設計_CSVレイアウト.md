# 資産管理システム 詳細設計書（CSVレイアウト）

## 0. 文書情報
- 文書名: 資産管理システム 詳細設計書（CSVレイアウト）
- 版数: v0.1（ドラフト）
- 作成日: 2026-02-17
- 文字コード: UTF-8（BOMなし）
- 区切り文字: `,`
- 改行: LF

## 1. 共通仕様
- ヘッダ行は必須
- 日付形式は `YYYY-MM-DD`
- 空値は空文字
- 文字列の前後空白はトリム
- インポート時は業務バリデーションを適用

## 2. 資産エクスポート（CSV-EXP-001）
### 2.1 レイアウト
| No | 項目名 | 物理名 | 型 | 必須 | 備考 |
|---:|---|---|---|---|---|
| 1 | 資産コード | asset_code | varchar(50) | 必須 | 一意 |
| 2 | 資産名 | asset_name | varchar(200) | 必須 | - |
| 3 | 大分類コード | category_l_code | varchar(20) | 必須 | - |
| 4 | 中分類コード | category_m_code | varchar(20) | 必須 | - |
| 5 | 小分類コード | category_s_code | varchar(20) | 必須 | - |
| 6 | ステータス | status | varchar(20) | 必須 | - |
| 7 | 予算紐付け状態 | budget_link_status | varchar(20) | 必須 | UNLINKED/LINKED |
| 8 | 予算ID | budget_id | bigint | 任意 | 後付け可 |
| 9 | 利用者 | person_attr_01 | bigint | 条件付必須 | PC時必須 |
| 10 | 管理責任者 | person_attr_02 | bigint | 必須 | - |
| 11 | 設置場所 | location_attr_01 | varchar(100) | 任意 | - |
| 12 | 保管場所 | location_attr_02 | varchar(100) | 任意 | - |
| 13 | 購入日 | date_attr_01 | date | 任意 | - |
| 14 | 利用開始日 | date_attr_02 | date | 任意 | - |
| 15 | 期限日 | date_attr_03 | date | 任意 | 購入日以降 |
| 16 | 製品型番 | free_text_attr_01 | varchar(200) | 任意 | - |
| 17 | 識別ラベル | free_text_attr_02 | varchar(200) | 任意 | - |
| 18 | 補足説明 | free_text_attr_03 | varchar(500) | 任意 | - |
| 19 | 運用メモ | memo_attr_01 | text | 任意 | 2000字以内 |
| 20 | 監査メモ | memo_attr_02 | text | 任意 | 2000字以内 |

## 3. 資産インポート（CSV-IMP-001）
### 3.1 用途
- 初期移行
- 一括更新（許可ロールのみ）

### 3.2 バリデーション
- 資産コード重複不可
- 分類階層整合必須
- `date_attr_03 >= date_attr_01`
- `budget_link_status='LINKED'` の場合 `budget_id` 必須

### 3.3 エラーファイル
- 行番号、項目名、エラーコード、メッセージを出力

## 4. 1:n属性インポート（CSV-IMP-002）
### 4.1 レイアウト
| No | 項目名 | 物理名 | 型 | 必須 | 備考 |
|---:|---|---|---|---|---|
| 1 | 資産コード | asset_code | varchar(50) | 必須 | 親資産参照 |
| 2 | 属性種別 | multi_attr_type | varchar(20) | 必須 | MULTI_01/MULTI_02 |
| 3 | 値 | value | varchar(500) | 必須 | - |
| 4 | 表示順 | sort_order | int | 任意 | 既定1 |

### 4.2 バリデーション
- `multi_attr_type='MULTI_02'` は同一資産内重複不可
- 親資産が存在しない行はエラー

## 5. 予算/執行済予算エクスポート（CSV-EXP-002）
| No | 項目名 | 物理名 | 型 | 必須 |
|---:|---|---|---|---|
| 1 | 年度 | fiscal_year | int | 必須 |
| 2 | 予算科目 | budget_category | varchar(100) | 必須 |
| 3 | 予算額 | planned_amount | numeric(18,2) | 必須 |
| 4 | 執行済日 | executed_date | date | 任意 |
| 5 | 執行済金額 | executed_amount | numeric(18,2) | 任意 |
| 6 | プロジェクトコード | project_code | varchar(30) | 必須 |

## 6. 運用ルール
- インポートは事前にプレビュー（件数/エラー）を表示
- 本取込は承認者または管理者のみ
- 取込結果は監査ログへ保存

## 7. バッチ連携
- BAT-002（未紐付け資産監視）で検出した対象は、必要に応じて `CSV-EXP-001` で出力し是正対象を共有する
- BAT-003（KPI集計）で利用する未紐付け件数は、CSV取込結果の最新状態を前提に集計する
- BAT-004（月次棚卸対象生成）実行前は、必要に応じて `CSV-IMP-001` による最新台帳反映を完了させる
