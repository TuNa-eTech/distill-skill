# Blind Test Packet — Distill MVP

Judge: `PENDING_JUDGE`
Date: `PENDING_DATE`
Pack under test: `mobile-dev/v0.1`

## Instructions

- Review the two options for each task without knowing which one used the pack.
- Pick one winner or mark a tie.
- Keep the reason short and concrete.
- Judge only the output quality for the stated task. Do not reward longer answers by default.
- If the two options are materially equivalent, choose `Tie`.

## Task T1 — State Management

- Prompt / scenario: Implement a Flutter payment schedule edit flow where the user can update amount, due date, and recurrence without losing unsaved local state.
- Option 1: `PENDING_GENERATED_OUTPUT`
- Option 2: `PENDING_GENERATED_OUTPUT`
- Winner: `PENDING_JUDGE_INPUT`
- Reason: `PENDING_JUDGE_INPUT`

## Task T2 — Navigation

- Prompt / scenario: Design the route/navigation handling for a Flutter app flow where tapping an unfinished cloud-sync settings feature must keep the user on the same screen and show clear "coming soon" feedback.
- Option 1: `PENDING_GENERATED_OUTPUT`
- Option 2: `PENDING_GENERATED_OUTPUT`
- Winner: `PENDING_JUDGE_INPUT`
- Reason: `PENDING_JUDGE_INPUT`

## Task T3 — Platform Integration

- Prompt / scenario: Add a first-home-entry notification permission prompt in Flutter with iOS and Android behavior separated cleanly and no startup jank.
- Option 1: `PENDING_GENERATED_OUTPUT`
- Option 2: `PENDING_GENERATED_OUTPUT`
- Winner: `PENDING_JUDGE_INPUT`
- Reason: `PENDING_JUDGE_INPUT`

## Task T4 — Code Review

- Prompt / scenario: Review a Flutter MR that moves paywall purchase errors from an inline blocking message to SnackBars and removes a native platform-channel workaround in favor of the official plugin API.
- Option 1: `PENDING_GENERATED_OUTPUT`
- Option 2: `PENDING_GENERATED_OUTPUT`
- Winner: `PENDING_JUDGE_INPUT`
- Reason: `PENDING_JUDGE_INPUT`

## Task T5 — Regression Test

- Prompt / scenario: Write a focused Flutter widget/regression test plan for a debt form where validation errors must clear immediately after the user fixes the input.
- Option 1: `PENDING_GENERATED_OUTPUT`
- Option 2: `PENDING_GENERATED_OUTPUT`
- Winner: `PENDING_JUDGE_INPUT`
- Reason: `PENDING_JUDGE_INPUT`

## Operator Notes

- Generate each task twice with the same model/settings:
  - Baseline: plain expert Flutter prompt, no Distill pack context.
  - Pack-injected: prompt generated through `.venv/bin/distill-build-prompt --role mobile-dev --task "<task>"`.
- Randomize which generated output becomes Option 1 / Option 2 per task.
- Keep the answer key outside this judge-facing packet until scoring is complete.

## Summary

- Pack wins: `PENDING_SCORING`
- Baseline wins: `PENDING_SCORING`
- Ties: `PENDING_SCORING`
- Win rate: `PENDING_SCORING`
- Verdict: `PENDING_SCORING`
- Notes: `PENDING_SCORING`
