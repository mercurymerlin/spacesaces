# SpacesAces - Clean db to remove Moves and game states
#              except a given start state and the best result state
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

import os
import sqlite3
import time

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def clean_state_history(db_path, start_state_id):
    conn = None
    highest_score_state = None
    print(f"\nBeginning clean for start state {start_state_id}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Acquire an exclusive lock on the database
        cursor.execute("BEGIN EXCLUSIVE TRANSACTION")

        start_time = time.time()

        # Find the state with the highest score for the given start state
        cursor.execute("""
                SELECT GameState, Score, DepthLvl
                FROM GameTree
                WHERE StartState = ?
                ORDER BY Score DESC, DepthLvl 
            """, (start_state_id,))
        highest_score_state, highest_score, depth = cursor.fetchone()

        # Delete all moves related to this start state
        cursor.execute("DELETE FROM Moves WHERE StartState = ?", (start_state_id,))
        deleted_moves = cursor.rowcount

        # Delete all game states except the start state and highest score state
        cursor.execute("""
                DELETE FROM GameTree
                WHERE StartState = ?
                AND GameState NOT IN (?, ?)
            """, (start_state_id, start_state_id, highest_score_state))
        deleted_states = cursor.rowcount

        # Commit the transaction
        conn.commit()

        end_time = time.time()
        operation_time = end_time - start_time

        print(f"\nCleaned state history for start state {start_state_id}")
        print(f"Kept start state {start_state_id} and highest score state {highest_score_state}")
        print(f"Highest score: {highest_score}, Depth: {depth}")
        print(f"Deleted moves: {deleted_moves}")
        print(f"Deleted states: {deleted_states}")
        print(f"Operation took {operation_time:.2f} seconds")

        # Prompt for VACUUM operation
        vacuum_choice = input("\nDo you want to perform a VACUUM operation to compact the database? (Y/N): ").lower()
        if vacuum_choice == 'y':
            vacuum_start_time = time.time()
            conn.execute("VACUUM")
            vacuum_end_time = time.time()
            vacuum_time = vacuum_end_time - vacuum_start_time
            print(f"VACUUM operation completed in {vacuum_time:.2f} seconds")

    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

    return highest_score_state

def main():
    db_path = os.path.expanduser('~/Database/GameTree.db')  # Replace with your actual database path

    clear_screen()
    print(f"Database path: {db_path}")

    while True:
        print("\nBacking up your database before cleaning is recommended")
        state_id = input("\nEnter a state ID to clean (or 'q' to quit): ")
        if state_id.lower() == 'q':
            break

        clear_screen()
        try:
            state_id = int(state_id)

            highest_score_state = clean_state_history(db_path, state_id)

            print(f"\nCleaned state history for start state {state_id}")
            print(f"Kept start state {state_id} and highest score state {highest_score_state}")

        except ValueError:
            print("Please enter a valid integer state ID.")

if __name__ == "__main__":
    main()