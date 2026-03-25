# GraphRAG Profiles

GraphRAG の profile は、同じコーパスに対して複数の設定・prompt・出力を安全に分離するための実行単位です。

## 目的

- `graphrag_quickstart/input` を共有コーパスとして固定する
- `profiles/<profile_name>/` を 1 つの workspace root として扱う
- profile ごとに `settings.yaml`、`prompts/`、`cache/`、`logs/`、`output/` を分ける
- `query` は `--root` で profile を選び、必要に応じて `--data` で別 profile の index を参照する

## 既定の profile

- `_template`
  - 新規 profile を作るときの複製元
  - 現在の quickstart 設定と prompt をベースにしている
- `legacy`
  - 現在の quickstart prompt 群を退避した参照用 profile
  - 比較・検証用の固定基準として使う

## 新しい profile の作り方

```powershell
python scripts\create_graphrag_profile.py legal_gpt5nano
```

このスクリプトは `_template` を複製し、`<profile_name>` の profile root を作ります。  
あわせて `.env.example` からローカル用の `.env` を生成します。  
`settings.yaml` と `prompts/` を編集したあと、`graphrag index` / `graphrag query` を profile root を指定して実行します。

```powershell
graphrag index --root graphrag_quickstart\profiles\legal_gpt5nano
graphrag query --root graphrag_quickstart\profiles\legal_gpt5nano "..."
```

## 運用ルール

- profile ごとに `output/`、`logs/`、`cache/` を分離する
- `graphrag_quickstart/input` は共有し、profile 側の `settings.yaml` から相対パスで参照する
- profile の切り替えは `--root` で行う
- 別 profile の index を比較したい場合は `--data` を使う

## 補足

`graphrag init` は新規 workspace を作る標準手段だが、この repo では profile template を複製する運用の方が安全です。
既存 prompt を壊さずに新しい profile を作れるため、`_template` 起点の複製を標準手順とします。
