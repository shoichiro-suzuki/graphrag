# GraphRAG Indexing 🤖

The GraphRAG indexing package is a data pipeline and transformation suite that is designed to extract meaningful, structured data from unstructured text using LLMs.

Indexing Pipelines are configurable. They are composed of workflows, standard and custom steps, prompt templates, and input/output adapters. Our standard pipeline is designed to:

- extract entities, relationships and claims from raw text
- perform community detection in entities
- generate community summaries and reports at multiple levels of granularity
- embed text into a vector space

The outputs of the pipeline are stored as Parquet tables by default, and embeddings are written to your configured vector store.

## Getting Started

### Requirements

See the [requirements](../developing.md#requirements) section in [Get Started](../get_started.md) for details on setting up a development environment.

To configure GraphRAG, see the [configuration](../config/overview.md) documentation.
After you have a config file you can run the pipeline using the CLI or the Python API.

## Usage

### CLI

```bash
uv run poe index --root <data_root> # default config mode
```

### Python API

Please see the indexing API [python file](https://github.com/microsoft/graphrag/blob/main/graphrag/api/index.py) for the recommended method to call directly from Python code.

## Further Reading

- To start developing within the _GraphRAG_ project, see [getting started](../developing.md)
- To understand the underlying concepts and execution model of the indexing library, see [the architecture documentation](../index/architecture.md)
- To read more about configuring the indexing engine, see [the configuration documentation](../config/overview.md)

---

# 日本語訳

# GraphRAG インデックス

GraphRAG の indexing パッケージは、LLM を使って非構造テキストから意味のある構造化データを抽出するためのデータパイプラインと変換スイートです。

Indexing pipeline は設定可能です。workflow、標準ステップとカスタムステップ、プロンプトテンプレート、入力/出力アダプタで構成されます。標準パイプラインは次を行うよう設計されています。

- 生テキストから entity、relationship、claim を抽出する
- entity の community detection を実行する
- さまざまな粒度で community summary と report を生成する
- テキストをベクトル空間に埋め込む

パイプラインの出力は既定で Parquet テーブルとして保存され、embedding は設定した vector store に書き込まれます。

## はじめに

### 要件

開発環境の構築方法の詳細は、[Get Started](../get_started.md) の [requirements](../developing.md#requirements) セクションを参照してください。

GraphRAG の設定方法は、[configuration](../config/overview.md) のドキュメントを参照してください。
設定ファイルを用意したら、CLI または Python API でパイプラインを実行できます。

## 使い方

### CLI

```bash
uv run poe index --root <data_root> # default config mode
```

### Python API

Python から直接呼び出す推奨方法は、indexing API の [python file](https://github.com/microsoft/graphrag/blob/main/graphrag/api/index.py) を参照してください。

## さらに読む

- GraphRAG プロジェクトで開発を始めるには、[getting started](../developing.md) を参照してください
- indexing ライブラリの基礎概念と実行モデルを理解するには、[architecture documentation](../index/architecture.md) を参照してください
- indexing engine の設定についてさらに読むには、[configuration documentation](../config/overview.md) を参照してください
