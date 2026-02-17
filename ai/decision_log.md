# Decision Log

## 2026-02-17
- 対象: 資産管理システム To-Be業務設計・要件定義ドラフト作成
- 判断:
  - 用語を `執行予算` ではなく `執行済予算` に統一する
  - 予算/執行済予算と資産の紐付けは必須ではなく後付け可能とする
  - 予算紐付け不明の資産も管理対象に含める
- 理由:
  - 現場実態として予算情報未確定の資産が存在し、登録禁止だと台帳欠損を招くため
  - 段階的整備を許容しつつ、未紐付け可視化で統制を維持するため
- 影響:
  - データ整合性要件を「登録時必須」から「未紐付け許容 + 状態管理」に変更
  - ダッシュボード/KPIに未紐付け資産の監視指標を追加

## 2026-02-17（追加）
- 対象: 画面遷移図（最小）とER案（最小）の文書化
- 判断:
  - 画面遷移はダッシュボード起点の最小導線に限定する
  - ERは `asset` 中心の統合モデルとし、有形/無形を同一テーブルで扱う
  - 予算紐付けは `asset.budget_id` のNULL許容で後付け要件を満たす
- 理由:
  - 初版は過不足なく実装起点を作ることを優先し、過剰な画面分割を避けるため
  - 構成管理と予算後付けの両要件を矛盾なく表現するため
- 影響:
  - `docs/asset-management-screen-flow.md` を追加
  - `docs/asset-management-er-draft.md` を追加

## 2026-02-17（追加2）
- 対象: 資産管理対象データ（分類3階層/属性20）の要件反映
- 判断:
  - 資産分類は `大分類/中分類/小分類` の3階層を必須管理とする
  - 属性情報は 20 属性をカテゴリ内訳付きで明示する
  - 1:n情報（2項目）は別テーブルで保持し、資産に複数行を許容する
- 理由:
  - 現場運用で分類粒度が必要であり、分類の曖昧さを防止するため
  - 単一値属性と複数値属性を分離し、将来拡張と整合性を両立するため
- 影響:
  - `docs/asset-management-tobe-requirements.md` を v0.2 に更新
  - `docs/asset-management-er-draft.md` に分類階層/属性保持モデルを追加

## 2026-02-17（追加3）
- 対象: 属性20の項目名・型・必須/任意・入力規則の明文化
- 判断:
  - 属性20を固定コード（`*_attr_*`）で定義し、要件書で管理する
  - 人属性は利用者マスタ参照（FK）を基本とする
  - 1:n情報2項目は別表（複数行）前提で定義する
- 理由:
  - 画面仕様/移行仕様/DDL草案に接続可能な粒度へ引き上げるため
  - 将来の項目名変更があってもコード基準で互換性を担保するため
- 影響:
  - `docs/asset-management-tobe-requirements.md` を v0.3 に更新
  - 属性20の定義表を追加

## 2026-02-17（追加4）
- 対象: 要件定義/基本設計の文書分離
- 判断:
  - 業務・機能・非機能・データ要件を `要件定義書` として独立させる
  - 実装方針・画面/データ/処理/権限を `基本設計書` として独立させる
  - 既存の画面遷移図・ER案を参照資産として再利用する
- 理由:
  - 工程境界（要件定義/基本設計）を明確化し、レビュー観点を分離するため
  - 以後の詳細設計・実装へのトレーサビリティを確保するため
- 影響:
  - `docs/asset-management-requirements-definition.md` を新規作成
  - `docs/asset-management-basic-design.md` を新規作成

## 2026-02-17（追加5）
- 対象: 詳細設計（画面項目/API/論理DDL）の初版作成
- 判断:
  - 詳細設計は `画面項目定義` `API` `DDL` の3文書に分離する
  - 画面項目は属性コード基準で定義し、要件表とのトレースを可能にする
  - DDL草案は要件制約（後付け予算、属性20、1:n属性、主要整合性）をDDL制約へ反映する
- 理由:
  - 実装着手時に参照する粒度を揃え、レビュー効率を上げるため
  - 設計変更時の影響範囲を文書単位で限定するため
- 影響:
  - `docs/asset-management-detail-screen-items.md` を新規作成
  - `docs/asset-management-detail-api.md` を新規作成
  - `docs/asset-management-logical-ddl-draft.sql` を新規作成

## 2026-02-17（追加6）
- 対象: 要件定義におけるアクター/ユースケース整理
- 判断:
  - 要件定義書にアクター定義を追加する
  - ユースケース（事前条件/成功条件）を追加する
  - ユースケースと機能要件の対応表を追加する
- 理由:
  - 要件レビューで業務視点の漏れを早期検出するため
  - 機能要件とのトレーサビリティを明示するため
- 影響:
  - `docs/asset-management-requirements-definition.md` を v1.1 に更新

## 2026-02-17（追加7）
- 対象: 要件/詳細設計の継続具体化
- 判断:
  - 要件定義書にユースケース詳細フロー（基本/代替/例外）を追加する
  - 期限通知・未紐付け監視を中心とするバッチ詳細設計を追加する
  - インポート/エクスポートのCSVレイアウト詳細を追加する
