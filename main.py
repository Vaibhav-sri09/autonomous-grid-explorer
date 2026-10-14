"""
main.py
Main entry point for "WALL-E and EVE's Signal" simulation.
Runs the autonomous search loop, logs actions, and generates the final report.
"""

import json
from environment import GridEnvironment
from agent import WalleAgent


def run_simulation(config_path="mission.json", max_steps=60):
    print("=" * 60)
    print("    WALL-E AND EVE'S SIGNAL - SIMULATION START")
    print("=" * 60)

    # 1. Initialize environment & agent
    env = GridEnvironment(config_path)
    public_info = env.get_public_info()
    agent = WalleAgent(public_info)

    print(f"Grid Size       : {public_info['grid_size'][0]}x{public_info['grid_size'][1]}")
    print(f"WALL-E Start    : {public_info['walle_start']}")
    print(f"Charging Station: {public_info['charging_station']}")
    print(f"Obstacles       : {public_info['obstacles']}")
    print(f"Starting Battery: {agent.battery}/{agent.max_battery}")
    print("-" * 60)
    print("Initial Grid:")
    print(env.render(candidates=agent.possible_eve_locations))
    print("-" * 60)

    action_log = []
    step_num = 0
    moves_count = 0
    scans_count = 0
    recharges_count = 0

    stop_reason = "Maximum steps reached without finding EVE."

    # 2. Main Simulation Loop
    while step_num < max_steps:
        decision = agent.decide_next_action()
        action_type = decision["action"]

        if action_type == "STOP":
            stop_reason = decision["reason"]
            print(f"\n[STOP TRIGGERED] Reason: {stop_reason}")
            break

        step_num += 1
        log_entry = {
            "step": step_num,
            "action": action_type,
            "reason": decision["reason"],
            "battery_before": agent.battery,
        }

        if action_type == "SCAN":
            scans_count += 1
            agent.battery -= 1
            observation = env.scan()
            agent.update_beliefs(agent.position, observation)

            log_entry["position"] = list(agent.position)
            log_entry["observation"] = observation
            log_entry["battery_after"] = agent.battery
            log_entry["remaining_candidates"] = len(agent.possible_eve_locations)
            log_entry["confidence_pct"] = agent.get_confidence()

            print(
                f"Step {step_num:02d} | [SCAN] at {agent.position} | "
                f"Obs: {observation['message']} | "
                f"Candidates: {len(agent.possible_eve_locations)} | "
                f"Conf: {agent.get_confidence()}% | Batt: {agent.battery}"
            )

        elif action_type == "MOVE":
            moves_count += 1
            target_cell = decision["target"]
            result = env.move(target_cell)

            if result["success"]:
                agent.position = target_cell
                agent.battery -= 1
                log_entry["position"] = list(agent.position)
                log_entry["observation"] = result["message"]
                log_entry["battery_after"] = agent.battery
                log_entry["remaining_candidates"] = len(agent.possible_eve_locations)
                log_entry["confidence_pct"] = agent.get_confidence()

                print(
                    f"Step {step_num:02d} | [MOVE] to {agent.position} | "
                    f"Batt: {agent.battery} | {decision['reason']}"
                )
            else:
                print(f"Step {step_num:02d} | [MOVE FAILED] {result['message']}")
                log_entry["observation"] = result["message"]
                log_entry["battery_after"] = agent.battery
                stop_reason = f"Move failed: {result['message']}"
                break

        elif action_type == "RECHARGE":
            result = env.recharge()
            if result["success"]:
                recharges_count += 1
                agent.battery = agent.max_battery
                log_entry["position"] = list(agent.position)
                log_entry["observation"] = result["message"]
                log_entry["battery_after"] = agent.battery
                log_entry["remaining_candidates"] = len(agent.possible_eve_locations)
                log_entry["confidence_pct"] = agent.get_confidence()

                print(
                    f"Step {step_num:02d} | [RECHARGE] at {agent.position} | "
                    f"Battery restored to {agent.battery} | {result['message']}"
                )
            else:
                log_entry["position"] = list(agent.position)
                log_entry["observation"] = result["message"]
                log_entry["battery_after"] = agent.battery
                log_entry["remaining_candidates"] = len(agent.possible_eve_locations)
                log_entry["confidence_pct"] = agent.get_confidence()

                print(f"Step {step_num:02d} | [RECHARGE FAILED] at {agent.position} | {result['message']}")
                stop_reason = f"Recharge failed: {result['message']}"
                action_log.append(log_entry)
                break

        action_log.append(log_entry)

        # Check battery exhaustion safeguard
        if agent.battery <= 0 and not agent.eve_found and agent.position != agent.charging_station:
            stop_reason = "WALL-E ran out of battery in the field!"
            print(f"\n[ALERT] {stop_reason}")
            break

    # 3. Save Action Log
    with open("action_log.json", "w") as f:
        json.dump(action_log, f, indent=2)

    # 4. Compile Final Report
    final_report = {
        "mission_name": "WALL-E and EVE's Signal",
        "target_found": agent.eve_found,
        "termination_reason": stop_reason,
        "total_steps": step_num,
        "moves_count": moves_count,
        "scans_count": scans_count,
        "recharges_count": recharges_count,
        "final_battery": agent.battery,
        "clues_collected_count": len(agent.clues_history),
        "clues": agent.clues_history,
        "remaining_possible_locations": [list(pos) for pos in sorted(agent.possible_eve_locations)],
        "final_confidence_pct": agent.get_confidence(),
    }

    with open("final_report.json", "w") as f:
        json.dump(final_report, f, indent=2)

    # 5. Display Final Summary
    print("\n" + "=" * 60)
    print("                     FINAL MISSION REPORT")
    print("=" * 60)
    print(f"EVE Found          : {'YES!' if agent.eve_found else 'NO'}")
    print(f"Termination Reason : {stop_reason}")
    print(f"Total Steps Taken  : {step_num}")
    print(f"Moves Made         : {moves_count}")
    print(f"Scans Performed    : {scans_count}")
    print(f"Recharges Done     : {recharges_count}")
    print(f"Remaining Battery  : {agent.battery}/{agent.max_battery}")
    print(f"Final Confidence   : {agent.get_confidence()}%")
    print(f"Possible Locations : {sorted(list(agent.possible_eve_locations))}")
    print("-" * 60)
    print("Final Grid (W = WALL-E, E = EVE, # = Obstacle, C = Charger):")
    print(env.render(candidates=agent.possible_eve_locations, reveal_eve=True))
    print("-" * 60)
    print("Logs saved to 'action_log.json' and 'final_report.json'.")
    print("=" * 60)

    return final_report


