# GraphRAG Profile: prompt_tuning_test_gpt54_mini

このプロファイルは、LLM 利用コスト、精度、確認工数のバランスを比較するためのベンチマーク用 workspace です。
複数の LLM モデルと prompt tuning の組み合わせを変えながら INDEX を作成し、どの条件が最も精度よく、実運用に向いているかを検証します。

## 目的

- LLM モデルごとのコスト差と出力品質を比較する
- prompt tuning の有無による INDEX 品質の差を比較する
- 同じ入力コーパスに対して、どの profile で作成した INDEX が最も良いかを評価する

## 前提

- 本 REPO の quickstart 基本 LLM モデルは非推論モデル前提だったため、`graphrag_quickstart/profiles/_template` の以下 3 つの prompt を推論モデル向けに改変している
  - `community_report_graph.txt`
  - `extract_graph.txt`
  - `summarize_descriptions.txt`
- そのうえで、`--no-discover-entity-types` を使った prompt tuning を適用し、`prompts/` に反映した prompt をこの profile の採用 prompt としている

## 採用プロンプト

- `prompts/extract_graph.txt`
- `prompts/summarize_descriptions.txt`
- `prompts/community_report_graph.txt`
- `prompts/community_report_text.txt` は共有 prompt として維持する

## Default 設定

- Index model: `gpt-5.4-mini`
- Query model: `gpt-5.4-mini`
- Prompt tuning output: `.\_prompt_tune_output_no_discover`（比較用の tuning 結果）

## プロンプトの由来

- `.\_prompt_tune_output_no_discover` は、`graphrag prompt-tune --no-discover-entity-types` で生成した結果を格納する
- `.\_prompt_tune_output_discover` は、`--discover-entity-types` 条件との比較用に残している
- `prompts/` 配下の内容は、`_template/prompts` の推論モデル向けカスタムを前提に、`.\_prompt_tune_output_no_discover` の tuning 結果を反映している

## 運用ルール

- prompt tuning をやり直すときは、出力先を条件ごとに分ける
- 例: `.\_prompt_tune_output_gpt54_mini_no_discover`
- 条件名がフォルダ名から分かるようにして、比較の取り違えを防ぐ
- 変更後は `settings.yaml` が参照する prompt パスと、`prompts/` の実体を必ず一致させる

## 実行例

```powershell
graphrag prompt-tune --root . --domain "prompt tuning test" --selection-method random --limit 15 --no-discover-entity-types --output .\_prompt_tune_output_no_discover
```

## この profile で見ること

- どの model と prompt の組み合わせが、最も安定して良い INDEX を作るか
- `--no-discover-entity-types` を使うことで、推論モデル向けに調整した prompt がどこまで効くか
- prompt tuning が品質向上に寄与する一方で、コスト増に見合うかどうか
