# Language Model Selection and Overriding

This page contains information on selecting a model to use and options to supply your own model for GraphRAG. Note that this is not a guide to finding the right model for your use case.

## Default Model Support

GraphRAG was built and tested using OpenAI models, so this is the default model set we support. This is not intended to be a limiter or statement of quality or fitness for your use case, only that it's the set we are most familiar with for prompting, tuning, and debugging.

GraphRAG uses [LiteLLM](https://docs.litellm.ai/) for calling language models. LiteLLM provides support for 100+ models though it is important to note that when choosing a model it must support returning [structured outputs](https://openai.com/index/introducing-structured-outputs-in-the-api/) adhering to a [JSON schema](https://docs.litellm.ai/docs/completion/json_mode).

Example using LiteLLM as the language model manager for GraphRAG:

```yaml
completion_models:
  default_completion_model:
    model_provider: gemini
    model: gemini-2.5-flash-lite
    auth_method: api_key
    api_key: ${GEMINI_API_KEY}

embedding_models:
  default_embedding_model:
    model_provider: gemini
    model: gemini-embedding-001
    auth_method: api_key
    api_key: ${GEMINI_API_KEY}
```

See [Detailed Configuration](yaml.md) for more details on configuration. [View LiteLLM basic usage](https://docs.litellm.ai/docs/#basic-usage) for details on how models are called (The `model_provider` is the portion prior to `/` while the `model` is the portion following the `/`).

## Model Selection Considerations

GraphRAG has been most thoroughly tested with the gpt-4 series of models from OpenAI, including gpt-4 gpt-4-turbo, gpt-4o, and gpt-4o-mini. Our [arXiv paper](https://arxiv.org/abs/2404.16130), for example, performed quality evaluation using gpt-4-turbo. As stated above, non-OpenAI models are supported through the use of LiteLLM but the suite of gpt-4 series of models from OpenAI remain the most tested and supported suite of models for GraphRAG – in other words, these are the models we know best and can help resolve issues with.

Versions of GraphRAG before 2.2.0 made extensive use of `max_tokens` and `logit_bias` to control generated response length or content. The introduction of the o-series of models added new, non-compatible parameters because these models include a reasoning component that has different consumption patterns and response generation attributes than non-reasoning models. GraphRAG 2.2.0 now supports these models, but there are important differences that need to be understood before you switch.

- Previously, GraphRAG used `max_tokens` to limit responses in a few locations. This is done so that we can have predictable content sizes when building downstream context windows for summarization. We have now switched from using `max_tokens` to use a prompted approach, which is working well in our tests. We suggest using `max_tokens` in your language model config only for budgetary reasons if you want to limit consumption, and not for expected response length control. We now also support the o-series equivalent `max_completion_tokens`, but if you use this keep in mind that there may be some unknown fixed reasoning consumption amount in addition to the response tokens, so it is not a good technique for response control.
- Previously, GraphRAG used a combination of `max_tokens` and `logit_bias` to strictly control a binary yes/no question during gleanings. This is not possible with reasoning models, so again we have switched to a prompted approach. Our tests with gpt-4o, gpt-4o-mini, and o1 show that this works consistently, but could have issues if you have an older or smaller model.
- The o-series models are much slower and more expensive. It may be useful to use an asymmetric approach to model use in your config: you can define as many models as you like in the `models` block of your settings.yaml and reference them by key for every workflow that requires a language model. You could use gpt-4o for indexing and o1 for query, for example. Experiment to find the right balance of cost, speed, and quality for your use case.
- The o-series models contain a form of native native chain-of-thought reasoning that is absent in the non-o-series models. GraphRAG's prompts sometimes contain CoT because it was an effective technique with the gpt-4\* series. It may be counterproductive with the o-series, so you may want to tune or even re-write large portions of the prompt templates (particularly for graph and claim extraction).

Example config with asymmetric model use:

```yaml
completion_models:
  extraction_completion_model:
    model_provider: openai
    model: gpt-4o
    auth_method: api_key
    api_key: ${GRAPHRAG_API_KEY}
  query_completion_model:
    model_provider: openai
    model: o1
    auth_method: api_key
    api_key: ${GRAPHRAG_API_KEY}
...
extract_graph:
  completion_model_id: extraction_completion_model
  prompt: "prompts/extract_graph.txt"
  entity_types: [organization, person, geo, event]
  max_gleanings: 1
...
global_search:
  completion_model_id: query_completion_model
  map_prompt: "prompts/global_search_map_system_prompt.txt"
  reduce_prompt: "prompts/global_search_reduce_system_prompt.txt"
  knowledge_prompt: "prompts/global_search_knowledge_system_prompt.txt"
```

Another option would be to avoid using a language model at all for the graph extraction, instead using the `fast` [indexing method](../index/methods.md) that uses NLP for portions of the indexing phase in lieu of LLM APIs.

## Using Custom Models

LiteLLM supports hundreds of models, but cases may still exist in which some users wish to use models not supported by LiteLLM. There are two approaches one can use to connect to unsupported models:

### Proxy APIs

Many users have used platforms such as [ollama](https://ollama.com/) and [LiteLLM Proxy Server](https://docs.litellm.ai/docs/simple_proxy) to proxy the underlying model HTTP calls to a different model provider. This seems to work reasonably well, but we frequently see issues with malformed responses (especially JSON), so if you do this please understand that your model needs to reliably return the specific response formats that GraphRAG expects. If you're having trouble with a model, you may need to try prompting to coax the format, or intercepting the response within your proxy to try and handle malformed responses.

### Model Protocol

We support model injection through the use of a standard completion and embedding Protocol and accompanying factories that you can use to register your model implementation. This is not supported with the CLI, so you'll need to use GraphRAG as a library.

- Our Protocol is [defined here](https://github.com/microsoft/graphrag/blob/main/packages/graphrag-llm/graphrag_llm/completion/completion.py)
- We have a simple mock implementation in our tests that you can [reference here](https://github.com/microsoft/graphrag/blob/main/packages/graphrag-llm/graphrag_llm/completion/mock_llm_completion.py)

Once you have a model implementation, you need to register it with our completion model factory or embedding model factory:

```python
from graphrag_llm.completion import LLMCompletion, register_completion

class MyCustomCompletionModel(LLMCompletion):
    ...
    # implementation

# elsewhere...
register_completion("my-custom-completion-model", MyCustomCompletionModel)
```

Then in your config you can reference the type name you used:

```yaml
completion_models:
  default_completion_model:
    type: my-custom-completion-model
    ...

extract_graph:
  completion_model_id: default_completion_model
  prompt: "prompts/extract_graph.txt"
  entity_types: [organization, person, geo, event]
  max_gleanings: 1
```

Note that your custom model will be passed the same params for init and method calls that we use throughout GraphRAG. There is not currently any ability to define custom parameters, so you may need to use closure scope or a factory pattern within your implementation to get custom config values.

---

# 日本語訳

# 言語モデルの選択と上書き

このページでは、GraphRAG で使うモデルの選び方と、独自モデルを使う方法を説明します。なお、これは「どのモデルがあなたの用途に最適か」を選ぶためのガイドではありません。

## デフォルトでサポートするモデル

GraphRAG は OpenAI のモデルを使って開発・検証されてきたため、これを既定のサポート対象として扱っています。これは、あなたの用途に対する品質や適合性を制限する意図ではなく、むしろ GraphRAG がもっともよく理解している、プロンプト調整・チューニング・デバッグの対象という意味です。

GraphRAG は [LiteLLM](https://docs.litellm.ai/) を使って言語モデルを呼び出します。LiteLLM は 100 以上のモデルをサポートしていますが、モデルを選ぶ際には、[構造化出力](https://openai.com/index/introducing-structured-outputs-in-the-api/) を返せること、つまり [JSON schema](https://docs.litellm.ai/docs/completion/json_mode) に従えることが重要です。

LiteLLM を使った設定例は次のとおりです。

```yaml
completion_models:
  default_completion_model:
    model_provider: gemini
    model: gemini-2.5-flash-lite
    auth_method: api_key
    api_key: ${GEMINI_API_KEY}

embedding_models:
  default_embedding_model:
    model_provider: gemini
    model: gemini-embedding-001
    auth_method: api_key
    api_key: ${GEMINI_API_KEY}
```

## モデル選定の考え方

GraphRAG は、OpenAI の gpt-4 系モデル、たとえば gpt-4、gpt-4-turbo、gpt-4o、gpt-4o-mini で最も広くテストされています。たとえば、私たちの [arXiv 論文](https://arxiv.org/abs/2404.16130) では、品質評価に gpt-4-turbo を使いました。前述のとおり、LiteLLM を通じて OpenAI 以外のモデルも使えますが、gpt-4 系は GraphRAG で最もテストが進んでおり、問題解決の手助けもしやすいモデル群です。

GraphRAG 2.2.0 より前は、応答長や内容の制御に `max_tokens` や `logit_bias` を多用していました。o-series モデルの登場で、これらは互換性のない新しいパラメータを持つようになりました。GraphRAG 2.2.0 ではこれらのモデルに対応しましたが、非推論型モデルと比べて、いくつかの重要な違いを理解しておく必要があります。

- 以前は、GraphRAG のいくつかの箇所で `max_tokens` を使って応答を制御していました。これは、後続の要約用コンテキストウィンドウに入る内容量を予測しやすくするためです。現在は、応答長の制御ではなく、予算上の制限として `max_tokens` を使うことを推奨します。o-series の同等パラメータである `max_completion_tokens` もサポートしていますが、これを使うと、応答トークンとは別に一定量の reasoning 消費が発生する可能性があるため、応答制御には適していません。
- 以前は、グラフ抽出時の yes/no 判定を厳密に制御するために `max_tokens` と `logit_bias` を組み合わせていました。推論モデルではこれが使えないため、現在はプロンプトでの制御に切り替えています。gpt-4o、gpt-4o-mini、o1 でのテストでは安定して動作していますが、古いモデルや小さいモデルでは問題が出るかもしれません。
- o-series はより遅く、より高価です。そのため、設定では非対称なモデル運用が有効です。GraphRAG は、`settings.yaml` の `models` ブロックで複数のモデルを定義し、必要な workflow ごとに個別のキーで参照できます。たとえば、indexing には gpt-4o、query には o1 を使う、といった分け方ができます。コスト、速度、品質のバランスを試してください。
- o-series には、非 o-series にはない native な chain-of-thought 推論があります。GraphRAG のプロンプトには、gpt-4* 系で有効だったため CoT が含まれていることがありますが、o-series では逆効果になる可能性があります。そのため、特に graph extraction や claim extraction のプロンプトテンプレートは、大きく調整あるいは書き換えたほうがよい場合があります。

非対称なモデル利用の設定例は次のとおりです。

```yaml
completion_models:
  extraction_completion_model:
    model_provider: openai
    model: gpt-4o
    auth_method: api_key
    api_key: ${GRAPHRAG_API_KEY}
  query_completion_model:
    model_provider: openai
    model: o1
    auth_method: api_key
    api_key: ${GRAPHRAG_API_KEY}
...
extract_graph:
  completion_model_id: extraction_completion_model
  prompt: "prompts/extract_graph.txt"
  entity_types: [organization, person, geo, event]
  max_gleanings: 1
...
global_search:
  completion_model_id: query_completion_model
  map_prompt: "prompts/global_search_map_system_prompt.txt"
  reduce_prompt: "prompts/global_search_reduce_system_prompt.txt"
  knowledge_prompt: "prompts/global_search_knowledge_system_prompt.txt"
```

別の選択肢として、言語モデルを使わずに graph extraction を行う方法もあります。`fast` [indexing method](../index/methods.md) を使うと、LLM API の代わりに NLP を使って一部の処理を行えます。

## 独自モデルの利用

LiteLLM は多くのモデルをサポートしていますが、それでも LiteLLM で対応していないモデルを使いたい場合があります。その場合は、次の 2 つの方法があります。

### Proxy API を使う

多くのユーザーは、[ollama](https://ollama.com/) や [LiteLLM Proxy Server](https://docs.litellm.ai/docs/simple_proxy) のような仕組みを使い、モデルへの HTTP 呼び出しを別のプロバイダに中継しています。これはかなりうまく動きますが、特に JSON などの形式が崩れたレスポンスの問題を見かけます。その場合、モデルに望む形式を返すようプロンプトを調整するか、Proxy 側でレスポンスを修正する必要があります。

### Model Protocol を使う

独自の completion / embedding プロトコルと factory を通じて、未対応のモデルを注入できます。これは CLI ではサポートされていないため、GraphRAG をライブラリとして利用する必要があります。

- プロトコル定義は [こちら](https://github.com/microsoft/graphrag/blob/main/packages/graphrag-llm/graphrag_llm/completion/completion.py) にあります。
- テスト用の簡単な mock 実装は [こちら](https://github.com/microsoft/graphrag/blob/main/packages/graphrag-llm/graphrag_llm/completion/mock_llm_completion.py) を参照してください。

実装を用意したら、completion model factory または embedding model factory に登録します。

```python
from graphrag_llm.completion import LLMCompletion, register_completion

class MyCustomCompletionModel(LLMCompletion):
    ...
    # implementation

# elsewhere...
register_completion("my-custom-completion-model", MyCustomCompletionModel)
```

その後、設定ファイルで次のように型名を参照できます。

```yaml
completion_models:
  default_completion_model:
    type: my-custom-completion-model
    ...

extract_graph:
  completion_model_id: default_completion_model
  prompt: "prompts/extract_graph.txt"
  entity_types: [organization, person, geo, event]
  max_gleanings: 1
```

なお、独自モデルには、GraphRAG 全体で使っているのと同じ初期化パラメータとメソッド呼び出しパラメータが渡されます。現時点では独自パラメータを定義する仕組みはないため、追加の設定値が必要な場合は、実装内で closure scope か factory pattern を使う必要があります。
