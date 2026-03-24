# Welcome to GraphRAG

👉 [Microsoft Research Blog Post](https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/) <br/>
👉 [GraphRAG Arxiv](https://arxiv.org/pdf/2404.16130)

<p align="center">
<img src="img/GraphRag-Figure1.jpg" alt="Figure 1: LLM-generated knowledge graph built from a private dataset using GPT-4 Turbo." width="450" align="center" />
</p>
<p align="center">
Figure 1: An LLM-generated knowledge graph built using GPT-4 Turbo.
</p>

GraphRAG is a structured, hierarchical approach to Retrieval Augmented Generation (RAG), as opposed to naive semantic-search
approaches using plain text snippets. The GraphRAG process involves extracting a knowledge graph out of raw text, building a community hierarchy, generating summaries for these communities, and then leveraging these structures when perform RAG-based tasks.

To learn more about GraphRAG and how it can be used to enhance your language model's ability to reason about your private data, please visit the [Microsoft Research Blog Post](https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/).

## Get Started with GraphRAG 🚀

To start using GraphRAG, check out the [_Get Started_](get_started.md) guide.
For a deeper dive into the main sub-systems, please visit the docpages for the [Indexer](index/overview.md) and [Query](query/overview.md) packages.

## GraphRAG vs Baseline RAG 🔍

Retrieval-Augmented Generation (RAG) is a technique to improve LLM outputs using real-world information. This technique is an important part of most LLM-based tools and the majority of RAG approaches use vector similarity as the search technique, which we call _Baseline RAG_. GraphRAG uses knowledge graphs to provide substantial improvements in question-and-answer performance when reasoning about complex information. RAG techniques have shown promise in helping LLMs to reason about _private datasets_ - data that the LLM is not trained on and has never seen before, such as an enterprise’s proprietary research, business documents, or communications. _Baseline RAG_ was created to help solve this problem, but we observe situations where baseline RAG performs very poorly. For example:

- Baseline RAG struggles to connect the dots. This happens when answering a question requires traversing disparate pieces of information through their shared attributes in order to provide new synthesized insights.
- Baseline RAG performs poorly when being asked to holistically understand summarized semantic concepts over large data collections or even singular large documents.

To address this, the tech community is working to develop methods that extend and enhance RAG. Microsoft Research’s new approach, GraphRAG, creates a knowledge graph based on an input corpus. This graph, along with community summaries and graph machine learning outputs, are used to augment prompts at query time. GraphRAG shows substantial improvement in answering the two classes of questions described above, demonstrating intelligence or mastery that outperforms other approaches previously applied to private datasets.

## The GraphRAG Process 🤖

GraphRAG builds upon our prior [research](https://www.microsoft.com/en-us/worklab/patterns-hidden-inside-the-org-chart) and [tooling](https://github.com/graspologic-org/graspologic) using graph machine learning. The basic steps of the GraphRAG process are as follows:

### Index

- Slice up an input corpus into a series of TextUnits, which act as analyzable units for the rest of the process, and provide fine-grained references in our outputs.
- Extract all entities, relationships, and key claims from the TextUnits.
- Perform a hierarchical clustering of the graph using the [Leiden technique](https://arxiv.org/pdf/1810.08473.pdf). To see this visually, check out Figure 1 above. Each circle is an entity (e.g., a person, place, or organization), with the size representing the degree of the entity, and the color representing its community.
- Generate summaries of each community and its constituents from the bottom-up. This aids in holistic understanding of the dataset.

### Query

At query time, these structures are used to provide materials for the LLM context window when answering a question. The primary query modes are:

- [_Global Search_](query/global_search.md) for reasoning about holistic questions about the corpus by leveraging the community summaries.
- [_Local Search_](query/local_search.md) for reasoning about specific entities by fanning-out to their neighbors and associated concepts.
- [_DRIFT Search_](query/drift_search.md) for reasoning about specific entities by fanning-out to their neighbors and associated concepts, but with the added context of community information.
- _Basic Search_ for those times when your query is best answered by baseline RAG (standard top _k_ vector search).

### Prompt Tuning

Using _GraphRAG_ with your data out of the box may not yield the best possible results.
We strongly recommend to fine-tune your prompts following the [Prompt Tuning Guide](prompt_tuning/overview.md) in our documentation.


## Versioning

Please see the [breaking changes](https://github.com/microsoft/graphrag/blob/main/breaking-changes.md) document for notes on our approach to versioning the project.

*Always run `graphrag init --root [path] --force` between minor version bumps to ensure you have the latest config format. Run the provided migration notebook between major version bumps if you want to avoid re-indexing prior datasets. Note that this will overwrite your configuration and prompts, so backup if necessary.*

---

# 日本語訳

# GraphRAG へようこそ

👉 [Microsoft Research Blog Post](https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/) <br/>
👉 [GraphRAG Arxiv](https://arxiv.org/pdf/2404.16130)

<p align="center">
<img src="img/GraphRag-Figure1.jpg" alt="Figure 1: GPT-4 Turbo を使って private dataset から構築した LLM 生成の knowledge graph." width="450" align="center" />
</p>
<p align="center">
図 1: GPT-4 Turbo を使って構築した LLM 生成の knowledge graph。
</p>

GraphRAG は、単純な plain text snippet を使う semantic search ベースのアプローチとは異なり、Retrieval Augmented Generation (RAG) に対する構造化された階層的アプローチです。GraphRAG の処理では、元テキストから knowledge graph を抽出し、community 階層を構築し、これらの community の要約を生成し、RAG ベースのタスクを実行するときにこれらの構造を利用します。

GraphRAG と、それがどのように language model の private data に対する推論能力を高めるかについては、[Microsoft Research Blog Post](https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/) を参照してください。

## GraphRAG を始める

GraphRAG を使い始めるには、[_Get Started_](get_started.md) ガイドを確認してください。
主要サブシステムをより深く理解するには、[Indexer](index/overview.md) と [Query](query/overview.md) パッケージのドキュメントページを参照してください。

## GraphRAG と Baseline RAG

Retrieval-Augmented Generation (RAG) は、現実世界の情報を使って LLM の出力を改善する技術です。この技術は多くの LLM ベースのツールで重要な役割を果たしており、RAG アプローチの大半は検索手法として vector similarity を使います。これを私たちは _Baseline RAG_ と呼びます。GraphRAG は knowledge graph を使うことで、複雑な情報を推論する際の質問応答性能を大きく改善します。RAG 技術は、LLM が学習しておらず見たことのない _private dataset_、たとえば企業の独自研究、業務文書、コミュニケーションなどに対して推論させる助けになることが示されています。_Baseline RAG_ はこの問題を解決するために作られましたが、baseline RAG が非常に弱い場面もあります。たとえば次のような場合です。

- Baseline RAG は点と点をつなぐのが苦手です。これは、質問に答えるために、共有属性を通して別々の情報片をたどり、新しい統合的な洞察を出す必要があるときに起こります。
- Baseline RAG は、大きなデータ集合や、単一の大きな文書について、要約された semantic concept を全体として理解するよう求められたときに弱いです。

これに対処するため、技術コミュニティでは RAG を拡張・強化する手法が開発されています。Microsoft Research の新しいアプローチである GraphRAG は、入力コーパスに基づく knowledge graph を作成します。この graph は、community summary や graph machine learning の出力とともに、query 時の prompt を拡張するために使われます。GraphRAG は、上で述べた 2 種類の質問への回答で大きな改善を示しており、private dataset にこれまで適用されてきた他の手法を上回る理解力を示しています。

## GraphRAG の処理

GraphRAG は、graph machine learning を使った先行研究と [tooling](https://github.com/graspologic-org/graspologic) の上に成り立っています。GraphRAG の基本手順は次のとおりです。

### Index

- 入力コーパスを複数の TextUnit に分割します。TextUnit は、その後の処理で分析単位として機能し、出力に細かい参照情報を提供します。
- TextUnit から、すべての entity、relationship、主要な claim を抽出します。
- [Leiden technique](https://arxiv.org/pdf/1810.08473.pdf) を使って graph を階層的にクラスタリングします。図として見たい場合は上の図 1 を参照してください。各円は entity で、サイズは entity の degree、色はその community を表します。
- 各 community とその構成要素の要約を、下位から順に生成します。これはデータセット全体の理解に役立ちます。

### Query

query 時には、これらの構造を使って、質問に答えるための材料を LLM の context window に供給します。主な query モードは次のとおりです。

- [_Global Search_](query/global_search.md) - community summary を活用して、コーパス全体に関する全体的な質問を推論します。
- [_Local Search_](query/local_search.md) - 近傍の entity や関連概念へ展開して、特定 entity を推論します。
- [_DRIFT Search_](query/drift_search.md) - 近傍の entity や関連概念へ展開しますが、community 情報を追加したバージョンです。
- _Basic Search_ - baseline RAG による回答が最も適している場合のための検索です。標準的な top `k` の vector search です。

### Prompt Tuning

GraphRAG をそのまま使うだけでは、最良の結果が得られないことがあります。
ドキュメントの [Prompt Tuning Guide](prompt_tuning/overview.md) に従って、prompt を微調整することを強く推奨します。

## バージョニング

このプロジェクトのバージョニング方針については、[breaking changes](https://github.com/microsoft/graphrag/blob/main/breaking-changes.md) を参照してください。

*マイナーバージョンをまたぐときは、常に `graphrag init --root [path] --force` を実行して、最新の config format を適用してください。メジャーバージョンをまたぐ場合、既存データセットを再 index したくないなら、提供されている migration notebook を実行してください。なお、この操作は設定と prompt を上書きするため、必要ならバックアップを取ってください。*