- 理由:
  - 実装前に業務シナリオと夜間運用・データ連携仕様を確定するため
  - 画面/API/DDLだけでは不足する運用仕様を補完するため
- 影響:
  - `docs/asset-management-requirements-definition.md` を v1.2 に更新
  - `docs/asset-management-detail-batch.md` を新規作成
  - `docs/asset-management-detail-csv-layout.md` を新規作成
  - `docs/asset-management-basic-design.md` の成果物連携を更新

## 2026-02-17（追加8）
- 対象: 認証（ログイン）要件の追加
- 判断:
  - 全業務画面/APIをログイン必須とする
  - ユーザ登録/変更/無効化は Django 管理画面でシステム管理者が実施する
  - 業務機能としてのユーザ自己登録API/画面は提供しない
- 理由:
  - 運用方針（管理者による統制）を要件へ明示し、実装ブレを防ぐため
- 影響:
  - `docs/asset-management-requirements-definition.md` を v1.3 に更新
  - `docs/asset-management-basic-design.md` に認証/ユーザ管理構成を追加
  - `docs/asset-management-detail-screen-items.md` にログイン画面定義を追加
  - `docs/asset-management-detail-api.md` に認証API方針を追加

## 2026-02-17（追加9）
- 対象: 工程ドキュメント不足点の是正
- 判断:
  - 要件定義の未展開ユースケース（UC-00/UC-12）に詳細フローを追加する
  - 要件定義のトレーサビリティにバッチ/CSV詳細を追加する
  - 基本設計の権限設計を機能単位マトリクスまで詳細化する
  - API認証方針を「Django認証呼び出しのラッパーAPI」として明文化する
  - バッチ出力先テーブルを論理DDLへ追加する
- 理由:
  - 要件〜詳細設計のトレーサビリティ欠落と実装解釈の曖昧さを解消するため
- 影響:
  - `docs/asset-management-requirements-definition.md` を v1.4 に更新
  - `docs/asset-management-basic-design.md` を v1.1 に更新
  - `docs/asset-management-detail-api.md` を v0.2 に更新
  - `docs/asset-management-logical-ddl-draft.sql` にバッチ関連テーブルを追加

## 2026-02-17（追加10）
- 対象: 実装着手前の残課題（認証/廃棄/監査/棚卸）解消
- 判断:
  - 要件定義に認証非機能（タイムアウト/ロック/CSRF）を追加する
  - APIに監査ログ取得と廃棄承認/差戻しエンドポイントを追加する
  - 画面項目に廃棄承認画面と監査ログ閲覧画面を追加する
  - DDLに棚卸結果テーブルを追加し、ユーザ参照を `auth_user` FKで明示する
- 理由:
  - ユースケースと詳細設計の実装ギャップを解消するため
- 影響:
  - `docs/asset-management-requirements-definition.md` を v1.5 に更新
  - `docs/asset-management-detail-screen-items.md` を v0.2 に更新
  - `docs/asset-management-detail-api.md` を拡張（監査/廃棄API）
  - `docs/asset-management-logical-ddl-draft.sql` を v0.2 に更新

## 2026-02-17（追加11）
- 対象: Django 実装の初期構築（MVP）
- 判断:
  - Djangoプロジェクトを新規作成し、`apps.account_requests` を中核アプリとして実装する
  - Interface層（API View）から更新処理を直接実行せず、Service層（`apps/account_requests/services`）経由へ統一する
  - 認証はSession認証を採用し、ログインロック（連続失敗5回で15分）とセッション制御（30分無操作 + 8時間上限）を実装する
  - 主要業務モデル（資産/属性/予算/廃棄/棚卸/監査）を実装し、要件定義の業務ルールをテストで担保する
- 理由:
  - 既存リポジトリにアプリ実装が存在せず、仕様をコードへ落とすための実行基盤が必要だったため
  - 規約の3層責務分離とテスト必須要件を満たすため
- 影響:
  - `config/settings.py`, `config/urls.py`, `config/middleware.py` を追加/更新
  - `apps/account_requests` 配下に models/services/serializers/views/urls/admin/forms/tests を実装
  - マイグレーション `apps/account_requests/migrations/0001_initial.py` を作成
  - `manage.py test` で5件成功

## 2026-02-17（追加12）
- 対象: Interface層（テンプレート画面）の実装
- 判断:
  - Web画面ルーティングを API と分離し、`web_urls.py` で管理する
  - ログインは Django 標準 `AuthenticationForm` + `LoginView` を利用する
  - 主要画面（ダッシュボード/資産一覧/資産詳細/廃棄承認/監査ログ）をテンプレートで実装し、他画面はプレースホルダで接続する
- 理由:
  - 設計文書に定義した Interface 層を実装し、ログイン後導線を検証可能にするため
- 影響:
  - `apps/account_requests/web_views.py`, `apps/account_requests/web_urls.py` を追加
  - `templates/account_requests/*.html` を追加
  - `config/urls.py`, `config/settings.py` を更新
  - `manage.py test` で8件成功

