# Native-Metric Panel for Family-Native Results Table

This panel reports per-system, per-family native metrics over the five `test` cases used in the main paper. Aggregate columns include both the valid-only mean (over cases the verifier accepted) and the penalized mean (invalid or missing cases substitute the score-zero reference for that metric). Cost/conditional metrics report a valid-only mean with the corresponding count; they are not penalized because a penalty value for a cost metric is ill-defined. Solver reference rows report exactly the values from the `experiments/main_solver/README.md` matrix; their valid-only and penalized means coincide because every reference run is valid.

## AEOSSP

Per-case native metrics (WCR, CR higher better; TAT seconds, PC Wh lower better). Empty fields mark invalid runs or undefined TAT (no completed tasks).

| System | Case | valid | WCR | CR | TAT (s) | PC (Wh) |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Claude Code + Claude Opus 4.6 | case_0001 | true | 0.6854 | 0.7268 | 1071.2 | 18621.4 |
| Claude Code + Claude Opus 4.6 | case_0002 | true | 0.7293 | 0.7538 | 1070.3 | 19616.0 |
| Claude Code + Claude Opus 4.6 | case_0003 | true | 0.7198 | 0.7408 | 985.0 | 17763.5 |
| Claude Code + Claude Opus 4.6 | case_0004 | true | 0.7158 | 0.7497 | 1058.3 | 18652.4 |
| Claude Code + Claude Opus 4.6 | case_0005 | true | 0.0000 | 0.0000 | — | 7860.0 |
| Codex CLI + GPT-5.4 | case_0001 | true | 0.6325 | 0.6651 | 1150.3 | 17644.8 |
| Codex CLI + GPT-5.4 | case_0002 | true | 0.7159 | 0.7404 | 948.6 | 19283.0 |
| Codex CLI + GPT-5.4 | case_0003 | true | 0.7202 | 0.7390 | 969.7 | 17853.3 |
| Codex CLI + GPT-5.4 | case_0004 | true | 0.6718 | 0.7063 | 1117.7 | 18142.8 |
| Codex CLI + GPT-5.4 | case_0005 | true | 0.7968 | 0.8284 | 939.0 | 22569.9 |
| Kimi CLI + Kimi K2.6 | case_0001 | true | 0.6276 | 0.6662 | 999.0 | 17508.0 |
| Kimi CLI + Kimi K2.6 | case_0002 | true | 0.7105 | 0.7376 | 932.5 | 19234.4 |
| Kimi CLI + Kimi K2.6 | case_0003 | true | 0.7075 | 0.7277 | 974.7 | 17809.4 |
| Kimi CLI + Kimi K2.6 | case_0004 | true | 0.6751 | 0.7031 | 1019.0 | 17952.2 |
| Kimi CLI + Kimi K2.6 | case_0005 | true | 0.7409 | 0.7635 | 937.5 | 21714.7 |
| OpenCode + MiniMax M2.7 | case_0001 | true | 0.5241 | 0.5645 | 979.0 | 15974.8 |
| OpenCode + MiniMax M2.7 | case_0002 | true | 0.0084 | 0.0095 | 252.4 | 7165.7 |
| OpenCode + MiniMax M2.7 | case_0003 | true | 0.1059 | 0.0805 | 1198.0 | 7521.8 |
| OpenCode + MiniMax M2.7 | case_0004 | true | 0.3655 | 0.2275 | 1216.4 | 10697.3 |
| OpenCode + MiniMax M2.7 | case_0005 | true | 0.0000 | 0.0000 | — | 7860.0 |
| OpenCode + DeepSeek V4 Pro | case_0001 | true | 0.6201 | 0.6559 | 984.0 | 17523.0 |
| OpenCode + DeepSeek V4 Pro | case_0002 | true | 0.7150 | 0.7393 | 935.2 | 19302.8 |
| OpenCode + DeepSeek V4 Pro | case_0003 | true | 0.6675 | 0.6865 | 988.9 | 17036.8 |
| OpenCode + DeepSeek V4 Pro | case_0004 | true | 0.6789 | 0.7126 | 1092.8 | 18052.6 |
| OpenCode + DeepSeek V4 Pro | case_0005 | true | 0.7287 | 0.7563 | 934.8 | 21445.9 |
| aeossp_standard_greedy_lns | case_0001 | true | 0.6183 | 0.6662 | 1118.2 | 17313.3 |
| aeossp_standard_greedy_lns | case_0002 | true | 0.6978 | 0.7393 | 1120.8 | 18804.4 |
| aeossp_standard_greedy_lns | case_0003 | true | 0.6988 | 0.7324 | 1150.9 | 17408.7 |
| aeossp_standard_greedy_lns | case_0004 | true | 0.6706 | 0.7094 | 1140.3 | 17715.6 |
| aeossp_standard_greedy_lns | case_0005 | true | 0.7227 | 0.7589 | 1111.2 | 21240.9 |
| aeossp_standard_mwis_conflict_graph | case_0001 | true | 0.7057 | 0.7432 | 1051.1 | 18773.7 |
| aeossp_standard_mwis_conflict_graph | case_0002 | true | 0.7763 | 0.8057 | 1013.3 | 20150.9 |
| aeossp_standard_mwis_conflict_graph | case_0003 | true | 0.7837 | 0.8063 | 1021.9 | 18710.1 |
| aeossp_standard_mwis_conflict_graph | case_0004 | true | 0.7395 | 0.7757 | 1036.2 | 18966.2 |
| aeossp_standard_mwis_conflict_graph | case_0005 | true | 0.7858 | 0.8168 | 966.6 | 22374.9 |

