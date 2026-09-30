# Native-Metric Panel for the Ablation Runs (Appendix G.2)

This panel reports per-system, per-condition native metrics for the two ablation studies over the five `test` cases each, for the Regional Coverage and Relay Constellation families. It is the companion to the main-experiment native-metric panel and uses identical aggregation rules. For each objective metric we report both the valid-only mean (over cases the verifier accepted) and the penalized mean (invalid cases substitute the score-zero native value for that metric). Every objective metric in these two families is higher-is-better, so the penalized substitution is always 0. Cost/conditional metrics report a valid-only mean with the count and are not penalized, because a penalty value for a cost metric is ill-defined; latency means are further restricted to cases with `service_fraction > 0`. The two evaluated readers are OpenCode + DeepSeek V4 Pro and OpenCode + MiniMax M2.7.

## Procedure injection

Conditions: **No procedure** (the main-experiment baseline run with no injected procedure), **Compact** (a single compact domain procedure), and **Procedure pack** (the full procedure pack).

### Regional Coverage

Per-case native metrics (weighted_coverage_ratio, coverage_ratio higher better; num_actions and min_battery_wh are cost/conditional). Score-zero reference for the penalized objective means: 0.

| System | Condition | Case | valid | weighted_coverage_ratio | coverage_ratio | num_actions | min_battery_wh |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| OpenCode + DeepSeek V4 Pro | No procedure | case_0001 | true | 0.5923 | 0.5974 | 64 | 492.9 |
| OpenCode + DeepSeek V4 Pro | No procedure | case_0002 | true | 0.2691 | 0.2636 | 15 | 496.7 |
| OpenCode + DeepSeek V4 Pro | No procedure | case_0003 | true | 0.4890 | 0.4908 | 64 | 486.9 |
| OpenCode + DeepSeek V4 Pro | No procedure | case_0004 | true | 0.1235 | 0.1067 | 64 | 496.6 |
| OpenCode + DeepSeek V4 Pro | No procedure | case_0005 | true | 0.5087 | 0.4133 | 64 | 487.6 |
| OpenCode + DeepSeek V4 Pro | Compact | case_0001 | true | 0.4862 | 0.4909 | 64 | 492.9 |
| OpenCode + DeepSeek V4 Pro | Compact | case_0002 | true | 0.0985 | 0.0884 | 9 | 496.7 |
| OpenCode + DeepSeek V4 Pro | Compact | case_0003 | true | 0.1913 | 0.1935 | 11 | 493.1 |
| OpenCode + DeepSeek V4 Pro | Compact | case_0004 | true | 0.6083 | 0.6034 | 64 | 496.6 |
| OpenCode + DeepSeek V4 Pro | Compact | case_0005 | true | 0.6902 | 0.7184 | 64 | 487.6 |
| OpenCode + DeepSeek V4 Pro | Procedure pack | case_0001 | true | 0.6773 | 0.6892 | 64 | 492.9 |
| OpenCode + DeepSeek V4 Pro | Procedure pack | case_0002 | true | 0.6321 | 0.6389 | 58 | 496.7 |
| OpenCode + DeepSeek V4 Pro | Procedure pack | case_0003 | true | 0.2643 | 0.2660 | 15 | 493.1 |
| OpenCode + DeepSeek V4 Pro | Procedure pack | case_0004 | true | 0.8591 | 0.8646 | 64 | 496.6 |
| OpenCode + DeepSeek V4 Pro | Procedure pack | case_0005 | true | 0.7861 | 0.7897 | 37 | 497.3 |
| OpenCode + MiniMax M2.7 | No procedure | case_0001 | true | 0.0000 | 0.0000 | 0 | 492.9 |
| OpenCode + MiniMax M2.7 | No procedure | case_0002 | true | 0.1697 | 0.1449 | 22 | 496.7 |
| OpenCode + MiniMax M2.7 | No procedure | case_0003 | true | 0.0501 | 0.0490 | 3 | 493.1 |
| OpenCode + MiniMax M2.7 | No procedure | case_0004 | true | 0.0000 | 0.0000 | 64 | 496.6 |
| OpenCode + MiniMax M2.7 | No procedure | case_0005 | true | 0.0000 | 0.0000 | 49 | 497.3 |
| OpenCode + MiniMax M2.7 | Compact | case_0001 | true | 0.2848 | 0.2933 | 16 | 492.9 |
| OpenCode + MiniMax M2.7 | Compact | case_0002 | true | 0.0288 | 0.0254 | 64 | 496.7 |
| OpenCode + MiniMax M2.7 | Compact | case_0003 | true | 0.0000 | 0.0000 | 9 | 493.1 |
| OpenCode + MiniMax M2.7 | Compact | case_0004 | true | 0.2501 | 0.2659 | 44 | 496.6 |
| OpenCode + MiniMax M2.7 | Compact | case_0005 | true | 0.0732 | 0.0738 | 64 | 484.4 |
| OpenCode + MiniMax M2.7 | Procedure pack | case_0001 | true | 0.0000 | 0.0000 | 64 | 492.9 |
| OpenCode + MiniMax M2.7 | Procedure pack | case_0002 | true | 0.0192 | 0.0163 | 64 | 412.3 |
| OpenCode + MiniMax M2.7 | Procedure pack | case_0003 | true | 0.2813 | 0.2812 | 21 | 493.1 |
| OpenCode + MiniMax M2.7 | Procedure pack | case_0004 | true | 0.4030 | 0.3993 | 46 | 496.6 |
| OpenCode + MiniMax M2.7 | Procedure pack | case_0005 | true | 0.4216 | 0.4319 | 64 | 482.7 |

