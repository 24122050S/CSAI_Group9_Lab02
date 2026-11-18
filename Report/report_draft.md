# CSC14003 — Introduction to Artificial Intelligence
# Project 2 Report: No-Guess Griductive Solver

* **Course:** CSC14003 — Introduction to Artificial Intelligence (FIT, VNU-HCMUS)
* **Demonstration Video (Google Drive):** `[INSERT_GOOGLE_DRIVE_PUBLIC_LINK_HERE]` *(Verify in Incognito window — Do NOT use YouTube)*

---

## 1. Project Planning and Task Distribution

> *Note: Update Student IDs, Names, and final completion percentages below before exporting `Report.pdf`.*

| Student ID | Full Name | Assigned Responsibilities | Completion (%) |
| :--- | :--- | :--- | :---: |
| `StudentID_1` | `[Member 1]` | Core data models, 4 core regions + Extension 1 advanced regions, `ClueValidator`, `SemanticEvaluator`, exhaustive truth-table tests | 100% |
| `StudentID_2` | `[Member 2]` | Automatic `CNFEncoder` (Combinatorial & Sinz Sequential Counter, Extensions 2 & 3), custom `DPLLSolver` & heuristics | 100% |
| `StudentID_3` | `[Member 3]` | `GameEngine` / `DeductiveLogicAgent` separation, `UniquenessChecker`, MUS `HintEngine`, Deduction Trace, puzzle generator | 100% |
| `StudentID_4` | `[Member 4]` | Interactive Web GUI, 13-puzzle benchmark suite (`3x3`, `4x4`, `5x5`), automated experiments, charts, report & demo video | 100% |

---

## 2. Problem Formulation

### 2.1 Propositional Variables
Consider an $N \times N$ Griductive board ($N \in \{3, 4, 5\}$) with rows numbered $1 \dots N$ (top to bottom) and columns lettered $\text{A}, \text{B}, \dots$ (left to right). Cells are ordered deterministically in **row-major order**:
$$\text{Idx}(r, c) = (r - 1) \cdot N + c \in \{1, 2, \dots, N^2\}$$
For each character $i \in \{1, \dots, N^2\}$, we define one **primary Boolean variable** $C_i$:
$$C_i = \begin{cases} \text{True}, & \text{if character } i \text{ is a Criminal,} \\ \text{False}, & \text{if character } i \text{ is Innocent.} \end{cases}$$
Auxiliary variables introduced by cardinality or parity encodings are allocated strictly in the disjoint range $\{N^2 + 1, N^2 + 2, \dots\}$ via `VariableManager`, ensuring primary character variables and auxiliary encoding variables never collide.

### 2.2 Clue Regions and Semantics
Every revealed clue is **guaranteed true** regardless of whether its owner is Criminal or Innocent. Let $\llbracket C_i \rrbracket \in \{0, 1\}$ denote the indicator of $C_i = \text{True}$.

* **Core Regions:**
  1. $\text{ROW}(r) = \{(r, c) \mid 0 \le c < N\}$
  2. $\text{COL}(c) = \{(r, c) \mid 1 \le r \le N\}$
  3. $\text{NEIGHBORS}(r_0, c_0) = \{(r, c) \neq (r_0, c_0) \mid |r - r_0| \le 1 \land |c - c_0| \le 1\}$
  4. $\text{CELL\_LIST}(L) = \{u_1, \dots, u_m\}$ with distinct cells $u_a \neq u_b$.

* **Core Clue Templates (6) & Implemented Extensions (5):**