## 2026-02-17（追加13）
- 対象: 残機能（構成管理/予算実績/ライセンス割当）のAPI実装拡張
- 判断:
  - 追加済みService（configuration/budget/license/inventory）をDRF APIへ正式接続する
  - 構成・予算・ライセンスは一覧/作成を基本とし、割当上限制約や廃棄資産禁止などの業務制約はService層で検証する
  - 棚卸結果の作成・更新はView直保存を廃止し、inventory_service経由へ統一する
- 理由:
  - 3層責務分離（View薄化、業務更新はService集約）を維持しつつ、未実装だった要件機能をAPIで利用可能にするため
- 影響:
  - `apps/account_requests/serializers.py` に構成/予算/執行済予算/ライセンス用シリアライザを追加
  - `apps/account_requests/views.py` に新規API Viewを追加し、inventory APIをService呼び出しへ変更
  - `apps/account_requests/urls.py` に `configurations` `budgets/*/executions` `license-pools/*/allocations` を追加
  - `apps/account_requests/migrations/0002_dashboardkpidaily_licensepool_and_more.py` を生成
  - `apps/account_requests/tests.py` に拡張APIの正常/異常ケースを追加し、`manage.py test` 11件成功

## 2026-02-17（追加14）
- 対象: 実装計画のマイルストン定義
- 判断:
  - 要件定義書に実装マイルストン（M1〜M6）を追加し、完了条件と現状ステータスを明示する
  - 直近実装は M5（画面機能拡張）→ M6（運用連携・受入）の順で進める
- 理由:
  - 実装完了までの進捗管理軸を明確化し、残作業の優先順位を共有するため
- 影響:
  - `docs/asset-management-requirements-definition.md` に「12. 実装マイルストン」を追加

## 2026-02-17（追加15）
- 対象: ローカル動作確認の準備自動化
- 判断:
  - デモユーザー/最小業務データを投入する管理コマンド `seed_demo_data` を追加する
  - ローカル検証は `migrate` 後に `seed_demo_data` 実行、`runserver` 起動を標準手順とする
- 理由:
  - 動作確認の初期セットアップを短時間で再現可能にし、検証開始までの手間を下げるため
- 影響:
  - `apps/account_requests/management/commands/seed_demo_data.py` を追加
  - ローカルDBにデモユーザー（admin/editor/approver）と基礎データを投入可能にした

## 2026-02-18（追加16）
- 対象: ドキュメント命名規則の変更
- 判断:
  - `docs` 配下ファイルを工程別の日本語連番（01〜12）に統一する
  - 参照リンクは新ファイル名へ更新し、参照切れを防止する
- 理由:
  - 文書の工程順を明確化し、閲覧順と管理性を高めるため
- 影響:
  - `docs` の12ファイルを日本語連番名へリネーム
  - `02_要件定義書.md`, `03_基本設計書.md`, `06_詳細設計_画面項目定義.md`, `09_詳細設計_バッチ設計.md` の参照パスを更新

## 2026-02-18（追加17）
- 対象: todo未完了項目の完了対応（文書整合/移行/帳票/UAT）
- 判断:
  - 連続文書ペア（01↔02〜11↔12）のMECEチェック結果を記録し、情報拡充で是正する
  - 移行・帳票・受入基準・UAT実施結果を独立文書として追加し、トレーサビリティを補強する
- 理由:
  - 工程間の抜け漏れを防ぎ、運用移行時の判断材料を揃えるため
- 影響:
  - `docs/13_文書整合MECEチェック記録.md` を追加
  - `docs/14_移行項目マッピング表.md` を追加
  - `docs/15_帳票レイアウト定義.md` を追加
  - `docs/16_受入基準詳細_UAT観点定義.md` を追加
  - `docs/17_UAT実施記録.md` を追加
  - `02_要件定義書.md` / `03_基本設計書.md` の参照一覧を更新

## 2026-02-17（追加15）
- 対象: M5/M6 の実装完了（画面機能拡張・CSV・バッチ・運用文書）
- 判断:
  - プレースホルダ画面を廃止し、構成/予算/ライセンス/PC/棚卸を実データ画面へ置換する
  - CSVは API（エクスポート/インポート）として提供し、取込結果に行別エラーを返す
  - バッチは Django 管理コマンドとして実行可能にし、日次3種+棚卸スナップショットを実装する
  - 運用手順書とUATチェックリストを追加し、受入観点を文書化する
- 理由:
  - 「すべての実装完了」要求に対し、M5/M6 の未着手項目をコードと運用文書の両面でクローズするため
- 影響:
  - `apps/account_requests/web_views.py`, `apps/account_requests/web_urls.py` を拡張
  - `apps/account_requests/views.py`, `apps/account_requests/urls.py`, `apps/account_requests/serializers.py` にCSV/PC APIを追加
  - `apps/account_requests/services/pc_service.py`, `csv_service.py`, `batch_service.py` を追加
  - `apps/account_requests/management/commands/*.py` を追加
  - `templates/account_requests/*` に実画面テンプレートを追加
  - `docs/asset-management-operation-runbook.md`, `docs/asset-management-uat-checklist.md` を追加
  - `manage.py test` 14件成功

