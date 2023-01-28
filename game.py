"""
Main module for the minesweeper game.
"""

import os
import time
import random
import json
from collections.abc import Generator
from typing import Literal
import sweeperlib as sl

DATA_JSON_ERROR = -1
DATA_NOT_FOUND = 0
DATA_EXISTS = 1

state = {
    "running": False,
    "won": False,
    "field": [],
    "visible": [],
    "clicks": 0,
    "mines": 0,
}


def main() -> None:
    """
    Show the main menu of the game. This is the main loop function of the game.
    """
    invalid = False
    while True:
        print("\n-:X Minesweeper X:-\n(P)lay\n(S)tatistics\n(Q)uit")

        if invalid:
            print("Enter a valid option.")
            invalid = False

        choice = make_choice(["play", "statistics", "quit"])
        if choice == 0:
            init_game()
        elif choice == 1:
            statistics()
        elif choice == 2:
            break
        else:
            invalid = True


def make_choice(options: list[str]) -> int:
    """
    Return index of first string in given list that starts with
    an user entered string. If it doesn't exist return `-1`.
    """
    choice = input(": ").lower()
    if len(choice) > 0:
        for i,option in enumerate(options):
            if option.startswith(choice):
                return i
    return -1


def init_game() -> None:
    """
    Initialize and start the game.
    """
    print("\n- Play -")
    width = get_positive_integer("Enter field width: ")
    height = get_positive_integer("Enter field height: ")
    print(f"There are {width * height} tiles in total.")
    while True:
        state["mines"] = get_positive_integer("Enter mine count: ")
        if state["mines"] < 1 or state["mines"] > width * height:
            print(f"Enter a number between 1 and {width * height}.")
        else:
            break

    print("Starting game...")
    state["running"] = True
    state["won"] = False
    state["field"], state["visible"] = create_field(width, height, state["mines"])
    state["clicks"] = 0
    play(width, height)


def get_positive_integer(message: str) -> int:
    """
    Ask the player for a positive integer with the given message until a valid input is given.
    """
    while True:
        try:
            number = int(input(message))
        except ValueError:
            print("Input should be an integer.")
        else:
            if number > 0:
                return number
            print("Number should be positive.")


def create_field(width: int, height: int, mines: int) -> tuple[list[list], list[list[str]]]:
    """
    Create a new pseudorandomly generated minefield with the given options.
    """
    tiles = ["x"] * mines + ["0"] * (width * height - mines)
    random.shuffle(tiles)
    field = list(chunks(tiles, width))
    for y,row in enumerate(field):
        for x,tile in enumerate(row):
            if not tile == "x":
                field[y][x] = str(count_surrounding_mines(x, y, field))

    visible = [[" "] * width for _ in range(height)]

    return field, visible


def chunks(list_: list, size: int) -> Generator[list, None, None]:
    """
    Split a list into chunks of a certain size.
    """
    for i in range(0, len(list_), size):
        yield list_[i:i + size]


def count_surrounding_mines(x: int, y: int, field: list[list[str]]) -> int:
    """
    Count how many mines surround a tile in given coordinates in a given field.
    """
    mines = 0
    for d_y in range(-1, 2):
        if 0 <= y + d_y < len(field):
            for d_x in range(-1, 2):
                if 0 <= x + d_x < len(field[y + d_y]):
                    if field[y + d_y][x + d_x] == "x":
                        mines += 1
    return mines


def play(width: int, height: int) -> None:
    """
    Create a game window with the given options and set start time.
    """
    sl.load_sprites("sprites")
    sl.create_window(width * 40, height * 40)
    sl.set_draw_handler(draw)
    sl.set_mouse_handler(handle_mouse)
    state["start_time"] = time.time()
    sl.start()


def draw() -> None:
    """
    Draw the currently visible field and game end text to the game window.
    """
    sl.clear_window()
    sl.begin_sprite_draw()
    for y,row in enumerate(state["visible"]):
        for x,tile in enumerate(row):
            sl.prepare_sprite(tile, x * 40, y * 40)
    sl.draw_sprites()
    if not state["running"]:
        width = len(state["field"][0]) * 40
        height = len(state["field"]) * 40
        if state["won"]:
            sl.draw_text("YOU WIN!",
                         width * 0.5 - min(width, height) * 0.2816,
                         height * 0.5 - min(width, height) * 0.048,
                         (0, 200, 0, 255), "consolas", min(width, height) / 10)
        else:
            sl.draw_text("GAME OVER!",
                         width * 0.5 - min(width, height) * 0.352,
                         height * 0.5 - min(width, height) * 0.048,
                         (200, 0, 0, 255), "consolas", min(width, height) / 10)
        sl.draw_text("(right click to close)",
                         width * 0.5 - min(width, height) * 0.39,
                         height * 0.5 - min(width, height) * 0.09,
                         (255, 255, 255, 255), "consolas", min(width, height) / 20)


