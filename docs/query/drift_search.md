# DRIFT Search 🔎

## Combining Local and Global Search

GraphRAG is a technique that uses large language models (LLMs) to create knowledge graphs and summaries from unstructured text documents and leverages them to improve retrieval-augmented generation (RAG) operations on private datasets. It offers comprehensive global overviews of large, private troves of unstructured text documents while also enabling exploration of detailed, localized information. By using LLMs to create comprehensive knowledge graphs that connect and describe entities and relationships contained in those documents, GraphRAG leverages semantic structuring of the data to generate responses to a wide variety of complex user queries.

DRIFT search (Dynamic Reasoning and Inference with Flexible Traversal) builds upon Microsoft’s GraphRAG technique, combining characteristics of both global and local search to generate detailed responses in a method that balances computational costs with quality outcomes using our [drift search](https://github.com/microsoft/graphrag/blob/main//graphrag/query/structured_search/drift_search/) method.

## Methodology

<p align="center">
<img src="https://www.microsoft.com/en-us/research/wp-content/uploads/2024/10/414141-original-w-labels-2048x339.png" alt="Figure 1. An entire DRIFT search hierarchy highlighting the three core phases of the DRIFT search process." align="center" />
</p>
<p align="center"><i><small>
Figure 1. An entire DRIFT search hierarchy highlighting the three core phases of the DRIFT search process. A (Primer): DRIFT compares the user’s query with the top K most semantically relevant community reports, generating a broad initial answer and follow-up questions to steer further exploration. B (Follow-Up): DRIFT uses local search to refine queries, producing additional intermediate answers and follow-up questions that enhance specificity, guiding the engine towards context-rich information. A glyph on each node in the diagram shows the confidence the algorithm has to continue the query expansion step.  C (Output Hierarchy): The final output is a hierarchical structure of questions and answers ranked by relevance, reflecting a balanced mix of global insights and local refinements, making the results adaptable and comprehensive.</small></i></p>


DRIFT Search introduces a new approach to local search queries by including community information in the search process. This greatly expands the breadth of the query’s starting point and leads to retrieval and usage of a far higher variety of facts in the final answer. This addition expands the GraphRAG query engine by providing a more comprehensive option for local search, which uses community insights to refine a query into detailed follow-up questions.

## Configuration

Below are the key parameters of the [DRIFTSearch class](https://github.com/microsoft/graphrag/blob/main//graphrag/query/structured_search/drift_search/search.py):

* `model`: Language model chat completion object to be used for response generation
- `context_builder`: [context builder](https://github.com/microsoft/graphrag/blob/main/graphrag/query/structured_search/drift_search/drift_context.py) object to be used for preparing context data from community reports and query information
- `config`: model to define the DRIFT Search hyperparameters. [DRIFT Config model](https://github.com/microsoft/graphrag/blob/main/graphrag/config/models/drift_search_config.py)
- `tokenizer`: token encoder for tracking the budget for the algorithm.
- `query_state`: a state object as defined in [Query State](https://github.com/microsoft/graphrag/blob/main/graphrag/query/structured_search/drift_search/state.py) that allows to track execution of a DRIFT Search instance, alongside follow ups and [DRIFT actions](https://github.com/microsoft/graphrag/blob/main/graphrag/query/structured_search/drift_search/action.py).

## How to Use

An example of a drift search scenario can be found in the following [notebook](../examples_notebooks/drift_search.ipynb).

## Learn More

For a more in-depth look at the DRIFT search method, please refer to our [DRIFT Search blog post](https://www.microsoft.com/en-us/research/blog/introducing-drift-search-combining-global-and-local-search-methods-to-improve-quality-and-efficiency/)

---

# 日本語訳

# DRIFT Search 🔎

## ローカル検索とグローバル検索の組み合わせ

GraphRAG は、大規模言語モデル（LLM）を使って非構造化テキスト文書から knowledge graph と要約を作成し、それらを活用して private dataset に対する retrieval-augmented generation（RAG）操作を改善する技術です。GraphRAG は、大きな private な非構造化テキスト文書群に対する包括的な全体概観を提供すると同時に、詳細で局所的な情報の探索も可能にします。LLM を使って、これらの文書に含まれる entity と relationship を結び付け、説明する包括的な knowledge graph を作成することで、GraphRAG はデータの semantic structuring を活用し、非常に幅広い複雑なユーザー質問に対する応答を生成します。

DRIFT search（Dynamic Reasoning and Inference with Flexible Traversal）は、Microsoft の GraphRAG 技術の上に構築され、global search と local search の両方の特性を組み合わせて、計算コストと品質のバランスを取りながら詳細な応答を生成する [drift search](https://github.com/microsoft/graphrag/blob/main//graphrag/query/structured_search/drift_search/) メソッドです。

## 方法論

<p align="center">
<img src="https://www.microsoft.com/en-us/research/wp-content/uploads/2024/10/414141-original-w-labels-2048x339.png" alt="図 1. DRIFT search の 3 つの中核フェーズを示す、全体の DRIFT search 階層。" align="center" />
</p>
<p align="center"><i><small>
図 1. DRIFT search の 3 つの中核フェーズを示す、全体の DRIFT search 階層。A（Primer）: DRIFT はユーザーのクエリを、意味的に最も関連性の高い上位 K 件の community report と比較し、探索を進めるための広い初期応答とフォローアップ質問を生成します。B（Follow-Up）: DRIFT は local search を使ってクエリを洗練し、さらに中間応答とフォローアップ質問を生成して具体性を高め、エンジンを文脈豊かな情報へ導きます。図中の各ノード上の記号は、クエリ拡張ステップを続けるためのアルゴリズムの確信度を示します。C（Output Hierarchy）: 最終出力は、関連度でランク付けされた質問と応答の階層構造であり、global な知見と local な洗練のバランスを反映して、結果を適応的かつ包括的なものにします。</small></i></p>


DRIFT Search は、community 情報を検索プロセスに組み込むことで、local search クエリに新しいアプローチを導入します。これにより、クエリの出発点の幅が大きく広がり、最終回答で使われる事実の種類がはるかに増えます。この追加により、GraphRAG の query engine は、community の知見を使ってクエリを詳細なフォローアップ質問へ洗練する、より包括的な local search の選択肢を提供します。

## 構成

以下は、[DRIFTSearch class](https://github.com/microsoft/graphrag/blob/main//graphrag/query/structured_search/drift_search/search.py) の主要なパラメータです。

* `model`: 応答生成に使用する言語モデルの chat completion オブジェクト
* `context_builder`: community report とクエリ情報からコンテキストデータを準備するために使用する [context builder](https://github.com/microsoft/graphrag/blob/main/graphrag/query/structured_search/drift_search/drift_context.py) オブジェクト
* `config`: DRIFT Search のハイパーパラメータを定義するためのモデル。[DRIFT Config model](https://github.com/microsoft/graphrag/blob/main/graphrag/config/models/drift_search_config.py)
* `tokenizer`: アルゴリズムの予算を追跡するための token encoder
* `query_state`: [Query State](https://github.com/microsoft/graphrag/blob/main/graphrag/query/structured_search/drift_search/state.py) で定義される state オブジェクト。DRIFT Search インスタンスの実行、フォローアップ、および [DRIFT actions](https://github.com/microsoft/graphrag/blob/main/graphrag/query/structured_search/drift_search/action.py) を追跡できる

## 使い方

drift search のシナリオの例は、次の [notebook](../examples_notebooks/drift_search.ipynb) にあります。

## 詳細

DRIFT search メソッドのより詳しい説明については、[DRIFT Search のブログ記事](https://www.microsoft.com/en-us/research/blog/introducing-drift-search-combining-global-and-local-search-methods-to-improve-quality-and-efficiency/) を参照してください。
