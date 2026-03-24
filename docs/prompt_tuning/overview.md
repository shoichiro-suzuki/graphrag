# Prompt Tuning ⚙️

This page provides an overview of the prompt tuning options available for the GraphRAG indexing engine.

## Default Prompts

The default prompts are the simplest way to get started with the GraphRAG system. It is designed to work out-of-the-box with minimal configuration. More details about each of the default prompts for indexing and query can be found on the [manual tuning](./manual_prompt_tuning.md) page.

## Auto Tuning

Auto Tuning leverages your input data and LLM interactions to create domain-adapted prompts for the generation of the knowledge graph. It is highly encouraged to run it as it will yield better results when executing an Index Run. For more details about how to use it, please refer to the [Auto Tuning](auto_prompt_tuning.md) page.

## Manual Tuning

Manual tuning is an advanced use-case. Most users will want to use the Auto Tuning feature instead. Details about how to use manual configuration are available in the [manual tuning](manual_prompt_tuning.md) page.

---

# 日本語訳

## プロンプト調整

このページでは、GraphRAG インデックスエンジンで利用できるプロンプト調整の選択肢を概要として説明します。

## デフォルトプロンプト

デフォルトプロンプトは、GraphRAG を使い始めるための最も簡単な方法です。最小限の設定でそのまま動作するように設計されています。各インデックス用およびクエリ用のデフォルトプロンプトの詳細は、[手動調整](./manual_prompt_tuning.md) のページを参照してください。

## 自動調整

自動調整は、入力データと LLM とのやり取りを利用して、知識グラフ生成に適したドメイン専用プロンプトを作成します。インデックス実行では、より良い結果が得られるため、実行が強く推奨されます。使い方の詳細は、[自動調整](auto_prompt_tuning.md) のページを参照してください。

## 手動調整

手動調整は上級者向けの用途です。多くのユーザーは、代わりに自動調整機能を使うことになるでしょう。手動設定の詳細は、[手動調整](manual_prompt_tuning.md) のページを参照してください。
