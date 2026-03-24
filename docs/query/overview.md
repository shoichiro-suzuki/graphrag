# Query Engine 🔎

The Query Engine is the retrieval module of the GraphRAG library, and operates over completed [indexes](../index/overview.md).
It is responsible for the following tasks:

- [Local Search](#local-search)
- [Global Search](#global-search)
- [DRIFT Search](#drift-search)
- Basic Search
- [Question Generation](#question-generation)

## Local Search

Local search generates answers by combining relevant data from the AI-extracted knowledge-graph with text chunks of the raw documents. This method is suitable for questions that require an understanding of specific entities mentioned in the documents (e.g. What are the healing properties of chamomile?).

For more details about how Local Search works please refer to the [Local Search](local_search.md) page.

## Global Search

Global search generates answers by searching over all AI-generated community reports in a map-reduce fashion. This is a resource-intensive method, but often gives good responses for questions that require an understanding of the dataset as a whole (e.g. What are the most significant values of the herbs mentioned in this notebook?).

More about this is provided on the [Global Search](global_search.md) page.

## DRIFT Search

DRIFT Search introduces a new approach to local search queries by including community information in the search process. This greatly expands the breadth of the query’s starting point and leads to retrieval and usage of a far higher variety of facts in the final answer. This expands the GraphRAG query engine by providing a more comprehensive option for local search, which uses community insights to refine a query into detailed follow-up questions.

To learn more about DRIFT Search, please refer to the [DRIFT Search](drift_search.md) page.

## Basic Search

GraphRAG includes a rudimentary implementation of basic vector RAG to make it easy to compare different search results based on the type of question you are asking. You can specify the top `k` text unit chunks to include in the summarization context.

## Question Generation

This functionality takes a list of user queries and generates the next candidate questions. This is useful for generating follow-up questions in a conversation or for generating a list of questions for the investigator to dive deeper into the dataset.

Information about how question generation works can be found at the [Question Generation](question_generation.md) documentation page.

---

# 日本語訳

# Query Engine

Query Engine は GraphRAG ライブラリの retrieval モジュールであり、完成済みの [index](../index/overview.md) に対して動作します。主に次の処理を担当します。

- [Local Search](#local-search)
- [Global Search](#global-search)
- [DRIFT Search](#drift-search)
- Basic Search
- [Question Generation](#question-generation)

## Local Search

Local search は、AI が抽出した knowledge graph の関連データと元文書の text chunk を組み合わせて回答を生成します。この方式は、文書内で言及された特定の entity を理解する必要がある質問に向いています。たとえば「カモミールの治癒特性は何か？」のような質問です。

Local Search の仕組みの詳細は [Local Search](local_search.md) ページを参照してください。

## Global Search

Global search は、AI が生成したすべての community report を map-reduce 形式で検索して回答を生成します。これは計算資源を多く使う方式ですが、データセット全体の理解が必要な質問にはよい結果を返すことが多いです。たとえば「このノートブックで言及されているハーブの中で、最も重要な価値は何か？」のような質問です。

詳細は [Global Search](global_search.md) ページを参照してください。

## DRIFT Search

DRIFT Search は、community 情報を検索プロセスに組み込むことで、local search クエリに新しいアプローチを導入します。これにより、クエリの出発点の幅が大きく広がり、最終回答で使われる事実の種類が大幅に増えます。GraphRAG の query engine を拡張し、community の知見を使ってクエリを詳細なフォローアップ質問へと絞り込む、より包括的な local search の विकल्पを提供します。

DRIFT Search の詳細は [DRIFT Search](drift_search.md) ページを参照してください。

## Basic Search

GraphRAG には、使っている質問の種類に応じて異なる検索結果を比較しやすくするための、基本的な vector RAG 実装も含まれています。要約コンテキストに含める top `k` 個の text unit chunk を指定できます。

## Question Generation

この機能は、ユーザーの質問リストを受け取り、次に候補となる質問を生成します。会話のフォローアップ質問を作る用途や、調査者がデータセットをさらに掘り下げるための質問リストを作る用途に有効です。

Question generation の仕組みは [Question Generation](question_generation.md) のドキュメントページを参照してください。
