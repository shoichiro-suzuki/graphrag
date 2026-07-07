# qwen3.6:27b の Thinking 出力が抑制されない問題 — サーバー側 根治手順

## 症状

`settings.yaml` で `extra_body.think: false` を指定しているにもかかわらず、
`extract_graph` の LLM 応答に `reasoning_content` として大量の Thinking 本文が
混入する。実測（キャッシュ10件、`cache/extract_graph/*_v4`）:

- 有用な抽出結果（content）: 合計 4,267 トークン
- Thinking（reasoning_content）: 合計 42,735 トークン
- **Thinkingの比率: 90.9%**

プロンプト末尾に `/no_think` を追加しても改善しない（再検証で reasoning比率 91.9%、
むしろ横ばい）。

## 根本原因（サーバー側ログから特定）

Ollama サーバー起動ログ（`tmp_log.txt`）より:

```
20: cmd="...llama-server.exe ... --no-jinja --chat-template chatml ... --no-jinja ..."
427: srv init: chat template, thinking = 0
432: msg="template selection" ... renderer=qwen3.5 ... chat_template="[tools thinking completion vision]" ...
```

- GGUFファイル自体には Qwen 公式の Jinja chat_template（thinking 分岐ロジック込み）が
  埋め込まれている（ログ150行目 `tokenizer.chat_template`）。
- しかし Ollama 0.30.10 はこのモデル（qwen35/Qwen3.6系マルチモーダルアーキテクチャ）に対し、
  内部の `llama-server` を起動する際に **`--no-jinja --chat-template chatml`を自動付与**し、
  GGUF内蔵の本来のテンプレートを使わず、固定の chatml 形式に差し替えている。
- 一方 Ollama 自身の「Go ネイティブ renderer」機構は `renderer=qwen3.5` を選択し、
  `thinking` を扱えるモデルとして認識している（432行目）。
- つまり **Ollama の新しい Go renderer 層と、実際にプロンプトを組み立てる
  `llama-server --no-jinja` 経路が食い違っており**、`think`/`/no_think` の指示が
  最終的なプロンプトに反映されないまま chatml テンプレートへ丸められている。

これはユーザー側の設定ミスではなく、**Ollama 0.30.10 における
qwen35系アーキテクチャ（Qwen3.6, Gated Delta Net/SSMハイブリッド構造）に対する
テンプレート選択ロジックの既知の不整合**と判断できる。

## 追記（2026-07-03・designgpu001実機検証）— 原因の切り分けとバージョンアップの結果

designgpu001上でOllamaを直接操作できたため、上記の対応手順1（バージョンアップ）を
実施し、あわせてエンドポイント別に `think:false` の効き方を実機比較した。

### 結果1: バージョンアップ（0.30.10 → 0.31.1）では直らない

`winget upgrade` で 0.31.1 に更新し、`scripts\server_serve-lan.ps1` 経由で
qwen3.6:27b を再起動・ウォームアップして起動ログを確認したが、
llama-server 起動コマンドは 0.31.1 でも変わらず

```
--no-jinja --chat-template chatml
```

が付与されたままだった。GGUF内蔵Jinjaテンプレートは依然として無視されている。
**対応手順1（バージョンアップ）は解決策にならないことを実機で確認済み。**
（この検証は目視でのバージョン確認のつもりで `winget upgrade --id Ollama.Ollama
--accept-package-agreements` を実行した結果、意図せず実際にアップグレードが
走ってしまったもの。LAN公開中の共有サーバーが数分間ダウンしたが、
`server_serve-lan.ps1` で正しい環境変数のもと再起動し復旧を確認済み。
以後この種の確認は `winget upgrade` ではなく `winget list --id <id>` に留めること。）

### 結果2: 原因は「Jinja無視」そのものより、OpenAI互換エンドポイント固有の問題

同一モデル・同一バージョン（0.31.1）・同一プロンプトで、叩くエンドポイントだけを
変えて `think:false` の効き方を比較した。

| 経路 | `think:false` | 結果 |
|---|---|---|
| Ollamaネイティブ `/api/chat` | 効く | レスポンスに `thinking`/`reasoning` 系フィールドが出ず、`content` のみでクリーン |
| OpenAI互換 `/v1/chat/completions`（**GraphRAG/litellm が実際に使う経路**） | **効かない** | `message.reasoning` に大量出力。あるテストでは `completion_tokens=2935` のうち `content` は約1,214文字、`reasoning` は約11,938文字（比率はベースラインの90.9%とほぼ一致） |

つまり **Ollama 0.30.10/0.31.1 いずれも、OpenAI互換エンドポイント
（`/v1/chat/completions`）だけが `think` パラメータを認識せず、
ネイティブ `/api/chat` は正しく `think:false` を反映する**。
GraphRAG側（`lite_llm_completion.py`）はOpenAI互換base_url経由でOllamaを叩いていると
推測されるため、これが reasoning 混入の直接原因である可能性が高い。

