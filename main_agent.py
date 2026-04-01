import os
import typing

from game_logic import heuristic_best_move_for_snake
from mcts import mcts_move


AGENT_TYPE = os.environ.get("AGENT_TYPE", "heuristic").lower()


def info() -> typing.Dict:
    print("INFO")
    return {
        "apiversion": "1",
        "author": "Group wangle",
        "color": "#66ccff",
        "head": "default",
        "tail": "default",
    }


def start(game_state: typing.Dict):
    print("GAME START")


def end(game_state: typing.Dict):
    print("GAME OVER\n")


def move(game_state: typing.Dict) -> typing.Dict:
    if AGENT_TYPE == "mcts":
        next_move = mcts_move(game_state, time_limit_ms=850)
    else:
        my_snake_id = game_state["you"]["id"]
        next_move = heuristic_best_move_for_snake(game_state, my_snake_id)

    print(f"MOVE {game_state['turn']}: {next_move}")
    return {"move": next_move}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})