## 2026-02-18（追加18）
- 対象: `.github/governance-periodic-checks.md` に基づく定期監査と是正
- 判断:
  - 一覧系性能はクエリ予算テストで継続監視する
  - ローカル全体テストは `--parallel 4` を標準とし、遅延調査時は `--durations` を必須併用する
  - 規約例外/互換コードは今回「新規なし」とし、記録テンプレートと点検頻度を Runbook に明文化する
- 理由:
  - 定期監査項目（性能・運用・例外・互換・頻度）を実測可能かつ再現可能な運用に固定するため
- 影響:
  - `apps/account_requests/tests.py` に `PerformanceGovernanceTests` を追加（固定条件 + クエリ予算）
  - `docs/11_運用手順書_Runbook.md` に並列実行・durations・例外/互換・頻度ルールを追記
  - `docs/18_定期監査結果_2026-02-18.md` を追加（実測値と是正結果を記録）
  - 基準変更は行っていないため、基準変更ログは未発生

## 2026-02-18（追加19）
- 対象: 月次監査の再現性向上（テンプレート標準化）
- 判断:
  - 月次監査は実行テンプレートを正本化し、同一フォーマットで継続記録する
  - Runbook と監査結果文書からテンプレートへ参照可能にする
- 理由:
  - 実施者差分による記録粒度のばらつきを防止し、前月比較を容易にするため
- 影響:
  - `docs/19_月次監査実行テンプレート.md` を追加
  - `docs/11_運用手順書_Runbook.md` にテンプレート利用手順を追記
  - `docs/18_定期監査結果_2026-02-18.md` に次回実行テンプレート参照を追記

## 2026-02-18（追加20）
- 対象: 月次監査結果の初回YYYY-MM版作成
- 判断:
  - テンプレート運用の初回実績として `2026-02` の月次版を作成する
  - 日次監査結果（18）をソースとし、月次比較可能なフォーマットに統一する
- 理由:
  - テンプレートだけでなく実体ファイルを先行作成し、次回以降の複製運用を容易にするため
- 影響:
  - `docs/20_月次監査結果_2026-02.md` を追加
  - `docs/19_月次監査実行テンプレート.md` に初回作成例の参照を追記
  - `docs/18_定期監査結果_2026-02-18.md` に月次集約版の参照を追記

## 2026-02-18（追加21）
- 対象: `01→10` 文書連鎖の反映漏れ精査と是正
- 判断:
  - 連鎖精査で確認した反映漏れは、最小差分で後続文書へ追記して整合を取る
  - 完了ログは `ai/done.md` を日付要約+詳細リンク形式へ再編し、今後の運用記録を簡素化する
- 理由:
  - 文書間トレーサビリティの抜けを防ぎ、レビュー時の追跡性を高めるため
- 影響:
  - `docs/02_要件定義書.md` に無形資産のフローティングライセンス記載を補完
  - `docs/03_基本設計書.md` に利用/貸出管理モジュールを追記
  - `docs/04_画面遷移図.md` に廃棄承認/監査ログ画面と遷移を追記
  - `docs/07_詳細設計_API設計.md` にPC管理APIとCSV APIを追記
  - `docs/09_詳細設計_バッチ設計.md` にDDLテーブル名レベルの入出力対応を追記
  - `docs/10_詳細設計_CSVレイアウト.md` にバッチ連携章を追記
  - `ai/done.md` を日付要約+詳細リンク形式へ更新

## 2026-02-18（追加22）
- 対象: 機能に対応する画面設計の追記と詳細設計以降への反映
- 判断:
  - 基本設計書に機能ID（F-00〜F-09）と画面ID（SCR-000〜SCR-080）の対応表を追加する
  - 詳細設計以降は同一IDを用いてトレーサビリティを揃える
- 理由:
  - 機能要件→画面設計→API/UATの追跡を明確にし、設計レビュー時の整合確認を容易にするため
- 影響:
  - `docs/03_基本設計書.md` に「機能と画面の対応」を追加
  - `docs/06_詳細設計_画面項目定義.md` に機能対応トレーサビリティ章を追加
  - `docs/07_詳細設計_API設計.md` に機能・画面・API対応表を追加
  - `docs/12_UATチェックリスト.md` に機能-画面対応の受入確認項目を追加

## 2026-02-18（追加23）
- 対象: 要件定義書への機能・画面トレーサビリティ反映
- 判断:
  - `docs/02_要件定義書.md` に `F-00〜F-09` と `SCR-000〜SCR-080` の対応表を追加する
- 理由:
  - 要件段階から機能と画面の対応を明示し、基本設計以降との追跡性を統一するため
- 影響:
  - `docs/02_要件定義書.md` に「11.1 機能・画面トレーサビリティ」を追加

## 2026-02-18（追加24）
- 対象: 利用/貸出管理（F-05）API実装とテスト整備
- 判断:
  - 貸出作成・返却の業務更新は `loan_service` に集約し、View は入出力と例外応答のみを担当する
  - `LoanHistory` モデルを追加し、貸出履歴を `asset` × `borrower` × `loaned_at/returned_at` で管理する
  - APIは `POST /api/v1/loan-histories` と `PATCH /api/v1/loan-histories/{id}/return` を提供する