### 示唆される次の一手（GraphRAG環境側での確認が必要）

GraphRAG環境は本リポジトリ（designgpu001）ではなくクライアント側にあるため、
以下は designgpu001 側では検証できない。GraphRAG/litellm 側で確認してほしい。

- litellm に Ollama ネイティブAPI（`/api/chat`）を叩くprovider設定
  （`ollama/` プレフィックス等）が使えないか確認し、OpenAI互換経由から切り替える。
- 切り替えられない場合、Ollamaの `/v1/chat/completions` が `think` 相当を
  どのパラメータ名で受け付けるか（例: `reasoning_effort` 等）をOllama側の
  OpenAI互換実装（ドキュメント/ソース）で確認する。
- どちらも難しい場合は対応手順4（クライアント側で `reasoning` を握りつぶす）が
  現実的な次善策になる。

## サーバー側で試す対応手順（優先順）

サーバーマシン（`10.116.130.134`）で以下を上から順に試す。

### 1. Ollama のバージョンアップ（最優先で確認） — ★2026-07-03 実施済み・効果なしと確認済み★

現在 `version 0.30.10`。Qwen3.6/Qwen3.5 系アーキテクチャ（`qwen35`）はまだ新しいため、
Ollama側のテンプレート処理に修正が入っている可能性が高い。

```powershell
ollama --version
# 最新版に更新後、再度モデルをpull/再起動して同じログを取得し
# 起動コマンドに --no-jinja が付くかどうか確認する
```

更新後、`ollama serve` のログ（今回の `tmp_log.txt` に相当する部分）で
起動コマンドラインに `--no-jinja --chat-template chatml` が **付かなくなっているか**を確認する。
付かなくなっていれば、GGUF内蔵のJinjaテンプレートがそのまま使われ、
`think` パラメータが正しく反映される可能性が高い。

### 2. Modelfile で TEMPLATE を明示指定する

バージョンアップで解決しない場合、Ollama の Modelfile 機構でテンプレートを
明示的に上書きする。

```powershell
ollama show qwen3.6:27b --modelfile > qwen3.6-27b.Modelfile
```

出力された Modelfile 内の `TEMPLATE` セクションが空、またはchatml相当になっている場合、
Qwen3.6公式の Jinja テンプレート（thinking分岐を含む）を明示的に書き込み、
別名タグとして再ビルドする。

```
# qwen3.6-27b.Modelfile の TEMPLATE セクションを Qwen公式テンプレートに置換後
ollama create qwen3.6-27b-fixed -f qwen3.6-27b.Modelfile
```

GraphRAG側の `settings.yaml` の `model:` をこの新タグに向ける。

### 3. `/no_think` をプロンプト冒頭（システムメッセージ側）に移す

今回の検証では抽出プロンプトの**末尾**（Output: の直後）に `/no_think` を入れて
効果がなかった。Qwen3系の一部バージョンでは `/no_think` は
「直前のユーザーターン」で解釈される仕様のため、末尾ではなく
**ユーザーメッセージの先頭**、または専用の system message として送る形に
変える余地がある。ただし手順1・2で解決しない場合の次善策であり、
テンプレート不整合（Jinja無視）が根本原因である以上、効果は限定的な可能性が高い。

### 4. （回避策・非推奨）クライアント側で reasoning_content を握りつぶす

サーバー側の対応が完了するまでの暫定措置。速度・コンテキスト消費の改善にはならないが、
GraphRAGの抽出精度への悪影響（reasoningが`content`に混入するケースがないか）を防ぐ。
`packages/graphrag-llm/graphrag_llm/completion/lite_llm_completion.py` の応答処理で
`reasoning_content` を破棄するフィルタを追加する。根治ではないため最終手段とする。

## 検証時の比較データ

- ベースライン（`think: false` のみ、対策前）:
  `graphrag_quickstart/profiles/local_llm_qwen36_27b/_baseline_think_default_20260703/`
  に `cache`/`output`/`logs` 一式を保存済み。reasoning比率 90.9%（10件）。
- `/no_think` 埋め込み検証（無効と判明）:
  検証時のキャッシュは `cache/extract_graph/`（4件、reasoning比率91.9%）に残存。
  再検証時は上書きされるため、必要なら退避してから次の対策を試すこと。
- 集計スクリプト:
  `analyze_reasoning_tokens.py`（セッションのスクラッチパッドに保存）
  `python analyze_reasoning_tokens.py <extract_graphキャッシュディレクトリ>` で
  content/reasoningのトークン比率を再集計できる。
- designgpu001実機検証（2026-07-03・Ollama 0.31.1・qwen3.6:27b）:
  同一の抽出プロンプトで `/api/chat` と `/v1/chat/completions` を比較。
  前者は `think:false` が効きreasoningフィールドなし。後者は
  `completion_tokens=2935`（content約1,214文字 / reasoning約11,938文字）で
  ベースラインとほぼ同じ比率のreasoning混入を再現。詳細は上記「追記」節を参照。