def handle_mouse(x: int, y: int, button, _) -> None:
    """
    Choose what to do based on mouse input.
    """
    if not state["running"]:
        if button == sl.MOUSE_RIGHT:
            sl.close()
        return

    x = x // 40
    y = y // 40
    if 0 <= x < len(state["field"][0]) and 0 <= y < len(state["field"]):
        if button == sl.MOUSE_LEFT:
            if state["visible"][y][x] == " ":
                state["clicks"] += 1
                explore_tile(x, y)
        elif button == sl.MOUSE_RIGHT:
            toggle_flag(x, y)


def toggle_flag(x: int, y: int) -> None:
    """
    Toggle flag on or off at given coordinates.
    """
    if state["visible"][y][x] == " ":
        state["visible"][y][x] = "f"
    elif state["visible"][y][x] == "f":
        state["visible"][y][x] = " "


def explore_tile(x: int, y: int) -> None:
    """
    Explore the tile at the given coordinates.
    """
    to_explore = [(x, y)]
    index = 0
    while index < len(to_explore):
        check_x, check_y = to_explore[index]
        state["visible"][check_y][check_x] = state["field"][check_y][check_x]
        if state["visible"][check_y][check_x] == "x":
            lose_game()
        elif count_unexplored_tiles() == 0:
            win_game()
        elif state["visible"][check_y][check_x] == "0":
            for tile in get_surrounding_tiles(check_x, check_y):
                if tile not in to_explore:
                    to_explore.append(tile)
        index += 1


def count_unexplored_tiles() -> int:
    """
    Return the amount of unexplored tiles that are not mines.
    """
    tiles = 0
    for y,row in enumerate(state["field"]):
        for x,tile in enumerate(row):
            if not tile == "x" and state["visible"][y][x] in (" ", "f"):
                tiles += 1
    return tiles


def lose_game() -> None:
    """
    Stop player input, show unflagged mines and save game data.
    """
    state["running"] = False
    show_unflagged_mines()
    save_game_data()


def show_unflagged_mines() -> None:
    """
    Make unflagged mines visible.
    """
    for y,row in enumerate(state["field"]):
        for x,tile in enumerate(row):
            if tile == "x" and not state["visible"][y][x] == "f":
                state["visible"][y][x] = "x"


def win_game() -> None:
    """
    Stop player input, flag unflagged mines and save game data.
    """
    state["running"] = False
    state["won"] = True
    flag_all_mines()
    save_game_data()


def flag_all_mines() -> None:
    """
    Place a flag on all mines.
    """
    for y,row in enumerate(state["field"]):
        for x,tile in enumerate(row):
            if tile == "x":
                state["visible"][y][x] = "f"


def get_surrounding_tiles(x: int, y: int) -> list:
    """
    Gets tile coordinates surrounding the given coordinates.
    """
    tiles = []
    for d_y in range(-1, 2):
        if 0 <= y + d_y < len(state["field"]):
            for d_x in range(-1, 2):
                if 0 <= x + d_x < len(state["field"][y + d_y]):
                    if not (d_x == 0 and d_y == 0):
                        tiles.append((x + d_x, y + d_y))
    return tiles