Score-zero references used for the penalized mean: TAT = mission horizon H = 43200 s for every test case; PC = per-case battery budget E_bud = case_0001: 31000 Wh, case_0002: 37000 Wh, case_0003: 33900 Wh, case_0004: 32300 Wh, case_0005: 41500 Wh.

Family aggregate (n_valid out of 5; valid-only mean / penalized mean for objective metrics; cost columns omitted because the family has no cost/conditional metric here).

| System | n_valid | WCR valid / pen | CR valid / pen | TAT s valid / pen | PC Wh valid / pen |
| --- | ---: | ---: | ---: | ---: | ---: |
| Claude Code + Claude Opus 4.6 | 5 | 0.5701 / 0.5701 | 0.5942 / 0.5942 | 1046.2 / 9477.0 | 16502.6 / 16502.6 |
| Codex CLI + GPT-5.4 | 5 | 0.7075 / 0.7075 | 0.7358 / 0.7358 | 1025.1 / 1025.1 | 19098.7 / 19098.7 |
| Kimi CLI + Kimi K2.6 | 5 | 0.6923 / 0.6923 | 0.7196 / 0.7196 | 972.5 / 972.5 | 18843.7 / 18843.7 |
| OpenCode + MiniMax M2.7 | 5 | 0.2008 / 0.2008 | 0.1764 / 0.1764 | 911.4 / 9369.1 | 9843.9 / 9843.9 |
| OpenCode + DeepSeek V4 Pro | 5 | 0.6820 / 0.6820 | 0.7101 / 0.7101 | 987.1 / 987.1 | 18672.2 / 18672.2 |
| aeossp_standard_greedy_lns | 5 | 0.6816 / 0.6816 | 0.7212 / 0.7212 | 1128.3 / 1128.3 | 18496.6 / 18496.6 |
| aeossp_standard_mwis_conflict_graph | 5 | 0.7582 / 0.7582 | 0.7895 / 0.7895 | 1017.8 / 1017.8 | 19795.2 / 19795.2 |

## SatNet

Per-case native metrics (U_rms, U_max in [0,1], lower better; n_satisfied_requests higher better).

| System | Case | valid | U_rms | U_max | n_satisfied_requests |
| --- | --- | --- | ---: | ---: | ---: |
| Claude Code + Claude Opus 4.6 | W10_2018 | true | 0.1072 | 0.2409 | 227 |
| Claude Code + Claude Opus 4.6 | W20_2018 | true | 0.1534 | 0.4560 | 241 |
| Claude Code + Claude Opus 4.6 | W30_2018 | false | — | — | — |
| Claude Code + Claude Opus 4.6 | W40_2018 | true | 0.2425 | 0.4875 | 225 |
| Claude Code + Claude Opus 4.6 | W50_2018 | true | 0.2652 | 0.4387 | 193 |
| Codex CLI + GPT-5.4 | W10_2018 | true | 0.1540 | 0.4143 | 234 |
| Codex CLI + GPT-5.4 | W20_2018 | true | 0.2299 | 0.8636 | 252 |
| Codex CLI + GPT-5.4 | W30_2018 | true | 0.2475 | 0.4649 | 202 |
| Codex CLI + GPT-5.4 | W40_2018 | true | 0.3646 | 0.5714 | 208 |
| Codex CLI + GPT-5.4 | W50_2018 | true | 0.1753 | 0.2811 | 219 |
| Kimi CLI + Kimi K2.6 | W10_2018 | true | 0.1360 | 0.3204 | 221 |
| Kimi CLI + Kimi K2.6 | W20_2018 | true | 0.2968 | 0.9548 | 204 |
| Kimi CLI + Kimi K2.6 | W30_2018 | true | 0.2197 | 0.5245 | 201 |
| Kimi CLI + Kimi K2.6 | W40_2018 | true | 0.2760 | 0.6835 | 223 |
| Kimi CLI + Kimi K2.6 | W50_2018 | true | 0.3107 | 0.5714 | 190 |
| OpenCode + MiniMax M2.7 | W10_2018 | true | 0.3273 | 0.7857 | 200 |
| OpenCode + MiniMax M2.7 | W20_2018 | true | 0.6408 | 1.0000 | 99 |
| OpenCode + MiniMax M2.7 | W30_2018 | true | 0.2978 | 0.6000 | 250 |
| OpenCode + MiniMax M2.7 | W40_2018 | true | 0.4830 | 0.8596 | 194 |
| OpenCode + MiniMax M2.7 | W50_2018 | false | — | — | — |
| OpenCode + DeepSeek V4 Pro | W10_2018 | true | 0.1367 | 0.6429 | 232 |
| OpenCode + DeepSeek V4 Pro | W20_2018 | true | 0.1622 | 0.6466 | 258 |
| OpenCode + DeepSeek V4 Pro | W30_2018 | true | 0.3483 | 0.9308 | 190 |
| OpenCode + DeepSeek V4 Pro | W40_2018 | true | 0.4142 | 1.0000 | 194 |
| OpenCode + DeepSeek V4 Pro | W50_2018 | true | 0.2786 | 0.7143 | 193 |
| satnet_milp_claudet2022 | W10_2018 | citation | 0.2600 | 0.4790 | 203 |
| satnet_milp_claudet2022 | W20_2018 | citation | 0.2100 | 0.6410 | 249 |
| satnet_milp_claudet2022 | W30_2018 | citation | 0.2900 | 0.6430 | 231 |
| satnet_milp_claudet2022 | W40_2018 | citation | 0.4000 | 1.0000 | 223 |
| satnet_milp_claudet2022 | W50_2018 | citation | 0.3500 | 0.6000 | 197 |
| satnet_rl_ppo_goh2021 | W10_2018 | citation | 0.2800 | 0.7100 | 204 |
| satnet_rl_ppo_goh2021 | W20_2018 | citation | 0.2700 | 0.8100 | 223 |
| satnet_rl_ppo_goh2021 | W30_2018 | citation | 0.2800 | 0.8500 | 229 |
| satnet_rl_ppo_goh2021 | W40_2018 | citation | 0.3900 | 0.8200 | 216 |
| satnet_rl_ppo_goh2021 | W50_2018 | citation | 0.3600 | 0.6700 | 185 |

