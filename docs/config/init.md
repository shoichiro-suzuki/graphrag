# Configuring GraphRAG Indexing

To start using GraphRAG, you must generate a configuration file. The `init` command is the easiest way to get started. It will create a `.env` and `settings.yaml` files in the specified directory with the necessary configuration settings. It will also output the default LLM prompts used by GraphRAG.

## Usage

```sh
graphrag init [--root PATH] [--force, --no-force]
```

## Options

- `--root PATH` - The project root directory to initialize graphrag at. Default is the current directory.
- `--force`, `--no-force` - Optional, default is --no-force. Overwrite existing configuration and prompt files if they exist.

## Example

```sh
graphrag init --root ./ragtest
```

## Output

The `init` command will create the following files in the specified directory:

- `settings.yaml` - The configuration settings file. This file contains the configuration settings for GraphRAG.
- `.env` - The environment variables file. These are referenced in the `settings.yaml` file.
- `prompts/` - The LLM prompts folder. This contains the default prompts used by GraphRAG, you can modify them or run the [Auto Prompt Tuning](../prompt_tuning/auto_prompt_tuning.md) command to generate new prompts adapted to your data.

## Next Steps

After initializing your workspace, you can either run the [Prompt Tuning](../prompt_tuning/auto_prompt_tuning.md) command to adapt the prompts to your data or even start running the [Indexing Pipeline](../index/overview.md) to index your data. For more information on configuration options available, see the [YAML details page](yaml.md).

---

# 日本語訳

# GraphRAG の設定初期化

GraphRAG を使い始めるには、設定ファイルを生成する必要があります。`init` コマンドが、最も簡単な開始方法です。指定したディレクトリに、必要な設定を含む `.env` と `settings.yaml` を作成します。また、GraphRAG で使う既定の LLM プロンプトも出力します。

## 使い方

```sh
graphrag init [--root PATH] [--force, --no-force]
```

## オプション

- `--root PATH` - GraphRAG を初期化するプロジェクトのルートディレクトリです。既定値はカレントディレクトリです。
- `--force`, `--no-force` - 任意指定です。既定値は `--no-force` です。既存の設定ファイルやプロンプトファイルがある場合、それらを上書きします。

## 実行例

```sh
graphrag init --root ./ragtest
```

## 出力

`init` コマンドは、指定したディレクトリに次のファイルを作成します。

- `settings.yaml` - 設定ファイルです。GraphRAG の設定内容が含まれます。
- `.env` - 環境変数ファイルです。これらは `settings.yaml` から参照されます。
- `prompts/` - LLM プロンプト用フォルダです。GraphRAG が使う既定プロンプトが含まれます。必要に応じて編集できますし、[Auto Prompt Tuning](../prompt_tuning/auto_prompt_tuning.md) コマンドを実行して、データに合わせた新しいプロンプトを生成することもできます。

## 次のステップ

ワークスペースの初期化後は、[Prompt Tuning](../prompt_tuning/auto_prompt_tuning.md) コマンドを実行してプロンプトをデータに合わせることもできますし、[Indexing Pipeline](../index/overview.md) を実行してデータの index を作成することもできます。利用可能な設定オプションの詳細は、[YAML 詳細ページ](yaml.md) を参照してください。
