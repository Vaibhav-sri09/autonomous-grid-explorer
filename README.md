# WALL-E and EVE's Signal 🚀

A Python-based autonomous robot simulation built for the **VinnovateIT club selection**.

WALL-E searches for EVE on a 5×5 grid using distance clues, avoids obstacles, finds shortest paths, and manages its battery to return safely to the charging station.

## ✨ Features

- 🧠 **Smart Search:** Narrows down EVE's possible locations using Manhattan distance.
- 🗺️ **BFS Pathfinding:** Finds the shortest path around obstacles.
- 🔋 **Battery Management:** Returns to the charging station before running low.
- 🔒 **Encapsulation:** EVE's position stays hidden from the agent until discovered.
- 📊 **Mission Reports:** Saves action logs and final results automatically.
- ✅ **Self-Tests:** Includes tests for key behaviours.

## 🛠️ Technologies

- Python 3
- Sets, dictionaries, and queues
- Breadth-First Search (BFS)
- JSON

**Dependencies:** Python standard library only.

## 📂 Project Structure

```text
├── main.py           # Runs the simulation and tests
├── agent.py          # Search logic and pathfinding
├── environment.py    # Grid world and sensor feedback
├── mission.json      # Mission configuration
├── README.md         # Project documentation
├── action_log.json   # Generated action history
└── final_report.json # Generated mission summary
```

## ▶️ Getting Started

Run the simulation:

```bash
python main.py
```

Run the self-tests:

```bash
python main.py --test
```

## 🧠 How It Works

1. WALL-E starts with all valid grid cells as possible EVE locations.
2. It scans for distance clues and eliminates impossible locations.
3. BFS helps it navigate around obstacles using shortest paths.
4. Battery checks ensure it can return to the charging station safely.
5. The mission ends when EVE is found or the mission is determined to be impossible.

## 🎯 Project Goal

Demonstrate autonomous search, pathfinding, logical inference, and battery-aware decision-making using core Python concepts.