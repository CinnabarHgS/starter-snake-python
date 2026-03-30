import copy
from collections import deque
from typing import Dict, List

Move = str
Point = Dict[str, int]

DIRECTIONS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


def clone_state(state: dict) -> dict:
    return copy.deepcopy(state)


def point_to_tuple(p: Point) -> tuple[int, int]:
    return (p["x"], p["y"])


def add(p: Point, dx: int, dy: int) -> Point:
    return {"x": p["x"] + dx, "y": p["y"] + dy}


def add_by_move(p: Point, move: Move) -> Point:
    dx, dy = DIRECTIONS[move]
    return add(p, dx, dy)


def manhattan(a: Point, b: Point) -> int:
    return abs(a["x"] - b["x"]) + abs(a["y"] - b["y"])


def in_bounds(p: Point, width: int, height: int) -> bool:
    return 0 <= p["x"] < width and 0 <= p["y"] < height


def get_snake_by_id(state: dict, snake_id: str) -> dict | None:
    for snake in state["board"]["snakes"]:
        if snake["id"] == snake_id:
            return snake
    return None


def is_terminal_for_snake(state: dict, snake_id: str) -> bool:
    return get_snake_by_id(state, snake_id) is None


def get_food_list(state: dict) -> list[Point]:
    return state["board"].get("food", [])


def get_hazard_set(state: dict) -> set[tuple[int, int]]:
    hazards = state["board"].get("hazards", [])
    return {point_to_tuple(h) for h in hazards}


def build_occupied_map(state: dict) -> set[tuple[int, int]]:
    occupied = set()
    snakes = state["board"]["snakes"]

    for snake in snakes:
        body = snake["body"]
        if len(body) <= 1:
            occupied.add(point_to_tuple(body[0]))
            continue

        for segment in body[:-1]:
            occupied.add(point_to_tuple(segment))

    return occupied


def get_enemy_head_danger_for_snake(state: dict, snake_id: str) -> set[tuple[int, int]]:
    danger = set()
    me = get_snake_by_id(state, snake_id)
    if me is None:
        return danger

    my_length = me["length"]

    for snake in state["board"]["snakes"]:
        if snake["id"] == snake_id:
            continue

        enemy_head = snake["body"][0]
        enemy_length = snake["length"]

        if enemy_length >= my_length:
            for dx, dy in DIRECTIONS.values():
                nxt = add(enemy_head, dx, dy)
                danger.add(point_to_tuple(nxt))

    return danger


def flood_fill_area(
    start: Point,
    width: int,
    height: int,
    blocked: set[tuple[int, int]],
    limit: int = 80,
) -> int:
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


def get_legal_moves_for_snake(state: dict, snake_id: str) -> list[Move]:
    board = state["board"]
    width = board["width"]
    height = board["height"]

    snake = get_snake_by_id(state, snake_id)
    if snake is None:
        return []

    my_head = snake["body"][0]
    occupied = build_occupied_map(state)

    legal = []
    for move, (dx, dy) in DIRECTIONS.items():
        nxt = add(my_head, dx, dy)

        if not in_bounds(nxt, width, height):
            continue
        if point_to_tuple(nxt) in occupied:
            continue

        legal.append(move)

    return legal


def evaluate_move_for_snake(state: dict, snake_id: str, move: Move) -> float:
    board = state["board"]
    width = board["width"]
    height = board["height"]

    snake = get_snake_by_id(state, snake_id)
    if snake is None:
        return -1e9

    my_head = snake["body"][0]
    my_health = snake["health"]
    my_length = snake["length"]

    foods = get_food_list(state)
    hazards = get_hazard_set(state)
    occupied = build_occupied_map(state)
    enemy_head_danger = get_enemy_head_danger_for_snake(state, snake_id)

    dx, dy = DIRECTIONS[move]
    nxt = add(my_head, dx, dy)
    nxt_t = point_to_tuple(nxt)

    if not in_bounds(nxt, width, height):
        return -1e9
    if nxt_t in occupied:
        return -1e9

    score = 0.0

    if nxt_t in enemy_head_danger:
        score -= 120.0

    if nxt_t in hazards:
        score -= 35.0

    blocked_for_fill = set(occupied)
    area = flood_fill_area(nxt, width, height, blocked_for_fill, limit=80)
    score += area * 3.0

    free_neighbors = count_free_neighbors(nxt, width, height, blocked_for_fill)
    score += free_neighbors * 8.0

    dist_food = min_food_distance(nxt, foods)
    current_dist_food = min_food_distance(my_head, foods)

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

    if any(nxt["x"] == food["x"] and nxt["y"] == food["y"] for food in foods):
        score += 35.0
        if my_health <= 40:
            score += 50.0

    cx = (width - 1) / 2
    cy = (height - 1) / 2
    dist_center = abs(nxt["x"] - cx) + abs(nxt["y"] - cy)
    score -= dist_center * 1.2

    if area < my_length:
        score -= 80.0

    if nxt_t not in hazards:
        score += 5.0

    return score


