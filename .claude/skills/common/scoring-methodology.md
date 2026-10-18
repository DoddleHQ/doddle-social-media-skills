# Scoring Methodology

How `dsocial` turns evidence into numbers. Skills explain these; they never recompute them.

Versions: `scoring_version` (weights/thresholds) and `data_version` (platform-spec registry).
Both print in every envelope. If either changes, scores are not comparable across runs.

## Single post (`dsocial validate-post`)

Composite = **post readiness**, 100 points across 6 checks. A check that does not apply is
excluded and the composite is normalised over the measured maximum. *Readiness is not
performance* — it measures compliance and craft, never results.

| Signal | Max | Class | Question |
|--------|-----|-------|----------|
| `post.length` | 30 | deterministic | Is the caption within the platform's caption limit? |
| `post.hashtags` | 20 | deterministic | Are hashtags within the platform's cap and starting range? |
| `post.media_alt` | 15 | deterministic | Does media carry alt text (where the platform supports it)? |
| `post.hook` | 15 | heuristic | Is the first line inside the 40–125 char scannable band? |
| `post.cta` | 10 | heuristic | Is there exactly one recognisable call to action? |
| `post.emoji` | 10 | heuristic | Is emoji use light enough to stay scannable? |

Tier bands: `Excellent ≥85`, `Good ≥70`, `Fair ≥55`, `Weak ≥40`, `Critical <40`.

## Account (`dsocial audit`, `dsocial report`)

Composite = weighted mean over the signals that were measured.

| Signal | Max | Class | Built from |
|--------|-----|-------|-----------|
| `audit.cadence` | 25 | deterministic | posts per week over the dated span (3/week is the starting line) |
| `audit.caption_compliance` | 25 | deterministic | share of captions within their platform's caption limit |
| `audit.alt_coverage` | 15 | deterministic | share of media posts with alt text |
| `audit.hashtag_fit` | 10 | deterministic | share of posts inside the platform's hashtag range |
| `audit.engagement` | 10 | deterministic | mean (likes+comments+shares+saves) ÷ impressions, when impressions exist |

## Calendar (`dsocial calendar`)

Not scored. Emits a deterministic schedule skeleton: dates, weekdays, platforms and a
round-robin pillar rotation. Weekday choice per cadence is fixed (`planner.WEEKDAY_PLANS`), so
the same inputs always produce the same calendar. It makes **no claim** about optimal times.

## Rules

1. A score is a pure function of the recorded input. Same input → same output (modulo
   `generated_at`), guarded by a determinism test.
2. `null` never counts as zero. It leaves the denominator.
3. Findings carry `points_lost` — what the fix recovers on the relevant scale, on the 100-point
   scale, before normalisation. They are pre-ranked by severity, then points.
4. Platform limits are read from the registry; the score changes if and only if the registry
   or the input changes.

## Not in scope of the score

Reach, follower growth, ad performance, brand lift and trend relevance require third-party or
live data. They are advisory or `live`, and never folded into the deterministic composite.
