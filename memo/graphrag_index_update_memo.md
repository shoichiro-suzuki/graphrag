# GraphRAG `index` / `update` 覚書

## 目的

`graphrag_quickstart/input` のテキストを対象にしたとき、`graphrag index` と `graphrag update` が何を更新し、何を更新しないかを整理する。

## 参照した主な箇所

- [docs/get_started.md](../docs/get_started.md)
- [docs/index/methods.md](../docs/index/methods.md)
- [docs/index/inputs.md](../docs/index/inputs.md)
- [docs/index/outputs.md](../docs/index/outputs.md)
- [docs/config/yaml.md](../docs/config/yaml.md)
- [packages/graphrag/graphrag/cli/main.py](../packages/graphrag/graphrag/cli/main.py)
- [packages/graphrag/graphrag/index/run/run_pipeline.py](../packages/graphrag/graphrag/index/run/run_pipeline.py)
- [packages/graphrag/graphrag/index/workflows/factory.py](../packages/graphrag/graphrag/index/workflows/factory.py)
- [packages/graphrag/graphrag/index/update/incremental_index.py](../packages/graphrag/graphrag/index/update/incremental_index.py)
- [packages/graphrag/graphrag/index/workflows/load_update_documents.py](../packages/graphrag/graphrag/index/workflows/load_update_documents.py)
- [packages/graphrag/graphrag/index/workflows/update_final_documents.py](../packages/graphrag/graphrag/index/workflows/update_final_documents.py)
- [packages/graphrag/graphrag/index/workflows/update_entities_relationships.py](../packages/graphrag/graphrag/index/workflows/update_entities_relationships.py)
- [packages/graphrag/graphrag/index/workflows/update_text_units.py](../packages/graphrag/graphrag/index/workflows/update_text_units.py)
- [packages/graphrag/graphrag/index/workflows/update_covariates.py](../packages/graphrag/graphrag/index/workflows/update_covariates.py)
- [packages/graphrag/graphrag/index/workflows/update_communities.py](../packages/graphrag/graphrag/index/workflows/update_communities.py)
- [packages/graphrag/graphrag/index/workflows/update_community_reports.py](../packages/graphrag/graphrag/index/workflows/update_community_reports.py)
- [packages/graphrag/graphrag/index/workflows/update_text_embeddings.py](../packages/graphrag/graphrag/index/workflows/update_text_embeddings.py)

## 結論

- `graphrag index` は、`input/` 配下の現在の内容を前提にインデックスを作り直す。
- `graphrag update` は、前回結果を土台にして、新しく増えた入力を差分追加する。
- 差分判定は `id` ではなく `title` ベースで行う。
- したがって、同じファイル名のまま中身だけ変えても、`update` では変更検出されない。
- 削除された入力は検出されるが、現行実装では最終インデックスからの削除反映までは行われない。

## 比較表

| 観点 | `graphrag index` | `graphrag update` |
| --- | --- | --- |
| 目的 | 入力全体からインデックスを作り直す | 前回インデックスに差分を追加する |
| 入力の見方 | `input/` 配下をそのまま対象にする | 前回 `documents` と今回の `input/` を比較する |
| 同一判定 | 判定ロジックは差分比較しない | `title` ベースで差分判定する |
| 追加ファイル | 全体再生成の中で反映される | 新規分だけ反映される |
| 既存ファイルの内容変更 | 再インデックスで反映される | 同じ `title` なら変更としては拾わない |
| 削除ファイル | 再インデックスで反映される | 検出はするが、削除反映はしない |
| 出力先 | `output/` | `update_output/` を経由して更新する |
| 既存ファイルの扱い | 同名ファイルは上書き | 前回結果をマージしつつ更新 |

## フロー図

```text
graphrag index
  input/
    -> load all documents
    -> build index from scratch
    -> write output/*.parquet
    -> overwrite same-name files

graphrag update
  input/
    -> load current documents
    -> compare with previous documents by title
    -> keep only new inputs
    -> merge with previous outputs
    -> write update_output/<timestamp>/...
    -> update output/*.parquet
```

## `graphrag index` の挙動