| Category | Template | Formal Semantics |
| :--- | :--- | :--- |
| Core 1 | `FACT(i, Criminal / Innocent)` | $C_i$ or $\neg C_i$ |
| Core 2 | `SAME(i, j)` | $C_i \leftrightarrow C_j$ |
| Core 3 | `DIFFERENT(i, j)` | $C_i \oplus C_j$ |
| Core 4 | `EXACTLY(k, R)` / `NO(R)` | $\sum_{i \in R} \llbracket C_i \rrbracket = k$ (`NO` $\equiv k=0$) |
| Core 5 | `AT_LEAST(k, R)` | $\sum_{i \in R} \llbracket C_i \rrbracket \ge k$ |
| Core 6 | `AT_MOST(k, R)` | $\sum_{i \in R} \llbracket C_i \rrbracket \le k$ |
| **Extension 1** | `ADVANCED_REGIONS` | `INTERSECTION(R1, R2)`, `COMMON_NEIGHBORS(i, j)`, `CORNERS`, `BOUNDARY`, `BETWEEN(i, j)`, `DIRECTIONAL`, `PROFESSION` |
| **Extension 2** | `MORE_CRIMINALS(R1, R2)` / `EQUAL_CRIMINALS(R1, R2)` | $\sum_{i \in R_1} \llbracket C_i \rrbracket > \sum_{j \in R_2} \llbracket C_i \rrbracket$ (or $=$) |
| **Extension 3** | `PARITY(R, ODD / EVEN)` | $\left(\sum_{i \in R} \llbracket C_i \rrbracket\right) \bmod 2 = 1 \text{ (or } 0\text{)}$ |
| **Extension 4** | `COMPOUND(AND / OR / IMPLIES, Φ1, Φ2)` | $\Phi_1 \land \Phi_2$, $\Phi_1 \lor \Phi_2$, or $\Phi_1 \to \Phi_2$ (matching Figure 1 cell A5) |
| **Extension 5** | `CONNECTED(R, status)` | Active `status` cells in $R$ induce $\le 1$ orthogonal grid component (matching Figure 1 cell D5) |

### 2.3 Public Knowledge Base $KB_t$ and Reveal Protocol
At deduction step $t$, let $\mathcal{R}_t \subseteq \{1, \dots, N^2\}$ be the set of revealed cards, $\text{status}(i) \in \{\text{Criminal}, \text{Innocent}\}$ be the proved verdict of $i \in \mathcal{R}_t$, and $\text{clue}(i)$ be its revealed statement. The public knowledge base is:
$$KB_t = \left(\bigwedge_{i \in \mathcal{R}_t} \text{CNF}(\text{clue}(i))\right) \;\land\; \left(\bigwedge_{i \in \mathcal{R}_t} U(i, \text{status}(i))\right)$$
where $U(i, \text{Criminal}) = (C_i)$ and $U(i, \text{Innocent}) = (\neg C_i)$.

**Strict Architectural Isolation:** `GameEngine` encapsulates the hidden ground truth and unrevealed clues in private attributes. `DeductiveLogicAgent` receives only an immutable `PublicGameState` where every unrevealed cell $j \notin \mathcal{R}_t$ has `status = UNKNOWN` and `clue = None`. When a verdict $v \in \{\text{CRIMINAL}, \text{INNOCENT}\}$ is submitted for an unrevealed cell $j$:
1. If neither $KB_t \models C_j$ nor $KB_t \models \neg C_j$, `GameEngine` rejects the move with **`NOT_PROVABLE`** (even if $v$ accidentally matches the hidden label!).
2. If $KB_t$ entails the opposite status, `GameEngine` rejects the move with **`CONTRADICTED`**.
3. Only when $KB_t$ logically entails $v$ does `GameEngine` accept the move (`ACCEPTED`), flip card $j$, and transition to $KB_{t+1}$.

---

## 3. CNF Encoding Derivations

### 3.1 Binary Clue Derivations (`SAME` and `DIFFERENT`)

**1. `SAME(i, j)`:** Characters $i$ and $j$ share the same status ($C_i \leftrightarrow C_j$):
$$\begin{aligned}
C_i \leftrightarrow C_j &\equiv (C_i \to C_j) \land (C_j \to C_i) \\
&\equiv (\neg C_i \lor C_j) \land (\neg C_j \lor C_i) \\
&\equiv (\neg C_i \lor C_j) \land (C_i \lor \neg C_j).
\end{aligned}$$
This yields **2 binary clauses** and **0 auxiliary variables**.

**2. `DIFFERENT(i, j)`:** Characters $i$ and $j$ have opposite statuses ($C_i \oplus C_j$):
$$\begin{aligned}
C_i \oplus C_j &\equiv (C_i \land \neg C_j) \lor (\neg C_i \land C_j) \\
&\equiv (C_i \lor \neg C_i) \land (C_i \lor C_j) \land (\neg C_j \lor \neg C_i) \land (\neg C_j \lor C_j) \quad \text{(distributivity)} \\
&\equiv (C_i \lor C_j) \land (\neg C_i \lor \neg C_j).
\end{aligned}$$
This also yields **2 binary clauses** and **0 auxiliary variables**.

---

### 3.2 Counting Clue Derivation (`EXACTLY(k, R)`)