Aggregate (n_valid out of 5; valid-only mean / penalized mean for objective metrics; valid-only mean with count for cost/conditional metrics).

| System | Condition | n_valid | weighted_coverage_ratio valid / pen | coverage_ratio valid / pen | num_actions valid mean (n) | min_battery_wh valid mean (n) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| OpenCode + DeepSeek V4 Pro | No procedure | 5 | 0.3965 / 0.3965 | 0.3744 / 0.3744 | 54.2 (n=5) | 492.1 (n=5) |
| OpenCode + DeepSeek V4 Pro | Compact | 5 | 0.4149 / 0.4149 | 0.4189 / 0.4189 | 42.4 (n=5) | 493.4 (n=5) |
| OpenCode + DeepSeek V4 Pro | Procedure pack | 5 | 0.6438 / 0.6438 | 0.6497 / 0.6497 | 47.6 (n=5) | 495.3 (n=5) |
| OpenCode + MiniMax M2.7 | No procedure | 5 | 0.0440 / 0.0440 | 0.0388 / 0.0388 | 27.6 (n=5) | 495.3 (n=5) |
| OpenCode + MiniMax M2.7 | Compact | 5 | 0.1273 / 0.1273 | 0.1317 / 0.1317 | 39.4 (n=5) | 492.7 (n=5) |
| OpenCode + MiniMax M2.7 | Procedure pack | 5 | 0.2250 / 0.2250 | 0.2258 / 0.2258 | 51.8 (n=5) | 475.5 (n=5) |

### Relay Constellation

Per-case native metrics (service_fraction, worst_demand_service_fraction higher better; num_added_satellites, mean_latency_ms, latency_p95_ms are cost/conditional; latency is defined only when service_fraction > 0). Score-zero reference for the penalized objective means: 0.

