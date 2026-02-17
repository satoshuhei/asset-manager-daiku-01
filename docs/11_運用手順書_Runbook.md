# 資産管理システム 運用手順書（Runbook）

## 1. 日次運用
- 保守期限通知バッチ: `python manage.py run_maintenance_notification_batch`
- 未紐付け資産監視バッチ: `python manage.py run_unlinked_asset_monitor_batch --threshold 10`
- KPI集計バッチ: `python manage.py run_dashboard_kpi_batch`

## 2. 月次運用
- 棚卸回を作成後、対象スナップショット生成:
  - `python manage.py run_inventory_snapshot_batch <cycle_id>`

## 3. CSV運用
- エクスポート: `GET /api/v1/assets/export-csv`
- インポート: `POST /api/v1/assets/import-csv`（multipart、`file` 必須）
- インポート結果は `imported` と `errors` を確認し、エラー行を再投入する

## 4. 監視ポイント
- 監視テーブル: `asset_budget_monitor_daily`, `dashboard_kpi_daily`
- 通知キュー: `notification_queue` の `PENDING` / `FAILED` 件数を確認
- 監査ログ: `audit_log` で重要操作（CREATE/UPDATE/UPSERT）を確認

## 5. 障害時対応
- バッチ失敗時はコマンドを再実行し、失敗時刻の監査ログを確認
- CSV取込エラーは `errors` の行番号・メッセージで修正
- 業務整合性エラー（422）は Service層バリデーション違反のため入力データを見直す

## 6. テスト実行パフォーマンス運用（定期監査）
- 反復開発（差分優先）:
  - `python manage.py test apps.account_requests.tests.PerformanceGovernanceTests --parallel 4 --durations 5`
- 全体回帰（PR前・マージ前）:
  - `python manage.py test --parallel 4 --durations 10`
- 変更影響確認（feature単位）:
  - `python manage.py test apps.account_requests.tests.<対象TestClass> --durations 10`
- 運用ルール:
  - ローカル全体実行の既定は `--parallel 4` とする
  - 遅延調査は `--durations` を必須併用し、上位遅延テストを記録する
  - 重いテスト追加時は、分割・共通化・Service単体化の軽量化案を同時提示する
  - `manage.py test` 実行時は高速ハッシュ設定（`MD5PasswordHasher`）を適用する
  - Web/APIテストでログイン状態のみ必要な場合は `force_login` を優先し、不要な認証I/Oを避ける

## 7. 規約例外/互換コードの管理
- 規約例外が必要な場合は実装前に `ai/decision_log.md` へ以下を記録する:
  - 例外理由 / 影響範囲 / 暫定・恒久 / 解消方針と期限 / オーナー / `ai/todo.md` タスクID / 失効日
- 互換コードを残す場合は、理由・期限・削除タスクを必須とし、四半期ごとに削除可否を `ai/todo.md` へ記録する

## 8. 定期レビュー頻度
- 週次: 変更点の軽量確認（10分）
- 月次: 性能・例外・互換コードの本監査（30〜60分）
- リリース前: 重点監査（必須）

## 9. 月次監査テンプレート
- 実施時は `docs/19_月次監査実行テンプレート.md` を複製して使用する
- 実施後は監査結果文書と `ai/decision_log.md` / `ai/todo.md` を更新する
