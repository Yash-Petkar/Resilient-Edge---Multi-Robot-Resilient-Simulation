import json
from pathlib import Path

import pytest

from core.simulation.world import WarehouseWorld


def test_default_world_is_deterministic_and_valid():
    a = WarehouseWorld()
    b = WarehouseWorld()
    assert a.to_dict() == b.to_dict()
    assert (a.width, a.height) == (24, 16)
    assert a.shelves
    assert a.pickup_stations and a.delivery_stations and a.charging_bays
    assert all(a.is_walkable(p) for p in a.operational_cells)


def test_world_configuration_is_external_and_round_trippable():
    cfg = WarehouseWorld.default_config(width=12, height=10)
    cfg["shelves"] = [[5, 3], [5, 4]]
    cfg["pickup_stations"] = {"P1": [1, 1]}
    cfg["delivery_stations"] = {"D1": [10, 8]}
    cfg["charging_bays"] = {"C1": [1, 8]}
    cfg["robot_starts"] = [[2, 8], [3, 8]]
    cfg["choke_points"] = [[4, 4]]
    cfg["aisles"] = {"horizontal": [0, 1, 5, 9], "vertical": [0, 1, 4, 5, 6, 7, 8, 9, 10, 11]}
    world = WarehouseWorld(config=cfg)
    restored = WarehouseWorld(config=world.to_dict())
    assert restored.to_dict() == world.to_dict()
    assert restored.is_walkable((4, 4))
    assert not restored.is_walkable((5, 3))


def test_json_configuration_file_is_supported():
    path = Path(__file__).parents[1] / "config" / "warehouse_default.json"
    world = WarehouseWorld(config_path=path)
    assert world.to_dict() == WarehouseWorld().to_dict()


def test_static_restricted_cells_are_not_walkable():
    world = WarehouseWorld(config={
        "width": 6, "height": 6,
        "shelves": [[2, 2]],
        "restricted_cells": [[3, 3]],
        "pickup_stations": {"P1": [0, 0]},
        "delivery_stations": {"D1": [5, 5]},
        "charging_bays": {"C1": [0, 5]},
        "robot_starts": [[1, 5]],
        "choke_points": [[1, 2]],
        "aisles": {"horizontal": [0, 1, 4, 5], "vertical": [0, 1, 4, 5]},
    })
    assert not world.is_walkable((2, 2))
    assert not world.is_walkable((3, 3))
    assert world.is_walkable((4, 4))


def test_dynamic_obstacles_change_walkability_and_can_be_removed():
    world = WarehouseWorld()
    cell = (5, 5)
    assert world.is_walkable(cell)
    world.add_dynamic_obstacle(cell)
    assert not world.is_walkable(cell)
    assert cell in world.dynamic_obstacles
    world.remove_dynamic_obstacle(cell)
    assert world.is_walkable(cell)


def test_blocked_aisle_cells_are_environmental_state_not_static_topology():
    world = WarehouseWorld()
    cell = (5, 5)
    world.block_cells([cell])
    assert cell in world.blocked_aisles
    assert not world.is_walkable(cell)
    world.unblock_cells([cell])
    assert world.is_walkable(cell)


def test_world_reset_preserves_topology_but_clears_environmental_faults():
    world = WarehouseWorld()
    topology = world.to_dict()
    world.add_dynamic_obstacle((5, 5))
    world.block_cells([(5, 6)])
    world.reset_dynamic_state()
    current = world.to_dict()
    for key in ("width", "height", "shelves", "restricted_cells", "pickup_stations",
                "delivery_stations", "charging_bays", "robot_starts", "choke_points", "aisles"):
        assert current[key] == topology[key]
    assert current["blocked_aisles"] == []
    assert current["dynamic_obstacles"] == []


def test_out_of_bounds_dynamic_obstacle_is_rejected():
    world = WarehouseWorld()
    with pytest.raises(ValueError):
        world.add_dynamic_obstacle((999, 999))