| System | Condition | Case | valid | service_fraction | worst_demand | num_added | mean_latency_ms | latency_p95_ms |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| OpenCode + DeepSeek V4 Pro | No procedure | case_0001 | true | 0.9222 | 0.5333 | 6 | 152.8 | 288.5 |
| OpenCode + DeepSeek V4 Pro | No procedure | case_0002 | true | 0.9524 | 0.6667 | 10 | 114.6 | 215.1 |
| OpenCode + DeepSeek V4 Pro | No procedure | case_0003 | true | 0.0000 | 0.0000 | 8 | — | — |
| OpenCode + DeepSeek V4 Pro | No procedure | case_0004 | true | 0.9222 | 0.6000 | 8 | 99.3 | 174.9 |
| OpenCode + DeepSeek V4 Pro | No procedure | case_0005 | true | 0.0000 | 0.0000 | 10 | — | — |
| OpenCode + DeepSeek V4 Pro | Compact | case_0001 | true | 0.7269 | 0.0889 | 0 | 133.0 | 177.1 |
| OpenCode + DeepSeek V4 Pro | Compact | case_0002 | true | 0.8365 | 0.5556 | 3 | 122.0 | 213.5 |
| OpenCode + DeepSeek V4 Pro | Compact | case_0003 | true | 0.5189 | 0.1500 | 0 | 101.3 | 138.7 |
| OpenCode + DeepSeek V4 Pro | Compact | case_0004 | true | 0.8408 | 0.5333 | 8 | 91.8 | 122.7 |
| OpenCode + DeepSeek V4 Pro | Compact | case_0005 | true | 0.3647 | 0.0000 | 0 | 104.0 | 112.2 |
| OpenCode + DeepSeek V4 Pro | Procedure pack | case_0001 | true | 0.7787 | 0.1667 | 2 | 144.7 | 215.3 |
| OpenCode + DeepSeek V4 Pro | Procedure pack | case_0002 | true | 0.5663 | 0.2000 | 0 | 112.2 | 150.7 |
| OpenCode + DeepSeek V4 Pro | Procedure pack | case_0003 | true | 0.5556 | 0.2500 | 0 | 122.1 | 164.0 |
| OpenCode + DeepSeek V4 Pro | Procedure pack | case_0004 | true | 0.3111 | 0.0000 | 8 | 116.9 | 165.3 |
| OpenCode + DeepSeek V4 Pro | Procedure pack | case_0005 | true | 0.7913 | 0.6750 | 10 | 145.8 | 238.4 |
| OpenCode + MiniMax M2.7 | No procedure | case_0001 | true | 0.0000 | 0.0000 | 6 | — | — |
| OpenCode + MiniMax M2.7 | No procedure | case_0002 | true | 0.0000 | 0.0000 | 2 | — | — |
| OpenCode + MiniMax M2.7 | No procedure | case_0003 | true | 0.0000 | 0.0000 | 8 | — | — |
| OpenCode + MiniMax M2.7 | No procedure | case_0004 | false | — | — | 8 | — | — |
| OpenCode + MiniMax M2.7 | No procedure | case_0005 | true | 0.0000 | 0.0000 | 1 | — | — |
| OpenCode + MiniMax M2.7 | Compact | case_0001 | true | 0.1111 | 0.0000 | 0 | 171.0 | 177.5 |
| OpenCode + MiniMax M2.7 | Compact | case_0002 | true | 0.0000 | 0.0000 | 4 | — | — |
| OpenCode + MiniMax M2.7 | Compact | case_0003 | true | 0.2000 | 0.0000 | 0 | 78.2 | 80.9 |
| OpenCode + MiniMax M2.7 | Compact | case_0004 | true | 0.0347 | 0.0000 | 0 | 176.7 | 186.0 |
| OpenCode + MiniMax M2.7 | Compact | case_0005 | true | 0.2762 | 0.0000 | 2 | 107.5 | 139.2 |
| OpenCode + MiniMax M2.7 | Procedure pack | case_0001 | true | 0.6880 | 0.0556 | 0 | 129.3 | 175.9 |
| OpenCode + MiniMax M2.7 | Procedure pack | case_0002 | true | 0.0000 | 0.0000 | 3 | — | — |
| OpenCode + MiniMax M2.7 | Procedure pack | case_0003 | true | 0.0000 | 0.0000 | 1 | — | — |
| OpenCode + MiniMax M2.7 | Procedure pack | case_0004 | true | 0.1833 | 0.0000 | 0 | 79.5 | 88.7 |
| OpenCode + MiniMax M2.7 | Procedure pack | case_0005 | true | 0.0000 | 0.0000 | 10 | — | — |

