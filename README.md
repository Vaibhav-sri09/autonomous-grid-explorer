# WALL-E and EVE's Signal 🚀

A beginner-friendly, clean Python simulation built for the **VinnovateIT club selection**.

In this project, an autonomous robot (**WALL-E**) searches for his lost companion (**EVE**) on a 5×5 grid. WALL-E must navigate around obstacles, track battery consumption, retreat to a charging station when power is low, and deduce EVE's hidden position purely through signal observations.

---

## 🎯 Project Highlights

- **Pure Python Standard Library**: No external dependencies (`numpy`, `pandas`, or external AI APIs) required.
- **True Encapsulation (Zero Cheating)**: EVE's coordinates are stored strictly inside the private environment (`_eve_position`). The agent only learns through distance clues returned by radar scans.
- **Belief State Filtering**: Maintains candidate locations using Python `set`s and updates them mathematically via Manhattan distance filtering.
- **BFS Shortest Path**: Uses Breadth-First Search to find the shortest obstacle-free route on a 2D grid.
- **Autonomous Battery Safeguard**: WALL-E calculates the exact return distance to the charging station and retreats proactively before running out of power.
- **Comprehensive Logging**: Automatically logs every step to `action_log.json` and produces a mission summary in `final_report.json`.

---

## 📁 Project Structure

```text
aiml,vinnovateit/
├── mission.json       # Mission settings (grid size, start, obstacles, charger, EVE)
├── environment.py     # Grid world, action execution, and sensor feedback
├── agent.py           # WALL-E's brain: BFS pathfinding, beliefs, and decision logic
├── main.py            # Simulation runner, terminal renderer, and self-tests
├── README.md          # Documentation and interview guide
├── action_log.json    # (Generated) Step-by-step action history
└── final_report.json  # (Generated) Final mission performance summary
```

---

## ⚡ How to Run

### 1. Run the Simulation
To execute the autonomous mission:
```bash
python main.py
```

You will see live console logs with an ASCII grid showing WALL-E (`W`), obstacles (`#`), the charging station (`C`), candidate possibilities (`?`), and EVE (`E`) upon discovery!

### 2. Run the Verification Self-Tests
To run the automated assertion checks (encapsulation, BFS, belief pruning):
```bash
python main.py --test
```

---

## 🧠 How It Works (The Logic)

### 1. Environment & Encapsulation (`environment.py`)
- The grid is $5 \times 5$ (coordinates $(0, 0)$ to $(4, 4)$).
- Obstacles block movement.
- `_eve_position` has a leading underscore, making it internal to `GridEnvironment`.
- `get_public_info()` shares grid bounds, obstacles, charger location, and starting coordinates, but **never** shares EVE's coordinates.
- When WALL-E executes `scan()`, the environment returns:
  $$\text{distance} = |r_{\text{walle}} - r_{\text{eve}}| + |c_{\text{walle}} - c_{\text{eve}}|$$

### 2. Belief State & Confidence (`agent.py`)
- **Initial Belief**: At the start, all non-obstacle cells are candidates in `possible_eve_locations`.
- **Filtering**: When a scan at $(r_s, c_s)$ reports distance $D$:
  $$\text{new\_candidates} = \{(r, c) \in \text{candidates} \mid |r - r_s| + |c - c_s| = D\}$$
- **Confidence Formula**:
  $$\text{Confidence} = \begin{cases} 100\% & \text{if EVE found} \\ \text{round}\left(\frac{100}{|\text{candidates}|}, 1\right)\% & \text{if candidates remain} \\ 0\% & \text{otherwise} \end{cases}$$

### 3. BFS Pathfinding (`agent.py`)
- Breadth-First Search (`collections.deque`) explores coordinates level-by-level (Up, Down, Left, Right).
- Guarantees the **shortest valid path** avoiding obstacles and grid boundaries.

### 4. Decision Priority Order
On every step, WALL-E follows strict battery-action priority rules:
1. **Mission Complete**: If EVE is found or candidate list is empty $\rightarrow$ `STOP`.
2. **Docked Station Check**: If at the charging station:
   - Recharge to 100% if battery is depleted.
   - If fully charged, verify that at least one candidate is within safe round-trip range; if not, halt safely (`Mission impossible`).
3. **Field Battery Safety**: In the field, if $\text{battery} \le \text{steps\_to\_charger} + 2 \rightarrow$ immediately `MOVE` toward charger.
4. **Safe Scanning**: Before scanning, verify $\text{battery} \ge 1 \text{ (scan)} + \text{steps\_to\_charger} + 2 \text{ (reserve)}$. If not, refuse to scan and return to charger.
5. **Explore with Destination Lookahead**: Advance toward the closest candidate only if:
   $$\text{battery} \ge 1 \text{ (move)} + \text{dest\_scan\_cost} + \text{return\_steps} + 2 \text{ (reserve)}$$
   Never assume a destination scan is free! If insufficient, return to charger immediately.

---

## 🎤 Interview Cheatsheet (Quick Q&A)

### Q1: How do you prove your AI agent isn't "cheating" by peeking at EVE's position?
> **Answer**: *"In `environment.py`, EVE's coordinate is stored in `self._eve_position`. The agent only receives `public_info`, which explicitly omits EVE. The agent can only learn by calling `scan()`, which computes the Manhattan distance on the fly. The agent literally has no variable referencing EVE's coordinates until it filters down its candidate set."*

### Q2: Why did you use Manhattan Distance instead of Euclidean distance?
> **Answer**: *"Because WALL-E moves on a grid grid-step by grid-step (orthogonal movement: Up, Down, Left, Right), Euclidean diagonal lines don't apply. Manhattan distance $|r_1 - r_2| + |c_1 - c_2|$ exactly matches the minimum step distance on a grid."*

### Q3: Why use BFS instead of DFS or A*?
> **Answer**:
> - *"DFS does not guarantee the shortest path."*
> - *"A\* requires heuristics; on a tiny 5×5 grid, BFS is optimal, extremely fast ($O(V + E)$ where $V = 25$), uses standard Python `collections.deque`, and has zero overhead."*

### Q4: How does the battery safety system prevent WALL-E from dying in the field?
> **Answer**: *"WALL-E uses a two-layer safety check: (1) A lookahead check before advancing that ensures moving forward leaves enough battery to return home with a safety reserve of $\ge 2$; (2) A return rule that triggers whenever $\text{battery} \le \text{steps\_to\_charger} + 2$, guaranteeing WALL-E always docks with positive battery reserve and never hits 0."*

### Q5: What data structures were chosen and why?
> - **`set`**: Used for `obstacles`, `visited`, and `possible_eve_locations` for $O(1)$ fast lookups, membership checks, and set discards.
> - **`deque`**: Used in BFS for $O(1)$ fast queue pop from the left.
> - **`dict`**: Used for mission configs, action logs, and observations.
