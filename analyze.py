# SpacesAces - Analysis process for exploring the game tree
# Copyright (C) 2024 John Barron <jbarronuk@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sqlite3
import os
import sys
from typing import Tuple, List, Dict, Optional

from gamestate import GameState


def clear_tables(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("DELETE FROM GameTree")
        cursor.execute("DELETE FROM Moves")
        cursor.execute("COMMIT")
        print("All tables cleared successfully\n")
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error clearing tables: {e}")


def execute_query(conn, query, params=None):
    """Execute a query and return the results."""
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        return results
    except sqlite3.Error as e:
        print(f"Error executing query: {e}")
        return None


def main():
    db_path = os.path.expanduser('~/Database/GameTree.db') # Replace with your actual database path
    db_path_read = 'file:' + db_path + '?readonly'

    # Establish connections to the database
    write_conn = None
    try:

        write_conn = sqlite3.connect(db_path)

        # write_conn.execute("PRAGMA journal_mode=WAL;")
        write_conn.execute("PRAGMA journal_mode=MEMORY;")
        write_conn.execute("PRAGMA synchronous=NORMAL;")
        write_conn.execute("PRAGMA cache_size=-1048576;")
        # write_conn.execute("PRAGMA mmap_size=30064771072;")  # 28GB mmap
        write_conn.execute("PRAGMA busy_timeout=30000;")
        # write_conn.execute("PRAGMA page_size=32768;")

        print("Connected for write to the database.")

    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")

    if write_conn is None:
        print("Failed to connect to the database.")
        return

    # Initialize start
    # user_input = input("Clear database Y or N?: ").strip().lower()
    # if user_input == 'y':
    #    clear_tables(write_conn)

    current_game = None
    user_input = input("Add a random start state Y or N?: ").strip().lower()
    if user_input == 'y':
        current_game = GameState()

    if user_input == 'n':
        filename = input("Enter filename to load: ")
        if filename:
            current_game = GameState.load_game(filename)

    search_fraction = None
    user_input = input("Set search breadth fraction: ").strip().lower()
    if user_input:
        search_fraction = float(user_input.strip())
    if not search_fraction:
        search_fraction = 0.75 # Originally was 0.95
    print(search_fraction)

    user_input = input("Set iterations to explore: ").strip().lower()
    num_iter = int(user_input.strip())

    user_input = input("Set start state to explore (0=All): ").strip().lower()
    start_id = int(user_input.strip())

    # Insert the initial state if specified into the database
    if current_game:
        try:
            # Insert the initial state into the database
            insert_game_state(write_conn, current_game)
            write_conn.commit()

        except sqlite3.Error as e:
            # If any operation fails, rollback the entire transaction
            write_conn.rollback()
            print(f"Error during insertion: {e}")

    next_iter = 0

    # results1 = []
    solution_found = False
    while next_iter < num_iter:

        # Open read connection
        try:
            read_conn = sqlite3.connect(db_path_read, uri=True)
            print("Connected for read to the database.")
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            break

        # Prepare the next iteration
        if start_id == 0:
            query = """
            SELECT StartState, MAX(LineLenVal), MAX(DepthLvl), MAX(Score)
            FROM GameTree
            WHERE GameOver = '0' 
            AND GameState NOT IN (SELECT FromState
                                        FROM Moves)
            GROUP BY StartState
            """
            results1 = execute_query(read_conn, query)
        else:
            query = """
            SELECT StartState, MAX(LineLenVal), MAX(DepthLvl), MAX(Score)
            FROM GameTree
            WHERE GameOver = '0'
            AND StartState = ?
            AND GameState NOT IN (SELECT FromState
                                        FROM Moves)
            GROUP BY StartState  
            """
            results1 = execute_query(read_conn, query, (start_id, ))

        # print(results1)
        if len(results1) == 0:
            print("Search ended")
            break

        for state_id, line_len_val, max_depth, max_score in results1:
            total_states = 0
            total_moves = 0
            print(f"\nState {state_id} " +
                  f"Max Line Value {line_len_val:.2f} " +
                  f"\nMax Depth {max_depth} Max Score {max_score} ")

            query = """
            SELECT StartState, GameState, Board, DepthLvl
            FROM GameTree
            WHERE GameOver = '0'
            AND StartState = ? 
            AND DepthLvl <= ?
            AND LineLenVal >= ?
            AND GameState NOT IN (SELECT FromState
                                  FROM Moves)
            """
            results2 = execute_query(read_conn, query,
                                     (state_id, max_depth, line_len_val * search_fraction))

            if not results2:
                print(f"No more states to expand at iteration {next_iter}")
                break

            progress_counter = 0
            if results2:
                print(f"Processing iteration: {next_iter}")
                for row in results2:
                    start_state = row[0]
                    state_id = row[1]
                    current_board = row[2]
                    current_depth = row[3]
                    total_states += 1
                    # Explore next state
                    expanded, solution_found = expand_tree(write_conn, start_state, state_id, current_board, current_depth)
                    total_moves += expanded

                    if solution_found:
                        print(f"\nSolution found! Perfect score of 48 achieved.")
                        break

                    sys.stdout.write('.')
                    sys.stdout.flush()
                    progress_counter += 1
                    if progress_counter % 80 == 0:  # Start a new line every so often
                        print()

        print(f'\nStates: {total_states} Moves: {total_moves}')
        next_iter += 1
        read_conn.close()

        if solution_found:
            break

    write_conn.close()


def expand_tree(conn: sqlite3.Connection, start_state: int, state_id: int, board: str, depth: int) -> Tuple[int, bool]:
    """ Expand the game tree with all possible moves for the input state """
    try:
        cursor = conn.cursor()
        game = GameState.load_game(board)
        expanded_count = 0

        for space_index in range(4):
            if game.moves[space_index]:
                for move_index in range(len(game.moves[space_index])):
                    new_game = GameState.load_game(board)
                    # Apply move
                    new_game.make_move(space_index, move_index)
                    from_rowcol = game.moves[space_index][move_index]
                    to_rowcol = game.spaces[space_index]
                    new_board = new_game.save_game()
                    new_score = new_game.calculate_score()
                    game_over = new_game.is_game_over()
                    new_game.calc_line_len()
                    active_spaces = sum(1 for lt in new_game.line_len if lt > 0)
                    tot_line_len = new_game.tot_line_len
                    line_len_val = 0.0

                    # Check if this new state is a solution
                    if new_score < 48:
                        line_len_val = (tot_line_len + new_score) / (48.0 - new_score)

                    # Insert new game state
                    cursor.execute("""
                    INSERT OR IGNORE INTO 
                    GameTree (StartState, Board, Score, ActiveSpaces, 
                                TotLineLen, LineLenVal, GameOver, DepthLvl)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (start_state, new_board, new_score, active_spaces,
                          tot_line_len, line_len_val, game_over, depth + 1))

                    # Get the ID of the new state (or existing state if it was already in the table)
                    query = """
                    SELECT GameState 
                    FROM GameTree 
                    WHERE StartState = ? 
                    AND Board = ?
                    """
                    results = execute_query(conn, query, (start_state, new_board))
                    new_state_id = results[0][0]

                    # Insert move
                    cursor.execute("""
                    INSERT OR IGNORE INTO 
                    Moves (StartState, FromState, ToState, MoveFromRow, MoveFromCol, MoveToRow, MoveToCol)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (start_state, state_id, new_state_id, from_rowcol[0], from_rowcol[1], to_rowcol[0], to_rowcol[1]))

                    if new_score == 48:
                        conn.commit()
                        return expanded_count, True

            expanded_count += 1
            conn.commit()

    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error expanding game tree: {e}")

    return expanded_count, False

def insert_game_state(conn, game_state):
    """Insert a new game state into the database."""
    try:
        cursor = conn.cursor()
        query = """
        INSERT INTO GameTree (Board, Score, ActiveSpaces, TotLineLen, 
                                LineLenVal, GameOver, DepthLvl)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        board_str = game_state.save_game()  # Assuming __str__ method gives the board representation
        score = game_state.calculate_score()
        depth = 0  # Initial state has depth 0
        game_over = game_state.is_game_over()
        game_state.calc_line_len()
        active_spaces = sum(1 for lt in game_state.line_len if lt > 0)
        tot_line_len = game_state.tot_line_len
        line_len_val = 0

        cursor.execute(query,
                       (board_str, score, active_spaces, tot_line_len,
                        line_len_val, game_over, depth))
        state_id = cursor.lastrowid
        print(f"Inserted new game state with ID: {state_id}")

        query = """
        UPDATE GameTree
        SET StartState = GameState
        WHERE GameState = ?
        """
        cursor.execute(query, (state_id,))

        if state_id:

            # Fetch and display the inserted state
            query = """
            SELECT GameState, Board, Score, DepthLvl 
            FROM GameTree 
            WHERE GameState = ?
            """
            results = execute_query(conn, query, (state_id,))

            if results:
                print("Inserted game state:")
                for row in results:
                    print(f"GameState: {row[0]}, Score: {row[2]}, Depth: {row[3]}")
                    print(f"Board:\n{row[1]}\n")
            else:
                print("Failed to retrieve the inserted game state.")

    except sqlite3.Error as e:
        print(f"Error inserting game state: {e}")
        return None

    cursor.close()


if __name__ == "__main__":
    main()