Aggregate (n_valid out of 5; valid-only mean / penalized mean for objective metrics; valid-only mean with count for cost/conditional metrics).

| System | Condition | n_valid | service_fraction valid / pen | worst_demand valid / pen | num_added valid mean (n) | mean_latency_ms (n_served) | latency_p95_ms (n_served) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| OpenCode + DeepSeek V4 Pro | No procedure | 5 | 0.5594 / 0.5594 | 0.3600 / 0.3600 | 8.40 (n=5) | 122.3 (n=3) | 226.2 (n=3) |
| OpenCode + DeepSeek V4 Pro | Compact | 5 | 0.6576 / 0.6576 | 0.2656 / 0.2656 | 2.20 (n=5) | 110.4 (n=5) | 152.8 (n=5) |
| OpenCode + DeepSeek V4 Pro | Procedure pack | 5 | 0.6006 / 0.6006 | 0.2583 / 0.2583 | 4.00 (n=5) | 128.4 (n=5) | 186.7 (n=5) |
| OpenCode + MiniMax M2.7 | No procedure | 4 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 4.25 (n=4) | — (n=0) | — (n=0) |
| OpenCode + MiniMax M2.7 | Compact | 5 | 0.1244 / 0.1244 | 0.0000 / 0.0000 | 1.20 (n=5) | 133.3 (n=4) | 145.9 (n=4) |
| OpenCode + MiniMax M2.7 | Procedure pack | 5 | 0.1743 / 0.1743 | 0.0111 / 0.0111 | 2.80 (n=5) | 104.4 (n=2) | 132.3 (n=2) |

## Memory accumulation

Conditions: **No memory** (the main-experiment baseline reader run), **Codex-derived** (the reader evaluated with memory accumulated by the Codex donor), and **DeepSeek-derived** (the reader evaluated with memory accumulated by the OpenCode + DeepSeek V4 Pro donor).

### Regional Coverage

Per-case native metrics (weighted_coverage_ratio, coverage_ratio higher better; num_actions and min_battery_wh are cost/conditional). Score-zero reference for the penalized objective means: 0.