Score-zero references for the penalized mean: U_rms = U_max = 1.0 (bounded in [0,1]); n_satisfied_requests = 0.

Family aggregate.

| System | n_valid | U_rms valid / pen | U_max valid / pen | n_sat valid / pen |
| --- | ---: | ---: | ---: | ---: |
| Claude Code + Claude Opus 4.6 | 4 | 0.1921 / 0.3537 | 0.4058 / 0.5246 | 221.5 / 177.2 |
| Codex CLI + GPT-5.4 | 5 | 0.2342 / 0.2342 | 0.5191 / 0.5191 | 223.0 / 223.0 |
| Kimi CLI + Kimi K2.6 | 5 | 0.2478 / 0.2478 | 0.6109 / 0.6109 | 207.8 / 207.8 |
| OpenCode + MiniMax M2.7 | 4 | 0.4372 / 0.5498 | 0.8113 / 0.8491 | 185.8 / 148.6 |
| OpenCode + DeepSeek V4 Pro | 5 | 0.2680 / 0.2680 | 0.7869 / 0.7869 | 213.4 / 213.4 |
| satnet_milp_claudet2022 | 5 (citation) | 0.3020 / 0.3020 | 0.6726 / 0.6726 | 220.6 / 220.6 |
| satnet_rl_ppo_goh2021 | 5 (citation) | 0.3160 / 0.3160 | 0.7720 / 0.7720 | 211.4 / 211.4 |

## SPOT-5

Per-case native metrics (computed_profit higher better; computed_selected higher better).

| System | Case | valid | computed_profit | computed_selected |
| --- | --- | --- | ---: | ---: |
| Claude Code + Claude Opus 4.6 | 1021 | true | 176246.0 | 311 |
| Claude Code + Claude Opus 4.6 | 1403 | false | — | — |
| Claude Code + Claude Opus 4.6 | 1506 | true | 168247.0 | 308 |
| Claude Code + Claude Opus 4.6 | 28 | false | — | — |
| Claude Code + Claude Opus 4.6 | 8 | true | 10.0 | 7 |
| Codex CLI + GPT-5.4 | 1021 | true | 176246.0 | 312 |
| Codex CLI + GPT-5.4 | 1403 | true | 176141.0 | 218 |
| Codex CLI + GPT-5.4 | 1506 | true | 168247.0 | 307 |
| Codex CLI + GPT-5.4 | 28 | true | 56053.0 | 47 |
| Codex CLI + GPT-5.4 | 8 | true | 10.0 | 7 |
| Kimi CLI + Kimi K2.6 | 1021 | true | 176246.0 | 312 |
| Kimi CLI + Kimi K2.6 | 1403 | true | 176141.0 | 218 |
| Kimi CLI + Kimi K2.6 | 1506 | true | 168247.0 | 306 |
| Kimi CLI + Kimi K2.6 | 28 | true | 56053.0 | 46 |
| Kimi CLI + Kimi K2.6 | 8 | true | 10.0 | 7 |
| OpenCode + MiniMax M2.7 | 1021 | true | 170198.0 | 244 |
| OpenCode + MiniMax M2.7 | 1403 | false | — | — |
| OpenCode + MiniMax M2.7 | 1506 | true | 5026.0 | 18 |
| OpenCode + MiniMax M2.7 | 28 | true | 52048.0 | 43 |
| OpenCode + MiniMax M2.7 | 8 | true | 10.0 | 7 |
| OpenCode + DeepSeek V4 Pro | 1021 | true | 176246.0 | 312 |
| OpenCode + DeepSeek V4 Pro | 1403 | true | 160127.0 | 194 |
| OpenCode + DeepSeek V4 Pro | 1506 | true | 168247.0 | 309 |
| OpenCode + DeepSeek V4 Pro | 28 | true | 56053.0 | 46 |
| OpenCode + DeepSeek V4 Pro | 8 | true | 9.0 | 6 |
| spot5_reference_lookup | 1021 | true | 169243.0 | 311 |
| spot5_reference_lookup | 1403 | true | 172143.0 | — |
| spot5_reference_lookup | 1506 | true | 164241.0 | — |
| spot5_reference_lookup | 28 | true | 56053.0 | — |
| spot5_reference_lookup | 8 | true | 10.0 | — |