def run_self_tests():
    """Comprehensive verification tests for all core features and edge cases."""
    print("\n" + "=" * 60)
    print("             RUNNING COMPREHENSIVE SELF-TESTS")
    print("=" * 60)
    import os

    # 1. Test Environment Encapsulation
    env = GridEnvironment("mission.json")
    info = env.get_public_info()
    assert "_eve_position" not in info, "EVE's hidden position leaked in public info!"
    assert "eve_hidden_position" not in info, "EVE's hidden key leaked in public info!"
    print("[PASS] Test 1: Encapsulation - EVE's coordinates are strictly hidden from agent.")

    # 2. Test Obstacle Avoidance (BFS)
    agent = WalleAgent(info)
    path = agent.bfs_shortest_path((0, 0), (4, 4))
    assert path is not None, "BFS failed to find path around obstacles!"
    for cell in path:
        assert cell not in agent.obstacles, f"BFS path passed through obstacle: {cell}"
    print("[PASS] Test 2: Obstacle Avoidance - BFS path safely circumvents all obstacles.")

    # 3. Test Belief Updates & Observation Influence
    obs1 = {"found": False, "signal_distance": 7, "message": "Signal: 7 steps away"}
    agent.update_beliefs((0, 0), obs1)
    assert len(agent.possible_eve_locations) == 2, f"Expected 2 candidates, got {len(agent.possible_eve_locations)}"
    assert (3, 4) in agent.possible_eve_locations and (4, 3) in agent.possible_eve_locations
    assert agent.get_confidence() == 50.0, f"Expected 50.0% confidence, got {agent.get_confidence()}%"

    obs2 = {"found": False, "signal_distance": 2, "message": "Signal: 2 steps away"}
    agent.update_beliefs((3, 4), obs2)
    assert len(agent.possible_eve_locations) == 1, f"Expected 1 candidate, got {len(agent.possible_eve_locations)}"
    assert (4, 3) in agent.possible_eve_locations
    assert agent.get_confidence() == 100.0, f"Expected 100.0% confidence, got {agent.get_confidence()}%"
    print("[PASS] Test 3: Belief Updates - Scan clues prune possibilities and update confidence.")

    # 4. Test Low-Battery Scanning Prevention & Safe Return
    low_bat_agent = WalleAgent(info)
    low_bat_agent.position = (3, 4)
    low_bat_agent.possible_eve_locations = {(3, 4)}
    # At (3, 4), steps_to_charger is 7. To scan safely: 1 (scan) + 7 (return) + 2 (reserve) = 10 needed.
    # With battery = 9, scanning would leave only 8 battery for a 7-step return (margin 1 < reserve 2).
    low_bat_agent.battery = 9
    decision = low_bat_agent.decide_next_action()
    assert decision["action"] == "MOVE", f"Expected MOVE to charger, got {decision['action']}"
    assert decision["action"] != "SCAN", "Agent illegally scanned when battery was insufficient!"
    path_back = low_bat_agent.bfs_shortest_path((3, 4), low_bat_agent.charging_station)
    assert decision["target"] == path_back[1], f"Expected step toward charger, got {decision['target']}"
    print("[PASS] Test 4: Low-Battery Scan Prevention - Refuses unsafe scan and retreats to charger.")

    # 5. Test Movement Lookahead Accounting for Destination Scan
    lookahead_agent = WalleAgent(info)
    lookahead_agent.position = (3, 3)
    lookahead_agent.clues_history.append({"scan_pos": (0, 0), "distance": 7})
    lookahead_agent.scanned_positions.add((0, 0))
    lookahead_agent.possible_eve_locations = {(3, 4)}

    # From (3, 3), steps_to_charger is 6, so field retreat threshold (battery <= 6 + 2 = 8) does NOT trigger with battery = 10.
    # Advancing to candidate (3, 4) requires: 1 (move) + 1 (destination scan) + 7 (return steps) + 2 (reserve) = 11 battery.
    # With battery = 10, the lookahead check is reached and rejects moving to (3, 4) specifically due to destination scan cost.
    lookahead_agent.battery = 10
    decision = lookahead_agent.decide_next_action()
    assert decision["action"] == "MOVE", f"Expected MOVE, got {decision['action']}"
    assert decision["target"] != (3, 4), "Agent illegally moved to candidate without destination scan power!"
    assert "Insufficient battery to advance safely" in decision["reason"], (
        f"Expected lookahead rejection reason, got: {decision['reason']}"
    )

    # With battery = 11 (affording move + dest scan + return + reserve), lookahead permits advancing:
    lookahead_agent.battery = 11
    decision_pass = lookahead_agent.decide_next_action()
    assert decision_pass["action"] == "MOVE"
    assert decision_pass["target"] == (3, 4), "Agent failed to advance when sufficient battery was present!"
    assert "Advancing toward candidate" in decision_pass["reason"]
    print("[PASS] Test 5: Movement Lookahead - Accounts for destination scan and asserts lookahead rejection.")

    # 6. Test Recharging, Result Verification & Mission Resumption
    recharge_agent = WalleAgent(info)
    recharge_agent.position = recharge_agent.charging_station
    recharge_agent.battery = 2
    decision = recharge_agent.decide_next_action()
    assert decision["action"] == "RECHARGE", f"Expected RECHARGE, got {decision['action']}"

    # Verify environment fails recharge if not at station
    env_fake = GridEnvironment("mission.json")
    env_fake.walle_pos = (1, 1)
    res_fake = env_fake.recharge()
    assert res_fake["success"] is False, "Environment should not succeed recharge away from base!"

    # Successful recharge at base
    env_real = GridEnvironment("mission.json")
    res_real = env_real.recharge()
    assert res_real["success"] is True
    recharge_agent.battery = recharge_agent.max_battery

    decision_after = recharge_agent.decide_next_action()
    assert decision_after["action"] in ("SCAN", "MOVE"), (
        f"Expected SCAN or MOVE after recharge, got {decision_after['action']}"
    )
    print("[PASS] Test 6: Recharging & Resumption - Validates recharge success flag, docks, and resumes search.")

    # 7. Test Mission Impossibility Handling
    impossible_info = dict(info)
    impossible_info["max_battery"] = 6  # 6 battery cannot support round trip to candidates at distance >= 2
    impossible_agent = WalleAgent(impossible_info)
    impossible_agent.update_beliefs((0, 0), {"found": False, "signal_distance": 7})
    decision_imp = impossible_agent.decide_next_action()
    assert decision_imp["action"] == "STOP", f"Expected STOP for impossible mission, got {decision_imp['action']}"
    assert "Mission impossible" in decision_imp["reason"], f"Unexpected reason: {decision_imp['reason']}"
    print("[PASS] Test 7: Impossibility Safeguard - Gracefully terminates when safe completion is impossible.")

    # 8. Test Full Simulation Execution & Action Log Safety
    report = run_simulation()
    assert os.path.exists("action_log.json"), "action_log.json was not created!"
    assert os.path.exists("final_report.json"), "final_report.json was not created!"
    assert report["target_found"] is True, "EVE was not successfully found in simulation!"

    with open("action_log.json", "r") as f:
        logs = json.load(f)

    for entry in logs:
        # Every step in the simulation must retain non-negative battery
        assert entry["battery_after"] >= 0, f"Step {entry['step']} ran out of battery!"
        # When docking to recharge, battery before recharge must be >= safety reserve (2)
        if entry["action"] == "RECHARGE":
            assert entry["battery_before"] >= 2, (
                f"WALL-E reached charging station with battery {entry['battery_before']} (< 2 reserve)!"
            )
    print("[PASS] Test 8: Full Simulation - Successful discovery, battery >= 2 at dock, reports saved.")
    print("\n" + "=" * 60)
    print("             ALL 8 SELF-TESTS PASSED SUCCESSFULLY!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        run_self_tests()
    else:
        run_simulation()
