import sqlite3
import csv
import os

from gamestate_new import GameState

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def trace_state_history(db_path, target_state_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    state_sequence = []
    current_state = target_state_id
    steps = 0

    while True:
        cursor.execute("""
            SELECT FromState 
            FROM Moves 
            WHERE ToState = ?
        """, (current_state,))
        result = cursor.fetchone()

        if result is None: # No parent state means initial state reached
            if not state_sequence:
                state_sequence = [(None, current_state)]
            else:
                state_sequence.append((None, current_state))
                print(f"Sequence traced: {current_state}\nSteps: {steps}")
            break

        steps += 1
        parent_state = result[0]
        state_sequence.append((parent_state, current_state))
        current_state = parent_state

    conn.close()

    # Reverse the sequence to get the path from initial state to target state
    state_sequence.reverse()

    return state_sequence


def print_state_details(db_path, csvfile, from_state, to_state):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Board, Score, DepthLvl
        FROM GameTree
        WHERE GameState = ?
    """, (to_state,))
    state_result = cursor.fetchone()

    if state_result:
        board, score, depth_lvl = state_result
        print(f"State ID: {to_state}")
        print(f"Depth: {depth_lvl}")

        game = GameState.load_game(board)
        game.calc_line_len()

        active_spaces = sum(1 for lt in game.line_len if lt > 0)
        tot_line_len = game.tot_line_len
        line_len_val = 0.0
        if score < 48:
            line_len_val = (tot_line_len + score) / (48.0 - score)

        # Write to CSV if csvfile is provided
        if csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow([to_state, depth_lvl, active_spaces,
                                 tot_line_len, line_len_val, score])

        if from_state:
            cursor.execute("""
                SELECT MoveFromRow, MoveFromCol, MoveToRow, MoveToCol
                FROM Moves
                WHERE FromState = ?
                AND ToState = ?
            """, (from_state, to_state,))
            move_result = cursor.fetchone()
            MoveFromRow, MoveFromCol, MoveToRow, MoveToCol = move_result
            print(f"Move from: {MoveFromRow}, {MoveFromCol}")
            print(f"Move to: {MoveToRow}, {MoveToCol}")

        print(game)


    else:
        print(f"No data found for State ID: {from_state}")

    conn.close()


def main():
    db_path = 'C:/Users/John/Database/GameTree3.db'  # Replace with your actual database path

    while True:
        state_id = input("\nEnter a state ID to trace (or 'q' to quit): ")
        if state_id.lower() == 'q':
            break

        csv_log = input("Enter filename to log csv data (or press Enter to skip logging): ")
        csvfile = None
        csv_writer = None

        if csv_log:
            try:
                csvfile = open(csv_log, 'w', newline='')
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(['State ID', 'Depth', 'Active Spaces', 'Tot Line Len',
                                     'Line Len Val', 'Score'])
            except IOError as e:
                print(f"Error opening CSV file: {e}")
                continue

        clear_screen()
        try:
            state_id = int(state_id)
            state_sequence = trace_state_history(db_path, state_id)

            print(f"Path to reach state {state_id}:")
            for from_state, to_state in state_sequence:
                print(f"\nMove from state {from_state} to state {to_state}:")
                print_state_details(db_path, csvfile, from_state, to_state)

        except ValueError:
            print("Please enter a valid integer state ID.")
        # except Exception as e:
        #    print(f"An error occurred: {e}")

        finally:
            if csvfile:
                csvfile.close()
                print(f"CSV file has been created: {csv_log}")


if __name__ == "__main__":
    main()