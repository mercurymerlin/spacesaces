# SpacesAces - GameState class for managing the game's state and rules
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

import random
import copy
from typing import Tuple, List, Dict, Optional
from enum import Enum

class ColorMode(Enum):
    DARK = "dark"
    LIGHT = "light"
    NONE = "none"

class GameState:
    """
    Manages the state and rules of a Spaces and Aces Solitaire game.

    Key components:
    - board: 2D list representing the game layout
    - spaces: List of empty space positions
    - moves: Available moves for each space
    - aces: Positions of aces on the board
    """

    suits = ['H', 'D', 'C', 'S']
    ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'J', 'Q', 'K']

    def calc_line_len(self) -> None:
        """ Calculate maximum moves down the line of each space to block """
        self.num_moves = sum(1 for moves in self.moves if moves)
        self.line_len = [0, 0, 0, 0]
        self.tot_line_len = 0

        # Loop through the four possible moves
        for space_index in range(4):
            # Deep copy current game state
            calc_game = copy.deepcopy(self)
            # check for spaces to the left of the current line
            (calc_row, calc_col) = calc_game.spaces[space_index]

            # Apply moves from here on in
            while True:
                # ignore foundation spaces
                if calc_col == 0:
                    break
                else:
                    # if spaces to the left, track back to the first available move if any
                    temp_col = calc_col
                    temp_card = calc_game.board[calc_row][temp_col - 1]
                    while (not temp_card
                           and temp_col > 0):
                        temp_index = calc_game.spaces.index((calc_row, temp_col))
                        if temp_index is not None:
                            temp_col -= 1
                            temp_card = calc_game.board[calc_row][temp_col]
                    # Break on blocking King found
                    if temp_card:
                        # temp_card cannot be None here
                        if temp_card[0] == 'K':
                            temp_col = 0
                            break
                        else:
                            temp_col += 1
                    else:
                        break

                   # apply preceding moves if need be
                    while (temp_card
                            and temp_col < calc_col):
                        temp_index = calc_game.spaces.index((calc_row, temp_col))
                        # only make move if it's possible
                        temp2 = calc_game.moves[temp_index]
                        if temp2:
                            calc_game.make_move(temp_index, 0)
                            temp_col += 1
                        else:
                            break

                 # Apply move
                if calc_game.moves[space_index]:
                    calc_game.make_move(space_index, 0)
                    (calc_row, calc_col) = calc_game.spaces[space_index]
                    self.line_len[space_index] += 1
                    self.tot_line_len += 1
                else:
                    break

    def make_move(self, space_index: int, move_index: int) -> None:
        """Execute a move in the game."""
        # Raise error if no move available
        if self.moves[space_index][move_index] is None:
            raise TypeError("No move available")

        # Get the source and target positions from spaces and moves
        space_row, space_col = self.spaces[space_index]
        source_row, source_col = self.moves[space_index][move_index]
        move_card = self.board[source_row][source_col]

        # Move the card
        self.board[space_row][space_col] = self.board[source_row][source_col]
        self.board[source_row][source_col] = None

        self.spaces[space_index] = (source_row, source_col)  # Update empty space location
        self.card_locations[move_card] = (space_row, space_col)

        # If ace was moved, remove it from the open aces list
        if move_card[0] == 'A':
            self.aces.remove((source_row, source_col))

        for i in range(4):
            self.update_moves(i)

    def update_moves(self, check_index: int) -> None:
        """ Reconstruct available moves for each space """
        check_row, check_col = self.spaces[check_index]

        # moves are already set if it's an initial space
        if check_col == 0:
            self.moves[check_index] = self.aces.copy()

        else:
            # Find potential new move
            self.moves[check_index] = None
            next_card = None
            prev_card = self.board[check_row][check_col - 1]

            if prev_card is not None: # Space to the left
                next_rank_ix = self.ranks.index(prev_card[0]) + 1  # Index of next rank
                if next_rank_ix < len(self.ranks): # Cannot go past King
                    next_card = (self.ranks[next_rank_ix], prev_card[1])  # Rank, suit
                    self.moves[check_index] = self.find_card(next_card)

    def is_game_over(self) -> bool :
        """Check if there are any available moves"""
        for moves in self.moves:
            if moves:
                return False
        return True

    def calculate_score(self) -> int:
        """Return the current game score."""
        total_cards = 0
        for row in range(4):
            in_sequence = 0
            ace = self.board[row][0]
            if ace:
                ace_suit = ace[1]
                for col in range(1, 14):
                    card = self.board[row][col]
                    if card:
                        rank = card[0]
                        suit = card[1]
                        if (suit == ace_suit
                        and col == self.ranks.index(rank)):
                            in_sequence += 1
                        else:
                            break
                    else:
                        break
            total_cards += in_sequence
        return total_cards

    def __init__(self):
        # Create a standard deck of cards
        self.deck = [(rank, suit) for suit in self.suits for rank in self.ranks]
        random.shuffle(self.deck)

        # Initialize the game board
        self.board = [[None] * 14 for _ in range(4)]
        # Row, Col, initial space column zero
        self.spaces = [(0, 0), (1, 0), (2, 0), (3, 0)]
        self.moves = [[], [], [], []]
        self.aces = []
        self.num_moves = 0
        self.line_len = [0, 0, 0, 0]
        self.tot_line_len = 0
        self.card_locations = {}  # New dictionary to store card locations

        # Deal cards to the board
        for row in range(4):
            for col in range(1, 14): # Start dealing from column 1
                card = self.deck.pop()
                self.card_locations[card] = (row, col)  # Store the location
                if card[0] == 'A':
                    self.aces.append((row, col))
                self.board[row][col] = card

        self.moves = [self.aces.copy() for _ in range(4)]

        # Build these during board initialization
        # Find initial empty spaces
        # self.empty_spaces = self.find_empty_spaces()
        # Find initial aces
        # self.aces = self.find_aces()

    def save_game(self, filename: Optional[str] = None) -> Optional[str]:
        """ Save game to a file """
        board_str = ""
        for row in self.board:
            row_str = ' '.join(['__' if card is None else f"{card[0]}{card[1]}" for card in row])
            board_str += row_str + '\n'

        if filename:
            with open(filename, 'w') as f:
                f.write(board_str)
        else:
            return board_str.strip()  # strip() removes the trailing newline

    @classmethod
    def load_game(cls, source=None):
        game = cls()  # Create a new instance
        game.board = []
        game.spaces = []
        game.moves = [[], [], [], []]
        game.num_moves = 0
        game.line_len = [0, 0, 0, 0]
        game.tot_line_len = 0
        game.aces = []

        if source is None:
            raise ValueError("Either filename or board string must be provided")

        # If source is a string and doesn't end with .txt, assume it's a board string
        if isinstance(source, str) and not source.endswith('.txt'):
            lines = source.strip().split('\n')
        else:
            # Assume it's a filename
            with open(source, 'r') as f:
                lines = f.readlines()

        for row_index, line in enumerate(lines):
                row = []
                for col_index, card_str in enumerate(line.strip().split()):
                    if card_str == '__':
                        card = None
                        game.spaces.append((row_index, col_index))
                    else:
                        card = (card_str[0], card_str[1])
                        game.card_locations[card] = (row_index, col_index)  # Store the location
                        if card[0] == 'A' and col_index > 0:
                            game.aces.append((row_index, col_index))
                    row.append(card)
                game.board.append(row)

        # Reconstruct moves
        for i in range(4):
            game.update_moves(i)

        return game

    def __str__(self, color_mode=ColorMode.LIGHT):
        self.calc_line_len()
        score = self.calculate_score()
        line_len_val = 0
        if score < 48:
            line_len_val = (self.tot_line_len + score) / (48 - score)

        # ANSI color codes
        if color_mode == ColorMode.DARK:
            RESET = "\033[0m"
            BOLD = "\033[1m"
            RED = "\033[91m"  # Bright Red
            GREEN = "\033[92m"  # Bright Green
            BLUE = "\033[94m"  # Bright Blue
            YELLOW = "\033[93m"  # Bright Yellow
        elif color_mode == ColorMode.LIGHT:
            RESET = "\033[0m"
            BOLD = "\033[1m"
            RED = "\033[31m"  # Regular Red
            GREEN = "\033[32m"  # Regular Green
            BLUE = "\033[34m"  # Regular Blue
            YELLOW = "\033[33m"  # Regular Yellow
        else:  # ColorMode.NONE
            RESET = BOLD = RED = GREEN = BLUE = YELLOW = ""

        # Function to get color for a card
        def get_card_color(card):
            if card is None:
                return RESET
            suit = card[1]
            return RED if suit in ['H', 'D'] else BLUE

        output = ""
        for row in self.board:
            for card in row:
                if card is None:
                    ## output += "__ "
                    output += f"{RESET}__ {RESET}"
                else:
                    rank, suit = card
                    color = get_card_color(card)
                    # output += f"{rank}{suit} "
                    output += f"{color}{rank}{suit}{RESET} "
            output += "\n"
        if len(self.aces) > 0:
            # output += "\nAces " + str(self.aces)
            output += f"\n{RESET}Aces:{RESET} {self.aces}\n"
        # output += "\nSpaces " + str(self.spaces)
        # output += "\nMoves " + str(self.moves)
        # output += "\n\nLine length " + str(self.line_len)
        # output += "\nTotal length " + str(self.tot_line_len)
        # output += "\nLine len value " + str(line_len_val)
        # output += "\n\nScore " + str(score)

        output += f"{RESET}Spaces:{RESET} {self.spaces}\n"
        output += f"{RESET}Moves:{RESET} {self.moves}\n"
        output += f"\n{RESET}{BOLD}Line length:{RESET} {self.line_len}\n"
        output += f"{RESET}{BOLD}Total length:{RESET} {self.tot_line_len}\n"
        output += f"{RESET}{BOLD}Line len value:{RESET} {line_len_val:.2f}\n"
        output += f"\n{BOLD}{GREEN}Score:{RESET} {score}\n"

        return output

    def find_card(self, next_card):
        card_locn = []
        for row in range(4):
            for col in range(1,14):
                card = self.board[row][col]
                if card  == next_card:
                    card_locn.append((row, col))
                    return card_locn # Return as soon as watch found
        return card_locn
