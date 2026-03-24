# Manual Prompt Tuning ⚙️

The GraphRAG indexer, by default, will run with a handful of prompts that are designed to work well in the broad context of knowledge discovery.
However, it is quite common to want to tune the prompts to better suit your specific use case.
We provide a means for you to do this by allowing you to specify a custom prompt file, which will each use a series of token-replacements internally.

Each of these prompts may be overridden by writing a custom prompt file in plaintext. We use token-replacements in the form of `{token_name}`, and the descriptions for the available tokens can be found below.

## Indexing Prompts

### Entity/Relationship Extraction

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/index/extract_graph.py)

#### Tokens

- **{input_text}** - The input text to be processed.
- **{entity_types}** - A list of entity types
- **{tuple_delimiter}** - A delimiter for separating values within a tuple. A single tuple is used to represent an individual entity or relationship.
- **{record_delimiter}** - A delimiter for separating tuple instances.
- **{completion_delimiter}** - An indicator for when generation is complete.

### Summarize Entity/Relationship Descriptions

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/index/summarize_descriptions.py)

#### Tokens

- **{entity_name}** - The name of the entity or the source/target pair of the relationship.
- **{description_list}** - A list of descriptions for the entity or relationship.

### Claim Extraction

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/index/extract_claims.py)

#### Tokens

- **{input_text}** - The input text to be processed.
- **{tuple_delimiter}** - A delimiter for separating values within a tuple. A single tuple is used to represent an individual entity or relationship.
- **{record_delimiter}** - A delimiter for separating tuple instances.
- **{completion_delimiter}** - An indicator for when generation is complete.
- **{entity_specs}** - A list of entity types.
- **{claim_description}** - Description of what claims should look like. Default is: `"Any claims or facts that could be relevant to information discovery."`

See the [configuration documentation](../config/overview.md) for details on how to change this.

### Generate Community Reports

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/index/community_report.py)

#### Tokens

- **{input_text}** - The input text to generate the report with. This will contain tables of entities and relationships.

## Query Prompts

### Local Search

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/query/local_search_system_prompt.py)

#### Tokens

- **{response_type}** - Describe how the response should look. We default to "multiple paragraphs".
- **{context_data}** - The data tables from GraphRAG's index.

### Global Search

[Mapper Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/query/global_search_map_system_prompt.py)

[Reducer Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/query/global_search_reduce_system_prompt.py)

[Knowledge Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/query/global_search_knowledge_system_prompt.py)

Global search uses a map/reduce approach to summarization. You can tune these prompts independently. This search also includes the ability to adjust the use of general knowledge from the model's training.

#### Tokens

- **{response_type}** - Describe how the response should look (reducer only). We default to "multiple paragraphs".
- **{context_data}** - The data tables from GraphRAG's index.

### Drift Search

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/query/drift_search_system_prompt.py)

#### Tokens

- **{response_type}** - Describe how the response should look. We default to "multiple paragraphs".
- **{context_data}** - The data tables from GraphRAG's index.
- **{community_reports}** - The most relevant community reports to include in the summarization.
- **{query}** - The query text as injected into the context.

---

# 日本語訳

# 手動プロンプト調整

GraphRAG のインデクサーは、既定では知識探索の広い用途にうまく動作するよう設計された一連のプロンプトで実行されます。
ただし、実際には、特定の用途により適した形へプロンプトを調整したいことがよくあります。
そのために、GraphRAG では、カスタムのプレーンテキストプロンプトファイルを指定できるようにしています。内部では、いくつかのトークン置換を使います。

各プロンプトは、プレーンテキストのカスタムプロンプトファイルを用意することで上書きできます。トークン置換は `{token_name}` の形式で行われ、利用可能なトークンの説明は以下に示します。

## インデックス用プロンプト

### Entity/Relationship Extraction

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/index/extract_graph.py)

#### トークン

- **{input_text}** - 処理対象の入力テキストです。
- **{entity_types}** - entity type の一覧です。
- **{tuple_delimiter}** - タプル内の値を区切るための区切り文字です。1 つのタプルは 1 つの entity または relationship を表します。
- **{record_delimiter}** - タプル同士を区切るための区切り文字です。
- **{completion_delimiter}** - 生成が完了したことを示す記号です。

### Entity/Relationship の説明要約

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/index/summarize_descriptions.py)

#### トークン

- **{entity_name}** - entity の名前、または relationship の source/target ペアです。
- **{description_list}** - entity または relationship の説明の一覧です。

### Claim Extraction

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/index/extract_claims.py)

#### トークン

- **{input_text}** - 処理対象の入力テキストです。
- **{tuple_delimiter}** - タプル内の値を区切るための区切り文字です。1 つのタプルは 1 つの entity または relationship を表します。
- **{record_delimiter}** - タプル同士を区切るための区切り文字です。
- **{completion_delimiter}** - 生成が完了したことを示す記号です。
- **{entity_specs}** - entity type の一覧です。
- **{claim_description}** - 抽出したい claim の説明です。既定値は `"Any claims or facts that could be relevant to information discovery."` です。

詳細は、これを変更する方法についての [設定ドキュメント](../config/overview.md) を参照してください。

### コミュニティレポートの生成

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/index/community_report.py)

#### トークン

- **{input_text}** - レポート生成に使う入力テキストです。ここには entity と relationship の表が含まれます。

## クエリ用プロンプト

### Local Search

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/query/local_search_system_prompt.py)

#### トークン

- **{response_type}** - 返答の見た目を指定します。既定値は `"multiple paragraphs"` です。
- **{context_data}** - GraphRAG の index から作られたデータ表です。

### Global Search

[Mapper Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/query/global_search_map_system_prompt.py)

[Reducer Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/query/global_search_reduce_system_prompt.py)

[Knowledge Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/query/global_search_knowledge_system_prompt.py)

Global search は map/reduce 型の要約を使います。各プロンプトは独立して調整できます。また、モデルが事前学習で持つ一般知識をどの程度使うかも調整できます。

#### トークン

- **{response_type}** - 返答の見た目を指定します。reducer 側で使います。既定値は `"multiple paragraphs"` です。
- **{context_data}** - GraphRAG の index から作られたデータ表です。

### Drift Search

[Prompt Source](http://github.com/microsoft/graphrag/blob/main/graphrag/prompts/query/drift_search_system_prompt.py)

#### トークン

- **{response_type}** - 返答の見た目を指定します。既定値は `"multiple paragraphs"` です。
- **{context_data}** - GraphRAG の index から作られたデータ表です。
- **{community_reports}** - 要約に含める、最も関連性の高い community report です。
- **{query}** - context に埋め込む query テキストです。