| System | Condition | Case | valid | weighted_coverage_ratio | coverage_ratio | num_actions | min_battery_wh |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| OpenCode + DeepSeek V4 Pro | No memory | case_0001 | true | 0.5923 | 0.5974 | 64 | 492.9 |
| OpenCode + DeepSeek V4 Pro | No memory | case_0002 | true | 0.2691 | 0.2636 | 15 | 496.7 |
| OpenCode + DeepSeek V4 Pro | No memory | case_0003 | true | 0.4890 | 0.4908 | 64 | 486.9 |
| OpenCode + DeepSeek V4 Pro | No memory | case_0004 | true | 0.1235 | 0.1067 | 64 | 496.6 |
| OpenCode + DeepSeek V4 Pro | No memory | case_0005 | true | 0.5087 | 0.4133 | 64 | 487.6 |
| OpenCode + DeepSeek V4 Pro | Codex-derived | case_0001 | true | 0.8302 | 0.8392 | 63 | 492.9 |
| OpenCode + DeepSeek V4 Pro | Codex-derived | case_0002 | true | 0.8832 | 0.8818 | 64 | 496.7 |
| OpenCode + DeepSeek V4 Pro | Codex-derived | case_0003 | true | 0.0000 | 0.0000 | 0 | 493.1 |
| OpenCode + DeepSeek V4 Pro | Codex-derived | case_0004 | true | 0.9323 | 0.9372 | 64 | 496.6 |
| OpenCode + DeepSeek V4 Pro | Codex-derived | case_0005 | true | 0.9780 | 0.9731 | 63 | 497.3 |
| OpenCode + DeepSeek V4 Pro | DeepSeek-derived | case_0001 | true | 0.2638 | 0.2728 | 38 | 492.9 |
| OpenCode + DeepSeek V4 Pro | DeepSeek-derived | case_0002 | true | 0.7738 | 0.7722 | 64 | 496.7 |
| OpenCode + DeepSeek V4 Pro | DeepSeek-derived | case_0003 | true | 0.8060 | 0.8058 | 59 | 493.1 |
| OpenCode + DeepSeek V4 Pro | DeepSeek-derived | case_0004 | true | 0.7376 | 0.7325 | 64 | 496.6 |
| OpenCode + DeepSeek V4 Pro | DeepSeek-derived | case_0005 | true | 0.6496 | 0.6777 | 64 | 487.6 |
| OpenCode + MiniMax M2.7 | No memory | case_0001 | true | 0.0000 | 0.0000 | 0 | 492.9 |
| OpenCode + MiniMax M2.7 | No memory | case_0002 | true | 0.1697 | 0.1449 | 22 | 496.7 |
| OpenCode + MiniMax M2.7 | No memory | case_0003 | true | 0.0501 | 0.0490 | 3 | 493.1 |
| OpenCode + MiniMax M2.7 | No memory | case_0004 | true | 0.0000 | 0.0000 | 64 | 496.6 |
| OpenCode + MiniMax M2.7 | No memory | case_0005 | true | 0.0000 | 0.0000 | 49 | 497.3 |
| OpenCode + MiniMax M2.7 | Codex-derived | case_0001 | true | 0.0786 | 0.0877 | 23 | 492.9 |
| OpenCode + MiniMax M2.7 | Codex-derived | case_0002 | true | 0.3121 | 0.3055 | 31 | 496.7 |
| OpenCode + MiniMax M2.7 | Codex-derived | case_0003 | true | 0.0000 | 0.0000 | 64 | 493.1 |
| OpenCode + MiniMax M2.7 | Codex-derived | case_0004 | true | 0.0928 | 0.0850 | 32 | 496.6 |
| OpenCode + MiniMax M2.7 | Codex-derived | case_0005 | true | 0.0000 | 0.0000 | 0 | 497.3 |
| OpenCode + MiniMax M2.7 | DeepSeek-derived | case_0001 | true | 0.0567 | 0.0526 | 64 | 492.9 |
| OpenCode + MiniMax M2.7 | DeepSeek-derived | case_0002 | true | 0.4203 | 0.4202 | 21 | 496.7 |
| OpenCode + MiniMax M2.7 | DeepSeek-derived | case_0003 | true | 0.0049 | 0.0049 | 52 | 483.5 |
| OpenCode + MiniMax M2.7 | DeepSeek-derived | case_0004 | true | 0.0000 | 0.0000 | 0 | 496.6 |
| OpenCode + MiniMax M2.7 | DeepSeek-derived | case_0005 | true | 0.3930 | 0.4342 | 20 | 494.0 |

Aggregate (n_valid out of 5; valid-only mean / penalized mean for objective metrics; valid-only mean with count for cost/conditional metrics).

| System | Condition | n_valid | weighted_coverage_ratio valid / pen | coverage_ratio valid / pen | num_actions valid mean (n) | min_battery_wh valid mean (n) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| OpenCode + DeepSeek V4 Pro | No memory | 5 | 0.3965 / 0.3965 | 0.3744 / 0.3744 | 54.2 (n=5) | 492.1 (n=5) |
| OpenCode + DeepSeek V4 Pro | Codex-derived | 5 | 0.7247 / 0.7247 | 0.7263 / 0.7263 | 50.8 (n=5) | 495.3 (n=5) |
| OpenCode + DeepSeek V4 Pro | DeepSeek-derived | 5 | 0.6461 / 0.6461 | 0.6522 / 0.6522 | 57.8 (n=5) | 493.4 (n=5) |
| OpenCode + MiniMax M2.7 | No memory | 5 | 0.0440 / 0.0440 | 0.0388 / 0.0388 | 27.6 (n=5) | 495.3 (n=5) |
| OpenCode + MiniMax M2.7 | Codex-derived | 5 | 0.0967 / 0.0967 | 0.0956 / 0.0956 | 30.0 (n=5) | 495.3 (n=5) |
| OpenCode + MiniMax M2.7 | DeepSeek-derived | 5 | 0.1750 / 0.1750 | 0.1824 / 0.1824 | 31.4 (n=5) | 492.7 (n=5) |

