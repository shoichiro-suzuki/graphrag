# Indexing Methods

GraphRAG is a platform for our research into RAG indexing methods that produce optimal context window content for language models. We have a standard indexing pipeline that uses a language model to extract the graph that our memory model is based upon. We may introduce additional indexing methods from time to time. This page documents those options.

## Standard GraphRAG

This is the method described in the original [blog post](https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/). Standard uses a language model for all reasoning tasks:

- entity extraction: LLM is prompted to extract named entities and provide a description from each text unit.
- relationship extraction: LLM is prompted to describe the relationship between each pair of entities in each text unit.
- entity summarization: LLM is prompted to combine the descriptions for every instance of an entity found across the text units into a single summary.
- relationship summarization: LLM is prompted to combine the descriptions for every instance of a relationship found across the text units into a single summary.
- claim extraction (optional): LLM is prompted to extract and describe claims from each text unit.
- community report generation: entity and relationship descriptions (and optionally claims) for each community are collected and used to prompt the LLM to generate a summary report.

`graphrag index --method standard`. This is the default method, so the method param can be omitted on the command line.

## FastGraphRAG

FastGraphRAG is a method that substitutes some of the language model reasoning for traditional natural language processing (NLP) methods. This is a hybrid technique that we developed as a faster and cheaper indexing alternative:

- entity extraction: entities are noun phrases extracted using NLP libraries such as NLTK and spaCy. There is no description; the source text unit is used for this.
- relationship extraction: relationships are defined as text unit co-occurrence between entity pairs. There is no description.
- entity summarization: not necessary.
- relationship summarization: not necessary.
- claim extraction: unused.
- community report generation: The direct text unit content containing each entity noun phrase is collected and used to prompt the LLM to generate a summary report.

`graphrag index --method fast`

FastGraphRAG has a handful of NLP [options built in](https://microsoft.github.io/graphrag/config/yaml/#extract_graph_nlp). By default we use NLTK + regular expressions for the noun phrase extraction, which is very fast but primarily suitable for English. We have built in two additional methods using spaCy: semantic parsing and CFG. We use the `en_core_web_md` model by default for spaCy, but note that you can reference any [supported model](https://spacy.io/models/) that you have installed. 

Note that we also generally configure the text chunking to produce much smaller chunks (50-100 tokens). This results in a better co-occurrence graph.

⚠️ Note on SpaCy models:

This package requires SpaCy models to function correctly. If the required model is not installed, the package will automatically download and install it the first time it is used.

You can install it manually by running `python -m spacy download <model_name>`, for example `python -m spacy download en_core_web_md`.


## Choosing a Method

Standard GraphRAG provides a rich description of real-world entities and relationships, but is more expensive than FastGraphRAG. We estimate graph extraction to constitute roughly 75% of indexing cost. FastGraphRAG is therefore much cheaper, but the tradeoff is that the extracted graph is less directly relevant for use outside of GraphRAG, and the graph tends to be quite a bit noisier. If high fidelity entities and graph exploration are important to your use case, we recommend staying with traditional GraphRAG. If your use case is primarily aimed at summary questions using global search, FastGraphRAG provides high quality summarization with much lower language model cost.

---

# 日本語訳

# インデックス方式

GraphRAG は、言語モデル用に最適なコンテキストウィンドウ内容を生成するインデックス手法を研究するためのプラットフォームです。標準のインデックスパイプラインは、LLM を使って、GraphRAG のメモリモデルの基盤となるグラフを抽出します。今後も、追加のインデックス方式を導入することがあります。このページでは、それらの選択肢を説明します。

## 標準 GraphRAG

これは、元の [ブログ記事](https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/) で説明された方式です。Standard では、すべての推論タスクに言語モデルを使います。

- entity extraction: LLM に、各 text unit から固有表現を抽出し、説明を付与させます。
- relationship extraction: LLM に、各 text unit 内の各エンティティ対の関係を記述させます。
- entity summarization: text unit 全体で見つかった各エンティティの説明をまとめ、1 つの要約に統合させます。
- relationship summarization: text unit 全体で見つかった各関係の説明をまとめ、1 つの要約に統合させます。
- claim extraction (optional): LLM に、各 text unit から主張を抽出し、説明させます。
- community report generation: 各コミュニティのエンティティ説明と関係説明、必要に応じて主張を集め、それを使って要約レポートを生成させます。

`graphrag index --method standard` で実行します。これはデフォルト方式なので、コマンドラインでは `method` 引数を省略できます。

## FastGraphRAG

FastGraphRAG は、言語モデルによる推論の一部を、従来型の自然言語処理 (NLP) 手法で置き換える方式です。これは、より高速で低コストなインデックス化の代替案として開発されたハイブリッド手法です。

- entity extraction: NLTK や spaCy などの NLP ライブラリを使って名詞句を抽出します。説明文は生成せず、元の text unit を使います。
- relationship extraction: エンティティ対の text unit 共起を関係として定義します。説明文は生成しません。
- entity summarization: 不要です。
- relationship summarization: 不要です。
- claim extraction: 使用しません。
- community report generation: エンティティの名詞句を含む text unit の生テキストを使って、LLM に要約レポートを生成させます。

`graphrag index --method fast` で実行します。

FastGraphRAG には、いくつかの NLP オプションが組み込まれています。既定では、名詞句抽出に NLTK と正規表現を使います。これは非常に高速ですが、主に英語向けです。さらに spaCy を使う 2 つの方式として、semantic parsing と CFG を用意しています。spaCy の既定モデルは `en_core_web_md` ですが、インストール済みであれば他の [対応モデル](https://spacy.io/models/) も参照できます。

また、通常は text chunking をより小さく設定します。50 から 100 トークン程度にすると、共起グラフの質が良くなります。

## 方式の選び方

Standard GraphRAG は、現実世界のエンティティと関係をより豊かに記述できますが、FastGraphRAG より高コストです。グラフ抽出だけで indexing コストのおよそ 75% を占めると見積もっています。そのため FastGraphRAG はかなり安価ですが、その代わり、抽出されたグラフは GraphRAG 以外で再利用する用途には直接的な関連性が低く、ノイズも多くなりがちです。高忠実度なエンティティやグラフ探索が重要なら、従来の GraphRAG を推奨します。主に global search による要約質問が目的なら、FastGraphRAG はずっと低い LLM コストで高品質な要約を提供します。
