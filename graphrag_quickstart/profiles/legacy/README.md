# GraphRAG Profile: legacy

This profile preserves the current quickstart setup as a fixed reference point.

## Purpose

- Compare future profiles against the current tuned baseline
- Preserve the prompt set adapted for GPT-5 reasoning models
- Keep the legacy behavior available for regression checks

## Defaults

- Index model: `gpt-5-nano`
- Query model: `gpt-5.4-mini`
- Prompts: current quickstart prompt set with reasoning-safe adjustments

## Notes

- This profile is the legacy snapshot of the current quickstart
- The prompt changes were made to reduce over-reasoning for GPT-5 reasoning models
- The shared corpus lives in `../../input`