### Relay Constellation

Per-case native metrics (service_fraction, worst_demand_service_fraction higher better; num_added_satellites, mean_latency_ms, latency_p95_ms are cost/conditional; latency is defined only when service_fraction > 0). Score-zero reference for the penalized objective means: 0.

| System | Condition | Case | valid | service_fraction | worst_demand | num_added | mean_latency_ms | latency_p95_ms |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| OpenCode + DeepSeek V4 Pro | No memory | case_0001 | true | 0.9222 | 0.5333 | 6 | 152.8 | 288.5 |
| OpenCode + DeepSeek V4 Pro | No memory | case_0002 | true | 0.9524 | 0.6667 | 10 | 114.6 | 215.1 |
| OpenCode + DeepSeek V4 Pro | No memory | case_0003 | true | 0.0000 | 0.0000 | 8 | — | — |
| OpenCode + DeepSeek V4 Pro | No memory | case_0004 | true | 0.9222 | 0.6000 | 8 | 99.3 | 174.9 |
| OpenCode + DeepSeek V4 Pro | No memory | case_0005 | true | 0.0000 | 0.0000 | 10 | — | — |
| OpenCode + DeepSeek V4 Pro | Codex-derived | case_0001 | true | 0.1852 | 0.0000 | 6 | 190.7 | 253.7 |
| OpenCode + DeepSeek V4 Pro | Codex-derived | case_0002 | true | 0.5401 | 0.1833 | 10 | 237.2 | 413.9 |
| OpenCode + DeepSeek V4 Pro | Codex-derived | case_0003 | true | 1.0000 | 1.0000 | 6 | 99.4 | 163.7 |
| OpenCode + DeepSeek V4 Pro | Codex-derived | case_0004 | true | 0.8597 | 0.4667 | 6 | 170.3 | 269.2 |
| OpenCode + DeepSeek V4 Pro | Codex-derived | case_0005 | true | 0.8182 | 0.5667 | 6 | 196.7 | 342.9 |
| OpenCode + DeepSeek V4 Pro | DeepSeek-derived | case_0001 | true | 0.8611 | 0.4333 | 3 | 158.7 | 275.4 |
| OpenCode + DeepSeek V4 Pro | DeepSeek-derived | case_0002 | true | 0.9635 | 0.8444 | 6 | 128.5 | 227.9 |
| OpenCode + DeepSeek V4 Pro | DeepSeek-derived | case_0003 | true | 0.9489 | 0.8667 | 7 | 133.6 | 186.0 |
| OpenCode + DeepSeek V4 Pro | DeepSeek-derived | case_0004 | true | 0.7037 | 0.3067 | 4 | 147.5 | 193.0 |
| OpenCode + DeepSeek V4 Pro | DeepSeek-derived | case_0005 | true | 0.6866 | 0.5417 | 4 | 264.7 | 452.1 |
| OpenCode + MiniMax M2.7 | No memory | case_0001 | true | 0.0000 | 0.0000 | 6 | — | — |
| OpenCode + MiniMax M2.7 | No memory | case_0002 | true | 0.0000 | 0.0000 | 2 | — | — |
| OpenCode + MiniMax M2.7 | No memory | case_0003 | true | 0.0000 | 0.0000 | 8 | — | — |
| OpenCode + MiniMax M2.7 | No memory | case_0004 | false | — | — | 8 | — | — |
| OpenCode + MiniMax M2.7 | No memory | case_0005 | true | 0.0000 | 0.0000 | 1 | — | — |
| OpenCode + MiniMax M2.7 | Codex-derived | case_0001 | true | 0.0000 | 0.0000 | 6 | — | — |
| OpenCode + MiniMax M2.7 | Codex-derived | case_0002 | true | 0.0000 | 0.0000 | 6 | — | — |
| OpenCode + MiniMax M2.7 | Codex-derived | case_0003 | true | 0.2156 | 0.0000 | 6 | 75.7 | 78.3 |
| OpenCode + MiniMax M2.7 | Codex-derived | case_0004 | true | 0.0000 | 0.0000 | 6 | — | — |
| OpenCode + MiniMax M2.7 | Codex-derived | case_0005 | true | 0.0000 | 0.0000 | 6 | — | — |
| OpenCode + MiniMax M2.7 | DeepSeek-derived | case_0001 | true | 0.0000 | 0.0000 | 3 | — | — |
| OpenCode + MiniMax M2.7 | DeepSeek-derived | case_0002 | true | 0.5508 | 0.0000 | 3 | 114.0 | 150.4 |
| OpenCode + MiniMax M2.7 | DeepSeek-derived | case_0003 | false | — | — | — | — | — |
| OpenCode + MiniMax M2.7 | DeepSeek-derived | case_0004 | true | 0.0000 | 0.0000 | 3 | — | — |
| OpenCode + MiniMax M2.7 | DeepSeek-derived | case_0005 | false | — | — | 3 | — | — |

