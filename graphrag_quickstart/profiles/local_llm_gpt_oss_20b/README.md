# GraphRAG Profile: local_llm_gpt_oss_20b

Azure OpenAI の埋め込みを維持しつつ、インデックス作成時のドキュメント解析だけを社内 LAN の OpenAI 互換 Ollama ゲートウェイへ切り替える実験用 profile です。

## モデル分担

| 用途 | model id | 接続先 |
|---|---|---|
| ドキュメント解析 | `local_completion_model` / `gpt-oss:20b` | `https://10.116.130.134:8443/v1` |
| 埋め込み | `default_embedding_model` | Azure OpenAI `text-embedding-3-large` |
| クエリ応答 | `query_completion_model` | Azure OpenAI `gpt-5.4-mini` |

## 解析をローカル LLM に切り替えている workflow

- `extract_graph`
- `summarize_descriptions`
- `extract_claims`（有効化した場合）
- `community_reports`

`embed_text` と検索系の `embedding_model_id` は `default_embedding_model` のままです。

## モデル固有設定

- ローカル解析モデル: `gpt-oss:20b`
- reasoning 系のため `extra_body.think: false` を設定しています。
- ローカルサーバーの上限に合わせ、`concurrent_requests: 3` に抑えています。
- 社内ゲートウェイは自己署名 TLS のため、`ssl_verify: false` を明示しています。
- `model_provider: openai`（OpenAI互換 `/v1` エンドポイント）経由では `extra_body.think: false` が効かない既知の問題があります。詳細と回避策（`ollama_chat` プロバイダーへの切り替え）は [`../LOCAL_LLM_THINKING_GUIDE.md`](../LOCAL_LLM_THINKING_GUIDE.md) を参照してください。

## 事前設定

`.env` に次の 2 つを設定します。値はログやチャットに貼らないでください。

``dotenv
GRAPHRAG_API_KEY=<AZURE_OPENAI_API_KEY>
LOCAL_LLM_API_KEY=<LOCAL_LLM_BEARER_TOKEN>
``

## 実行例

``powershell
Set-Location C:\Users\3783\Documents\graphrag
graphrag_quickstart\.venv\Scripts\python.exe -m graphrag index --root graphrag_quickstart\profiles\local_llm_gpt_oss_20b
``

本番的に回す前に、まず `--dry-run --skip-validation` で設定読み込みを確認してください。

``powershell
graphrag_quickstart\.venv\Scripts\python.exe -m graphrag index --root graphrag_quickstart\profiles\local_llm_gpt_oss_20b --dry-run --skip-validation
``

## 注意

- 埋め込みを Azure OpenAI に残すため、インデックス生成時の外部通信はゼロにはなりません。
- ローカル LLM は Azure OpenAI より出力揺れが大きくなりやすいため、最初は小さい入力セットで `extract_graph` と `community_reports` の品質を目視確認してください。