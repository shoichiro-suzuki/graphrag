# GraphRAG トークンコスト記録メモ

## 目的

`graphrag index` / `graphrag update` / `graphrag query` の実行ごとに、LLM の利用トークン数と推定コストを確認できるようにするための覚書。

このメモでは、どこで計測して、どこに保存して、どう確認するかを整理する。

## 参照した主な箇所

- [packages/graphrag-llm/graphrag_llm/metrics/command_cost_recorder.py](../packages/graphrag-llm/graphrag_llm/metrics/command_cost_recorder.py)
- [packages/graphrag-llm/graphrag_llm/metrics/default_metrics_processor.py](../packages/graphrag-llm/graphrag_llm/metrics/default_metrics_processor.py)
- [packages/graphrag-llm/graphrag_llm/model_cost_registry/model_cost_registry.py](../packages/graphrag-llm/graphrag_llm/model_cost_registry/model_cost_registry.py)
- [packages/graphrag/graphrag/index/run/run_pipeline.py](../packages/graphrag/graphrag/index/run/run_pipeline.py)
- [packages/graphrag/graphrag/cli/index.py](../packages/graphrag/graphrag/cli/index.py)
- [packages/graphrag/graphrag/cli/query.py](../packages/graphrag/graphrag/cli/query.py)
- [graphrag_quickstart/settings.yaml](../graphrag_quickstart/settings.yaml)
- [packages/graphrag/graphrag/config/init_content.py](../packages/graphrag/graphrag/config/init_content.py)

## 結論

- 実行コストは `output/command_costs.jsonl` に append-only で記録する。
- 料金は `model_cost_registry` で管理し、実行ログとは分離する。
- `reasoning_tokens` は別項目として記録するが、課金計算では `completion_tokens` に足さない。
- `graphrag update` は workflow 単位の内訳を持ち、`graphrag query` はコマンド単位の記録を持つ。

## 何が記録されるか

1 行の JSON に、少なくとも次を含める。

- `command`
- `timestamp`
- `model_id`
- `prompt_tokens`
- `completion_tokens`
- `reasoning_tokens`
- `total_tokens`
- `input_cost`
- `output_cost`
- `total_cost`
- `scope_breakdown`
- `model_breakdown`

加えて、CLI から渡された補助情報も残る。

- `graphrag index` / `graphrag update`
  - `indexing_method`
  - `is_update_run`
  - `cache_enabled`
  - `verbose`
- `graphrag query`
  - `search_type`
  - `streaming`
  - `community_level`
  - `response_type`
  - `dynamic_community_selection` など

## コスト計算の仕組み

### 料金の保管

モデル単価は [model_cost_registry.py](../packages/graphrag-llm/graphrag_llm/model_cost_registry/model_cost_registry.py) で管理する。

現行の quickstart では、`query` 系は `gpt-5.4-mini`、`index` 系の一部 workflow は `gpt-5-nano` を使う。

登録している単価は次のとおり。

| モデル | 入力単価 | 出力単価 |
|---|---:|---:|
| `gpt-5.4-mini` | `$0.750 / 100万トークン` | `$4.500 / 100万トークン` |
| `gpt-5-nano` | `$0.050 / 100万トークン` | `$0.400 / 100万トークン` |

### モデル選択の場所

利用モデルは `settings.yaml` の `completion_models` で切り替える。

- `default_completion_model`
  - `index` 系の生成処理で使う既定モデル
- `query_completion_model`
  - `query` 系で使うモデル
- `gpt-5-nano`
  - `index` 側で個別に割り当てる軽量モデル

現行 quickstart では、`index` 側の `extract_graph` / `summarize_descriptions` / `extract_claims` / `community_reports` に `gpt-5-nano` を割り当て、`query` 側は `query_completion_model` 経由で `gpt-5.4-mini` を使う。

### 計算式

現行実装では、課金対象トークンは次のように扱う。

- `input_cost = prompt_tokens * input_cost_per_token`
- `output_cost = completion_tokens * output_cost_per_token`
- `total_cost = input_cost + output_cost`

`reasoning_tokens` は `completion_tokens_details.reasoning_tokens` から取得して別項目に保存するが、`completion_tokens` に足し込まない。

これは Azure OpenAI の reasoning 系モデルで、`reasoning_tokens` が `completion_tokens_details` の内訳として返るため、`completion_tokens + reasoning_tokens` にすると二重計上になり得るため。

### 実装上の記録先

- API レスポンス由来のトークン集計
  - [default_metrics_processor.py](../packages/graphrag-llm/graphrag_llm/metrics/default_metrics_processor.py)