def save_game_data() -> None:
    """
    Print current game data to player and add it to the data.json file.
    Create the file if it doesn't exist.
    """
    data = {}
    try:
        with open("data.json", "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    if "games" not in data:
        data["games"] = []
    current = {}

    datetime = time.localtime()
    current["date"] = f"{str(datetime[2]).zfill(2)}/{str(datetime[1]).zfill(2)}/{datetime[0]}"
    current["clock"] = f"{str(datetime[3]).zfill(2)}:{str(datetime[4]).zfill(2)}"
    current["dimensions"] = [len(state["field"][0]), len(state["field"])]
    current["mines"] = state["mines"]
    current["result"] = [state["won"], count_unflagged_mines()]
    current["time"] = time.time() - state["start_time"]
    current["clicks"] = state["clicks"]

    print_game(current)
    data["games"].append(current)
    with open("data.json", "w", encoding="utf-8") as json_file:
        json.dump(data, json_file)


def count_unflagged_mines() -> int:
    """
    Return the amount of unflagged mines.
    """
    mines = 0
    for y,row in enumerate(state["field"]):
        for x,tile in enumerate(row):
            if tile == "x" and not state["visible"][y][x] == "f":
                mines += 1
    return mines


def statistics() -> None:
    """
    Show the game statistics.
    """
    invalid = False
    while True:
        print("\n- Statistics -")
        data_state = DATA_EXISTS

        try:
            with open("data.json", "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
            data_state = validate_data(data)
        except FileNotFoundError:
            data_state = DATA_NOT_FOUND
        except json.JSONDecodeError:
            data_state = DATA_JSON_ERROR

        if data_state == DATA_NOT_FOUND:
            print("No previous game data found.")
        else:
            if data_state == DATA_EXISTS:
                print_stats(data["games"])
                print("(H)istory")
            elif data_state == DATA_JSON_ERROR:
                print("Game data file invalid.")
            print("(R)eset")
        print("(B)ack")

        if invalid:
            print("Enter a valid option.")
            invalid = False

        choice = make_choice(["history", "reset", "back"])
        if choice == 0 and data_state == DATA_EXISTS:
            history(data["games"])
        elif choice == 1 and data_state != DATA_NOT_FOUND:
            os.remove("data.json")
        elif choice == 2:
            break
        else:
            invalid = True


def validate_data(data: dict) -> Literal[1, -1]:
    """
    Validate data loaded from a json file. Return 1 if data is valid, otherwise return -1.
    """
    try:
        for game in data["games"]:
            if not validate_variables([
                (game["date"], str),
                (game["clock"], str),
                (game["dimensions"], list),
                (game["dimensions"][0], int),
                (game["dimensions"][1], int),
                (game["mines"], int),
                (game["result"], list),
                (game["result"][0], bool),
                (game["result"][1], int),
                (game["time"], float),
                (game["clicks"], int),
            ]) or len(game["dimensions"]) != 2 or len(game["result"]) != 2:
                break
        else:
            return 1
    except (KeyError, IndexError):
        pass
    return -1


def validate_variables(var_list: list[tuple[any, type]]) -> bool:
    """
    Check if all variables in a list are of their required type.
    """
    for var in var_list:
        if not isinstance(var[0], var[1]):
            return False
    return True


def print_stats(games: list[dict]) -> None:
    """
    Print the overall statistics based on previously played games.
    """
    playtime = 0
    clicks = 0
    field_types = {}
    for game in games:
        playtime += game["time"]
        clicks += game["clicks"]
        field_type = f"{game['dimensions'][0]} x {game['dimensions'][1]} / {game['mines']}"

        if field_type in field_types:
            field_types[field_type] += 1
        else:
            field_types[field_type] = 1

    print(f"Games played: {len(games)}")
    print(f"Time played: {int(playtime / 60)}:{str(int(playtime % 60)).zfill(2)}")
    print(f"Total clicks: {clicks}")
    if max(field_types.values()) > 1:
        print(f"Favorite settings: {max(field_types, key=field_types.get)}")


def history(games: list[dict]) -> None:
    """
    Show history of played games.
    """
    invalid = False
    while True:
        print("\n- History -")
        for game in games:
            print_game(game)
        print("(B)ack")

        if invalid:
            print("Enter a valid option.")
            invalid = False

        choice = make_choice(["back"])
        if choice == 0:
            break
        invalid = True


def print_game(game: dict) -> None:
    """
    Print the given game as a formated string.
    """
    datetime = f"[{game['date']} {game['clock']}]"
    field_type = f"{game['dimensions'][0]} x {game['dimensions'][1]}, "
    field_type += f"{game['mines']} mine{plural_end(game['mines'])}"
    if not game['result'][0]:
        field_type += f" ({game['result'][1]} left)"
        results = "| L "
    else:
        results = "| W "
    results += f"| {int(game['time'] / 60)}:{str(int(game['time'] % 60)).zfill(2)} "
    results += f"| {game['clicks']} click{plural_end(game['clicks'])} |"
    print(" - ".join([datetime, results, field_type]))


def plural_end(value: int) -> Literal["s", ""]:
    """
    Return `"s"` if value is read as plural and `""` if not.
    """
    return "s" if abs(value) != 1 else ""


if __name__ == "__main__":
    main()