- 既定の `index` は standard パイプラインを使う。`--method standard` が省略時の既定。([docs/index/methods.md](../docs/index/methods.md))
- 入力を読み込んで、`output/` に parquet を出力する。([docs/get_started.md](../docs/get_started.md))
- 出力ファイルは上書き保存される。`write_dataframe` は `Storage.set(...)` を使うため、同名ファイルは置き換わる。([packages/graphrag/graphrag/index/run/run_pipeline.py](../packages/graphrag/graphrag/index/run/run_pipeline.py), [packages/graphrag-storage/graphrag_storage/tables/parquet_table_provider.py](../packages/graphrag-storage/graphrag_storage/tables/parquet_table_provider.py), [packages/graphrag-storage/graphrag_storage/file_storage.py](../packages/graphrag-storage/graphrag_storage/file_storage.py))

## `graphrag update` の挙動

- `graphrag update` は CLI の別コマンドとして定義されている。([packages/graphrag/graphrag/cli/main.py](../packages/graphrag/graphrag/cli/main.py))
- `update_output_storage` を使って、前回出力を保ったまま増分更新を行う。既定の保存先は `update_output/`。([docs/config/yaml.md](../docs/config/yaml.md), [packages/graphrag/graphrag/config/defaults.py](../packages/graphrag/graphrag/config/defaults.py))
- `load_update_documents` で前回の `documents` と今回の input を比較し、新規分だけを更新対象にする。([packages/graphrag/graphrag/index/workflows/load_update_documents.py](../packages/graphrag/graphrag/index/workflows/load_update_documents.py))
- 差分判定は `final_docs["title"]` と `input_dataset["title"]` の比較で行う。([packages/graphrag/graphrag/index/update/incremental_index.py](../packages/graphrag/graphrag/index/update/incremental_index.py))

## 何が更新されるか

- `documents`
- `entities`
- `relationships`
- `text_units`
- `covariates`
- `communities`
- `community_reports`
- `text embeddings`

これらは、前回分と delta をマージするか、delta に対して再生成される。([packages/graphrag/graphrag/index/workflows/update_final_documents.py](../packages/graphrag/graphrag/index/workflows/update_final_documents.py), [packages/graphrag/graphrag/index/workflows/update_entities_relationships.py](../packages/graphrag/graphrag/index/workflows/update_entities_relationships.py), [packages/graphrag/graphrag/index/workflows/update_text_units.py](../packages/graphrag/graphrag/index/workflows/update_text_units.py), [packages/graphrag/graphrag/index/workflows/update_covariates.py](../packages/graphrag/graphrag/index/workflows/update_covariates.py), [packages/graphrag/graphrag/index/workflows/update_communities.py](../packages/graphrag/graphrag/index/workflows/update_communities.py), [packages/graphrag/graphrag/index/workflows/update_community_reports.py](../packages/graphrag/graphrag/index/workflows/update_community_reports.py), [packages/graphrag/graphrag/index/workflows/update_text_embeddings.py](../packages/graphrag/graphrag/index/workflows/update_text_embeddings.py))

## 何が更新されないか

- `input/` の元ファイルそのもの
- 同じ `title` のまま中身だけ変えたファイルの変更検出
- 削除済み入力の最終インデックスからの除去

`deleted_inputs` は計算されるが、現行の update ワークフローでは使われていない。([packages/graphrag/graphrag/index/update/incremental_index.py](../packages/graphrag/graphrag/index/update/incremental_index.py), [packages/graphrag/graphrag/index/workflows/load_update_documents.py](../packages/graphrag/graphrag/index/workflows/load_update_documents.py))

## 実務上の使い分け

- 初回作成や、入力全体を正として再構築したいときは `graphrag index`
- 小さな追加だけを反映したいときは `graphrag update`
- ファイル削除や既存ファイルの内容変更を確実に反映したいときは、`input/` を整えてから `graphrag index` で作り直す

## 補足

- `cache/` は再実行時の LLM 呼び出しを高速化するために使われる。([docs/config/yaml.md](../docs/config/yaml.md))
- `context.json` と `stats.json` は出力に保存され、update 時も状態管理に使われる。([packages/graphrag/graphrag/index/run/run_pipeline.py](../packages/graphrag/graphrag/index/run/run_pipeline.py))
