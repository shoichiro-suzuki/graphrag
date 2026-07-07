# ローカルLLM（Ollama経由）で Thinking/Reasoning 出力を抑制するガイド

対象: `local_llm_*` プロファイル全般
（`local_llm_qwen36_27b` での実機検証結果をもとに一般化したもの）

## 結論（先に要点）

`settings.yaml` の `completion_models.local_completion_model` で
`model_provider: openai` + `api_base: .../v1`（OpenAI互換エンドポイント）を
使っている限り、`extra_body.think: false` を指定しても**効かない**。

対策は1つ:

```diff
  local_completion_model:
-   model_provider: openai
-   api_base: https://10.116.130.134:8443/v1
+   model_provider: ollama_chat
+   api_base: https://10.116.130.134:8443
    auth_method: api_key
    api_key: ${LOCAL_LLM_API_KEY}
    call_args:
      ssl_verify: false
-     extra_body:
-       think: false
+     think: false
    retry:
      type: exponential_backoff
```

変更点は3つだけ:

1. `model_provider: openai` → `model_provider: ollama_chat`
2. `api_base` の末尾から `/v1` を削除（`ollama_chat` は Ollama ネイティブ
   `/api/chat` を叩くため、ベースURLのみを渡す）
3. `think: false`（や他のモデル固有パラメータ）は `extra_body` の入れ子から
   `call_args` 直下のトップレベルキーに移す

`ssl_verify: false` はそのままでよいが、**間欠的に自己署名証明書のSSL検証
エラーが発生することがある**（下記「既知の副作用」参照）。

## なぜ `openai` プロバイダーだと効かないのか

- GraphRAG は LiteLLM 経由で LLM を呼んでおり、`model_provider: openai` を
  指定すると LiteLLM は Ollama の **OpenAI互換エンドポイント**
  （`/v1/chat/completions`）を叩く。
- 実機検証の結果、Ollama（0.30.10 / 0.31.1 いずれでも確認）は
  **OpenAI互換エンドポイント経由だと `think` パラメータを認識しない**。
  一方 Ollama **ネイティブの `/api/chat`** エンドポイントは `think:false` を
  正しく反映する。
- LiteLLM には Ollama ネイティブ `/api/chat` 専用の `ollama_chat/` プレフィックス
  （プロバイダー）が存在し、`think` はキーワード引数（`call_args` 直下）として
  素通しされる。これに切り替えることで根治する。
- 参考: Qwen3.6:27b での実測では、`openai` プロバイダー経由だと
  `completion_tokens` の 90%超が reasoning（Thinking）で占められていたが、
  `ollama_chat` プロバイダーに切り替えた後は **reasoning_tokens が全期間で 0**
  になることを確認済み。処理速度も体感で7倍前後改善した。

## モデルごとの注意点（要検証・一律ではない）

Thinking/Reasoning の制御パラメータ名や挙動はモデルアーキテクチャによって
異なる。**`think: false` が万能というわけではない**ため、プロファイルを
切り替える際は必ず少数チャンクで実機検証すること。

