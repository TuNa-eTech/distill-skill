# Blind Test Answer Key — Distill MVP

Status: `pending_generation`
Date prepared: `2026-04-25`
Pack under test: `mobile-dev/v0.1`

This file is operator-only. Do not share it with judges before all judgments are
recorded in `blind_test_packet.md`.

## Task Mapping

| Task | Option 1 | Option 2 | Pack option | Judge winner | Counted result |
|---|---|---|---|---|---|
| T1 | `PENDING_BASELINE_OR_PACK` | `PENDING_BASELINE_OR_PACK` | `PENDING` | `PENDING` | `PENDING` |
| T2 | `PENDING_BASELINE_OR_PACK` | `PENDING_BASELINE_OR_PACK` | `PENDING` | `PENDING` | `PENDING` |
| T3 | `PENDING_BASELINE_OR_PACK` | `PENDING_BASELINE_OR_PACK` | `PENDING` | `PENDING` | `PENDING` |
| T4 | `PENDING_BASELINE_OR_PACK` | `PENDING_BASELINE_OR_PACK` | `PENDING` | `PENDING` | `PENDING` |
| T5 | `PENDING_BASELINE_OR_PACK` | `PENDING_BASELINE_OR_PACK` | `PENDING` | `PENDING` | `PENDING` |

## Scoring Rule

```text
win_rate = pack_wins / (pack_wins + baseline_wins)
```

- Ties are excluded from the denominator.
- Pass if `win_rate >= 60%`.
- Fail soft if ties are `>= 70%`.
- Fail hard if pack-injected output loses `>= 40%` of non-tie judgments.

## Current Score

- Pack wins: `PENDING`
- Baseline wins: `PENDING`
- Ties: `PENDING`
- Win rate: `PENDING`
- Verdict: `PENDING_EXTERNAL_JUDGMENT`