Score-zero references for the penalized mean: computed_profit = 0; computed_selected = 0.

Family aggregate.

| System | n_valid | profit valid / pen | selected valid / pen |
| --- | ---: | ---: | ---: |
| Claude Code + Claude Opus 4.6 | 3 | 114834.3 / 68900.6 | 208.7 / 125.2 |
| Codex CLI + GPT-5.4 | 5 | 115339.4 / 115339.4 | 178.2 / 178.2 |
| Kimi CLI + Kimi K2.6 | 5 | 115339.4 / 115339.4 | 177.8 / 177.8 |
| OpenCode + MiniMax M2.7 | 4 | 56820.5 / 45456.4 | 78.0 / 62.4 |
| OpenCode + DeepSeek V4 Pro | 5 | 112136.4 / 112136.4 | 173.4 / 173.4 |
| spot5_reference_lookup | 5 | 112338.0 / 112338.0 | — / — |

## Stereo Imaging

Per-case native metrics (normalized_quality, coverage_ratio higher better).

| System | Case | valid | normalized_quality | coverage_ratio |
| --- | --- | --- | ---: | ---: |
| Claude Code + Claude Opus 4.6 | case_0001 | true | 0.0218 | 0.0282 |
| Claude Code + Claude Opus 4.6 | case_0002 | false | — | — |
| Claude Code + Claude Opus 4.6 | case_0003 | true | 0.9206 | 0.9421 |
| Claude Code + Claude Opus 4.6 | case_0004 | true | 0.0155 | 0.0159 |
| Claude Code + Claude Opus 4.6 | case_0005 | false | — | — |
| Codex CLI + GPT-5.4 | case_0001 | true | 0.9694 | 0.9718 |
| Codex CLI + GPT-5.4 | case_0002 | true | 0.9675 | 0.9917 |
| Codex CLI + GPT-5.4 | case_0003 | true | 0.6906 | 0.7934 |
| Codex CLI + GPT-5.4 | case_0004 | true | 0.0079 | 0.0079 |
| Codex CLI + GPT-5.4 | case_0005 | true | 0.8098 | 0.8511 |
| Kimi CLI + Kimi K2.6 | case_0001 | true | 0.0000 | 0.0000 |
| Kimi CLI + Kimi K2.6 | case_0002 | true | 0.0125 | 0.0165 |
| Kimi CLI + Kimi K2.6 | case_0003 | true | 0.0000 | 0.0000 |
| Kimi CLI + Kimi K2.6 | case_0004 | true | 0.0000 | 0.0000 |
| Kimi CLI + Kimi K2.6 | case_0005 | true | 0.0000 | 0.0000 |
| OpenCode + MiniMax M2.7 | case_0001 | true | 0.0000 | 0.0000 |
| OpenCode + MiniMax M2.7 | case_0002 | false | — | — |
| OpenCode + MiniMax M2.7 | case_0003 | false | — | — |
| OpenCode + MiniMax M2.7 | case_0004 | false | — | — |
| OpenCode + MiniMax M2.7 | case_0005 | false | — | — |
| OpenCode + DeepSeek V4 Pro | case_0001 | true | 0.0000 | 0.0000 |
| OpenCode + DeepSeek V4 Pro | case_0002 | true | 0.0000 | 0.0000 |
| OpenCode + DeepSeek V4 Pro | case_0003 | true | 0.6498 | 0.9421 |
| OpenCode + DeepSeek V4 Pro | case_0004 | false | — | — |
| OpenCode + DeepSeek V4 Pro | case_0005 | true | 0.0000 | 0.0000 |
| stereo_imaging_cp_local_search_stereo_insertion | case_0001 | true | 0.9581 | 0.9789 |
| stereo_imaging_cp_local_search_stereo_insertion | case_0002 | true | 0.9887 | 0.9917 |
| stereo_imaging_cp_local_search_stereo_insertion | case_0003 | true | 0.9572 | 0.9587 |
| stereo_imaging_cp_local_search_stereo_insertion | case_0004 | true | 0.9238 | 0.9444 |
| stereo_imaging_cp_local_search_stereo_insertion | case_0005 | true | 0.9747 | 0.9787 |
| stereo_imaging_time_window_pruned_stereo_milp | case_0001 | true | 0.9130 | 0.9296 |
| stereo_imaging_time_window_pruned_stereo_milp | case_0002 | true | 0.9772 | 0.9917 |
| stereo_imaging_time_window_pruned_stereo_milp | case_0003 | true | 0.9176 | 0.9421 |
| stereo_imaging_time_window_pruned_stereo_milp | case_0004 | true | 0.8532 | 0.8968 |
| stereo_imaging_time_window_pruned_stereo_milp | case_0005 | true | 0.9388 | 0.9574 |

Score-zero references for the penalized mean: normalized_quality = 0; coverage_ratio = 0.

Family aggregate.

