# Experimental Benchmark Results (Section 4.5)

All configurations were evaluated on the exact same 19-puzzle benchmark suite (including Extension 4-5 showcases, coupled backtrack stress cases, `STUCK`, and `INCONSISTENT` diagnostic cases).

## 1. Detailed Per-Puzzle Results (`1_Comb_Fixed` Baseline)

| Puzzle ID | Grid | State | Primary + Aux Vars | Peak Clauses | SAT Calls | Decisions | Propagations | Backtracks | Steps (Waves) | Runtime (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `3x3_01_core_intro` | 3x3 | `SOLVED` | 9 + 0 | 60 | 75 | 3 | 449 | 0 | 8 (5) | 21.45 |
| `3x3_02_neighbors_chain` | 3x3 | `SOLVED` | 9 + 0 | 34 | 58 | 0 | 382 | 0 | 7 (3) | 12.53 |
| `3x3_03_extensions_mix` | 3x3 | `SOLVED` | 9 + 0 | 45 | 59 | 0 | 381 | 0 | 7 (4) | 14.69 |
| `3x3_04_ambiguous_case` | 3x3 | `STUCK` | 9 + 0 | 15 | 42 | 30 | 230 | 0 | 2 (1) | 4.33 |
| `3x3_05_inconsistent_case` | 3x3 | `INCONSISTENT` | 9 + 0 | 9 | 1 | 0 | 2 | 0 | 0 (0) | 0.36 |
| `3x3_06_compound_connected` | 3x3 | `SOLVED` | 9 + 54 | 256 | 71 | 236 | 1257 | 0 | 8 (3) | 147.28 |
| `4x4_01_core_patrol` | 4x4 | `SOLVED` | 16 + 0 | 186 | 170 | 24 | 1957 | 0 | 13 (5) | 163.90 |
| `4x4_02_core_precinct` | 4x4 | `SOLVED` | 16 + 0 | 205 | 200 | 136 | 1980 | 0 | 14 (6) | 111.05 |
| `4x4_03_ext_intersections` | 4x4 | `SOLVED` | 16 + 5 | 157 | 191 | 10 | 2079 | 0 | 14 (6) | 68.77 |
| `4x4_04_ext_professions` | 4x4 | `SOLVED` | 16 + 4 | 213 | 232 | 0 | 2387 | 0 | 15 (9) | 114.33 |
| `4x4_05_ext_deep_chain` | 4x4 | `SOLVED` | 16 + 8 | 182 | 214 | 172 | 2693 | 0 | 14 (6) | 227.38 |
| `4x4_06_coupled_crucible` | 4x4 | `SOLVED` | 16 + 0 | 1112 | 136 | 420 | 2081 | 109 | 11 (7) | 195.10 |
| `4x4_07_coupled_parity_matrix` | 4x4 | `SOLVED` | 16 + 10 | 178 | 136 | 597 | 2898 | 192 | 11 (8) | 179.74 |
| `5x5_01_core_metropolis` | 5x5 | `SOLVED` | 25 + 0 | 448 | 446 | 230 | 6667 | 0 | 22 (6) | 1007.21 |
| `5x5_02_ext_grand_inquest` | 5x5 | `SOLVED` | 25 + 15 | 407 | 542 | 205 | 7667 | 6 | 23 (10) | 603.92 |
| `5x5_03_single_seed_stress` | 5x5 | `SOLVED` | 25 + 16 | 281 | 575 | 200 | 8344 | 0 | 24 (10) | 465.01 |
| `5x5_04_coupled_labyrinth` | 5x5 | `SOLVED` | 25 + 8 | 458 | 417 | 1410 | 6806 | 282 | 20 (10) | 789.61 |
| `5x5_05_coupled_fortress` | 5x5 | `SOLVED` | 25 + 3 | 288 | 417 | 1821 | 7817 | 645 | 20 (11) | 1603.91 |
| `5x5_06_figure1_showcase` | 5x5 | `SOLVED` | 25 + 42 | 1206 | 431 | 1215 | 12302 | 17 | 21 (3) | 4383.14 |

## 2. Aggregate Comparison Across Solver & Encoding Configurations (17 Solvable Puzzles)

| Configuration | Avg Aux Vars | Avg Peak Clauses | Total SAT Calls | Total Decisions | Total Propagations | Total Backtracks | Total Runtime (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `1_Comb_Fixed` | 9.7 | 336.2 | 4370 | 6679 | 68147 | 1251 | 10109.05 |
| `2_Seq_Fixed` | 165.2 | 392.6 | 4370 | 8299 | 359704 | 1251 | 52075.89 |
| `3_Comb_JW` | 9.7 | 336.2 | 4370 | 7010 | 63883 | 274 | 10152.68 |
| `4_Comb_JW_Pruned` | 9.7 | 336.2 | 2380 | 2586 | 31958 | 272 | 6282.10 |
