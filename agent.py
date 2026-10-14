"""
agent.py
Autonomous WALL-E agent that:
- Maintains belief distribution of EVE's possible locations.
- Updates beliefs using Manhattan distance clues from scans.
- Uses Breadth-First Search (BFS) for shortest obstacle-avoiding paths.
- Monitors battery level and safely retreats to recharge when necessary.
"""

from collections import deque


class WalleAgent:
    def __init__(self, public_info):
        # Known terrain and rules
        self.grid_size = public_info["grid_size"]
        self.rows, self.cols = self.grid_size
        self.position = tuple(public_info["walle_start"])
        self.charging_station = tuple(public_info["charging_station"])
        self.obstacles = {tuple(o) for o in public_info["obstacles"]}
        self.max_battery = public_info["max_battery"]
        self.battery = self.max_battery

        # Knowledge and beliefs about EVE
        # Initially, any valid non-obstacle cell could contain EVE
        self.possible_eve_locations = {
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) not in self.obstacles
        }
        self.scanned_positions = set()
        self.clues_history = []
        self.eve_found = False

    def get_confidence(self):
        """
        Confidence calculation based on remaining possibilities.
        100% if EVE is found or exactly 1 possibility remains.
        """
        if self.eve_found:
            return 100.0
        num_candidates = len(self.possible_eve_locations)
        if num_candidates == 0:
            return 0.0
        return round(100.0 / num_candidates, 1)

    def bfs_shortest_path(self, start, goal):
        """
        Finds the shortest path from start to goal avoiding obstacles.
        Returns a list of coordinates [start, ..., goal] or None if unreachable.
        """
        if start == goal:
            return [start]

        queue = deque([[start]])
        visited = {start}

        while queue:
            path = queue.popleft()
            curr_r, curr_c = path[-1]

            # Explore 4 orthogonal neighbors
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (curr_r + dr, curr_c + dc)
                nr, nc = neighbor

                within_bounds = 0 <= nr < self.rows and 0 <= nc < self.cols
                if within_bounds and neighbor not in self.obstacles and neighbor not in visited:
                    if neighbor == goal:
                        return path + [neighbor]
                    visited.add(neighbor)
                    queue.append(path + [neighbor])

        return None

    def update_beliefs(self, scan_pos, observation):
        """
        Updates the set of possible EVE locations based on scan results.
        Filters out any candidate whose distance does not match the clue.
        """
        self.scanned_positions.add(scan_pos)

        if observation["found"]:
            self.eve_found = True
            self.possible_eve_locations = {scan_pos}
            return

        signal_dist = observation["signal_distance"]
        self.clues_history.append({"scan_pos": scan_pos, "distance": signal_dist})

        # Remove the current cell since EVE is not here
        self.possible_eve_locations.discard(scan_pos)

        # Keep only cells whose Manhattan distance to scan_pos exactly equals signal_dist
        new_candidates = set()
        for cr, cc in self.possible_eve_locations:
            dist = abs(cr - scan_pos[0]) + abs(cc - scan_pos[1])
            if dist == signal_dist:
                new_candidates.add((cr, cc))

        self.possible_eve_locations = new_candidates

    def decide_next_action(self):
        """
        Decides WALL-E's next action using strict battery-safety priorities:
        1. Goal check: Stop if EVE is found or no candidate locations remain.
        2. Station check: If docked at charging station, recharge if depleted.
           If fully charged, verify that at least one candidate is within safe round-trip range.
        3. Field battery safety: In the field, return to charger immediately if battery is low.
        4. Safe scanning: Only scan if battery is sufficient for the scan, the return trip, and a safety reserve of 2.
        5. Safe movement: Advance toward the closest candidate only if lookahead confirms enough battery
           for the move, a potential destination scan, the return trip, and the safety reserve.
        """
        safety_reserve = 2

        # 1. Goal Check
        if self.eve_found:
            return {"action": "STOP", "target": None, "reason": "EVE found!"}

        if not self.possible_eve_locations:
            return {"action": "STOP", "target": None, "reason": "No possible locations remaining."}

        # Shortest path to charging station from current position
        path_to_charger = self.bfs_shortest_path(self.position, self.charging_station)
        if path_to_charger is None:
            return {"action": "STOP", "target": None, "reason": "Mission impossible: Path to charger is blocked."}

        steps_to_charger = len(path_to_charger) - 1

        # 2. Docked at Charging Station Check
        if self.position == self.charging_station:
            # Determine if candidate is reachable and compute needed battery for next step
            best_candidate = None
            best_path = None
            min_path_len = float("inf")
            for candidate in sorted(self.possible_eve_locations):
                path = self.bfs_shortest_path(self.position, candidate)
                if path and len(path) < min_path_len:
                    min_path_len = len(path)
                    best_candidate = candidate
                    best_path = path

            needed_for_next_move = float("inf")
            if best_path and len(best_path) > 1:
                next_step = best_path[1]
                path_from_next_to_charger = self.bfs_shortest_path(next_step, self.charging_station)
                return_steps = (len(path_from_next_to_charger) - 1) if path_from_next_to_charger else 0
                dest_scan_cost = (
                    1 if (next_step in self.possible_eve_locations and next_step not in self.scanned_positions) else 0
                )
                needed_for_next_move = 1 + dest_scan_cost + return_steps + safety_reserve

            # Recharge if battery has depleted by >= 2 units (e.g. returning from an expedition)
            # or if current battery cannot safely afford the next move.
            # Avoids wasting a step topping up 1 unit (17/18 -> 18/18) when WALL-E can safely advance.
            should_recharge = (self.battery <= self.max_battery - 2) or (self.battery < needed_for_next_move)
            if self.battery < self.max_battery and should_recharge:
                return {
                    "action": "RECHARGE",
                    "target": None,
                    "reason": f"Docked at station. Recharging battery ({self.battery}/{self.max_battery}) to full.",
                }

            # If fully charged at base, verify that at least one candidate is within safe operational range
            reachable_and_feasible = False
            for cand in self.possible_eve_locations:
                cand_path = self.bfs_shortest_path(self.charging_station, cand)
                if cand_path:
                    cand_steps = len(cand_path) - 1
                    # Round trip = steps out + 1 (destination scan) + steps back + safety reserve
                    round_trip_cost = (2 * cand_steps) + 1 + safety_reserve
                    if round_trip_cost <= self.max_battery:
                        reachable_and_feasible = True
                        break

            if not reachable_and_feasible and len(self.clues_history) > 0:
                return {
                    "action": "STOP",
                    "target": None,
                    "reason": f"Mission impossible: Remaining candidates exceed safe battery round-trip range for capacity ({self.max_battery}).",
                }

        # 3. Field Battery Safety Rule
        # In the field, if battery is only enough for the return trip + safety reserve, retreat now!
        if self.position != self.charging_station and self.battery <= (steps_to_charger + safety_reserve):
            return {
                "action": "MOVE",
                "target": path_to_charger[1],
                "reason": f"Low battery ({self.battery}). Returning to charger with safety reserve.",
            }

        # 4. Safe Scanning Priority
        should_scan = (
            len(self.clues_history) == 0 and self.position == self.charging_station
        ) or (
            self.position in self.possible_eve_locations and self.position not in self.scanned_positions
        )
        if should_scan and self.position not in self.scanned_positions:
            cost_of_scan = 1
            battery_needed_for_scan = cost_of_scan + steps_to_charger + safety_reserve

            if self.battery >= battery_needed_for_scan:
                return {"action": "SCAN", "target": None, "reason": "Scanning for EVE's signal."}
            else:
                # Cannot afford scan without violating safety reserve! Return to charger
                if self.position != self.charging_station:
                    return {
                        "action": "MOVE",
                        "target": path_to_charger[1],
                        "reason": f"Insufficient battery to scan safely ({self.battery} < {battery_needed_for_scan}). Returning to charger.",
                    }
                else:
                    return {
                        "action": "RECHARGE",
                        "target": None,
                        "reason": "Recharging at station before scanning.",
                    }

        # 5. Safe Movement Toward Nearest Candidate
        best_candidate = None
        best_path = None
        min_path_len = float("inf")

        for candidate in sorted(self.possible_eve_locations):
            path = self.bfs_shortest_path(self.position, candidate)
            if path and len(path) < min_path_len:
                min_path_len = len(path)
                best_candidate = candidate
                best_path = path

        if best_path and len(best_path) > 1:
            next_step = best_path[1]

            # Movement lookahead check:
            # Must account for:
            # - 1 battery for the move to next_step
            # - 1 battery for a potential scan if next_step is an unscanned candidate
            # - Shortest return path from next_step back to the charger
            # - Safety reserve of 2 units
            path_from_next_to_charger = self.bfs_shortest_path(next_step, self.charging_station)
            if path_from_next_to_charger is None:
                return {
                    "action": "MOVE",
                    "target": path_to_charger[1],
                    "reason": "Next step has no valid path to charger. Returning to safety.",
                }

            return_steps = len(path_from_next_to_charger) - 1
            dest_scan_cost = (
                1 if (next_step in self.possible_eve_locations and next_step not in self.scanned_positions) else 0
            )
            needed_battery = 1 + dest_scan_cost + return_steps + safety_reserve

            if self.battery < needed_battery:
                if self.position != self.charging_station:
                    return {
                        "action": "MOVE",
                        "target": path_to_charger[1],
                        "reason": f"Insufficient battery to advance safely ({self.battery} < {needed_battery}). Returning to charger.",
                    }
                else:
                    return {
                        "action": "STOP",
                        "target": None,
                        "reason": f"Mission impossible: Move toward candidate requires {needed_battery} battery, exceeding capacity ({self.battery}).",
                    }

            return {
                "action": "MOVE",
                "target": next_step,
                "reason": f"Advancing toward candidate {best_candidate}.",
            }

        return {"action": "STOP", "target": None, "reason": "No reachable candidate found."}
