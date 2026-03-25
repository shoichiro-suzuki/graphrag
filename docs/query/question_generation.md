# Question Generation ❔

## Entity-based Question Generation

The [question generation](https://github.com/microsoft/graphrag/blob/main//graphrag/query/question_gen/) method combines structured data from the knowledge graph with unstructured data from the input documents to generate candidate questions related to specific entities.

## Methodology
Given a list of prior user questions, the question generation method uses the same context-building approach employed in [local search](local_search.md) to extract and prioritize relevant structured and unstructured data, including entities, relationships, covariates, community reports and raw text chunks. These data records are then fitted into a single LLM prompt to generate candidate follow-up questions that represent the most important or urgent information content or themes in the data.

## Configuration

Below are the key parameters of the [Question Generation class](https://github.com/microsoft/graphrag/blob/main//graphrag/query/question_gen/local_gen.py):

* `model`: Language model chat completion object to be used for response generation
* `context_builder`: [context builder](https://github.com/microsoft/graphrag/blob/main//graphrag/query/structured_search/local_search/mixed_context.py) object to be used for preparing context data from collections of knowledge model objects, using the same context builder class as in local search
* `system_prompt`: prompt template used to generate candidate questions. Default template can be found at [system_prompt](https://github.com/microsoft/graphrag/blob/main//graphrag/prompts/query/question_gen_system_prompt.py)
* `llm_params`: a dictionary of additional parameters (e.g., temperature, max_tokens) to be passed to the LLM call
* `context_builder_params`: a dictionary of additional parameters to be passed to the [`context_builder`](https://github.com/microsoft/graphrag/blob/main//graphrag/query/structured_search/local_search/mixed_context.py) object when building context for the question generation prompt
* `callbacks`: optional callback functions, can be used to provide custom event handlers for LLM's completion streaming events

## How to Use

An example of the question generation function can be found in the following [notebook](../examples_notebooks/local_search.ipynb).

---

# 日本語訳

# Question Generation ❔

## エンティティベースの質問生成

[question generation](https://github.com/microsoft/graphrag/blob/main//graphrag/query/question_gen/) method は、knowledge graph の構造化データと input documents の非構造化データを組み合わせて、特定の entity に関連する候補質問を生成します。

## 方法

事前のユーザー質問の一覧を与えると、question generation method は [local search](local_search.md) で使われるものと同じ context-building アプローチを使って、entity、relationship、covariate、community report、raw text chunk を含む関連する構造化データと非構造化データを抽出し、優先順位を付けます。これらのデータレコードは、その後、単一の LLM prompt にまとめられ、データ内で最も重要または緊急性の高い情報内容やテーマを表す候補の follow-up questions を生成します。

## 設定

以下は [Question Generation class](https://github.com/microsoft/graphrag/blob/main//graphrag/query/question_gen/local_gen.py) の主要パラメータです。

* `model`: 応答生成に使用する language model の chat completion object
* `context_builder`: [context builder](https://github.com/microsoft/graphrag/blob/main//graphrag/query/structured_search/local_search/mixed_context.py) object。knowledge model objects のコレクションから context data を準備するために使用します。local search と同じ context builder class を使います
* `system_prompt`: candidate questions を生成するための prompt template。既定の template は [system_prompt](https://github.com/microsoft/graphrag/blob/main//graphrag/prompts/query/question_gen_system_prompt.py) にあります
* `llm_params`: LLM 呼び出しに渡す追加パラメータの dictionary（例: temperature, max_tokens）
* `context_builder_params`: question generation prompt の context を構築するときに [`context_builder`](https://github.com/microsoft/graphrag/blob/main//graphrag/query/structured_search/local_search/mixed_context.py) object に渡す追加パラメータの dictionary
* `callbacks`: 任意の callback function。LLM の completion streaming event に対してカスタム event handler を提供するために使用できます

## 使い方

question generation function の例は、次の [notebook](../examples_notebooks/local_search.ipynb) にあります。
