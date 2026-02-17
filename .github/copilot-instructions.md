# Copilot Instructions for account-management-01

このファイルは、本リポジトリで Copilot が常時参照する実行規約である。  
定期監査で運用する項目は `.github/governance-periodic-checks.md` を参照する。

## 0. 規定レベル（MUST / SHOULD / MAY）

- MUST: 必須。未充足は完了不可（原則ブロック）。
- SHOULD: 強く推奨。未実施時は理由を記録しレビュー合意を要する。
- MAY: 任意。状況に応じて採用する。

## 1. 適用範囲

- 対象: 本リポジトリの設計・実装・テスト・ドキュメント作業（MUST）
- 対象者: 開発者、Copilot、レビュー担当者（MUST）

## 2. 優先順位

1. 本ファイル
2. 個別設計書
3. 既存実装慣習

## 3. 設計原則

- Django を前提とする（MUST）。
- 不変原則: `1ユーザー × 1システム × 1権限 = 1申請レコード`（MUST）
- 状態遷移は `workflow_service` 経由のみ許可し、直接 `status` 更新を禁止する（MUST）。
- 認可・テナント境界を破る実装を禁止する（MUST）。

## 4. アーキテクチャと責務

### 4.1 必須3層

- Interface: `views.py`, `templates/`, `forms.py`, `urls.py`（MUST）
- Application: `apps/account_requests/services/*.py`（MUST）
- Domain/Persistence: `models.py`, QuerySet/Manager, migrations（MUST）

依存方向は `Interface -> Application -> Domain/Persistence` のみ許可。逆方向依存・循環依存は禁止。

### 4.2 配置基準（迷ったとき）

- 入力形式/必須チェック: Form（MUST）
- 画面分岐とレスポンス: View（MUST）
- 複数画面で再利用する業務処理: Service（MUST）
- DB絞り込み共通化: QuerySet/Manager（MUST）
- データ一意性/項目制約: Model + DB制約（MUST）

## 5. 実装ガードレール

- View は薄く保ち、業務判断・更新ロジックを持たない（MUST）。
- View にロジックを書かない（MUST）。
- Service 経由で業務処理・更新処理を行う（MUST）。
- View から ORM 直接更新を禁止する（MUST）。
- View の ORM 参照は表示制御に必要な最小限のみ許可する（MUST）。
- 検索/絞り込み/並び替え/ページングは DB 評価優先で実装する（MUST）。
- 早期 `list()` 化による不要な全件実体化を禁止する（MUST）。
- 新規層を増やさない（3層固定）（MUST）。

## 6. セキュリティとドメイン制約

- 認可・テナント境界を破る実装を禁止する（MUST）。
- `raw SQL` は原則禁止。必要時は理由・影響を記録する（MUST）。
- 将来のマルチテナント拡張を壊す設計を禁止する（MUST）。

## 7. テスト方針

- 全業務ロジックにテストを実装する（`pytest` または `Django TestCase`）（MUST）。
- 正常系・異常系を必ず含める（MUST）。
- テスト未整備の機能は未完成として扱う（MUST）。

## 8. 実行プロトコル

### 8.1 実装前

- 影響レイヤを明確化する（MUST）。
- 不変原則・認可・テナント境界への影響を確認する（MUST）。

### 8.2 実装後（完了条件）

- [ ] YES / [ ] NO: テストを作成・更新した
- [ ] YES / [ ] NO: `ai/decision_log.md` を更新した（設計判断）
- [ ] YES / [ ] NO: `ai/todo.md` に作業実行メモを更新した
- [ ] YES / [ ] NO: `ai/todo.md` の進捗を更新した
- [ ] YES / [ ] NO: 規約違反の自己点検を実施した
- [ ] YES / [ ] NO: 必要な改善提案を提示した

## 9. 変更管理

- 作業実行前にタスクを `ai/todo.md` に記録する（MUST）。
- 設計・構造変更は必ず `ai/decision_log.md` に記録する（MUST）。
- 作業実行後はタスクを `ai/todo.md` から`ai/done.md`に移動する（MUST）。

## 10. 禁止事項

- View から直接 DB 更新（MUST）
- 記録なしの構造変更（MUST）
- テスト削除（MUST）
- ワークフロー定義の直接改変（理由・合意なし）（MUST）
- テスト維持のみを目的とした互換コード追加（MUST）

## 11. 改善提案

- 設計重複、レイヤ違反、テスト不足、将来拡張阻害、パフォーマンス懸念を検出した場合、改善提案を提示する（MUST）。
- 提案フォーマット: 改善提案 / 理由 / 影響範囲 / 実施難易度（低・中・高）
- 提出先: PR説明、または `ai/decision_log.md` / `ai/todo.md` の当該作業記録（MUST）

## 12. 定期監査への委譲

以下は常時読み込み対象から外し、定期チェックと是正で運用する。

- 一覧系の測定基準・クエリ予算
- テスト実行パフォーマンス運用
- 規約例外の詳細管理（失効日、オーナー、解消タスク）
- 互換コードの棚卸し
- 用語定義・改定履歴

詳細は `.github/governance-periodic-checks.md` を参照する。