Consider a concrete 4-cell region $R = \{1, 2, 3, 4\}$ (e.g., $\{A1, B1, A2, B2\}$) and $k = 2$:
$$\text{EXACTLY}(2, \{1,2,3,4\}) \equiv \text{AT\_MOST}(2, \{1,2,3,4\}) \land \text{AT\_LEAST}(2, \{1,2,3,4\}).$$

#### A. Direct Combinatorial Encoding
* **Upper bound (`AT_MOST(k, R)`):** At most $k$ variables are True iff **no subset of size $k + 1$** has all variables True:
  $$\sum_{i \in R} \llbracket C_i \rrbracket \le k \iff \bigwedge_{\substack{S \subseteq R \\ |S| = k + 1}} \neg\left(\bigwedge_{i \in S} C_i\right) \equiv \bigwedge_{\substack{S \subseteq R \\ |S| = k + 1}} \left(\bigvee_{i \in S} \neg C_i\right).$$
  For $|R|=4, k=2$ ($k+1 = 3$), there are $\binom{4}{3} = 4$ clauses:
  $$(\neg C_1 \lor \neg C_2 \lor \neg C_3) \land (\neg C_1 \lor \neg C_2 \lor \neg C_4) \land (\neg C_1 \lor \neg C_3 \lor \neg C_4) \land (\neg C_2 \lor \neg C_3 \lor \neg C_4).$$
* **Lower bound (`AT_LEAST(k, R)`):** At least $k$ variables are True iff at most $|R| - k$ variables are False, so **every subset of size $|R| - k + 1$** contains at least one True variable:
  $$\sum_{i \in R} \llbracket C_i \rrbracket \ge k \iff \bigwedge_{\substack{S \subseteq R \\ |S| = |R| - k + 1}} \left(\bigvee_{i \in S} C_i\right).$$
  For $|R|=4, k=2$ ($4 - 2 + 1 = 3$), there are $\binom{4}{3} = 4$ clauses:
  $$(C_1 \lor C_2 \lor C_3) \land (C_1 \lor C_2 \lor C_4) \land (C_1 \lor C_3 \lor C_4) \land (C_2 \lor C_3 \lor C_4).$$
Total for `EXACTLY(2, {1,2,3,4})`: **8 clauses**, **0 auxiliary variables**.

#### B. Sinz (2005) Sequential Counter Encoding
To avoid $\binom{|R|}{k+1}$ blowup on larger regions (such as 8-neighbor or boundary regions on $5 \times 5$ grids), our encoder also implements **Sinz's Sequential Counter** (`EncodingMode.SEQUENTIAL`). For $\sum_{i=1}^{n} l_i \le k$ ($1 \le k < n$), we introduce $(n-1) \cdot k$ auxiliary partial-sum variables $s_{i,j}$ ($1 \le i \le n-1, 1 \le j \le k$) meaning *"among $l_1 \dots l_i$, at least $j$ literals are True"*:
1. Base ($i=1$): $(\neg l_1 \lor s_{1,1})$ and $(\neg s_{1,j})$ for $2 \le j \le k$.
2. Step ($2 \le i \le n-1$):
   $$(\neg l_i \lor s_{i,1}) \land (\neg s_{i-1,1} \lor s_{i,1}) \land \bigwedge_{j=2}^{k} \Big[(\neg l_i \lor \neg s_{i-1,j-1} \lor s_{i,j}) \land (\neg s_{i-1,j} \lor s_{i,j})\Big] \land (\neg l_i \lor \neg s_{i-1,k}).$$
3. Overflow check at $i=n$: $(\neg l_n \lor \neg s_{n-1,k})$.

#### C. Extension Encodings (`COMPARE_COUNT` and `PARITY`)
* **`MORE_CRIMINALS(R1, R2)`:** After canceling common cells $R_1 \cap R_2$, let $R_1' = R_1 \setminus R_2$ and $R_2' = R_2 \setminus R_1$. For each $j \in R_2'$, introduce auxiliary variable $\bar{A}_j \leftrightarrow \neg C_j$ via $(\neg \bar{A}_j \lor \neg C_j) \land (\bar{A}_j \lor C_j)$. Then:
  $$\sum_{i \in R_1'} C_i > \sum_{j \in R_2'} C_j \iff \sum_{i \in R_1'} C_i + \sum_{j \in R_2'} \bar{A}_j \ge |R_2'| + 1.$$
* **`PARITY(R, ODD/EVEN)`:** Chained via Tseitin XOR auxiliary variables $z_m \leftrightarrow (z_{m-1} \oplus C_{i_m})$, using only $4(|R|-2) + 2$ short clauses of length $\le 3$ instead of $2^{|R|-1}$ exponential clauses.

