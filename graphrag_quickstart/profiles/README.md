# GraphRAG Profiles

`graphrag_quickstart/profiles` には、用途の異なる profile を置いています。
このディレクトリの README は、どの profile をどの目的で使うかをすぐ判断できるようにするための案内です。

## 使い分け

- 新しい domain や設定を作り始めるときは `_template`
- 既存の quickstart 設定を固定参照として残したいときは `legacy`
- LLM モデルと prompt tuning の組み合わせを比較したいときは `prompt_tuning_test_nano` と `prompt_tuning_test_gpt54_mini`

## プロファイル一覧

| Profile | 役割 | 主な用途 |
|---|---|---|
| `_template` | ひな形 | 新しい profile を作るための出発点 |
| `legacy` | 固定参照 | 現在の quickstart 仕様を基準として残す |
| `prompt_tuning_test_nano` | ベンチマーク用 | LLM モデルと prompt tuning 条件の比較実験 |
| `prompt_tuning_test_gpt54_mini` | ベンチマーク用 | GPT-5.4-mini を使う比較実験 |

## インデックス作成例

| Profile | 実行例 |
|---|---|
| `_template` | `Set-Location graphrag_quickstart\profiles\_template; graphrag index --root .` |
| `legacy` | `Set-Location graphrag_quickstart\profiles\legacy; graphrag index --root .` |
| `prompt_tuning_test_nano` | `Set-Location graphrag_quickstart\profiles\prompt_tuning_test_nano; graphrag index --root .` |
| `prompt_tuning_test_gpt54_mini` | `Set-Location graphrag_quickstart\profiles\prompt_tuning_test_gpt54_mini; graphrag index --root .` |

## 共通の前提

- どの profile も共有コーパスは `../../input` を使う
- まず profile を複製し、必要な `settings.yaml` と `prompts/` を調整する
- profile ごとの細部は、それぞれの配下にある README を参照する

## `prompt_tuning_test_nano` と `prompt_tuning_test_gpt54_mini`

この 2 つの profile は、LLM 利用コスト、精度、確認工数のバランスを比較するための実験用 profile です。
本 REPO の quickstart 基本 LLM モデルは非推論モデル前提だったため、`_template` の `community_report_graph.txt`、`extract_graph.txt`、`summarize_descriptions.txt` を推論モデル向けに改変したうえで、`--no-discover-entity-types` を使った prompt tuning を適用しています。
`prompt_tuning_test_nano` は INDEX 側のモデルに `gpt-5-nano` を使い、`prompt_tuning_test_gpt54_mini` は `gpt-5.4-mini` を使います。
その結果を使って、どの profile で作成した INDEX が最も精度よく、どの条件が費用対効果に優れるかを検証します。

## 推論用カスタム手順

新しい profile で同じ系統の prompt を作るときは、毎回 `_template` と比較し直さず、次の 3 本を標準カスタムとして先に適用します。

- `extract_graph.txt`
  - `entity_types` を明示し、入力テキストに明示された entity と relationship だけを抽出する
  - 出力は入力と同じ言語にそろえ、根拠のない推測をしない
- `summarize_descriptions.txt`
  - 1 つ以上の entity に対する third person の要約にする
  - `{max_length}` で長さを制御し、対立する説明は 1 つに統合する
- `community_report_graph.txt`
  - JSON 形式の report 構造、grounding rules、`{max_report_length}` の長さ制限を固定する
  - そのうえで各 profile のドメイン固有の例と評価対象だけを差し替える

この 3 本を共通カスタムとして確定してから、`prompt_tune` の結果を各 profile の `prompts/` に反映すると、比較生成を毎回やり直さずに済みます。

## 参考

- `_template/README.md`
- `legacy/README.md`
- `prompt_tuning_test_nano/README.md`
- `prompt_tuning_test_gpt54_mini/README.md`
