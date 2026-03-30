# Welcome to
# __________         __    __  .__                               __
# \______   \_____ _/  |__/  |_|  |   ____   ______ ____ _____  |  | __ ____
#  |    |  _/\__  \\   __\   __\  | _/ __ \ /  ___//    \\__  \ |  |/ // __ \
#  |    |   \ / __ \|  |  |  | |  |_\  ___/ \___ \|   |  \/ __ \|    <\  ___/
#  |________/(______/__|  |__| |____/\_____>______>___|__(______/__|__\\_____>
#
# This file can be a nice home for your Battlesnake logic and helper functions.
#
# To get you started we've included code to prevent your Battlesnake from moving backwards.
# For more info see docs.battlesnake.com

import random
import typing
from collections import deque

# info is called when you create your Battlesnake on play.battlesnake.com
# and controls your Battlesnake's appearance
# TIP: If you open your Battlesnake URL in a browser you should see this data

Move = str
Point = typing.Dict[str, int]

def info() -> typing.Dict:
    print("INFO")

    return {
        "apiversion": "1",
        "author": "Group wangle",  # TODO: Your Battlesnake Username
        "color": "#66ccff",  # TODO: Choose color
        "head": "default",  # TODO: Choose head
        "tail": "default",  # TODO: Choose tail
    }


# start is called when your Battlesnake begins a game
def start(game_state: typing.Dict):
    print("GAME START")


# end is called when your Battlesnake finishes a game
def end(game_state: typing.Dict):
    print("GAME OVER\n")

DIRECTIONS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


def add(p: Point, dx: int, dy: int) -> Point:
    return {"x": p["x"] + dx, "y": p["y"] + dy}


def manhattan(a: Point, b: Point) -> int:
    return abs(a["x"] - b["x"]) + abs(a["y"] - b["y"])


def point_to_tuple(p: Point) -> tuple[int, int]:
    return (p["x"], p["y"])


def in_bounds(p: Point, width: int, height: int) -> bool:
    return 0 <= p["x"] < width and 0 <= p["y"] < height


def get_hazard_set(game_state: typing.Dict) -> set[tuple[int, int]]:
    hazards = game_state["board"].get("hazards", [])
    return {point_to_tuple(h) for h in hazards}


def build_occupied_map(game_state: typing.Dict) -> set[tuple[int, int]]:
    """
    Conservative body blocking:
    - block all snake body segments except each snake's tail
    - because tail may move away next turn if that snake does not eat
    This is not perfect, but is a strong baseline heuristic.
    """
    occupied = set()
    snakes = game_state["board"]["snakes"]

    for snake in snakes:
        body = snake["body"]
        if len(body) <= 1:
            occupied.add(point_to_tuple(body[0]))
            continue

        for segment in body[:-1]:
            occupied.add(point_to_tuple(segment))

    return occupied


def get_enemy_head_danger(game_state: typing.Dict) -> set[tuple[int, int]]:
    """
    Squares where moving could lose a head-to-head against an enemy
    of equal or greater length.
    """
    danger = set()
    my_length = game_state["you"]["length"]

    for snake in game_state["board"]["snakes"]:
        if snake["id"] == game_state["you"]["id"]:
            continue

        enemy_head = snake["body"][0]
        enemy_length = snake["length"]

        if enemy_length >= my_length:
            for dx, dy in DIRECTIONS.values():
                nxt = add(enemy_head, dx, dy)
                danger.add(point_to_tuple(nxt))

    return danger


def get_food_list(game_state: typing.Dict) -> list[Point]:
    return game_state["board"].get("food", [])


def get_legal_moves(game_state: typing.Dict) -> list[Move]:
    board = game_state["board"]
    width = board["width"]
    height = board["height"]

    my_head = game_state["you"]["body"][0]
    occupied = build_occupied_map(game_state)

    legal = []
    for move, (dx, dy) in DIRECTIONS.items():
        nxt = add(my_head, dx, dy)

        if not in_bounds(nxt, width, height):
            continue

        if point_to_tuple(nxt) in occupied:
            continue

        legal.append(move)

    return legal