---

## 4. Algorithms

### 4.1 Custom DPLL SAT Solver (`solver/dpll.py`)
1. **Unit Propagation:** Repeatedly scans unresolved clauses for unit clauses $(L)$. Assigns $L = \text{True}$ (`propagations += 1`), removes satisfied clauses containing $L$, and strips $\neg L$ from remaining clauses until fixed point or an empty clause `()` is produced.
2. **Conflict Detection:** Immediately halts the current branch and returns `UNSAT` whenever an empty clause `()` or contradictory unit literal arises.
3. **Optional Pure-Literal Elimination:** Identifies variables occurring with only a single polarity across active clauses and assigns them to satisfy those clauses.
4. **Deterministic Variable Selection:** Supports `FIXED_ORDER` (smallest unassigned variable ID) and deterministic 2-sided **Jeroslow-Wang** ($J(v) = \sum_{C \ni v} 2^{-|C|} + \sum_{C \ni \neg v} 2^{-|C|}$, tie-broken by smallest variable ID).
5. **Complete Assignment Guarantee:** When all clauses are satisfied, any unconstrained variables in $1 \dots V_{\text{total}}$ are deterministically assigned `False` so `solve()` always returns a complete assignment.

### 4.2 Entailment Classification & Witness-Guided Pruning (`agent/deductive_agent.py`)
For each unresolved character $i \notin \mathcal{R}_t$:
* $KB_t \models C_i \iff KB_t \land \neg C_i \text{ is UNSAT}$ (`CRIMINAL`)
* $KB_t \models \neg C_i \iff KB_t \land C_i \text{ is UNSAT}$ (`INNOCENT`)
* Both satisfiable $\implies$ `UNKNOWN` (agent **never guesses**).
* $KB_t$ itself is UNSAT $\implies$ `INCONSISTENT`.

**Witness-Guided Optimization:** Whenever a SAT query returns a satisfying model $M$, $M$ simultaneously serves as a satisfiability witness for $C_j = M(C_j)$ across **every** unresolved cell $j$. Recording `seen_true[j]` and `seen_false[j]` from every model $M$ immediately classifies any cell with both witnesses as `UNKNOWN` (0 extra SAT calls) and requires at most 1 refutation check for remaining cells, yielding the exact same logical deductions with dramatically fewer SAT calls.

### 4.3 Global Uniqueness Check (`agent/uniqueness.py`) & MUS Hint (`agent/hint.py`)
* **Uniqueness Check:** Solves $KB_{\text{complete}}$ for a first model $M^*$, appends the **primary-only blocking clause** $B(M^*) = \bigvee_{i=1}^{N^2} (\neg C_i \text{ if } M^*(C_i) \text{ else } C_i)$, and re-solves. `UNSAT` proves global uniqueness.
* **Deletion-Based MUS Hint:** Once cell $i^*$ is proved forced ($KB_t \land \neg L_{i^*}$ is `UNSAT`), iteratively tests removing each revealed clue $c$ from $KB_t$; if $(KB_t \setminus \{c\}) \land \neg L_{i^*}$ becomes `SAT`, clue $c$ is essential and highlighted in the GUI without ever inspecting hidden data.

---

## 5. Experimental Evaluation

All 4 solver/encoding configurations were evaluated on the exact same 13-puzzle suite (`3x3` $\times 5$, `4x4` $\times 5$, `5x5` $\times 3$, including `STUCK` and `INCONSISTENT` diagnostic cases). Charts (`chart_runtime_by_grid.png`, `chart_sat_calls_and_decisions.png`, `chart_clauses_comb_vs_seq.png`) are saved in `Source/experiments/results/`.

### 5.1 Per-Puzzle Metrics (`1_Comb_Fixed` Baseline)

