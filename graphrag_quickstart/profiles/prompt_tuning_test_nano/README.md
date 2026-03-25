# GraphRAG Profile: prompt_tuning_test_nano

This profile is for prompt-tuning experiments on the current quickstart corpus.

## Purpose

- Copy this profile to create a new profile under `graphrag_quickstart/profiles/<name>`
- Keep the shared corpus in `../../input`
- Use this as the baseline for prompt tuning and model comparison

## Defaults

- Index model: `gpt-5-nano`
- Query model: `gpt-5.4-mini`
- Prompts: current reasoning-safe quickstart prompt set

## After copying

- Edit `settings.yaml` for the new profile
- Fill in the local `.env` with your API key
- Adjust prompts only where the new domain requires it

## Prompt tuning

Run prompt tuning from this profile root after `graphrag init` has completed:

```powershell
graphrag prompt-tune --root . --domain "prompt tuning test" --selection-method random --limit 15 --no-discover-entity-types --output .\_prompt_tune_output
```

- The generated files are `extract_graph.txt`, `summarize_descriptions.txt`, and `community_report_graph.txt`
- Review the generated prompts in `.\_prompt_tune_output` before copying them into `.\prompts`
- `prompt-tune` uses `default_completion_model`, so the tuning model follows the profile's default completion model setting
- Use `--discover-entity-types` only when you also want GraphRAG to infer entity types automatically
