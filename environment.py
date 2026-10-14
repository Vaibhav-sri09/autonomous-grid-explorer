"""
environment.py
Manages the 5x5 simulation grid, obstacles, charging station,
and keeps EVE's coordinates strictly private.
WALL-E interacts only through actions: move, scan, and recharge.
"""

import json


class GridEnvironment:
    def __init__(self, config_path="mission.json"):
        with open(config_path, "r") as f:
            data = json.load(f)

        self.rows, self.cols = data["grid_size"]
        self.walle_pos = tuple(data["walle_start"])
        self.charging_station = tuple(data["charging_station"])
        self.obstacles = {tuple(obs) for obs in data["obstacles"]}
        self.max_battery = data.get("max_battery", 20)

        # EVE's position is strictly private (hidden) to prevent cheating
        self._eve_position = tuple(data["eve_hidden_position"])

    def get_public_info(self):
        """
        Returns only the terrain information WALL-E is allowed to know.
        Never reveals EVE's hidden position.
        """
        return {
            "grid_size": (self.rows, self.cols),
            "walle_start": self.walle_pos,
            "charging_station": self.charging_station,
            "obstacles": list(self.obstacles),
            "max_battery": self.max_battery,
        }

    def is_valid_cell(self, pos):
        """Checks if a coordinate is inside the grid and not an obstacle."""
        r, c = pos
        within_bounds = 0 <= r < self.rows and 0 <= c < self.cols
        not_blocked = pos not in self.obstacles
        return within_bounds and not_blocked

    def move(self, new_pos):
        """Moves WALL-E to an adjacent non-obstacle cell."""
        new_pos = tuple(new_pos)
        r1, c1 = self.walle_pos
        r2, c2 = new_pos

        # Check adjacency (Manhattan distance == 1)
        is_adjacent = abs(r1 - r2) + abs(c1 - c2) == 1

        if is_adjacent and self.is_valid_cell(new_pos):
            self.walle_pos = new_pos
            return {
                "success": True,
                "position": self.walle_pos,
                "message": f"WALL-E moved to {self.walle_pos}",
            }
        else:
            return {
                "success": False,
                "position": self.walle_pos,
                "message": f"Illegal move from {self.walle_pos} to {new_pos}",
            }

    def scan(self):
        """
        Scans from WALL-E's current location.
        Returns distance clue without exposing EVE's exact coordinates.
        """
        if self.walle_pos == self._eve_position:
            return {
                "found": True,
                "signal_distance": 0,
                "message": "Direct signal! EVE is right here!",
            }

        # Calculate Manhattan distance to hidden EVE
        dist = abs(self.walle_pos[0] - self._eve_position[0]) + abs(
            self.walle_pos[1] - self._eve_position[1]
        )
        return {
            "found": False,
            "signal_distance": dist,
            "message": f"Signal received: EVE is {dist} step(s) away.",
        }

    def recharge(self):
        """Recharges WALL-E only if currently at the charging station."""
        if self.walle_pos == self.charging_station:
            return {
                "success": True,
                "message": f"WALL-E docked at {self.charging_station} and fully recharged!",
            }
        return {
            "success": False,
            "message": f"Cannot recharge: not at charging station {self.charging_station}.",
        }

    def render(self, candidates=None, reveal_eve=False):
        """Draws a clean ASCII grid to visually follow the mission."""
        grid_lines = []
        top_border = "   +" + "---+" * self.cols
        grid_lines.append(top_border)

        for r in range(self.rows):
            row_str = f" {r} |"
            for c in range(self.cols):
                pos = (r, c)
                if pos == self.walle_pos and reveal_eve and pos == self._eve_position:
                    cell_sym = "W&E"
                elif pos == self.walle_pos:
                    cell_sym = " W "
                elif reveal_eve and pos == self._eve_position:
                    cell_sym = " E "
                elif pos in self.obstacles:
                    cell_sym = " # "
                elif pos == self.charging_station:
                    cell_sym = " C "
                elif candidates and pos in candidates:
                    cell_sym = " ? "
                else:
                    cell_sym = " . "
                row_str += cell_sym + "|"
            grid_lines.append(row_str)
            grid_lines.append(top_border)

        col_header = "     " + "   ".join(str(c) for c in range(self.cols))
        grid_lines.append(col_header)
        return "\n".join(grid_lines)