| Puzzle ID | Grid | State | Primary + Aux Vars | Peak Clauses | SAT Calls | Decisions | Propagations | Backtracks | Steps (Waves) | Runtime (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `3x3_01_core_intro` | 3x3 | `SOLVED` | 9 + 0 | 60 | 75 | 3 | 449 | 0 | 8 (5) | 17.06 |
| `3x3_02_neighbors_chain` | 3x3 | `SOLVED` | 9 + 0 | 34 | 58 | 0 | 382 | 0 | 7 (3) | 10.34 |
| `3x3_03_extensions_mix` | 3x3 | `SOLVED` | 9 + 0 | 45 | 59 | 0 | 381 | 0 | 7 (4) | 12.47 |
| `3x3_04_ambiguous_case` | 3x3 | `STUCK` | 9 + 0 | 15 | 42 | 30 | 230 | 0 | 2 (1) | 3.69 |
| `3x3_05_inconsistent_case` | 3x3 | `INCONSISTENT` | 9 + 0 | 9 | 1 | 0 | 2 | 0 | 0 (0) | 0.31 |
| `4x4_01_core_patrol` | 4x4 | `SOLVED` | 16 + 0 | 186 | 170 | 24 | 1957 | 0 | 13 (5) | 146.72 |
| `4x4_02_core_precinct` | 4x4 | `SOLVED` | 16 + 0 | 205 | 200 | 136 | 1980 | 0 | 14 (6) | 95.30 |
| `4x4_03_ext_intersections` | 4x4 | `SOLVED` | 16 + 5 | 157 | 191 | 10 | 2079 | 0 | 14 (6) | 64.90 |
| `4x4_04_ext_professions` | 4x4 | `SOLVED` | 16 + 4 | 213 | 232 | 0 | 2387 | 0 | 15 (9) | 120.67 |
| `4x4_05_ext_deep_chain` | 4x4 | `SOLVED` | 16 + 8 | 182 | 214 | 172 | 2693 | 0 | 14 (6) | 326.76 |
| `5x5_01_core_metropolis` | 5x5 | `SOLVED` | 25 + 0 | 448 | 446 | 230 | 6667 | 0 | 22 (6) | 1033.17 |
| `5x5_02_ext_grand_inquest` | 5x5 | `SOLVED` | 25 + 15 | 407 | 542 | 205 | 7667 | 6 | 23 (10) | 493.50 |
| `5x5_03_single_seed_stress` | 5x5 | `SOLVED` | 25 + 16 | 281 | 575 | 200 | 8344 | 0 | 24 (10) | 389.91 |

### 5.2 Aggregate Comparison Across Configurations (11 Solvable Puzzles)

| Configuration | Avg Aux Vars | Avg Peak Clauses | Total SAT Calls | Total Decisions | Total Propagations | Total Backtracks | Total Runtime (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `1_Comb_Fixed` | 4.4 | 201.6 | 2,762 | 980 | 34,986 | 6 | 2,710.81 |
| `2_Seq_Fixed` | 146.3 | 349.6 | 2,762 | 1,449 | 155,074 | 6 | 20,189.98 |
| `3_Comb_JW_PLE` | 4.4 | 201.6 | 2,762 | 944 | 34,768 | 0 | 2,975.34 |
| `4_Comb_JW_Pruned` | 4.4 | 201.6 | 1,555 | 367 | 18,468 | 0 | 1,865.04 |

### Key Experimental Observations
1. **Correctness Consistency Across Encodings & Heuristics:** All 4 configurations (`1_Comb_Fixed`, `2_Seq_Fixed`, `3_Comb_JW_PLE`, `4_Comb_JW_Pruned`) produce the **exact same terminal states, deduction steps, and reveal waves** across all 13 benchmark puzzles:
   * All 11 standard puzzles (`3x3`, `4x4`, `5x5`) reach `SOLVED` with zero guesses.
   * `3x3_04_ambiguous_case` solves `B1` and `C1` in Wave 1 and halts cleanly at `STUCK` without guessing (`UniquenessChecker` confirms multiple solutions).
   * `3x3_05_inconsistent_case` immediately detects `INCONSISTENT` (`KB_0` is UNSAT) in 1 SAT call.
2. **Combinatorial vs. Sinz Sequential Counter:** On $3 \times 3$ and $4 \times 4$ puzzles with small regions ($|R| \le 5$), Direct Combinatorial introduces 0 cardinality auxiliary variables and propagates rapidly. On $5 \times 5$ puzzles with larger regions (8-neighbors, 16-cell boundaries), Sequential Counter keeps clause growth linear $O(|R|\cdot k)$ at the cost of extra auxiliary variables.
3. **Impact of Witness-Guided Pruning & Jeroslow-Wang:** Witness-guided model reuse (`4_Comb_JW_Pruned`) slashes total SAT calls by **~60–75%** on $4 \times 4$ and $5 \times 5$ grids by eliminating redundant satisfiable refutation checks.
4. **Limitations:** Pure propositional DPLL without conflict-driven clause learning (CDCL) or watched literals re-simplifies clause lists at each node; while $3 \times 3$ to $5 \times 5$ puzzles solve in milliseconds, scaling to $10 \times 10+$ grids with global connectivity constraints would benefit from 2-watched literals and CDCL learned clauses.

---

## 6. References & Appendix

### 6.1 References
1. Davis, M., & Putnam, H. (1960). *A computing procedure for quantification theory*. Journal of the ACM, 7(3), 201–215.
2. Davis, M., Logemann, G., & Loveland, D. (1962). *A machine program for theorem-proving*. Communications of the ACM, 5(7), 394–397.
3. Sinz, C. (2005). *Towards an optimal CNF encoding of Boolean cardinality constraints*. In Principles and Practice of Constraint Programming (CP 2005), LNCS 3709, pp. 827–831.
4. Jeroslow, R. G., & Wang, J. (1990). *Solving propositional satisfiability problems*. Annals of Mathematics and Artificial Intelligence, 1(1), 167–187.
5. Russell, S., & Norvig, P. (2020). *Artificial Intelligence: A Modern Approach* (4th ed.), Chapter 7: Logical Agents.
6. Griductive Official Game & Rules: https://griductive.com

### 6.2 Appendix: Generative AI (LLM) Usage Disclosure
Generative AI tools were used responsibly as an engineering & documentation assistant during this project:
* **Architecture & Planning:** Structuring modular separation between `GameEngine` and `DeductiveLogicAgent`, reviewing edge cases in `NOT_PROVABLE` vs. `CONTRADICTED` handling.
* **Verification & Testing:** Designing exhaustive $2^9 = 512$ truth-table equivalence tests comparing `SemanticEvaluator` against `CNFEncoder + DPLLSolver`.
* **Frontend Styling & Plotting Boilerplate:** Assisting with CSS layout for the interactive card grid and `matplotlib` chart formatting scripts.
* **Representative Prompts Used:**
  1. *"Read the CSC14003 Project 2 Griductive Solver specification and build a detailed roadmap strictly aligned with the grading rubric."*
  2. *"Verify the CNF encoding of Sinz (2005) sequential counters and Tseitin XOR parity chains against a direct semantic evaluator across all 512 assignments of a 3x3 board."*
  3. *"Design deletion-based Minimal Unsatisfiable Subset extraction so the Hint button highlights relevant revealed clues without accessing hidden puzzle state."*

---

## 7. Demonstration Video Script (5–10 Minutes — Google Drive)

1. **[0:00 – 1:00] Overview & Architecture:** Show directory structure (`Source/main.py`), launch `python main.py`, explain strict separation between `GameEngine` (secret truth) and `DeductiveLogicAgent` (`PublicGameState` only).
2. **[1:00 – 3:30] Graphical Interface & Manual Gameplay (5 pts):**
   * Load `3x3_01_core_intro`. Point out row/column coordinates (`A1..C3`), names, professions, face-up vs. face-down cards.
   * Click `A1` to demonstrate **visual clue region highlighting** (`Row 1`).
   * Intentionally click `Criminal` on unforced `B2` $\to$ show **`NOT_PROVABLE`** warning (even though `B2` is secretly Criminal, guessing is rejected and card stays face-down!).
   * Intentionally click `Innocent` on forced `B1` $\to$ show **`CONTRADICTED`** error.
   * Click **`Hint`** $\to$ show `B1` pulsing + `A1` highlighted as the minimal supporting clue.
   * Click `Criminal` on `B1` $\to$ show **`ACCEPTED`**, card flip, and newly revealed clue!
3. **[3:30 – 6:30] Automated Solver, Extensions & Uniqueness Check (5 pts):**
   * Click **`Step`** twice and expand the **Deduction Trace** panel to show `KB_t ∧ ¬C_i → UNSAT` SAT queries and live `Primary Vars`, `Aux Vars`, `Clauses`, `Propagations`.
   * Load `4x4_03_ext_intersections`, toggle between `Combinatorial` and `Sinz Sequential Counter` (point out `Auxiliary Vars` changing live!), run **`Check Uniqueness`**, then run animated **`Auto Solve`**.
   * Load `5x5_03_single_seed_stress` (25 characters, 1 starting card $\to$ 24 steps!) and run **`Auto Solve`**.
   * Briefly load `3x3_04_ambiguous_case` (`STUCK` — refuses to guess!) and `3x3_05_inconsistent_case` (`INCONSISTENT` — detects UNSAT!).
4. **[6:30 – 7:30] Benchmark Summary & Wrap-up:** Show generated charts in `Source/experiments/results/` and conclude.