- 理由:
  - 3層責務分離（Interface→Application→Domain）を維持しつつ、要件定義・基本設計の貸出機能を実装へ反映するため
  - 廃棄資産貸出禁止・未返却重複貸出禁止・二重返却禁止の業務制約をサービス層で一元管理するため
- 影響:
  - `apps/account_requests/models.py` に `LoanHistory` を追加
  - `apps/account_requests/migrations/0003_loanhistory.py` を追加
  - `apps/account_requests/services/loan_service.py` を追加
  - `apps/account_requests/serializers.py`, `views.py`, `urls.py`, `tests.py` を更新
  - `manage.py test apps.account_requests.tests` 21件成功

## 2026-02-18（追加25）
- 対象: 予算要件（分類3階層・属性20・1:n情報）の追加
- 判断:
  - 予算情報の分類は `大分類/中分類/小分類` の3階層を必須管理とする
  - 予算属性情報は20属性をカテゴリ内訳付きで明示する
  - 予算の1:n情報（2項目）は別テーブル管理とし、予算単位で複数行を許容する
- 理由:
  - 予算管理の粒度を資産管理と同等にそろえ、分類・属性の抜け漏れを防ぐため
  - 将来拡張時に単一値属性と複数値属性を分離して整合性を維持するため
- 影響:
  - `docs/02_要件定義書.md` を v1.6 に更新
  - 業務ルールへ予算分類/属性/1:n要件を追加
  - データ要件へ「6.4 予算管理対象データ（追加要件）」を追加

## 2026-02-18（追加26）
- 対象: 予算要件の詳細設計反映（画面/API/DDL）
- 判断:
  - 予算の3階層分類・属性20・1:n情報2項目を詳細設計へ展開する
  - 1:n情報は `multi_attributes` で受け取り、物理設計では別テーブルで複数行保持する
- 理由:
  - 要件追加（v1.6）を実装可能な粒度に落とし込み、設計間の不整合を防止するため
- 影響:
  - `docs/06_詳細設計_画面項目定義.md` を v0.3 に更新
  - `docs/07_詳細設計_API設計.md` を v0.3 に更新
  - `docs/08_詳細設計_論理DDL.sql` を v0.3 に更新

## 2026-02-18（追加27）
- 対象: 部分実装（機能/画面/項目）の棚卸し
- 判断:
  - 未実装ではなく「部分実装」に限定して差分を抽出する
  - 棚卸し結果は次実装の優先順が分かる形で記録する
- 理由:
  - 実装済み範囲を活かしながら、完成度不足の箇所を優先的に埋めるため
- 影響:
  - `ai/部分実装棚卸し_2026-02-18.md` を追加

## 2026-02-18（追加28）
- 対象: 部分実装解消の優先順位付き実装計画（MVP順）
- 判断:
  - 部分実装の解消は `P1:資産編集API完成化` → `P2:廃棄承認/棚卸UI` → `P3:予算入力拡張` → `P4:監査ログ検索/ダッシュボード拡張` の順で進める
  - 最初の実装着手は、規約違反リスクが最も高い資産編集API（View直更新のService化 + 属性20/1:n更新）とする
- 理由:
  - 業務停止リスク低減と3層責務分離の是正を同時に達成するため
  - 棚卸し結果をそのまま実装バックログへ接続し、短期スプリントで段階完了できるようにするため
- 影響:
  - `ai/部分実装解消_優先実装計画_2026-02-18.md` を追加

## 2026-02-18（追加29）
- 対象: 部分実装解消/未実装棚卸し対応のP1実装（資産編集API）
- 判断:
  - `PUT /api/v1/assets/{asset_id}` の更新処理をView直更新から `asset_service.update_asset` 経由へ移行する
  - 資産更新時に属性20（`AssetAttributeValue`）および1:n属性（`AssetAttributeMultiValue`）を同一処理で更新可能にする
  - PC資産の業務制約（`person_attr_01` 必須）を更新時にも適用する
- 理由:
  - 3層責務分離規約を順守しつつ、部分実装棚卸しで特定した最優先ギャップを解消するため
  - 未実装棚卸しで指摘された資産編集未完成（属性/複数値更新不足）を先行して埋めるため
- 影響:
  - `apps/account_requests/services/asset_service.py` に `update_asset` を追加
  - `apps/account_requests/serializers.py` に `AssetUpdateSerializer` を追加
  - `apps/account_requests/views.py` の資産更新APIをService呼び出しへ変更
  - `apps/account_requests/tests.py` に資産更新APIの正常系/異常系テストを追加
  - `manage.py test apps.account_requests.tests` 23件成功

## 2026-02-18（追加30）
- 対象: 部分実装解消/未実装棚卸し対応のP2実装（廃棄承認UI・棚卸UI）
- 判断:
  - 廃棄承認画面に承認/差戻しフォームを追加し、更新処理は `disposal_service`（approve/reject）経由で実行する
  - 棚卸画面に差異登録フォームと是正更新フォームを追加し、更新処理は `inventory_service`（create/update）経由で実行する
  - Web画面の更新結果は同一画面へリダイレクトし、ValidationError時は画面上にエラーメッセージを表示する