Aggregate (n_valid out of 5; valid-only mean / penalized mean for objective metrics; valid-only mean with count for cost/conditional metrics).

| System | Condition | n_valid | service_fraction valid / pen | worst_demand valid / pen | num_added valid mean (n) | mean_latency_ms (n_served) | latency_p95_ms (n_served) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| OpenCode + DeepSeek V4 Pro | No memory | 5 | 0.5594 / 0.5594 | 0.3600 / 0.3600 | 8.40 (n=5) | 122.3 (n=3) | 226.2 (n=3) |
| OpenCode + DeepSeek V4 Pro | Codex-derived | 5 | 0.6806 / 0.6806 | 0.4433 / 0.4433 | 6.80 (n=5) | 178.9 (n=5) | 288.7 (n=5) |
| OpenCode + DeepSeek V4 Pro | DeepSeek-derived | 5 | 0.8328 / 0.8328 | 0.5986 / 0.5986 | 4.80 (n=5) | 166.6 (n=5) | 266.9 (n=5) |
| OpenCode + MiniMax M2.7 | No memory | 4 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 4.25 (n=4) | — (n=0) | — (n=0) |
| OpenCode + MiniMax M2.7 | Codex-derived | 5 | 0.0431 / 0.0431 | 0.0000 / 0.0000 | 6.00 (n=5) | 75.7 (n=1) | 78.3 (n=1) |
| OpenCode + MiniMax M2.7 | DeepSeek-derived | 3 | 0.1836 / 0.1102 | 0.0000 / 0.0000 | 3.00 (n=3) | 114.0 (n=1) | 150.4 (n=1) |

## Cross-checks

**Primary native metric tracks the normalized five-case mean in every condition.** The table below pairs the penalized five-case normalized mean (the quantity behind the current normalized appendix tables) with the penalized mean of each family's primary native metric (Regional Coverage: weighted_coverage_ratio; Relay Constellation: service_fraction), in condition order. Both primaries are higher-is-better, so the two columns should move in the same direction. No condition shows a normalized score rising while the primary native metric fails to move with it, or vice versa.

