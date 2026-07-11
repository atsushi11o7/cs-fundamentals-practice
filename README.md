# cs-fundamentals-practice

サービス・アプリケーションを設計・実装するために必要な技術と考え方を、レイヤーごとに整理した学習ノート。
各トピックは「**動く実装（標準ライブラリのみ）**」と「**なぜそう設計するのかの解説**」をセットで扱う。

## このノートの考え方

サービスは、いくつかの層（レイヤー）の積み重ねとして捉えられる。
データをどう持ち、どう処理し、どう外部に公開し、どう速く安全に大規模に保つか。
本ノートはこの流れに沿って技術を配置し、最後にそれらを組み合わせて実際のサービスを設計する。

- **実装はすべて標準ライブラリのみ**（`sqlite3` などの同梱モジュールは使う）。
  特定のフレームワークに依存しない普遍的な考え方を、自分で書いて理解することを重視する。
- 各トピックは独立して読める。興味のある層から読んでよい。
- 各トピックの解説では、結論だけでなく「設計上の判断とトレードオフ」を言葉にする。

## 構成

### 01. Data Layer — データをどう持つか
- **data_modeling** — エンティティ・リレーション・正規化。属性を持つ中間テーブル、スナップショット
- **database_fundamentals** — `sqlite3` でインデックス・トランザクション・制約を実際に動かす
- **caching** — Cache-Aside・TTL・無効化

### 02. Application Layer — データをどう処理するか
- **data_structures** — 辞書 / リスト / 集合 / deque の使い分け（Stack・Queue）
- **aggregation** — 合計・カウント・グルーピング
- **sorting** — 複合キーでの並べ替え
- **searching** — 線形探索・二分探索・境界探索（自前実装）
- **interval_handling** — 区間の重なり判定・予約管理
- **graph_traversal** — グラフ / 木の探索（BFS・DFS・最短ホップ）

### 03. Interface Layer — どう外部に公開するか
- **http_basics** — HTTP リクエスト / レスポンスを自前でパース・生成
- **rest_api_design** — リソース指向・ステータスコード・べき等性（最小ルータ）
- **realtime_communication** — ロングポーリング・SSE・WebSocket ハンドシェイク

### 04. Reliability & Scale — どう速く・安全に・大規模に保つか
- **concurrency** — 競合（レースコンディション）とロック
- **rate_limiting** — 固定ウィンドウ・トークンバケット
- **scaling_patterns** — ラウンドロビン負荷分散・コンシステントハッシュ
- **web_performance** — 条件付きリクエスト（ETag / 304）・gzip 圧縮

### 05. Design Practice — 設計をどう進めるか
- **design_method** — 設計の型（要件確認 → 機能洗い出し → データ設計 → 構成 → スケール対応 → 運用監視）
- **case_studies** — 01〜04 を組み合わせた実践
  - **url_shortener** — URL短縮。base62 採番・キャッシュ・レート制限を組み合わせた API
  - **booking_system** — 予約システム（ロードマップ形式）。希少資源が「時間帯」。核は処理・並行制御
  - **ec_inventory** — EC在庫・注文（ロードマップ形式）。希少資源が「個数」。核はデータ設計

## 各トピックの構成

```
トピック/
├── README.md          # 技術の本質・設計上の判断・トレードオフ
├── xxx.py             # 実装（標準ライブラリのみ、動くコード）
└── tests/             # 動作確認（pytest）
```

設計の進め方（`design_method`）のように、プロセスが主題で実装コードを持たないトピックもある。
ケーススタディには、段階的に育てる `stageN_*.py` の形を取るものもある。

## 設計実践（05）の読み方

`design_method` が設計の「型」で、`case_studies` がその適用例。型は2通りの書き方で示している。

- **設計書形式**：型の6見出しで設計を記述（`url_shortener`）。
- **ロードマップ形式**：一番単純な形から段階的に育て、各段が型のどのステップを進めるか明記
  （`booking_system` / `ec_inventory`）。

2つのロードマップ型ケーススタディは対になっている。

| | booking_system | ec_inventory |
|---|---|---|
| 希少資源 | 時間帯（区間） | 個数（カウント） |
| 核 | 区間の重なり・並行制御 | データ設計（関係・不変条件） |
| 並行制御 | プロセス内ロック | DB のトランザクション＋制約 |

## セットアップとテスト

```bash
uv sync                 # 依存（pytest）をインストール
uv run pytest -v        # 全テスト実行
uv run pytest 01_data_layer/caching -v   # 特定トピックのみ
```

uv を使わない場合は `pip install pytest` して `pytest -v`。

## 実装状況

すべてのトピックが 実装（または解説）＋テストを備える（テスト計 162 件）。

| レイヤー | トピック |
|---|---|
| 01 Data | data_modeling / database_fundamentals / caching |
| 02 App | data_structures / aggregation / sorting / searching / interval_handling / graph_traversal |
| 03 Interface | http_basics / rest_api_design / realtime_communication |
| 04 Reliability & Scale | concurrency / rate_limiting / scaling_patterns / web_performance |
| 05 Design Practice | design_method / case_studies（url_shortener / booking_system / ec_inventory） |
