# Lighting and Platform Forward Test — 2026-08-20

## Scope

Three blind forward cases were run against the candidate Yi Director Skill. The evaluator received the task prompt without the implementation audit or expected answer.

This is a focused behavior check, not a full external model evaluation and not evidence that the complete regression suite has passed.

## Results

| Case | Result | Verified behavior |
| --- | --- | --- |
| `L1-banquet-arc` | PASS | Preserved the formal storyboard, dialogue and sound; derived warm practical versus cool city/pool sources; protected crystal highlights; kept the corridor darker; avoided generic lighting adjectives. |
| `L2-reverse-world-light` | PASS | Changed only `【摄影】`; kept the east window fixed in world space; reprojected the key across the reverse angle; recovered black-suit texture without lifting the whole image or inventing a rim light. |
| `P1-explicit-seedance-export` | PASS | Returned only the requested platform prompt; preserved exact dialogue, character tags, shoulder continuity and 0–4/4–8/8–12 timing; kept the world-space key stable across reverse shots. |

## Decision

The narrative-lighting chain and explicit platform-export boundary are suitable for the public plugin candidate. The nine unexecuted cases in `evals/lighting-platform-regression.yaml` remain pending and must not be reported as passed.