| Ablation | Family | System | Normalized (cond 1 / 2 / 3) | Primary native penalized (same order) | Direction |
| --- | --- | --- | --- | --- | --- |
| Procedure | Regional Coverage | DeepSeek V4 Pro | 35.79 / 40.38 / 55.25 | wcr 0.3965 / 0.4149 / 0.6438 | ↑↑ consistent |
| Procedure | Regional Coverage | MiniMax M2.7 | 17.73 / 20.96 / 24.62 | wcr 0.0440 / 0.1273 / 0.2250 | ↑↑ consistent |
| Procedure | Relay Constellation | DeepSeek V4 Pro | 35.67 / 39.17 / 36.05 | sf 0.5594 / 0.6576 / 0.6006 | peak at cond 2, consistent |
| Procedure | Relay Constellation | MiniMax M2.7 | 0.00 / 6.53 / 9.34 | sf 0.0000 / 0.1244 / 0.1743 | ↑↑ consistent |
| Memory | Regional Coverage | DeepSeek V4 Pro | 35.79 / 60.08 / 53.00 | wcr 0.3965 / 0.7247 / 0.6461 | peak at cond 2, consistent |
| Memory | Regional Coverage | MiniMax M2.7 | 17.73 / 20.94 / 26.23 | wcr 0.0440 / 0.0967 / 0.1750 | ↑↑ consistent |
| Memory | Relay Constellation | DeepSeek V4 Pro | 35.67 / 45.09 / 54.19 | sf 0.5594 / 0.6806 / 0.8328 | ↑↑ consistent |
| Memory | Relay Constellation | MiniMax M2.7 | 0.00 / 2.26 / 5.78 | sf 0.0000 / 0.0431 / 0.1102 | ↑↑ consistent |

These reproduce the request's stated normalized five-case means exactly: procedure injection Regional DeepSeek 35.79/40.38/55.25 and MiniMax 17.73/20.96/24.62, Relay DeepSeek 35.67/39.17/36.05 and MiniMax 0.00/6.53/9.34; memory accumulation Regional DeepSeek 35.79/60.08/53.00 and MiniMax 17.73/20.94/26.23, Relay DeepSeek 35.67/45.09/54.19 and MiniMax 0.00/2.26/5.78. The No-procedure / No-memory baseline rows match the main native-metric panel value-for-value (e.g. Relay DeepSeek service_fraction 0.5594, Regional MiniMax weighted_coverage_ratio 0.0440), confirming the baselines are the same runs.

**Secondary-metric notes (no contradiction, but useful for figure design).**
- Relay Constellation, MiniMax M2.7: `worst_demand_service_fraction` stays pinned at 0.0000 across all three conditions in both ablations even as `service_fraction` rises, i.e. the hardest-to-serve demand window is never served regardless of procedure or memory.
- Relay Constellation, DeepSeek V4 Pro, memory: latency rises as service improves — mean latency over served cases goes 122.3 ms (No memory) → 178.9 ms (Codex-derived) → 166.6 ms (DeepSeek-derived), so the service gains come with higher latency. Latency is a cost metric and is not penalized, so it is reported valid-only over served cases only.

## Provenance

- Per-run native metrics are the verifier metric fields surfaced per `run.json`; values were read from the run-summary CSVs that index those artifacts:
  - Procedure injection: `results/agent_runs/experiments/skill_injection/summaries/runs.csv`
  - Memory accumulation: `results/agent_runs/experiments/memory_accumulation/summaries/runs.csv`
  - The `result_path` column in each CSV points to the originating `run.json` (baseline conditions resolve under `results/agent_runs/experiments/main_agentic/matrix/...`; intervention conditions under the corresponding `skill_injection/` or `memory_accumulation/` run trees). The relay Codex-derived DeepSeek `case_0003` run.json was spot-checked field-by-field against the CSV and agreed exactly.
- Condition mapping (harness ids → reader/condition labels):
  - Readers (`harness`): `opencode_dpsk` = OpenCode + DeepSeek V4 Pro; `opencode_minimax` = OpenCode + MiniMax M2.7.
  - Procedure injection conditions (`condition`): `no_skill` = No procedure; `compact_domain` = Compact; `skill_pack` = Procedure pack.
  - Memory conditions: `no_memory` (memory_source `none`) = No memory; `cross_benchmark_round_robin_v1` with memory_source `codex` = Codex-derived; with memory_source `opencode_dpsk` = DeepSeek-derived. Rows with `harness=codex` or `memory_source=opencode_minimax` are donor/cross cells that were not evaluated and are excluded.
- Validity is the verifier `valid == true` field; `verifier_invalid` and `no_solution` rows count as invalid for n_valid and take the score-zero substitution (0) in the penalized mean.
- Existing per-family ablation aggregates used for orientation only: `experiments/skill_injection/reports/` and `experiments/memory_accumulation/reports/`.
