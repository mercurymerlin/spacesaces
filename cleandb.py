# SpacesAces - Clean db to remove Moves and all game states except a given start state
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

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def clean_state_history(db_path, start_state_id):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # Start a transaction
            cursor.execute("BEGIN TRANSACTION")

            # Find the state with the highest score for the given start state
            cursor.execute("""
                SELECT GameState, Score, DepthLvl
                FROM GameTree
                WHERE StartState = ?
                ORDER BY Score DESC, DepthLvl 
            """, (start_state_id,))
            highest_score_state = cursor.fetchone()[0]

            # Delete all moves related to this start state
            cursor.execute("""
                DELETE FROM Moves
                WHERE StartState = ?
            """, (start_state_id,))

            # Delete all game states except the start state and highest score state
            cursor.execute("""
                DELETE FROM GameTree
                WHERE StartState = ?
                AND GameState <> ?
                AND GameState <> ?
            """, (start_state_id, start_state_id, highest_score_state))

            # Commit the transaction
            conn.commit()

            print(f"Cleaned state history for start state {start_state_id}")
            print(f"Kept start state {start_state_id} and highest score state {highest_score_state}")

        except sqlite3.Error as e:
            # If an error occurs, roll back the transaction
            conn.rollback()
            print(f"An error occurred: {e}")

        finally:
            # Close the connection
            conn.close()

        return highest_score_state

def main():
    db_path = os.path.expanduser('~/Database/GameTree.db')  # Replace with your actual database path

    while True:
        print("Backing up your database before cleaning is recommended")
        state_id = input("\nEnter a state ID to clean (or 'q' to quit): ")
        if state_id.lower() == 'q':
            break

        clear_screen()
        try:
            state_id = int(state_id)

            highest_score_state = clean_state_history(db_path, state_id)

            print(f"Cleaned state history for start state {state_id}")
            print(f"Kept start state {state_id} and highest score state {highest_score_state}")

        except ValueError:
            print("Please enter a valid integer state ID.")