- コマンド単位の台帳化
  - [command_cost_recorder.py](../packages/graphrag-llm/graphrag_llm/metrics/command_cost_recorder.py)

## 粒度の違い

### `graphrag index`

- コマンド全体を 1 レコードとして記録する。
- さらに pipeline 内の各 workflow を `scope_breakdown` で分ける。
- workflow 名は [run_pipeline.py](../packages/graphrag/graphrag/index/run/run_pipeline.py) の実行単位に対応する。
- 現行の quickstart 設定では、`extract_graph` / `summarize_descriptions` / `extract_claims` / `community_reports` に `gpt-5-nano` を割り当てている。

### `graphrag update`

- 基本は `index` と同じ記録方式。
- `scope_breakdown` によって、どの workflow でどれだけ使ったかを見られる。
- `update` 特有の差分処理は、`indexing_method` / `is_update_run` のメタデータで区別できる。

### `graphrag query`

- 実行全体を 1 レコードで記録する。
- `global` / `local` / `drift` / `basic` は `search_type` で区別する。
- クエリは workflow をまたがないため、`index` / `update` よりも単純な台帳になる。
- 現行の quickstart 設定では、`local_search` / `global_search` / `drift_search` / `basic_search` は `query_completion_model` を参照し、`query_completion_model` は `gpt-5.4-mini` を指している。

## ログ確認方法

### 1. 最新 1 件を見る

```powershell
Get-Content -Encoding utf8 output/command_costs.jsonl | Select-Object -Last 1
```

### 2. JSON として読みやすくする

```powershell
Get-Content -Encoding utf8 output/command_costs.jsonl |
  Select-Object -Last 1 |
  ConvertFrom-Json |
  Format-List *
```

### 3. workflow ごとの内訳を見る

```powershell
$record = Get-Content -Encoding utf8 output/command_costs.jsonl |
  Select-Object -Last 1 |
  ConvertFrom-Json

$record.scope_breakdown | Format-List
```

### 4. `update` の差分確認

- `command` が `graphrag update` になっているかを見る。
- `is_update_run` が `True` か確認する。
- `scope_breakdown` の各 workflow に、token / cost が入っているか確認する。

### 5. `query` の確認

- `command` が `graphrag query` になっているかを見る。
- `search_type` が `global` / `local` / `drift` / `basic` のどれかを確認する。
- `scope_breakdown` が空でも問題ない。クエリはコマンド単位の集計が目的。

### 6. 集計スクリプトでまとめて読む

`scripts/summarize_command_costs.py` を使うと、`command_costs.jsonl` を `command` ごとに集計して Markdown で見られる。

```powershell
.\.venv\Scripts\python.exe scripts\summarize_command_costs.py graphrag_quickstart\output\command_costs.jsonl
```

出力をファイルに保存する場合は `-o` を付ける。

```powershell
.\.venv\Scripts\python.exe scripts\summarize_command_costs.py graphrag_quickstart\output\command_costs.jsonl -o graphrag_quickstart\output\command_costs_summary.md
```

このスクリプトでは次が見やすくなる。

- `graphrag index` / `graphrag update` / `graphrag query` の合計
- モデル別の内訳
- workflow 別の内訳
- 各 run の時刻とコスト

## 例

```json
{
  "command": "graphrag update",
  "timestamp": "2026-03-25T12:34:56.789+09:00",
  "model_id": "multiple",
  "prompt_tokens": 12345,
  "completion_tokens": 6789,
  "reasoning_tokens": 512,
  "input_cost": 0.00925875,
  "output_cost": 0.0305505,
  "total_cost": 0.03980925,
  "indexing_method": "standard",
  "is_update_run": true,
  "total_tokens": 19134,
  "scope_breakdown": {
    "create_communities": {
      "prompt_tokens": 1000,
      "completion_tokens": 2000,
      "reasoning_tokens": 128,
      "total_cost": 0.01,
      "model_breakdown": {},
      "scope_breakdown": {}
    }
  }
}
```

## 運用上の注意

- `command_cost_recorder` はプロセスグローバルのシングルトンなので、同一プロセス内で複数コマンドを同時実行する用途には向かない。
- ファイル書き込みに失敗した場合は warning を出すが、記録自体は失われる可能性がある。ディスク容量や権限は別途監視する。
- `stats.json` は既存どおり残し、コスト記録は別ファイルに分離する。

## 使い分けの目安

- 実行ごとのコストを追いたい場合は `output/command_costs.jsonl`
- 処理時間やメモリを追いたい場合は `output/stats.json`
- workflow ごとの詳細を追いたい場合は `scope_breakdown`
- 人間がざっと確認したい場合は `scripts/summarize_command_costs.py`
