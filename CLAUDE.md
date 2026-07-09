# CLAUDE.md

このリポジトリで作業する際の指針。Claude Code はこのファイルを常に読み込む。

## プロジェクト概要

サービス・アプリケーション設計に必要な技術と考え方を、レイヤーごとに整理した**学習用の技術ノート**。
各トピックは「動く実装」と「なぜそう設計するのかの解説」をセットで扱う。

- **勉強用リポジトリ。外部ライブラリは使わず、標準ライブラリのみで実装する。**
  特定のフレームワークに依存しない普遍的な考え方を扱うのが目的。
- 実装コードのランタイム依存はゼロ（`pyproject.toml` の `dependencies = []`）。
  `pytest` は開発用（テスト実行）依存としてのみ許可。
- 新しいトピックを足すときも、この「標準ライブラリのみ」の方針を必ず守る。
  便利なライブラリで済ませたくなっても、自前で実装して仕組みを理解することが目的。

## ディレクトリ構成

レイヤーごとに番号付きディレクトリで分類する。

```
01_data_layer/           データをどう持つか（modeling / DB基礎 / caching）
02_application_layer/    データをどう処理するか（データ構造 / 集計 / ソート / 探索 / 区間）
03_interface_layer/      どう外部に公開するか（HTTP / REST / リアルタイム通信）
04_reliability_and_scale/ 速く・安全に・大規模に（並行処理 / レート制限 / 性能 / スケール）
05_design_practice/      設計をどう進めるか（設計手法 / ケーススタディ）
```

### 各トピックの構成

```
トピック/
├── README.md          # 技術の本質・設計上の判断・トレードオフ（解説主体）
├── xxx.py             # 実装（標準ライブラリのみ、動くコード）
└── tests/             # 動作確認（pytest）
    └── test_xxx.py
```

- 解説主体のトピックは実装コードを持たない場合がある（`README.md` のみ）。
- 実装を追加したら、対応する `tests/test_xxx.py` を必ずセットで用意する。
- ルート `README.md` の「実装状況」表も更新する。

## コーディング方針

- **実装と解説はセット。** コードだけ・解説だけで完結させない。
  `README.md` には「なぜその設計にするか」「トレードオフは何か」を日本語で書く。
- 標準ライブラリのみ。外部依存を足さない。
- 実装は「動く最小コード」を志向する。過度な抽象化より、仕組みが読み取れることを優先。
- コメント・ドキュメントは日本語。既存ファイルのスタイル（docstring・コメント密度・命名）に合わせる。
- テストは `test_*.py`・関数は `test_*`（`pyproject.toml` の pytest 設定）。
  各トピックのテストは `sys.path.insert` で対象モジュールを読み込む既存パターンに合わせる。

## 開発コマンド

```bash
uv sync                 # 依存（pytest）をインストール
uv run pytest -v        # 全テスト実行
uv run pytest 02_application_layer/sorting -v   # 特定トピックのみ
```

uv を使わない場合は `pip install pytest` して `pytest -v`。

## Git・コミット

- コミットメッセージ: **タイトル1行のみ・英語の命令形・〜72文字・本文なし・`Co-Authored-By` フッターなし**。
  例: `Add cache-aside implementation`, `Fix interval overlap edge case`。
- 1コミット = 1論理変更。`git add -A` ではなく対象ファイルを明示的に stage する。
- ブランチ運用: `feature/<topic>` を切って作業し、PR 経由でレビュー後 `main` へマージする。
  `main` への直接コミットはしない。
- `.env` や `tmp/`・`__pycache__` など gitignore 対象は絶対にコミットしない。

## GitHub 操作（Issue / PR）

- リモート `origin` = `atsushi11o7/cs-fundamentals-practice`、`gh` 認証済み。Issue / PR の作成・更新は `gh` から行える。
  - Issue: `gh issue create --title "..." --body "..."`
  - PR: ブランチを push 後 `gh pr create --base main --title "..." --body "..."`
- トークンは絶対にコミットしない（環境変数 / `gh auth login` で管理）。

## 秘密情報の扱い

- `.env` は秘密情報。**明示的な許可がない限り閲覧・編集しない**。トークンや API キーの値はユーザー自身が設定する。
- 新しい環境変数を足すときは雛形の `.env.example` 側を更新する。