- 理由:
  - SCR-060（IV-003〜IV-005）および SCR-070（DP-004〜DP-006）の未実装/部分実装を優先解消するため
  - View薄化とService集約の規約を維持しつつ、運用に直結する操作UIを実用化するため
- 影響:
  - `apps/account_requests/web_views.py` に廃棄承認/棚卸のPOST処理を追加
  - `templates/account_requests/disposal_approval.html` に承認/差戻しフォームを追加
  - `templates/account_requests/inventory_list.html` に差異登録/更新フォームを追加
  - `apps/account_requests/tests.py` にWeb操作テストを2件追加
  - `manage.py test apps.account_requests.tests` 25件成功

## 2026-02-18（追加31）
- 対象: テスト実行時間対策（リファクタリング + 運用見直し）
- 判断:
  - `manage.py test` 実行時に `MD5PasswordHasher` を適用し、認証系テストの計算コストを削減する
  - テスト共通データは `setUpTestData` へ移行し、クラス内テストごとの重複生成を解消する
  - Web/APIテストではログイン状態だけが必要なケースで `force_login` を優先する
- 理由:
  - 反復開発時の待ち時間を短縮し、実装サイクルを維持するため
- 影響:
  - `config/settings.py` に test実行時の高速ハッシュ設定を追加
  - `apps/account_requests/tests.py` を `setUpTestData` / `force_login` 中心へリファクタリング
  - `docs/11_運用手順書_Runbook.md` に運用ルールを追記
  - `manage.py test apps.account_requests.tests --durations 10` で 27件 / 1.690秒（OK）

## 2026-02-18（追加32）
- 対象: P3実装（予算3階層分類・属性20・1:n情報）
- 判断:
  - 予算分類3階層を `BudgetCategoryL/M/S` としてモデル化し、`Budget` に `budget_category_s` FK を追加する
  - 予算属性20を `BudgetAttributeValue`（1:1）で保持し、1:n情報は `BudgetAttributeMultiValue`（複数行）で保持する
  - APIに `PUT /api/v1/budgets/{budget_id}` を追加し、属性/1:nの更新をService経由で処理する
  - 予算画面に3階層選択・属性20入力・1:n入力を追加する
- 理由:
  - 要件/詳細設計で追加済みの予算要件を実装へ反映し、未実装棚卸し項目を解消するため
- 影響:
  - `apps/account_requests/models.py` と `migrations/0004_budget_category_and_attributes.py` を追加更新
  - `services/budget_service.py`, `serializers.py`, `views.py`, `urls.py`, `web_views.py`, `budget_list.html` を更新
  - `seed_demo_data.py` を更新して予算分類データを投入可能化
  - `apps/account_requests/tests.py` に予算属性/1:nの作成・更新テストを追加

## 2026-02-18（追加33）
- 対象: P4実装（監査ログ検索UI + ダッシュボード不足指標）
- 判断:
  - 監査ログ画面に `対象テーブル/操作種別/実行者ID/実行日From-To` の検索フォームを追加し、DBフィルタで絞り込みを実装する
  - ダッシュボードに `予算消化率`（執行済合計/予算合計）と `保守期限30日以内件数` を追加表示する
  - 監査ログ一覧は `changed_by` を `select_related` して表示時の参照を最適化する
- 理由:
  - SCR-080（AL-001〜AL-005）と SCR-001（DS-001, DS-003）の未実装項目を解消するため
  - 検索/集計をDB評価優先で実装し、運用時の負荷増加を抑えるため
- 影響:
  - `apps/account_requests/web_views.py` を更新
  - `templates/account_requests/audit_logs.html` を更新
  - `templates/account_requests/dashboard.html` を更新
  - `apps/account_requests/tests.py` にWebテスト2件を追加
  - `manage.py test apps.account_requests.tests --durations 10` で29件成功

## 2026-02-18（追加34）
- 対象: 要件追加（資産状態マスタ/遷移マスタ管理 + 資産一覧画面で状態遷移）
- 判断:
  - 資産状態は `AssetStatusMaster`（大分類 × 状態コード）で管理し、約10状態を保持可能とする
  - 状態遷移は `AssetStatusTransitionMaster`（大分類 × 遷移元 × 遷移先）で管理する
  - `workflow_service` は固定遷移辞書を廃止し、遷移マスタ参照で遷移可否を判定する
  - 資産一覧画面（SCR-010）に行単位の遷移先選択と遷移実行を追加する
- 理由:
  - 大分類ごとに異なる業務状態/遷移ルールを運用可能にし、画面から即時に状態更新できるようにするため
  - 規約（状態遷移は `workflow_service` 経由）を厳守するため
