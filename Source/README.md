# Griductive Solver — Project 2 (CSC14003: Introduction to AI)

A complete, no-guess **Griductive** game implementation and propositional deduction solver built from scratch using **automatic CNF encoding** and a **custom Davis–Putnam–Logemann–Loveland (DPLL) SAT solver**.

---

## 1. Key Features Aligned with Specification

* **Playable Interactive GUI (`gui/`):**
  * Displays $N \times N$ coordinates (`A1..E5`), character names & professions, face-up clues, and face-down cards.
  * Supports calling unrevealed suspects `INNOCENT` or `CRIMINAL`, strictly distinguishing `ACCEPTED`, `NOT_PROVABLE` (neither verdict forced — even if guessed right by luck!), and `CONTRADICTED` (opposite verdict forced).
  * Click any revealed card to visually highlight all referenced/counted cells on the board.
  * Built-in controls: **Stage Selector**, **Load Custom JSON**, **Restart**, **Hint** (with deletion-based Minimal Unsatisfiable Subset clue highlighting), **Step**, **Auto Solve** (with speed control), and **Check Uniqueness**.
* **Strict Role Separation (`engine/` vs `agent/`):**
  * `GameEngine` privately owns hidden statuses and unrevealed clues.
  * `DeductiveLogicAgent` and `HintEngine` receive **only** immutable `PublicGameState` snapshots.
* **Automatic Logical Representation & CNF Encoder (`logic/`):**
  * Deterministic variable map keeping primary variables ($C_1 \dots C_{N^2}$) strictly separate from auxiliary variables ($> N^2$).
  * Supports all **6 required core clue templates** (`FACT`, `SAME`, `DIFFERENT`, `EXACTLY` / `NO`, `AT_LEAST`, `AT_MOST`) across all 4 required regions (`ROW`, `COL`, `NEIGHBORS`, `CELL_LIST`).
  * Implements **5 distinct extension families** (exceeding the minimum 2 required):
    1. *Extension 1 — Advanced Region Expressions*: `INTERSECTION`, `COMMON_NEIGHBORS`, `CORNERS`, `BOUNDARY`, `BETWEEN`, `DIRECTIONAL`, `PROFESSION`.
    2. *Extension 2 — Regional Count Comparison*: `MORE_CRIMINALS`, `EQUAL_CRIMINALS`.
    3. *Extension 3 — Parity Constraints*: `PARITY` (`ODD` / `EVEN`) via Tseitin XOR chains.
    4. *Extension 4 — Compound Clues*: `COMPOUND` (`AND`, `OR`, `IMPLIES`) via positive selector relaxation and structural De Morgan negation.
    5. *Extension 5 — Orthogonal Connectivity*: `CONNECTED` (1D path forbidden-triple encoding & general 2D Canonical-Root BFS Layered Reachability encoding).
  * Implements **both** *Direct Combinatorial* and *Sinz (2005) Sequential Counter* cardinality encodings, plus a standalone **Direct Semantic Evaluator** (`logic/evaluator.py`) verified exhaustively over all $2^9 = 512$ truth assignments.
* **Custom Pure-Python DPLL SAT Solver (`solver/dpll.py`):**
  * Unit propagation, conflict detection, deterministic variable selection (`FIXED_ORDER` and deterministic `JEROSLOW_WANG`), optional pure-literal elimination, recursive branching & backtracking, complete assignment output, and detailed metrics (`decisions`, `propagations`, `backtracks`, `runtime`).

---

## 2. Installation

Requires **Python 3.10+**. From the `Source/` directory:

```bash
pip install -r requirements.txt
```

---

## 3. Running the Program

### Launch the Interactive Graphical Interface (Default)
```bash
cd Source
python main.py
```
This starts the local server and opens the Griductive GUI automatically in your browser (default `http://127.0.0.1:5050`).

### Run CLI Solver Trace on a Specific Puzzle
```bash
python main.py --cli puzzles/3x3/3x3_01_core_intro.json
python main.py --cli puzzles/5x5/5x5_03_single_seed_stress.json --encoding SEQUENTIAL --heuristic JEROSLOW_WANG --prune
```

### Run Full Experimental Benchmarks & Generate Charts (Section 4.5)
```bash
python main.py --benchmark
```
Outputs CSV metrics, Markdown summary tables, and PNG charts to `Source/experiments/results/`.

### Run Unit Test Suite
```bash
python -m pytest tests -v
```