| System | n_valid | quality valid / pen | coverage valid / pen |
| --- | ---: | ---: | ---: |
| Claude Code + Claude Opus 4.6 | 3 | 0.3193 / 0.1916 | 0.3287 / 0.1972 |
| Codex CLI + GPT-5.4 | 5 | 0.6891 / 0.6891 | 0.7232 / 0.7232 |
| Kimi CLI + Kimi K2.6 | 5 | 0.0025 / 0.0025 | 0.0033 / 0.0033 |
| OpenCode + MiniMax M2.7 | 1 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| OpenCode + DeepSeek V4 Pro | 4 | 0.1624 / 0.1300 | 0.2355 / 0.1884 |
| stereo_imaging_cp_local_search_stereo_insertion | 5 | 0.9605 / 0.9605 | 0.9705 / 0.9705 |
| stereo_imaging_time_window_pruned_stereo_milp | 5 | 0.9200 / 0.9200 | 0.9435 / 0.9435 |

## Regional Coverage

Per-case native metrics (weighted_coverage_ratio, coverage_ratio higher better; num_actions and min_battery_wh are conditional/cost metrics).

| System | Case | valid | weighted_coverage_ratio | coverage_ratio | num_actions | min_battery_wh |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Claude Code + Claude Opus 4.6 | case_0001 | true | 0.0000 | 0.0000 | 0 | 492.9 |
| Claude Code + Claude Opus 4.6 | case_0002 | true | 0.0000 | 0.0000 | 0 | 496.7 |
| Claude Code + Claude Opus 4.6 | case_0003 | true | 0.0000 | 0.0000 | 0 | 493.1 |
| Claude Code + Claude Opus 4.6 | case_0004 | true | 0.0000 | 0.0000 | 0 | 496.6 |
| Claude Code + Claude Opus 4.6 | case_0005 | true | 0.0000 | 0.0000 | 0 | 497.3 |
| Codex CLI + GPT-5.4 | case_0001 | true | 0.9464 | 0.9498 | 64 | 492.9 |
| Codex CLI + GPT-5.4 | case_0002 | true | 0.5082 | 0.5136 | 30 | 496.7 |
| Codex CLI + GPT-5.4 | case_0003 | true | 0.9544 | 0.9535 | 54 | 493.1 |
| Codex CLI + GPT-5.4 | case_0004 | true | 1.0000 | 1.0000 | 28 | 496.6 |
| Codex CLI + GPT-5.4 | case_0005 | true | 0.9896 | 0.9878 | 53 | 492.4 |
| Kimi CLI + Kimi K2.6 | case_0001 | true | 0.9843 | 0.9858 | 64 | 492.9 |
| Kimi CLI + Kimi K2.6 | case_0002 | true | 0.9907 | 0.9921 | 49 | 496.7 |
| Kimi CLI + Kimi K2.6 | case_0003 | true | 0.7958 | 0.7954 | 61 | 493.1 |
| Kimi CLI + Kimi K2.6 | case_0004 | true | 0.9947 | 0.9946 | 64 | 496.6 |
| Kimi CLI + Kimi K2.6 | case_0005 | true | 0.9552 | 0.9567 | 64 | 490.8 |
| OpenCode + MiniMax M2.7 | case_0001 | true | 0.0000 | 0.0000 | 0 | 492.9 |
| OpenCode + MiniMax M2.7 | case_0002 | true | 0.1697 | 0.1449 | 22 | 496.7 |
| OpenCode + MiniMax M2.7 | case_0003 | true | 0.0501 | 0.0490 | 3 | 493.1 |
| OpenCode + MiniMax M2.7 | case_0004 | true | 0.0000 | 0.0000 | 64 | 496.6 |
| OpenCode + MiniMax M2.7 | case_0005 | true | 0.0000 | 0.0000 | 49 | 497.3 |
| OpenCode + DeepSeek V4 Pro | case_0001 | true | 0.5923 | 0.5974 | 64 | 492.9 |
| OpenCode + DeepSeek V4 Pro | case_0002 | true | 0.2691 | 0.2636 | 15 | 496.7 |
| OpenCode + DeepSeek V4 Pro | case_0003 | true | 0.4890 | 0.4908 | 64 | 486.9 |
| OpenCode + DeepSeek V4 Pro | case_0004 | true | 0.1235 | 0.1067 | 64 | 496.6 |
| OpenCode + DeepSeek V4 Pro | case_0005 | true | 0.5087 | 0.4133 | 64 | 487.6 |
| regional_coverage_celf_submodular | case_0001 | true | 0.8978 | 0.9055 | — | 492.90 |
| regional_coverage_celf_submodular | case_0002 | true | 0.9979 | 0.9976 | — | 496.67 |
| regional_coverage_celf_submodular | case_0003 | true | 0.9481 | 0.9471 | — | 493.13 |
| regional_coverage_celf_submodular | case_0004 | true | 1.0000 | 1.0000 | — | 496.56 |
| regional_coverage_celf_submodular | case_0005 | true | 0.9976 | 0.9978 | — | 491.63 |
| regional_coverage_cp_local_search | case_0001 | true | 1.0000 | 1.0000 | — | 492.90 |
| regional_coverage_cp_local_search | case_0002 | true | 0.9989 | 0.9986 | — | 496.67 |
| regional_coverage_cp_local_search | case_0003 | true | 0.9776 | 0.9781 | — | 493.13 |
| regional_coverage_cp_local_search | case_0004 | true | 1.0000 | 1.0000 | — | 496.56 |
| regional_coverage_cp_local_search | case_0005 | true | 1.0000 | 1.0000 | — | 497.26 |

