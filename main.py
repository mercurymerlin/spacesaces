# Patience driver program

import os

from gamestate_new import GameState

def main():
    msg = ""
    game = GameState()
    move_depth = 0

    while not game.is_game_over():
        clear_screen()
        print(f"\nMove depth: {move_depth}\n")
        print(game)
        # print(game.calculate_score())
        print(msg)

        move = get_move_input()
        if move == 'save':
            filename = input("Enter filename to save: ")
            game.save_game(filename)
            msg = "Game saved successfully."
            continue

        if move == 'load':
            filename = input("Enter filename to load: ")
            game = game.load_game(filename)
            msg = "Game loaded successfully."
            continue

        space_index, move_index = move
        msg = ""
        try:
            game.make_move(space_index, move_index)
            move_depth += 1
        except TypeError:
            msg = "Invalid move"

    msg = ("Game over\n"
           + "Your score: " + str(game.calculate_score()) + " cards")
    clear_screen()
    print("\n")
    print(game)
    print(msg)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def get_move_input():
    while True:
        user_input = input("Enter move (space,move), space only, or 's' or 'l': ").strip().lower()

        if user_input == 's':
            return 'save'
        if user_input == 'l':
            return 'load'


        try:
            if ',' in user_input:
                space_index, move_index = map(int, user_input.split(','))
                return space_index, move_index
            else:
                space_index = int(user_input)
                return space_index, 0
        except ValueError:
            print("Invalid input. Please try again.")

if __name__ == "__main__":
    main()