- 影響:
  - `apps/account_requests/models.py` に状態/遷移マスタを追加し、`asset.status` を動的化
  - `apps/account_requests/migrations/0005_asset_status_master_and_transition.py` を追加
  - `apps/account_requests/services/workflow_service.py` をマスタ参照へ改修
  - `apps/account_requests/services/asset_service.py` の直接ステータス更新を廃止
  - `apps/account_requests/web_views.py` / `templates/account_requests/asset_list.html` に一覧遷移UIを追加
  - `apps/account_requests/tests.py`, `apps/account_requests/management/commands/seed_demo_data.py`, `apps/account_requests/admin.py` を更新
  - `docs/02_要件定義書.md`, `docs/06_詳細設計_画面項目定義.md`, `docs/08_詳細設計_論理DDL.sql` を更新
  - `manage.py test apps.account_requests.tests --durations 10` 31件成功

## 2026-02-18（追加35）
- 対象: ローカル動作準備（大量サンプルデータ投入）
- 判断:
  - `seed_demo_data` に `--bulk-size` オプションを追加し、多めデータ投入を標準化する
  - 既存データ重複を避けるため `AS-BULK-XXXX` コード体系で存在チェック後に投入する
- 理由:
  - ローカル画面/APIの動作確認を実データ量に近い状態で即実行できるようにするため
- 影響:
  - `apps/account_requests/management/commands/seed_demo_data.py` を更新
  - `manage.py migrate` を実行して `0003` `0004` `0005` を適用
  - `manage.py seed_demo_data --bulk-size 500` を実行し、500件投入

## 2026-02-18（追加36）
- 対象: 資産項目の実装状況精査レポート（定義/表示/登録/変更）
- 判断:
  - 資産項目は「定義は整備済み、登録/変更はAPI中心に実装済み、表示機能は部分実装」と評価する
  - Web画面は資産一覧/詳細ともに設計定義（SCR-010/011）の一部項目が未反映のため、表示観点は継続改善対象とする
- 理由:
  - 実装済み範囲と不足範囲を観点別に可視化し、次の改善優先順位を明確化するため
- 影響:
  - `ai/資産項目実装精査レポート_2026-02-18.md` を追加

## 2026-02-18（追加37）
- 対象: 資産項目改善の優先順位化（実装バックログ化）
- 判断:
  - 精査レポートの差分を P1〜P5 の段階実装タスクへ分解し、一覧表示/検索（P1/P2）を最優先とする
  - 短期は表示・検索の運用価値を先に回収し、Web登録/編集フォーム（P4/P5）は後続スプリントに配置する
- 理由:
  - 現場運用における検索性と視認性の改善が最も即効性が高く、既存API資産を活かして段階導入できるため
- 影響:
  - `ai/資産項目改善タスク一覧_2026-02-18.md` を追加

## 2026-02-18（追加38）
- 対象: P1 資産一覧の表示不足解消（分類/利用者/期限日）
- 判断:
  - 一覧表示の追加項目は `Asset` の直接項目へ寄せず、`AssetAttributeValue` を `select_related` で同時取得して表示する
  - テンプレートでは未設定値を `-` 表示とし、欠損データでも一覧表示を維持する
- 理由:
  - 既存データモデル（属性20分離）を維持しつつ、N+1を抑制して一覧要件を満たすため
- 影響:
  - `apps/account_requests/web_views.py` と `templates/account_requests/asset_list.html` を更新
  - `apps/account_requests/tests.py` に一覧表示検証テストを追加

## 2026-02-18（追加39）
- 対象: P2 資産一覧の検索条件拡張（AS-S-002〜006）
- 判断:
  - 検索条件として `asset_name`（部分一致）、`category_s_id`、`status`（複数選択）、`budget_link_status`、`person_attr_01_id` を `AssetListView` に追加する
  - ステータスは `<select multiple>` で受け取り、`request.GET.getlist('status')` を使ってDBフィルタする
  - 検索値保持は `search` コンテキストで統一し、画面再描画時の入力保持を保証する
- 理由:
  - SCR-010 の検索要件を満たしつつ、既存一覧画面の導線を維持して最小差分で機能拡張するため
- 影響:
  - `apps/account_requests/web_views.py` と `templates/account_requests/asset_list.html` を更新
  - `apps/account_requests/tests.py` に複合検索のWebテストを追加

## 2026-02-18（追加40）
- 対象: P3 資産詳細の表示拡張（分類階層 + 属性20 + 1:n属性）
- 判断:
  - `AssetDetailView` で分類階層と属性参照に必要な `select_related` を追加し、詳細表示の取得を1画面内で完結させる
  - 画面では属性20を固定順（AS-A-001〜020）で表示し、1:n属性は `MULTI_01` と `MULTI_02` に分割して一覧表示する
  - 未設定項目は `-` 表示とし、属性未登録データでも詳細画面を表示可能にする
- 理由:
  - SCR-011 の表示要件を満たしつつ、既存データ構造（属性20 + 1:n）をそのまま表現するため
- 影響:
  - `apps/account_requests/web_views.py` と `templates/account_requests/asset_detail.html` を更新
  - `apps/account_requests/tests.py` に詳細表示テストを追加