Score-zero references for the penalized objective means: weighted_coverage_ratio = 0; coverage_ratio = 0. Cost/conditional metrics (num_actions, min_battery_wh) are reported as valid-only means with no penalty.

Family aggregate.

| System | n_valid | weighted valid / pen | coverage valid / pen | num_actions valid mean (n) | min_battery_wh valid mean (n) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Claude Code + Claude Opus 4.6 | 5 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0 (n=5) | 495.3 (n=5) |
| Codex CLI + GPT-5.4 | 5 | 0.8797 / 0.8797 | 0.8809 / 0.8809 | 45.8 (n=5) | 494.3 (n=5) |
| Kimi CLI + Kimi K2.6 | 5 | 0.9441 / 0.9441 | 0.9449 / 0.9449 | 60.4 (n=5) | 494.0 (n=5) |
| OpenCode + MiniMax M2.7 | 5 | 0.0440 / 0.0440 | 0.0388 / 0.0388 | 27.6 (n=5) | 495.3 (n=5) |
| OpenCode + DeepSeek V4 Pro | 5 | 0.3965 / 0.3965 | 0.3744 / 0.3744 | 54.2 (n=5) | 492.1 (n=5) |
| regional_coverage_celf_submodular | 5 | 0.9683 / 0.9683 | 0.9696 / 0.9696 | — (n=0) | 494.18 (n=5) |
| regional_coverage_cp_local_search | 5 | 0.9953 / 0.9953 | 0.9953 / 0.9953 | — (n=0) | 495.30 (n=5) |

## Revisit Constellation

Per-case native metrics (capped_max_revisit_gap_hours lower better; num_satellites is a secondary cost objective).

| System | Case | valid | capped_max_revisit_gap_hours | num_satellites |
| --- | --- | --- | ---: | ---: |
| Claude Code + Claude Opus 4.6 | case_0001 | true | 6.0000 | 10 |
| Claude Code + Claude Opus 4.6 | case_0002 | true | 8.0000 | 9 |
| Claude Code + Claude Opus 4.6 | case_0003 | true | 6.0000 | 16 |
| Claude Code + Claude Opus 4.6 | case_0004 | true | 8.0000 | 10 |
| Claude Code + Claude Opus 4.6 | case_0005 | true | 6.0000 | 12 |
| Codex CLI + GPT-5.4 | case_0001 | true | 6.0628 | 18 |
| Codex CLI + GPT-5.4 | case_0002 | true | 8.0000 | 9 |
| Codex CLI + GPT-5.4 | case_0003 | true | 6.0000 | 15 |
| Codex CLI + GPT-5.4 | case_0004 | true | 12.2624 | 19 |
| Codex CLI + GPT-5.4 | case_0005 | true | 6.0000 | 19 |
| Kimi CLI + Kimi K2.6 | case_0001 | true | 6.1784 | 14 |
| Kimi CLI + Kimi K2.6 | case_0002 | true | 8.0000 | 8 |
| Kimi CLI + Kimi K2.6 | case_0003 | true | 6.0000 | 20 |
| Kimi CLI + Kimi K2.6 | case_0004 | true | 8.0000 | 18 |
| Kimi CLI + Kimi K2.6 | case_0005 | true | 6.0000 | 12 |
| OpenCode + MiniMax M2.7 | case_0001 | false | — | — |
| OpenCode + MiniMax M2.7 | case_0002 | false | — | — |
| OpenCode + MiniMax M2.7 | case_0003 | false | — | — |
| OpenCode + MiniMax M2.7 | case_0004 | false | — | — |
| OpenCode + MiniMax M2.7 | case_0005 | false | — | — |
| OpenCode + DeepSeek V4 Pro | case_0001 | true | 6.0000 | 15 |
| OpenCode + DeepSeek V4 Pro | case_0002 | true | 8.0000 | 15 |
| OpenCode + DeepSeek V4 Pro | case_0003 | true | 6.0000 | 20 |
| OpenCode + DeepSeek V4 Pro | case_0004 | true | 8.2053 | 19 |
| OpenCode + DeepSeek V4 Pro | case_0005 | true | 6.0000 | 16 |
| revisit_constellation_j2_rgt_set_cover | case_0001 | true | 6.0000 | 16 |
| revisit_constellation_j2_rgt_set_cover | case_0002 | true | 8.0000 | 15 |
| revisit_constellation_j2_rgt_set_cover | case_0003 | true | 6.0000 | 20 |
| revisit_constellation_j2_rgt_set_cover | case_0004 | true | 8.0000 | 15 |
| revisit_constellation_j2_rgt_set_cover | case_0005 | true | 6.0000 | 20 |
| revisit_constellation_rgt_apc_gap_constructive | case_0001 | true | 7.3074 | 20 |
| revisit_constellation_rgt_apc_gap_constructive | case_0002 | true | 9.0287 | 20 |
| revisit_constellation_rgt_apc_gap_constructive | case_0003 | true | 8.1119 | 20 |
| revisit_constellation_rgt_apc_gap_constructive | case_0004 | true | 10.1600 | 19 |
| revisit_constellation_rgt_apc_gap_constructive | case_0005 | true | 9.5278 | 20 |

