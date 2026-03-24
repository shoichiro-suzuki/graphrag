# Getting Started

⚠️ GraphRAG can consume a lot of LLM resources! We strongly recommend starting with the tutorial dataset here until you understand how the system works, and consider experimenting with fast/inexpensive models first before committing to a big indexing job.

## Requirements

[Python 3.10-3.12](https://www.python.org/downloads/)

The following is a simple end-to-end example for using GraphRAG on the command line after installing from [pypi](https://pypi.org/project/graphrag/).

It shows how to use the system to index some text, and then use the indexed data to answer questions about the documents.

## Install GraphRAG

To get started, create a project space and python virtual environment to install `graphrag`.

### Create Project Space

```bash
mkdir graphrag_quickstart
cd graphrag_quickstart
python -m venv .venv
```
### Activate Python Virtual Environment - Unix/MacOS

```bash
source .venv/bin/activate
```

### Activate Python Virtual Environment - Windows

```bash
.venv\Scripts\activate
```

### Install GraphRAG

```bash
python -m pip install graphrag
```

### Initialize GraphRAG

To initialize your workspace, first run the `graphrag init` command.

```sh
graphrag init
```

When prompted, specify the default chat and embedding models you would like to use in your config.

This will create two files, `.env` and `settings.yaml`, and a directory `input`, in the current directory.

- `input` Location of text files to process with `graphrag`.
- `.env` contains the environment variables required to run the GraphRAG pipeline. If you inspect the file, you'll see a single environment variable defined,
  `GRAPHRAG_API_KEY=<API_KEY>`. Replace `<API_KEY>` with your own OpenAI or Azure API key.
- `settings.yaml` contains the settings for the pipeline. You can modify this file to change the settings for the pipeline.

### Download Sample Text

Get a copy of A Christmas Carol by Charles Dickens from a trusted source:

```sh
curl https://www.gutenberg.org/cache/epub/24022/pg24022.txt -o ./input/book.txt
```

## Set Up Workspace Variables

### Using OpenAI

If running in OpenAI mode, you only need to update the value of `GRAPHRAG_API_KEY` in the `.env` file with your OpenAI API key.

### Using Azure OpenAI

In addition to setting your API key, Azure OpenAI users should set the variables below in the settings.yaml file. To find the appropriate sections, just search for the `models:` root configuration; you should see two sections, one for the default chat endpoint and one for the default embeddings endpoint. Here is an example of what to add to the chat model config:

```yaml
type: chat
model_provider: azure
model: gpt-4.1
deployment_name: <AZURE_DEPLOYMENT_NAME>
api_base: https://<instance>.openai.azure.com
api_version: 2024-02-15-preview # You can customize this for other versions
```

#### Using Managed Auth on Azure

To use managed auth, edit the auth_type in your model config and *remove* the api_key line:

```yaml
auth_type: azure_managed_identity # Default auth_type is is api_key
```

You will also need to login with [az login](https://learn.microsoft.com/en-us/cli/azure/authenticate-azure-cli) and select the subscription with your endpoint.

## Index

Now we're ready to index!

```sh
graphrag index
```

![pipeline executing from the CLI](img/pipeline-running.png)

This process will usually take a few minutes to run. Once the pipeline is complete, you should see a new folder called `./output` with a series of parquet files.

# Query

Now let's ask some questions using this dataset.

Here is an example using Global search to ask a high-level question:

```sh
graphrag query "What are the top themes in this story?"
```

Here is an example using Local search to ask a more specific question about a particular character:

```sh
graphrag query \
"Who is Scrooge and what are his main relationships?" \
--method local
```

Please refer to [Query Engine](query/overview.md) docs for detailed information about how to leverage our Local and Global search mechanisms for extracting meaningful insights from data after the Indexer has wrapped up execution.

# Going Deeper

- For more details about configuring GraphRAG, see the [configuration documentation](config/overview.md).
- To learn more about Initialization, refer to the [Initialization documentation](config/init.md).
- For more details about using the CLI, refer to the [CLI documentation](cli.md).
- Check out our [visualization guide](visualization_guide.md) for a more interactive experience in debugging and exploring the knowledge graph.

---

# 日本語訳

# Getting Started

⚠️ GraphRAG は多くの LLM リソースを消費する可能性があります。システムの動作を理解するまでは、このチュートリアル用データセットから始めることを強く推奨します。大きな indexing を実行する前に、まず高速で低コストなモデルを試すことを検討してください。

## 要件

[Python 3.10-3.12](https://www.python.org/downloads/)

以下は、[pypi](https://pypi.org/project/graphrag/) からインストールしたあと、コマンドラインで GraphRAG を使うための、シンプルな end-to-end の例です。

この例では、テキストを index し、その index 済みデータを使って文書に関する質問に答える方法を示します。

## GraphRAG のインストール

まず、`graphrag` をインストールするためのプロジェクト領域と Python の仮想環境を作成します。

### プロジェクト領域の作成

```bash
mkdir graphrag_quickstart
cd graphrag_quickstart
python -m venv .venv
```

### Python 仮想環境の有効化 - Unix/MacOS

```bash
source .venv/bin/activate
```

### Python 仮想環境の有効化 - Windows

```bash
.venv\Scripts\activate
```

### GraphRAG のインストール

```bash
python -m pip install graphrag
```

### GraphRAG の初期化

ワークスペースを初期化するには、まず `graphrag init` コマンドを実行します。

```sh
graphrag init
```

プロンプトが表示されたら、設定で使いたい既定の chat model と embedding model を指定してください。

これにより、現在のディレクトリに `.env`、`settings.yaml`、`input` ディレクトリの 3 つが作成されます。

- `input` - `graphrag` で処理するテキストファイルの置き場所です。
- `.env` - GraphRAG pipeline の実行に必要な環境変数を含みます。ファイルを確認すると、`GRAPHRAG_API_KEY=<API_KEY>` という 1 つの環境変数が定義されているはずです。`<API_KEY>` を、ご自身の OpenAI か Azure の API key に置き換えてください。
- `settings.yaml` - pipeline の設定を含みます。このファイルを編集すると、pipeline の設定を変更できます。

### サンプルテキストのダウンロード

Charles Dickens の *A Christmas Carol* を、信頼できるソースから入手します。

```sh
curl https://www.gutenberg.org/cache/epub/24022/pg24022.txt -o ./input/book.txt
```

## ワークスペース変数の設定

### OpenAI を使う場合

OpenAI モードで実行する場合は、`.env` ファイルの `GRAPHRAG_API_KEY` の値を、OpenAI API key に更新するだけで構いません。

### Azure OpenAI を使う場合

API key の設定に加えて、Azure OpenAI を使う場合は `settings.yaml` に以下の変数を設定してください。該当箇所は `models:` の root 設定を探すと見つかります。chat endpoint 用と embeddings endpoint 用の 2 セクションがあるはずです。以下は chat model 設定に追加する例です。

```yaml
type: chat
model_provider: azure
model: gpt-4.1
deployment_name: <AZURE_DEPLOYMENT_NAME>
api_base: https://<instance>.openai.azure.com
api_version: 2024-02-15-preview # You can customize this for other versions
```

#### Azure で Managed Auth を使う場合

managed auth を使うには、model config の `auth_type` を編集し、`api_key` 行を削除します。

```yaml
auth_type: azure_managed_identity # Default auth_type is is api_key
```

また、[az login](https://learn.microsoft.com/en-us/cli/azure/authenticate-azure-cli) でログインし、endpoint のある subscription を選択する必要があります。

## Index

それでは、index を実行できます。

```sh
graphrag index
```

![pipeline executing from the CLI](img/pipeline-running.png)

この処理には通常、数分かかります。pipeline が完了すると、`./output` フォルダが新しく作成され、その中に一連の parquet ファイルが出力されます。

# Query

それでは、このデータセットに質問してみましょう。

以下は、Global search を使って高レベルの質問をする例です。

```sh
graphrag query "What are the top themes in this story?"
```

以下は、Local search を使って特定の登場人物についてより具体的な質問をする例です。

```sh
graphrag query \
"Who is Scrooge and what are his main relationships?" \
--method local
```

Indexer の実行後に、データから意味のある洞察を引き出すために Local / Global search をどう活用するかについては、[Query Engine](query/overview.md) のドキュメントを参照してください。

# さらに進む

- GraphRAG の設定の詳細は、[configuration documentation](config/overview.md) を参照してください。
- Initialization の詳細は、[Initialization documentation](config/init.md) を参照してください。
- CLI の使い方の詳細は、[CLI documentation](cli.md) を参照してください。
- 知識グラフのデバッグや探索を、より対話的に行うには [visualization guide](visualization_guide.md) を参照してください。
