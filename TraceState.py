import sqlite3
import os

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


def print_state_details(db_path, from_state, to_state):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Board, Score, DepthLvl
        FROM GameTree
        WHERE GameState = ?
    """, (to_state,))
    state_result = cursor.fetchone()

    if state_result:
        board, score, depth = state_result
        print(f"State ID: {to_state}")
        print(f"Depth: {depth}")
        print(f"Score: {score}")
        print("Board:")
        print(board)
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

        print()
    else:
        print(f"No data found for State ID: {from_state}")

    conn.close()


def main():
    db_path = 'GameTree2.db'  # Replace with your actual database path

    while True:
        state_id = input("Enter a state ID to trace (or 'q' to quit): ")
        if state_id.lower() == 'q':
            break

        clear_screen()
        try:
            state_id = int(state_id)
            state_sequence = trace_state_history(db_path, state_id)

            print(f"Path to reach state {state_id}:\n")
            for from_state, to_state in state_sequence:
                print(f"Move from state {from_state} to state {to_state}:")
                print_state_details(db_path, from_state, to_state)

        except ValueError:
            print("Please enter a valid integer state ID.")
        # except Exception as e:
        #    print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()