def flood_fill_area(
    start: Point,
    width: int,
    height: int,
    blocked: set[tuple[int, int]],
    limit: int = 80,
) -> int:
    """
    Estimate reachable free area from a square.
    Capped for speed.
    """
    start_t = point_to_tuple(start)
    if start_t in blocked or not in_bounds(start, width, height):
        return 0

    q = deque([start])
    seen = {start_t}
    area = 0

    while q and area < limit:
        cur = q.popleft()
        area += 1

        for dx, dy in DIRECTIONS.values():
            nxt = add(cur, dx, dy)
            nxt_t = point_to_tuple(nxt)

            if nxt_t in seen:
                continue
            if nxt_t in blocked:
                continue
            if not in_bounds(nxt, width, height):
                continue

            seen.add(nxt_t)
            q.append(nxt)

    return area


def min_food_distance(p: Point, foods: list[Point]) -> int:
    if not foods:
        return 999
    return min(manhattan(p, food) for food in foods)


def count_free_neighbors(
    p: Point,
    width: int,
    height: int,
    blocked: set[tuple[int, int]],
) -> int:
    count = 0
    for dx, dy in DIRECTIONS.values():
        nxt = add(p, dx, dy)
        if in_bounds(nxt, width, height) and point_to_tuple(nxt) not in blocked:
            count += 1
    return count


def evaluate_move(game_state: typing.Dict, move: Move) -> float:
    board = game_state["board"]
    width = board["width"]
    height = board["height"]

    my_head = game_state["you"]["body"][0]
    my_health = game_state["you"]["health"]
    my_length = game_state["you"]["length"]

    foods = get_food_list(game_state)
    hazards = get_hazard_set(game_state)
    occupied = build_occupied_map(game_state)
    enemy_head_danger = get_enemy_head_danger(game_state)

    dx, dy = DIRECTIONS[move]
    nxt = add(my_head, dx, dy)
    nxt_t = point_to_tuple(nxt)

    # Hard safety checks
    if not in_bounds(nxt, width, height):
        return -1e9
    if nxt_t in occupied:
        return -1e9

    score = 0.0

    # Strongly avoid risky head-to-head squares
    if nxt_t in enemy_head_danger:
        score -= 120.0

    # Hazard penalty
    if nxt_t in hazards:
        score -= 35.0

    # Space / survivability
    blocked_for_fill = set(occupied)
    area = flood_fill_area(nxt, width, height, blocked_for_fill, limit=80)
    score += area * 3.0

    # Mobility right after moving
    free_neighbors = count_free_neighbors(nxt, width, height, blocked_for_fill)
    score += free_neighbors * 8.0

    # Food logic
    dist_food = min_food_distance(nxt, foods)
    current_dist_food = min_food_distance(my_head, foods)

    # If health is low, care a lot more about food
    if my_health <= 25:
        score -= dist_food * 12.0
        if dist_food < current_dist_food:
            score += 20.0
    elif my_health <= 50:
        score -= dist_food * 6.0
        if dist_food < current_dist_food:
            score += 10.0
    else:
        score -= dist_food * 2.0
        if dist_food < current_dist_food:
            score += 4.0

    # Direct food reward
    if any(nxt["x"] == food["x"] and nxt["y"] == food["y"] for food in foods):
        score += 35.0
        if my_health <= 40:
            score += 50.0

    # Prefer more central squares a bit
    cx = (width - 1) / 2
    cy = (height - 1) / 2
    dist_center = abs(nxt["x"] - cx) + abs(nxt["y"] - cy)
    score -= dist_center * 1.2

    # If area is too small for our body length, penalize a lot
    if area < my_length:
        score -= 80.0

    # Small bonus for not entering hazard when alternatives likely exist
    if nxt_t not in hazards:
        score += 5.0

    return score

# move is called on every turn and returns your next move
# Valid moves are "up", "down", "left", or "right"
# See https://docs.battlesnake.com/api/example-move for available data
def move(game_state: typing.Dict) -> typing.Dict:
    legal_moves = get_legal_moves(game_state)

    if not legal_moves:
        print(f"MOVE {game_state['turn']}: no legal moves, default down")
        return {"move": "down"}

    scored_moves = []
    for m in legal_moves:
        s = evaluate_move(game_state, m)
        scored_moves.append((s, m))

    scored_moves.sort(reverse=True)
    best_score, best_move = scored_moves[0]

    debug_scores = ", ".join([f"{m}:{round(s, 1)}" for s, m in scored_moves])
    print(f"MOVE {game_state['turn']}: {best_move} | {debug_scores}")

    return {"move": best_move}


# Start server when `python main.py` is run
if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
