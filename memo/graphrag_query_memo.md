# GraphRAG Query 種別の覚書

## 目的

`graphrag index` 後に使えるクエリの種類と、各方式の概要・コマンド例を1枚で見られるように整理する。

## 前提

- `graphrag query` は完成済みの index に対して動作する。([docs/query/overview.md](../docs/query/overview.md))
- CLI の `--method` は `global` / `local` / `drift` / `basic` を受け付ける。既定は `global`。([packages/graphrag/graphrag/cli/main.py](../packages/graphrag/graphrag/cli/main.py))
- `Question Generation` は `graphrag query` の method ではなく、別の機能として扱われる。([docs/query/overview.md](../docs/query/overview.md), [docs/query/question_generation.md](../docs/query/question_generation.md))

## 方式一覧

| 種別 | 概要 | 向いている質問 | コマンド例 |
| --- | --- | --- | --- |
| `global` | community report をまとめて、データセット全体を map-reduce で要約する。 | 全体傾向、テーマ、横断的な要約 | `graphrag query "What are the top themes in this story?"` |
| `local` | knowledge graph の entity と raw text を組み合わせ、特定 entity を深掘りする。 | 特定人物、物、概念の詳細 | `graphrag query "Who is Scrooge and what are his main relationships?" --method local` |
| `drift` | local search を拡張し、community 情報を使って段階的に探索する。 | 深掘りが必要だが、local だけでは広がりが足りない質問 | `graphrag query "How does the story develop?" --method drift` |
| `basic` | 単純な vector RAG の基本検索。`text_units` を中心に参照する。 | 比較検証、軽量な検索 | `graphrag query "What does the document say about memory?" --method basic` |
| `question generation` | 既存の質問履歴から次の候補質問を生成する。CLI の `query --method` ではない。 | フォローアップ質問の候補生成 | CLI ではなく Python API / notebook 経由 |

## 補足メモ

- `global` は全体要約寄りで、コミュニティレポートを使う。([docs/query/global_search.md](../docs/query/global_search.md))
- `local` は特定 entity の関係・属性・関連テキストを引いてくる。([docs/query/local_search.md](../docs/query/local_search.md))
- `drift` は `global` と `local` の間を埋めるような探索で、コミュニティ情報を使って質問を掘り下げる。([docs/query/drift_search.md](../docs/query/drift_search.md))
- `basic` は GraphRAG の標準的な知識グラフ検索ではなく、比較用の簡易ベクトル検索。([docs/query/overview.md](../docs/query/overview.md))

## 使いどころの具体例

### `global`

- 文書全体の主題を知りたいとき
- いくつかの章や複数文書をまたいだ共通テーマをまとめたいとき
- 「このデータセット全体で何が重要か」を先に把握したいとき
- 個別の登場人物や単語ではなく、全体の傾向を短く掴みたいとき

### `local`

- 特定の人物、組織、場所、概念について深く知りたいとき
- 名前が出てきた対象の関係性を確認したいとき
- ある entity がどの文脈で出てくるかを追いたいとき
- 文章中の局所的な根拠を重視して答えを出したいとき

### `drift`

- `local` だけでは少し狭く、もう少し探索の幅がほしいとき
- 1つの entity から始めて、関連トピックへ段階的に広げたいとき
- 問いが最初から明確ではなく、質問を掘り下げながら答えを作りたいとき
- `global` の全体把握と `local` の局所把握の中間を取りたいとき

### `basic`

- GraphRAG の知識グラフを使う前に、文書の素の近傍検索を見たいとき
- 比較検証として簡易な検索結果を見たいとき
- entity の関係を厳密に追う必要はなく、近い text unit を拾えればよいとき
- 実験的に軽く試したいとき

### `question generation`

- 既存の質問から次に聞くべき候補を作りたいとき
- 調査の途中で、見落としやすい論点を洗い出したいとき
- 対話形式でフォローアップ質問を出したいとき
- 検索ではなく「次の質問を作る」こと自体が目的のとき

## コマンド例

```bash
# 全体テーマの要約
graphrag query "What are the top themes in this story?"

# 特定人物の関係を掘る
graphrag query "Who is Scrooge and what are his main relationships?" --method local

# 段階的に深掘りする
graphrag query "How does the story develop?" --method drift

# 基本ベクトル検索で確認する
graphrag query "What does the document say about memory?" --method basic
```

## Question Generation について

`Question Generation` は `query` の method ではないため、`graphrag query --method question_generation` のような使い方はしない。  
仕様は [docs/query/question_generation.md](../docs/query/question_generation.md) にあり、同じ context-building を使って候補質問を生成する機能として説明されている。