| プロファイル | モデル | 既知の情報 |
|---|---|---|
| `local_llm_qwen36_27b` | qwen3.6:27b（dense, family: `qwen35`） | `think:false`（`call_args`直下）が有効（`ollama_chat`経由）。実機検証済み。逆に`/no_think`のプロンプト埋め込みは無効。 |
| `local_llm_qwen3_30b_a3b` | qwen3:30b-a3b（MoE, family: `qwen3moe`） | **`think:false`パラメータは無効**（`ollama_chat`経由でも本文にThinkingが混入し続ける）。実機検証済み。回避策として`call_args`から`think`を削除し、代わりにプロンプト末尾に`/no_think`を埋め込む方式を採用。**ただしこれは思考トークンの生成自体を止めるものではない**（下記「`/no_think`は根治ではない」参照）。**重要な注意**: `think`パラメータをリクエストに含めたまま`/no_think`を併用すると、`/no_think`側が無視される（生Ollama API `/api/chat` で確認）。両者は排他的に使うこと。 |
| `local_llm_gemma4_26b` | gemma4:26b-a4b-it-qat | Gemmaシリーズはthinking機能を持たない通常のinstruction-tunedモデルである可能性が高い。`think:false` は無害だが恐らく無意味（reasoning自体が発生しない）。念のため`ollama_chat`切り替え後も出力にreasoning系フィールドが無いか確認すること。 |
| `local_llm_gpt_oss_20b` / `local_llm_ollama`（同じ`gpt-oss:20b`） | gpt-oss:20b | OpenAI系アーキテクチャ由来のreasoningモデル。`think`ではなく `reasoning_effort`（`low`/`medium`/`high`等）のような別パラメータ名で制御する設計の可能性がある。`think:false` が効くかは未検証。qwen3_30b_a3bの前例からモデルごとに個別検証が必須と分かったため、安易に「効くはず」と決め打ちしないこと。 |

### `think`パラメータの対応状況はモデルファミリー単位で異なる（qwen3.6:27b vs qwen3:30b-a3b の教訓）

同じ「Ollama上のQwen3系列」でも、dense版（qwen3.6:27b, family: `qwen35`）とMoE版
（qwen3:30b-a3b, family: `qwen3moe`）でThinking制御の対応状況が真逆だった。

- dense版: `think:false`パラメータが有効。プロンプト内`/no_think`は無効。
- MoE版: `think:false`パラメータが無効（サーバーに送信はされているが無視される）。
  プロンプト内`/no_think`は有効だが、`think`パラメータを同時送信すると無効化される。

**教訓**: モデル名やパラメータサイズが似ていても、`model_provider: ollama_chat`+
`think:false`の組み合わせが常に有効とは限らない。新しいプロファイルを作る際は
必ず単発のcompletion呼び出しで実機検証し、`content`にThinkingが混入していないか
（`<think>`タグの断片や思考過程の文章が残っていないか）を目視確認すること。

### `/no_think`は「パーサー汚染の防止」であって「思考の根治」ではない（重要な訂正）

qwen3:30b-a3bで`/no_think`をプロンプト埋め込みした状態で本番インデックス作成
（3ドキュメント、18チャンク）を実行し、`cache/extract_graph/`の生応答を直接確認した
ところ、次の事実が判明した。

- `message.content`（GraphRAGのパーサーが読む本文）は完全にクリーン。
  `<think>`タグの混入やパースエラーは一切なし。
- しかし `message.reasoning_content`（別フィールド）には、
  依然として"Okay, let's tackle this..."のような**長大な思考過程がそのまま
  出力され続けている**（1応答あたり平均4,330 completion tokens相当、
  応答によっては5,000トークン超）。

つまり `/no_think` は「モデルに思考をさせない」のではなく、**Ollama/LiteLLMが
`content`と`reasoning_content`を別フィールドに分離して返す挙動を利用して、
GraphRAG側のパース対象からThinkingを追い出しているだけ**である。

**実害の面では対策として機能している**（JSON/パースエラー0件、community_reports
欠落0件）が、**速度・GPU負荷の面では根治になっていない**。実際、この実行では
`extract_graph`ワークフローだけで50分49秒（全体の94%）を要しており、1チャンク
あたり平均145秒はモデルが裏で思考トークンを生成し続けているコストを含んでいる
と考えられる。GraphRAGのメトリクス上は`reasoning_tokens: 0`と表示されるが、
これは計測ロジックが`reasoning_content`を計上していないだけで、実態の処理時間
やサーバー負荷を正しく反映していない点に注意すること。

qwen3.6:27bの`think:false`（`call_args`直下）による対策とは異なり、
**qwen3:30b-a3bでは思考トークンの生成そのものを止める方法が見つかっていない**。
処理速度を重視する場合はこの点を踏まえてモデル選定すること。

**検証方法**（`analyze_reasoning_tokens.py` を流用）:

