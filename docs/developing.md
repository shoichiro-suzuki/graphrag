# Development Guide

# Requirements

| Name                | Installation                                                 | Purpose                                                                             |
| ------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| Python 3.10-3.12    | [Download](https://www.python.org/downloads/)                | The library is Python-based.                                                        |
| uv                  | [Instructions](https://docs.astral.sh/uv/)                   | uv is used for package management and virtualenv management in Python codebases     |

# Getting Started

## Install Dependencies

```sh
# install python dependencies
uv sync --all-packages
```

## Execute the Indexing Engine

```sh
uv run poe index <...args>
```

## Executing Queries

```sh
uv run poe query <...args>
```

# Azurite

Some unit and smoke tests use Azurite to emulate Azure resources. This can be started by running:

```sh
./scripts/start-azurite.sh
```

or by simply running `azurite` in the terminal if already installed globally. See the [Azurite documentation](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite) for more information about how to install and use Azurite.

# Lifecycle Scripts

Our Python package utilize uv to manage dependencies and [poethepoet](https://pypi.org/project/poethepoet/) to manage build scripts.

Available scripts are:

- `uv run poe index` - Run the Indexing CLI
- `uv run poe query` - Run the Query CLI
- `uv build` - This will build a wheel file and other distributable artifacts.
- `uv run poe test` - This will execute all tests.
- `uv run poe test_unit` - This will execute unit tests.
- `uv run poe test_integration` - This will execute integration tests.
- `uv run poe test_smoke` - This will execute smoke tests.
- `uv run poe test_verbs` - This will execute tests of the basic workflows.
- `uv run poe check` - This will perform a suite of static checks across the package, including:
  - formatting
  - documentation formatting
  - linting
  - security patterns
  - type-checking
- `uv run poe fix` - This will apply any available auto-fixes to the package. Usually this is just formatting fixes.
- `uv run poe fix_unsafe` - This will apply any available auto-fixes to the package, including those that may be unsafe.
- `uv run poe format` - Explicitly run the formatter across the package.

## Troubleshooting

### "RuntimeError: llvm-config failed executing, please point LLVM_CONFIG to the path for llvm-config" when running uv install

Make sure llvm-9 and llvm-9-dev are installed:

`sudo apt-get install llvm-9 llvm-9-dev`

and then in your bashrc, add

`export LLVM_CONFIG=/usr/bin/llvm-config-9`

---

# 日本語訳

# 開発ガイド

## 要件

| 名前 | インストール | 目的 |
| --- | --- | --- |
| Python 3.10-3.12 | [Download](https://www.python.org/downloads/) | このライブラリは Python ベースです。 |
| uv | [Instructions](https://docs.astral.sh/uv/) | uv は Python コードベースでのパッケージ管理と virtualenv 管理に使います。 |

## はじめに

### 依存関係のインストール

```sh
# install python dependencies
uv sync --all-packages
```

### Indexing Engine の実行

```sh
uv run poe index <...args>
```

### Query の実行

```sh
uv run poe query <...args>
```

## Azurite

一部の unit test と smoke test では、Azure リソースを模擬するために Azurite を使います。次のコマンドで起動できます。

```sh
./scripts/start-azurite.sh
```

あるいは、すでにグローバルにインストールされていれば、ターミナルで `azurite` を実行するだけでも構いません。Azurite のインストール方法や使い方の詳細は [Azurite documentation](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite) を参照してください。

## ライフサイクルスクリプト

この Python パッケージは、依存関係の管理に uv を、ビルドスクリプトの管理に [poethepoet](https://pypi.org/project/poethepoet/) を使っています。

利用可能なスクリプトは次のとおりです。

- `uv run poe index` - Indexing CLI を実行します。
- `uv run poe query` - Query CLI を実行します。
- `uv build` - wheel ファイルやその他の配布用成果物をビルドします。
- `uv run poe test` - すべてのテストを実行します。
- `uv run poe test_unit` - unit test を実行します。
- `uv run poe test_integration` - integration test を実行します。
- `uv run poe test_smoke` - smoke test を実行します。
- `uv run poe test_verbs` - 基本 workflow のテストを実行します。
- `uv run poe check` - パッケージ全体に対して静的チェックを実行します。内容は次のとおりです。
  - formatting
  - documentation formatting
  - linting
  - security patterns
  - type-checking
- `uv run poe fix` - 利用可能な自動修正を適用します。通常は formatting 修正です。
- `uv run poe fix_unsafe` - unsafe になりうるものも含め、利用可能な自動修正を適用します。
- `uv run poe format` - パッケージ全体に formatter を明示的に実行します。

## トラブルシューティング

### `uv install` 実行時に `"RuntimeError: llvm-config failed executing, please point LLVM_CONFIG to the path for llvm-config"` が出る場合

`llvm-9` と `llvm-9-dev` がインストールされていることを確認してください。

```sh
sudo apt-get install llvm-9 llvm-9-dev
```

そのうえで、`bashrc` に次を追加してください。

```sh
export LLVM_CONFIG=/usr/bin/llvm-config-9
```