def heuristic_best_move_for_snake(state: dict, snake_id: str) -> str:
    legal = get_legal_moves_for_snake(state, snake_id)
    if not legal:
        return "down"

    best_move = legal[0]
    best_score = float("-inf")

    for move in legal:
        score = evaluate_move_for_snake(state, snake_id, move)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move


def evaluate_state_for_snake(state: dict, snake_id: str) -> float:
    snake = get_snake_by_id(state, snake_id)
    if snake is None:
        return -1e6

    score = 0.0
    score += snake["length"] * 20.0
    score += snake["health"] * 0.5

    legal = get_legal_moves_for_snake(state, snake_id)
    score += len(legal) * 15.0

    if legal:
        best_local = max(evaluate_move_for_snake(state, snake_id, m) for m in legal)
        score += 0.5 * best_local

    return score


def resolve_deaths(snakes: list[dict], width: int, height: int) -> list[dict]:
    alive = []

    # wall / health
    for snake in snakes:
        head = snake["body"][0]
        if not in_bounds(head, width, height):
            continue
        if snake["health"] <= 0:
            continue
        alive.append(snake)

    # body collision
    body_cells = []
    for snake in alive:
        for segment in snake["body"][1:]:
            body_cells.append((segment["x"], segment["y"]))

    alive2 = []
    for snake in alive:
        head_t = point_to_tuple(snake["body"][0])
        if head_t in body_cells:
            continue
        alive2.append(snake)

    # head-to-head
    head_map = {}
    for snake in alive2:
        head_t = point_to_tuple(snake["body"][0])
        head_map.setdefault(head_t, []).append(snake)

    final_alive = []
    for snake in alive2:
        head_t = point_to_tuple(snake["body"][0])
        group = head_map[head_t]
        if len(group) == 1:
            final_alive.append(snake)
        else:
            max_len = max(s["length"] for s in group)
            winners = [s for s in group if s["length"] == max_len]
            if len(winners) == 1 and snake in winners:
                final_alive.append(snake)

    return final_alive


def simulate_one_turn(state: dict, my_snake_id: str, my_move: str) -> dict:
    new_state = clone_state(state)
    snakes = new_state["board"]["snakes"]

    chosen_moves = {}
    for snake in snakes:
        sid = snake["id"]
        if sid == my_snake_id:
            chosen_moves[sid] = my_move
        else:
            chosen_moves[sid] = heuristic_best_move_for_snake(new_state, sid)

    # move + base health loss
    for snake in snakes:
        sid = snake["id"]
        move = chosen_moves[sid]
        new_head = add_by_move(snake["body"][0], move)
        snake["body"].insert(0, new_head)
        snake["health"] -= 1

    food_positions = {point_to_tuple(f) for f in new_state["board"]["food"]}
    eaten = set()

    for snake in snakes:
        head_t = point_to_tuple(snake["body"][0])
        if head_t in food_positions:
            snake["health"] = 100
            snake["length"] += 1
            eaten.add(head_t)
        else:
            snake["body"].pop()

    new_state["board"]["food"] = [
        f for f in new_state["board"]["food"]
        if point_to_tuple(f) not in eaten
    ]

    hazard_positions = {point_to_tuple(h) for h in new_state["board"].get("hazards", [])}
    for snake in snakes:
        if point_to_tuple(snake["body"][0]) in hazard_positions:
            snake["health"] -= 15  # first simple approximation

    survivors = resolve_deaths(
        new_state["board"]["snakes"],
        new_state["board"]["width"],
        new_state["board"]["height"],
    )
    new_state["board"]["snakes"] = survivors

    me = get_snake_by_id(new_state, my_snake_id)
    if me is not None:
        new_state["you"] = me

    new_state["turn"] += 1
    return new_state