Score-zero reference for the penalized mean of capped_max_revisit_gap_hours: mission horizon H = 48.0 hours for every test case. num_satellites is a cost metric (valid-only mean only).

Family aggregate.

| System | n_valid | gap_h valid / pen | num_satellites valid mean (n) |
| --- | ---: | ---: | ---: |
| Claude Code + Claude Opus 4.6 | 5 | 6.8000 / 6.8000 | 11.40 (n=5) |
| Codex CLI + GPT-5.4 | 5 | 7.6650 / 7.6650 | 16.00 (n=5) |
| Kimi CLI + Kimi K2.6 | 5 | 6.8357 / 6.8357 | 14.40 (n=5) |
| OpenCode + MiniMax M2.7 | 0 | — / 48.0000 | — (n=0) |
| OpenCode + DeepSeek V4 Pro | 5 | 6.8411 / 6.8411 | 17.00 (n=5) |
| revisit_constellation_j2_rgt_set_cover | 5 | 6.8000 / 6.8000 | 17.20 (n=5) |
| revisit_constellation_rgt_apc_gap_constructive | 5 | 8.8272 / 8.8272 | 19.80 (n=5) |

## Relay Constellation

Per-case native metrics (service_fraction, worst_demand_service_fraction higher better; num_added_satellites, mean_latency_ms, latency_p95_ms are cost/conditional metrics; latency is defined only when service_fraction > 0).

| System | Case | valid | service_fraction | worst_demand | num_added | mean_latency_ms | latency_p95_ms |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Claude Code + Claude Opus 4.6 | case_0001 | false | — | — | 0 | — | — |
| Claude Code + Claude Opus 4.6 | case_0002 | false | — | — | 0 | — | — |
| Claude Code + Claude Opus 4.6 | case_0003 | false | — | — | 0 | — | — |
| Claude Code + Claude Opus 4.6 | case_0004 | true | 0.9444 | 0.6667 | 8 | 94.4 | 161.8 |
| Claude Code + Claude Opus 4.6 | case_0005 | false | — | — | 0 | — | — |
| Codex CLI + GPT-5.4 | case_0001 | true | 0.8981 | 0.3889 | 2 | 149.5 | 253.6 |
| Codex CLI + GPT-5.4 | case_0002 | true | 0.9821 | 0.8750 | 2 | 132.8 | 223.0 |
| Codex CLI + GPT-5.4 | case_0003 | true | 1.0000 | 1.0000 | 2 | 96.1 | 163.8 |
| Codex CLI + GPT-5.4 | case_0004 | true | 0.8970 | 0.5467 | 1 | 100.2 | 158.5 |
| Codex CLI + GPT-5.4 | case_0005 | true | 0.8988 | 0.6083 | 5 | 152.2 | 275.5 |
| Kimi CLI + Kimi K2.6 | case_0001 | true | 0.8296 | 0.0778 | 2 | 139.5 | 218.2 |
| Kimi CLI + Kimi K2.6 | case_0002 | true | 0.9524 | 0.6667 | 3 | 136.5 | 254.3 |
| Kimi CLI + Kimi K2.6 | case_0003 | true | 1.0000 | 1.0000 | 3 | 104.2 | 180.3 |
| Kimi CLI + Kimi K2.6 | case_0004 | true | 0.9296 | 0.7778 | 4 | 101.6 | 173.4 |
| Kimi CLI + Kimi K2.6 | case_0005 | true | 0.6287 | 0.0889 | 2 | 143.3 | 275.8 |
| OpenCode + MiniMax M2.7 | case_0001 | true | 0.0000 | 0.0000 | 6 | — | — |
| OpenCode + MiniMax M2.7 | case_0002 | true | 0.0000 | 0.0000 | 2 | — | — |
| OpenCode + MiniMax M2.7 | case_0003 | true | 0.0000 | 0.0000 | 8 | — | — |
| OpenCode + MiniMax M2.7 | case_0004 | false | — | — | 8 | — | — |
| OpenCode + MiniMax M2.7 | case_0005 | true | 0.0000 | 0.0000 | 1 | — | — |
| OpenCode + DeepSeek V4 Pro | case_0001 | true | 0.9222 | 0.5333 | 6 | 152.8 | 288.5 |
| OpenCode + DeepSeek V4 Pro | case_0002 | true | 0.9524 | 0.6667 | 10 | 114.6 | 215.1 |
| OpenCode + DeepSeek V4 Pro | case_0003 | true | 0.0000 | 0.0000 | 8 | — | — |
| OpenCode + DeepSeek V4 Pro | case_0004 | true | 0.9222 | 0.6000 | 8 | 99.3 | 174.9 |
| OpenCode + DeepSeek V4 Pro | case_0005 | true | 0.0000 | 0.0000 | 10 | — | — |
| relay_constellation_mclp_teg_contact_plan | case_0001 | true | 0.9259 | 0.5556 | 3 | 158.96 | 289.55 |
| relay_constellation_mclp_teg_contact_plan | case_0002 | true | 0.9524 | 0.6667 | 3 | 123.49 | 220.87 |
| relay_constellation_mclp_teg_contact_plan | case_0003 | true | 0.9300 | 0.6500 | 2 | 101.51 | 177.11 |
| relay_constellation_mclp_teg_contact_plan | case_0004 | true | 0.9444 | 0.6667 | 3 | 100.39 | 166.51 |
| relay_constellation_mclp_teg_contact_plan | case_0005 | true | 0.9111 | 0.6250 | 4 | 151.25 | 232.03 |
| relay_constellation_umcf_srr_contact_plan | case_0001 | true | 0.9241 | 0.5444 | 3 | 156.93 | 298.10 |
| relay_constellation_umcf_srr_contact_plan | case_0002 | true | 0.9393 | 0.6667 | 2 | 133.96 | 234.08 |
| relay_constellation_umcf_srr_contact_plan | case_0003 | true | 0.9911 | 0.9667 | 2 | 108.60 | 191.60 |
| relay_constellation_umcf_srr_contact_plan | case_0004 | true | 0.8893 | 0.4133 | 2 | 109.27 | 191.25 |
| relay_constellation_umcf_srr_contact_plan | case_0005 | true | 0.8941 | 0.6250 | 4 | 169.92 | 342.66 |