## 2026-02-18（追加41）
- 対象: P4 資産登録Webフォーム実装（SCR-010上での登録）
- 判断:
  - `/assets` の POST は `action` パラメータで「状態遷移」と「資産登録」を分岐し、登録時は `asset_service.create_asset` を呼び出す
  - 登録フォームは一覧画面に統合し、基本情報 + 属性20 + 1:n属性（改行区切り）を受け付ける
  - 入力エラー時は同画面再描画でエラーメッセージと入力値保持を行う
- 理由:
  - 既存導線を維持しつつ、View直更新禁止ルールを満たしたWeb登録機能を最小差分で追加するため
- 影響:
  - `apps/account_requests/web_views.py` と `templates/account_requests/asset_list.html` を更新
  - `apps/account_requests/tests.py` に登録の正常系/異常系Webテストを追加

## 2026-02-18（追加42）
- 対象: P5 資産編集Webフォーム実装（SCR-011上での更新）
- 判断:
  - `/assets/{id}` の POST は `action=update_asset` で更新処理を受け、`asset_service.update_asset` 経由で資産/属性/1:nを更新する
  - 状態更新は `update_asset` 内の `workflow_service` 遷移制約に従わせ、不正遷移時は詳細画面でエラー表示する
  - 編集フォームは詳細画面に統合し、入力エラー時の再描画で入力値を保持する
- 理由:
  - View直更新禁止と状態遷移制約の両方を守りながら、Web編集導線を最小差分で追加するため
- 影響:
  - `apps/account_requests/web_views.py` と `templates/account_requests/asset_detail.html` を更新
  - `apps/account_requests/tests.py` に更新の正常系/異常系Webテストを追加

## 2026-02-18（追加43）
- 対象: 最終回帰実行時の資産一覧Webクエリ予算見直し
- 判断:
  - `PerformanceGovernanceTests.test_query_budget_asset_list_web` のクエリ予算を 12件以内から 16件以内へ更新する
  - 予算更新後に `manage.py test apps.account_requests.tests --durations 10` を再実行し、全38件成功を完了条件とする
- 理由:
  - P4/P5で資産一覧・詳細のWeb導線が拡張され、一覧表示時に必要な選択肢取得クエリが増加したため
- 影響:
  - `apps/account_requests/tests.py`（性能ガバナンス閾値）を更新
  - 全体回帰 `apps.account_requests.tests` 38件成功を確認

## 2026-02-18（追加44）
- 対象: サンプルデータ準備（運用実行）
- 判断:
  - `migrate` 実行後に `seed_demo_data --bulk-size 500` を実行し、既存重複はスキップして現在データを維持する
  - サンプル有効性確認として `Asset` 総件数を確認し、501件を準備完了とする
- 理由:
  - ローカルで即時に画面/API検証できるデータ量を確保しつつ、既存の検証データを毀損しないため
- 影響:
  - DBマイグレーション適用済み（追加適用なし）
  - `seed_demo_data` 実行結果: `bulk assets created: 0`（重複回避）
  - `Asset` 総件数 501件を確認

## 2026-02-18（追加45）
- 対象: BootstrapによるWeb UIリッチ化
- 判断:
  - `base.html` に Bootstrap 5.3.3 を導入し、共通ナビゲーション/コンテナ/基本スタイルを統一する
  - 主要画面（`dashboard` / `asset_list` / `asset_detail`）をカード・グリッド・レスポンシブテーブル・フォームコントロールへ刷新する
  - 既存機能や入力項目は維持し、見た目改善のみを行う
- 理由:
  - 機能要件を変えずに可読性・操作性・視認性を短時間で改善し、ユーザー体験を向上させるため
- 影響:
  - `templates/account_requests/base.html` を更新
  - `templates/account_requests/dashboard.html` を更新
  - `templates/account_requests/asset_list.html` を更新
  - `templates/account_requests/asset_detail.html` を更新
  - 主要Webテスト3件成功を確認

## 2026-02-18（追加46）
- 対象: Bootstrap UI適用範囲の全画面統一（残画面仕上げ）
- 判断:
  - 主要4画面に続き、残り8画面（`configuration_list` / `budget_list` / `license_pool_list` / `pc_management` / `inventory_list` / `disposal_approval` / `audit_logs` / `login`）を同一Bootstrapトーンへ統一する
  - UI刷新は見た目・レイアウトのみを対象とし、POSTパラメータ名・フォーム項目・画面導線は変更しない
  - 仕上げ検証として対象導線のWebテスト5件とテンプレートエラーチェックを実施し、機能退行なしを完了条件とする
- 理由:
  - 画面ごとの見た目差を解消し、操作体験を一貫化するため
  - 既存業務ロジック（Service層経由更新）を維持しつつ、低リスクでUX改善を完了するため
- 影響:
  - `templates/account_requests/configuration_list.html` を更新
  - `templates/account_requests/budget_list.html` を更新
  - `templates/account_requests/license_pool_list.html` を更新
  - `templates/account_requests/pc_management.html` を更新
  - `templates/account_requests/inventory_list.html` を更新
  - `templates/account_requests/disposal_approval.html` を更新
  - `templates/account_requests/audit_logs.html` を更新
  - `templates/account_requests/login.html` を更新
  - 代表Webテスト5件成功、および対象テンプレートのエラー0件を確認
