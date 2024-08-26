import sqlite3
import sys

from gamestate import GameState


def connect_to_database(db_path):
    """Establish a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        print("Successfully connected to the database.")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None


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
    db_path = 'GameTree.db'  # Replace with your actual database path
    conn = connect_to_database(db_path)

    if not conn:
        print("Failed to connect to the database.")

    else:
        # Initialize start
        user_input = input("Clear database Y or N?: ").strip().lower()
        if user_input == 'y':
            clear_tables(conn)

        current_game = None
        user_input = input("Add a random start state Y or N?: ").strip().lower()
        if user_input == 'y':
            current_game = GameState()
        if user_input == 'n':
            filename = input("Enter filename to load: ")
            if filename:
                current_game = GameState.load_game(filename)

        user_input = input("Set maximum depth to explore: ").strip().lower()
        max_depth = int(user_input.strip())

        # Insert the initial state if specified into the database
        if current_game:
            try:
                # Insert the initial state into the database
                insert_game_state(conn, current_game)
                conn.commit()

            except sqlite3.Error as e:
                # If any operation fails, rollback the entire transaction
                conn.rollback()
                print(f"Error during insertion: {e}")

        # Prepare to expand the next depth level
        query = """
        SELECT MIN(DepthLvl)
        FROM GameTree
        WHERE GameOver is '0' 
        AND Gamestate NOT IN (SELECT Fromstate
                              FROM Moves)        
        """
        results = execute_query(conn, query)
        current_depth = results[0][0]

        while current_depth < max_depth:
            query = """
            SELECT StartState, GameState, Board
            FROM GameTree
            WHERE GameOver is '0' 
            AND DepthLvl = ?
            AND Gamestate NOT IN (SELECT Fromstate
                                    FROM Moves)
            """
            results = execute_query(conn, query, (current_depth,))

            if not results:
                print(f"No more states to expand at depth {current_depth}")
                break

            total_states = 0
            total_moves = 0
            progress_counter = 0
            if results:
                print(f"Processing moves depth: {current_depth}")
                for row in results:
                    start_state = row[0]
                    state_id = row[1]
                    current_board = row[2]
                    total_moves += expand_tree(conn, start_state, state_id, current_board, current_depth)
                    total_states += 1
                    sys.stdout.write('.')
                    sys.stdout.flush()
                    progress_counter += 1
                    if progress_counter % 80 == 0:  # Start a new line every so often
                        print()

            print(f'\nStates: {total_states} Moves: {total_moves}')
            current_depth += 1

        conn.close()


def expand_tree(conn, start_state, state_id, board, depth):
    # try:
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

                # Insert new game state
                cursor.execute("""
                INSERT OR IGNORE INTO GameTree (StartState, Board, Score, GameOver, DepthLvl)
                VALUES (?, ?, ?, ?, ?)
                """, (start_state, new_board, new_score, game_over, depth + 1))

                # Get the ID of the new state (or existing state if it was already in the table)
                query = """
                SELECT GameState 
                FROM GameTree 
                WHERE Board = ?
                """
                results = execute_query(conn, query, (new_board,))
                new_state_id = results[0][0]

                # Insert move
                cursor.execute("""
                INSERT OR IGNORE INTO Moves (FromState, ToState, MoveFromRow, MoveFromCol, MoveToRow, MoveToCol)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (state_id, new_state_id, from_rowcol[0], from_rowcol[1], to_rowcol[0], to_rowcol[1]))
        expanded_count += 1
    conn.commit()

    # except sqlite3.Error as e:
    #    conn.rollback()
    #    print(f"Error expanding game tree: {e}")

    return expanded_count


def insert_game_state(conn, game_state):
    """Insert a new game state into the database."""
    try:
        cursor = conn.cursor()
        query = """
        INSERT INTO GameTree (Board, Score, GameOver, DepthLvl)
        VALUES (?, ?, ?, ?)
        """
        board_str = game_state.save_game()  # Assuming __str__ method gives the board representation
        score = game_state.calculate_score()
        depth = 0  # Initial state has depth 0
        game_over = game_state.is_game_over()

        cursor.execute(query, (board_str, score, game_over, depth))
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