1. 対象プロファイルの `cache/extract_graph/` を退避してから空にする
   （`.gitkeep` は残す）
2. `settings.yaml` を上記の diff の通り `ollama_chat` に変更
3. 少数チャンクだけ `graphrag index` を実行
4. `python graphrag_quickstart/profiles/local_llm_qwen36_27b/analyze_reasoning_tokens.py <対象profileのcache/extract_graphパス>` で
   `reasoning_tok` が 0 になっているか確認
5. 0 にならない場合、そのモデル固有の reasoning 制御パラメータ名を調べ、
   `call_args` に正しいキーで追加する（`extra_body` に入れず、
   `ollama_chat` の場合はトップレベルに置くこと）

## 既知の副作用（要フォローアップ）

### SSL証明書検証エラーが間欠的に発生する

`ollama_chat` プロバイダーに切り替えた後、`call_args.ssl_verify: false` を
指定していても、まれに以下のエラーで一部リクエストが失敗することを確認した。

```
litellm.exceptions.APIConnectionError: litellm.APIConnectionError:
Ollama_chatException - Cannot connect to host ... ssl:True
[SSLCertVerificationError: ... certificate verify failed]
```

- LiteLLM (v1.82.6) のコードを確認した限り `ssl_verify` は正しく配線されており、
  恒常的なバグではなさそうだった。
- 実際に2回連続で同一設定・同一データで実行したところ、1回目は18チャンク中
  2チャンクで発生（失敗率2.4%）、2回目は95リクエスト全て成功（失敗率0%）と、
  **再現性のない間欠的な現象**だった。
- パイプライン自体は落ちず、失敗したチャンクだけスキップされる
  （`error extracting graph` の警告ログが出る）。
- 現状は `retry: exponential_backoff` に任せる運用で許容範囲。
  頻発するようならサーバー側（Ollamaゲートウェイ）のTLS終端の安定性を
  疑うこと。

### community_reports で JSON 出力の乱れが起きることがある

Thinking抑制とは別軸の問題として、`create_community_reports` ワークフローで
以下のようなエラーが起きることを確認した。

- `json.decoder.JSONDecodeError`（LLMが構文の壊れたJSONを返す）
- `pydantic_core._pydantic_core.ValidationError: ... rating Field required`
  （必須フィールド `rating` が欠落したJSONを返す）

いずれもモデルが `community_report_graph.txt` / `community_report_text.txt`
プロンプトの出力フォーマット指示を完全には守れなかったケース。
該当コミュニティのレポート1件が欠落するだけでパイプライン全体は継続する
（`No report found for community: <id>` の警告が出る）。
出力精度に関わる問題のため、コミュニティ数が多い実データで運用する際は
欠落件数を確認すること。

## クリア手順の注意（作業事故の記録）

`cache`/`output`/`logs` を空にして再実行する際、`output/lancedb/` は
**ディレクトリ構造**（`*.lance/`）を含むため、ファイルだけを消す
コマンド（例: `find output -type f ! -name .gitkeep -delete`）では
**消え残る**。古い `.lance` ディレクトリが残ったまま次の実行に入ると、
`generate_text_embeddings` ワークフローが

```
ValueError: Table 'entity_description' was not found
```

のようなエラーで即座に失敗し、embeddingが一切生成されないまま
パイプラインだけ完走したように見えることがある。
再実行前に `output` 配下は**ディレクトリごと**削除すること
（`.gitkeep` を後で作り直す）。

## 検証用スクリプト

`graphrag_quickstart/profiles/local_llm_qwen36_27b/analyze_reasoning_tokens.py`
に、`cache/extract_graph/*_v4` キャッシュから content/reasoning のトークン比率を
集計するスクリプトがある。他プロファイルでも `<対象profile>/cache/extract_graph`
を引数に渡せばそのまま使える。

```powershell
python graphrag_quickstart/profiles/local_llm_qwen36_27b/analyze_reasoning_tokens.py `
  graphrag_quickstart/profiles/<対象profile>/cache/extract_graph
```