Score-zero references for the penalized objective means: service_fraction = 0; worst_demand_service_fraction = 0. Cost/conditional metrics (num_added_satellites, mean_latency_ms, latency_p95_ms) are valid-only means with no penalty; latency means are restricted to cases with service_fraction > 0.

Family aggregate.

| System | n_valid | service valid / pen | worst valid / pen | num_added valid mean (n) | mean_latency_ms (n_served) | latency_p95_ms (n_served) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Claude Code + Claude Opus 4.6 | 1 | 0.9444 / 0.1889 | 0.6667 / 0.1333 | 8.00 (n=1) | 94.4 (n=1) | 161.8 (n=1) |
| Codex CLI + GPT-5.4 | 5 | 0.9352 / 0.9352 | 0.6838 / 0.6838 | 2.40 (n=5) | 126.2 (n=5) | 214.9 (n=5) |
| Kimi CLI + Kimi K2.6 | 5 | 0.8681 / 0.8681 | 0.5222 / 0.5222 | 2.80 (n=5) | 125.0 (n=5) | 220.4 (n=5) |
| OpenCode + MiniMax M2.7 | 4 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 4.25 (n=4) | — (n=0) | — (n=0) |
| OpenCode + DeepSeek V4 Pro | 5 | 0.5594 / 0.5594 | 0.3600 / 0.3600 | 8.40 (n=5) | 122.3 (n=3) | 226.2 (n=3) |
| relay_constellation_mclp_teg_contact_plan | 5 | 0.9328 / 0.9328 | 0.6328 / 0.6328 | 3.00 (n=5) | 127.1 (n=5) | 217.2 (n=5) |
| relay_constellation_umcf_srr_contact_plan | 5 | 0.9276 / 0.9276 | 0.6432 / 0.6432 | 2.60 (n=5) | 135.7 (n=5) | 251.5 (n=5) |

## Cross-checks

- SPOT-5 Claude Code computed_profit penalized mean reproduces the existing summary (both report 68900.6 over 5 cases with two invalid runs).
- Relay Constellation Claude Code service_fraction penalized mean reproduces 0.1889.
- SatNet penalized U_rms differs from the existing per-family summary because the existing summary averages U_rms over valid cases only. Penalized U_rms for Claude Code = (0.1072 + 0.1534 + 1.0 + 0.2425 + 0.2652) / 5 = 0.3537, confirming the requested value. Penalized U_rms for OpenCode + MiniMax M2.7 = (0.3273 + 0.6408 + 0.2978 + 0.4830 + 1.0) / 5 = 0.5498 (the W50_2018 invalid case substitutes 1.0). The matching penalized U_max values are reported in the SatNet aggregate table.

## Provenance

- Agent runs (per-case CSVs):
  - `results/agent_runs/experiments/main_agentic/matrix/summaries/benchmarks/aeossp_standard.csv`
  - `.../regional_coverage.csv`
  - `.../relay_constellation.csv`
  - `.../revisit_constellation.csv`
  - `.../satnet.csv`
  - `.../spot5.csv`
  - `.../stereo_imaging.csv`
- Per-family agent summaries used for sanity checks: `experiments/main_agentic/reports/<family>.md`.
- Solver reference numbers transcribed from `experiments/main_solver/README.md` (matrix snapshot at commit `e07f0161ea5d4bb83099ac68131f1a31124c8698`).
- Score-zero references:
  - AEOSSP TAT: mission horizon H = 43200 s (12 h) read from `benchmarks/aeossp_standard/dataset/cases/test/case_000{1..5}/mission.yaml`.
  - AEOSSP PC: per-case battery budget E_bud = sum of `resource_model.battery_capacity_wh` across the satellites in `satellites.yaml`. Values used: case_0001 31000, case_0002 37000, case_0003 33900, case_0004 32300, case_0005 41500 Wh.
  - Revisit `capped_max_revisit_gap_hours`: H = 48 h read from `benchmarks/revisit_constellation/dataset/cases/test/case_000{1..5}/mission.json`.
  - Bounded lower-is-better: U_rms = U_max = 1.0.
  - Higher-is-better: 0.
