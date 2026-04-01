from __future__ import annotations
from dataclasses import dataclass, field
import math
import time
from typing import Optional

from game_logic import (
    clone_state,
    get_legal_moves_for_snake,
    simulate_one_turn,
    evaluate_state_for_snake,
    is_terminal_for_snake,
    heuristic_best_move_for_snake,
)

EXPLORATION_C = 1.4
ROLLOUT_DEPTH = 4


@dataclass
class Node:
    state: dict
    my_snake_id: str
    parent: Optional["Node"] = None
    move_from_parent: Optional[str] = None
    children: dict[str, "Node"] = field(default_factory=dict)
    untried_moves: list[str] = field(default_factory=list)
    visits: int = 0
    value: float = 0.0

    def is_fully_expanded(self) -> bool:
        return len(self.untried_moves) == 0

    def best_child_ucb(self, c: float = EXPLORATION_C) -> "Node":
        best_score = float("-inf")
        best_node = None

        for child in self.children.values():
            if child.visits == 0:
                return child

            exploit = child.value / child.visits
            explore = c * math.sqrt(math.log(self.visits) / child.visits)
            score = exploit + explore

            if score > best_score:
                best_score = score
                best_node = child

        return best_node

    def best_child_by_visits(self) -> "Node":
        return max(self.children.values(), key=lambda n: n.visits)


def rollout(state: dict, my_snake_id: str, max_depth: int = ROLLOUT_DEPTH) -> float:
    cur = clone_state(state)

    for _ in range(max_depth):
        if is_terminal_for_snake(cur, my_snake_id):
            break

        legal = get_legal_moves_for_snake(cur, my_snake_id)
        if not legal:
            break

        move = heuristic_best_move_for_snake(cur, my_snake_id)
        cur = simulate_one_turn(cur, my_snake_id, move)

    return evaluate_state_for_snake(cur, my_snake_id)


def expand(node: Node) -> Node:
    move = node.untried_moves.pop()
    next_state = simulate_one_turn(node.state, node.my_snake_id, move)

    child = Node(
        state=next_state,
        my_snake_id=node.my_snake_id,
        parent=node,
        move_from_parent=move,
        untried_moves=get_legal_moves_for_snake(next_state, node.my_snake_id),
    )
    node.children[move] = child
    return child


def backpropagate(node: Node, reward: float) -> None:
    cur = node
    while cur is not None:
        cur.visits += 1
        cur.value += reward
        cur = cur.parent


def mcts_move(game_state: dict, time_limit_ms: int = 850) -> str:
    my_snake_id = game_state["you"]["id"]
    legal = get_legal_moves_for_snake(game_state, my_snake_id)

    if not legal:
        return "down"
    if len(legal) == 1:
        return legal[0]

    root = Node(
        state=clone_state(game_state),
        my_snake_id=my_snake_id,
        untried_moves=legal[:],
    )

    deadline = time.perf_counter() + time_limit_ms / 1000.0

    while time.perf_counter() < deadline:
        node = root

        # Selection
        while node.is_fully_expanded() and node.children:
            node = node.best_child_ucb()

        # Expansion
        if not is_terminal_for_snake(node.state, node.my_snake_id) and node.untried_moves:
            node = expand(node)

        # Simulation
        reward = rollout(node.state, node.my_snake_id)

        # Backpropagation
        backpropagate(node, reward)

    best = root.best_child_by_visits()
    return best.move_from_parent