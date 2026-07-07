# GraphRAG Profile: local_llm_qwen3_30b_a3b

Azure OpenAI の埋め込みを維持しつつ、インデックス作成時のドキュメント解析だけを社内 LAN の OpenAI 互換 Ollama ゲートウェイへ切り替える実験用 profile です。

## モデル分担

| 用途 | model id | 接続先 |
|---|---|---|
| ドキュメント解析 | `local_completion_model` / `qwen3:30b-a3b` | `https://10.116.130.134:8443/v1` |
| 埋め込み | `default_embedding_model` | Azure OpenAI `text-embedding-3-large` |
| クエリ応答 | `query_completion_model` | Azure OpenAI `gpt-5.4-mini` |

## 解析をローカル LLM に切り替えている workflow

- `extract_graph`
- `summarize_descriptions`
- `extract_claims`（有効化した場合）
- `community_reports`

`embed_text` と検索系の `embedding_model_id` は `default_embedding_model` のままです。

## モデル固有設定

- ローカル解析モデル: `qwen3:30b-a3b`（Qwen3 MoEアーキテクチャ、`qwen3.6:27b`とはfamilyが異なる）
- **`model_provider: ollama_chat` を使用していますが、`think` パラメータはこのモデルでは無効です。** 実機検証の結果、`think:false`をリクエストに含めると`/no_think`インライン指示が無視されることが判明したため、`call_args`から`think`を削除し、代わりに`extract_graph.txt` / `summarize_descriptions.txt` / `community_report_graph.txt` / `community_report_text.txt` の末尾に `/no_think` を追記しています。
- **注意: `/no_think` はパーサーに渡る `content` フィールドの汚染を防ぐだけで、モデル内部の思考トークン生成自体は止まりません。** 本番実行時のキャッシュを確認したところ、`reasoning_content`には依然として長大な思考過程（1応答あたり平均4,300トークン超）が出力されており、`extract_graph`工程が約51分（全体の94%）を占める一因になっています。qwen3.6:27bの`think:false`根治とは異なり速度改善効果は限定的です。詳細は [`../LOCAL_LLM_THINKING_GUIDE.md`](../LOCAL_LLM_THINKING_GUIDE.md) を参照してください。
- ローカルサーバーの上限に合わせ、`concurrent_requests: 3` に抑えています。
- 社内ゲートウェイは自己署名 TLS のため、`ssl_verify: false` を明示しています。

## 事前設定

`.env` に次の 2 つを設定します。値はログやチャットに貼らないでください。

``dotenv
GRAPHRAG_API_KEY=<AZURE_OPENAI_API_KEY>
LOCAL_LLM_API_KEY=<LOCAL_LLM_BEARER_TOKEN>
``

## 実行例

``powershell
Set-Location C:\Users\3783\Documents\graphrag
graphrag_quickstart\.venv\Scripts\python.exe -m graphrag index --root graphrag_quickstart\profiles\local_llm_qwen3_30b_a3b
``

本番的に回す前に、まず `--dry-run --skip-validation` で設定読み込みを確認してください。

``powershell
graphrag_quickstart\.venv\Scripts\python.exe -m graphrag index --root graphrag_quickstart\profiles\local_llm_qwen3_30b_a3b --dry-run --skip-validation
``

## 注意

- 埋め込みを Azure OpenAI に残すため、インデックス生成時の外部通信はゼロにはなりません。
- ローカル LLM は Azure OpenAI より出力揺れが大きくなりやすいため、最初は小さい入力セットで `extract_graph` と `community_reports` の品質を目視確認してください。