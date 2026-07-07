"""extract_graph キャッシュの content / reasoning_content トークン比率を集計する。

使い方:
    python analyze_reasoning_tokens.py <extract_graphキャッシュディレクトリ>
"""

import json
import sys
import glob

import tiktoken


def main(cache_dir: str) -> None:
    files = sorted(glob.glob(f"{cache_dir}/*_v4"))
    enc = tiktoken.get_encoding("o200k_base")

    total_content_tok = 0
    total_reasoning_tok = 0
    print(f"対象ディレクトリ: {cache_dir}")
    print(f"総ファイル数: {len(files)}")
    print()

    for f in files:
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        msg = data["result"]["response"]["choices"][0]["message"]
        content = msg.get("content") or ""
        reasoning = msg.get("reasoning_content") or ""
        c_tok = len(enc.encode(content))
        r_tok = len(enc.encode(reasoning))
        total_content_tok += c_tok
        total_reasoning_tok += r_tok
        finish = data["result"]["response"]["choices"][0].get("finish_reason")
        name = f.split("/")[-1].split("\\")[-1][:20]
        print(f"{name}... | content_tok={c_tok:5d} | reasoning_tok={r_tok:6d} | finish_reason={finish}")

    print()
    print("合計 content_tok:", total_content_tok)
    print("合計 reasoning_tok:", total_reasoning_tok)
    denom = total_content_tok + total_reasoning_tok
    if denom:
        print("reasoningの比率:", round(total_reasoning_tok / denom * 100, 1), "%")


if __name__ == "__main__":
    main(sys.argv[1])
