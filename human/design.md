# Problem Design & Selection

Learnings from 5 studies across 5 problems (FacLoc, MaxSAT, QAP, GC, LOP), distilled into criteria for selecting and evaluating optimisation problems for autoresearch.


## Problem Selection Criteria

Quantitative thresholds derived from 5-study data:

| Criterion | Measure | Good | Bad |
|-----------|---------|------|-----|
| Depth | plateau_trial | >20 | <10 |
| Solve variety | distinct_levels / num_trials | >0.15 | <0.10 |
| Headroom | best_improvement vs bounds | significant gap | near ceiling |
| Metric granularity | distinct_levels in 50 trials | >10 | <=5 |
| Guidance sensitivity | max-min best_improvement across studies | >2% | <1% |
| Time utilisation | avg_training_time / budget | 20-70% | >90% or <5% |


## Current Problem Scorecards

### FacLoc (Facility Location, uncapacitated)
Best problem in the ensemble.
- **Depth:** high (plateau >20 trials)
- **Solve variety:** high (6+ initialization strategies: facility-first, load-balanced, cost-aware random, ILS, SA, 2-opt)
- **Headroom:** high (67% improvement, LP relaxation bound far away)
- **Metric granularity:** high (continuous cost metric)
- **Guidance sensitivity:** 3.29% swing across studies (64.18% -> 67.17%)
- **Time utilisation:** 15-20% of budget

### MaxSAT (Maximum Satisfiability)
Strong but approaching ceiling.
- **Depth:** high (92% -> 99% across studies)
- **Solve variety:** high (WalkSAT, clause-weighting, 2-opt/3-opt, first-improvement GSAT)
- **Headroom:** LOW (99.31% — nearly solved)
- **Metric granularity:** medium (unsat clause count, baseline 29-48 clauses)
- **Guidance sensitivity:** HIGH (4.93% swing — most responsive to guidance)
- **Time utilisation:** ~20% of budget

### QAP (Quadratic Assignment Problem)
Good continuous metric, stuck at plateau. Needs investigation.
- **Depth:** low (plateau_trial ~9)
- **Solve variety:** low (greedy + 1-opt dominates)
- **Headroom:** high (12.5% improvement — large gap remains)
- **Metric granularity:** high (continuous cost metric)
- **Guidance sensitivity:** low (2.04% swing across studies)
- **Time utilisation:** ~22% of budget
- **Key bottleneck:** rand75a instance timeout kills diversity — Scientists can't explore complex algorithms before hitting time limit


## Removed Problems & Why

### TSP (Travelling Salesman Problem)
Removed after initial evaluation.
- **Failure mode:** Memorised dominant algorithm (nearest-neighbor + 2-opt)
- **Evidence:** Ceiling at ~0.200 improvement that doesn't vary regardless of guidance. 750-city instances consumed 90% of time budget, leaving no room for algorithmic diversity.
- **Lesson:** A "solved" problem with well-known optimal heuristics produces worse signal than a less famous problem where the LLM must genuinely explore.

### GC (Graph Colouring)
Removed after 5 studies.
- **Failure mode:** Memorised dominant algorithm (DSATUR)
- **Evidence:** Only 4 distinct avg_improvement values across 57 trials. Plateau at trial 7. All algorithm families (multi-start, perturbation, greedy removal, SA) converge to same colour counts (26, 32, 42).
- **Scaling attempted:** 300/400/300e node graphs — didn't help. DSATUR dominance is algorithmic, not a metric granularity issue.
- **Lesson:** If the LLM has memorised a dominant algorithm, increasing problem size doesn't create algorithmic diversity — it just makes the dominant algorithm slower.

### LOP (Linear Ordering Problem)
Removed after 5 studies.
- **Failure mode:** Actively harmed by guidance changes
- **Evidence:** Regressed from 9.62% to 4.82% across studies. Study 4 concrete initialization examples re-suggested strategies from 35+ prior trials that were already exhausted, causing -4.18% regression.
- **Memory.md showed:** "DO NOT try: ILS, perturbation, more starts, Or-opt, 3-opt, or hybrid greedy variants" — yet guidance kept encouraging exactly these.
- **Lesson:** A problem where all obvious approaches are already exhausted produces negative signal — guidance can only re-suggest tried strategies, actively harming performance.


## Guidance Design Patterns

Learnings from 5 studies of Supervisor guidance changes:

1. **Simple focused additions work.** Study 2 added one section (Neighborhood Structure) and gained +1.25% aggregate. Clear, concrete, additive.

2. **"Skip" instructions are catastrophic.** Study 3 added "If you already use 2-opt, skip to initialization diversity" and MaxSAT crashed -4.23%. Conditional instructions that delete guidance sections remove examples Scientists need.

3. **Generic guidance diverges by problem type.** This is structural, not tunable. MaxSAT +6% while LOP -0.34% from the same guidance change. Problems have different algorithmic profiles that generic guidance cannot bridge.

4. **Concrete examples beat abstract concepts.** "Try multi-seed restarts with 5-10 random seeds" works better than "consider initialization diversity approaches."

5. **Re-suggesting exhausted strategies causes regression.** If Scientists have already tried initialization diversity for 35+ trials, guidance that says "try initialization diversity with concrete examples" just wastes budget re-exploring dead ends.

6. **Recovery is possible.** Removing the bad "skip" checkpoint in Study 4 restored MaxSAT to 99.31% (best ever). Bad guidance changes are reversible if diagnosed correctly.
