"""
Tristen, Nathan
Spider_solitaire
12-03-24 - Created File/Started Basic Structure
12-05-24 - (Nathan) Started Work on GUI
12-09-24 - (Nathan) 
    * Implemented standard Spider Solitaire rules for two suits.
    * Dealt the initial ten piles with proper face-down and face-up distribution.
    * Adjusted move logic so that any card or movable sequence can be moved onto an empty column.
    * Enforced that no new deal can occur if there are empty columns (except for the initial state).
    * Implemented proper dealing of additional rows from the stock, including the final partial deal.
    * Updated the display so that face-down cards appear above face-up cards with different overlaps.
12-15-24 - (Nathan)
    * Fixed Bugs to do with completed suits not moving to the foundation
    * Fixed empty column bug where empty columns weren't playable
12-16-24 - (Nathan)
    * Created more tests


Curent Bugs:
    * Undo doesn't hide flipped cards

Wish List:
    - Cleaner GUI (To-Do: remove face down text and change the culumn color to something other than green. Maybe add a colored background.)
    - Auto Move (Ie, simply pressing on a card will move it to a any posibly move location, instead of the curerent click then choose method)
"""

import sys
import random
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
    QGridLayout,
    QFrame,
    QMessageBox,
    QSizePolicy,
    QVBoxLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class Card:
    """Class to define cards and suits"""
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.face_up = False

    def __repr__(self):
        return f"{self.rank} of {self.suit}" if self.face_up else "Card Face Down"

    def flip(self):
        self.face_up = not self.face_up

    @property
    def display_rank(self):
        rank_map = {1: "A", 11: "J", 12: "Q", 13: "K"}
        return rank_map.get(self.rank, str(self.rank))

    @property
    def display_suit(self):
        if self.suit == "Spades":
            return "♠"
        elif self.suit == "Hearts":
            return "♥"
        return self.suit

class WildCard(Card):
    """Placeholder card for empty columns."""
    def __init__(self):
        super().__init__(0, "Wildcard")
        self.face_up = True

    def __repr__(self):
        return "Wildcard"


class Deck:
    """Class to represent a deck of cards with only Spades and Hearts."""
    
    def __init__(self):
        suits = ['Spades', 'Hearts','Spades', 'Hearts']
        ranks = list(range(1, 14))  # 1 = Ace, 11 = Jack, 12 = Queen, 13 = King
        
        self.cards = []
        for _ in range(2):  # Two decks
            for suit in suits:
                for rank in ranks:
                    self.cards.append(Card(rank, suit))

        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, num_cards):
        if num_cards > len(self.cards):
            raise ValueError(f"Cannot deal {num_cards} cards; only {len(self.cards)} cards remaining.")
        dealt_cards = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt_cards


class SpiderSolitaire:
    """Class for the game logic of Spider Solitaire (Two Suit Version)"""
    def __init__(self):
        self.deck = Deck()
        self.columns = []
        for i in range(10):
            if i < 6:
                pile = self.deck.deal(5)
            else:
                pile = self.deck.deal(6)
            for c in pile[:-1]:
                c.face_up = False
            pile[-1].face_up = True
            self.columns.append(pile)

        self.foundations = [[] for _ in range(8)]
        self.moves = 0
        self.deal_count = 0
        self.max_draws = 5

        # Track move history for undo functionality
        self.move_history = []

    def add_wildcard_to_empty_columns(self):
        for col in self.columns:
            if not col:  # Add wildcard if column is empty
                col.append(WildCard())

    def deal_additional_row(self):
        if self.deal_count >= self.max_draws:
            return False

        new_cards = self.deck.deal(10)
        for i, col in enumerate(self.columns):
            if isinstance(col[-1], WildCard):
                col.pop()  # Remove placeholder before adding new cards
            col.append(new_cards[i])
            col[-1].face_up = True
        self.deal_count += 1
        self.move_history.append(('deal', new_cards))
        return True

    def can_move_card(self, from_col, card_index, to_col):
        # Allow moving any card or sequence to an empty column with a WildCard
        if to_col and isinstance(to_col[-1], WildCard):
            return True

        # Standard move check for valid sequences
        movable_sequence = self.get_movable_sequence(from_col, card_index)
        if not movable_sequence:
            return False

        top_dest_card = to_col[-1]
        return movable_sequence[0].rank == top_dest_card.rank - 1

    def get_movable_sequence(self, col, start_index):
        if start_index < 0 or start_index >= len(col):
            return []
        if not col[start_index].face_up:
            return []

        sequence = col[start_index:]
        for i in range(len(sequence) - 1):
            if (
                sequence[i].suit != sequence[i + 1].suit
                or sequence[i].rank != sequence[i + 1].rank + 1
            ):
                return []

        return sequence

    def move_sequence(self, from_col, card_index, to_col):
        # Allow moving any sequence or single card to a WildCard column
        if to_col and isinstance(to_col[-1], WildCard):
            to_col.pop()  # Remove wildcard before adding cards

        movable_sequence = self.get_movable_sequence(from_col, card_index)
        if not movable_sequence:  # If no valid sequence, allow a single card
            movable_sequence = [from_col[card_index]]

        # Record the move for undo functionality
        self.move_history.append(('move', from_col, to_col, movable_sequence))

        # Move cards from source column to target column
        moving_cards = from_col[card_index:]
        del from_col[card_index:]
        to_col.extend(moving_cards)

        # Flip the last card in the source column if needed
        if from_col and not from_col[-1].face_up:
            from_col[-1].flip()

        self.moves += 1
        self.add_wildcard_to_empty_columns()
        self.check_for_complete_suits(to_col)

    def undo_last_move(self):
        if not self.move_history:
            return False

        last_move = self.move_history.pop()

        if last_move[0] == 'move':
            _, from_col, to_col, moved_cards = last_move
            del to_col[-len(moved_cards):]
            from_col.extend(moved_cards)
            if from_col and not from_col[-1].face_up:
                from_col[-1].flip()
        elif last_move[0] == 'deal':
            _, dealt_cards = last_move
            for col, card in zip(self.columns, dealt_cards):
                col.pop()
        self.add_wildcard_to_empty_columns()
        return True

    def check_for_complete_suits(self, column):
        while len(column) >= 13:
            last_13 = column[-13:]
            if self.is_full_sequence(last_13):
                for _ in range(13):
                    column.pop()
                for f in self.foundations:
                    if len(f) == 0:
                        f.extend(last_13)  # Move the sequence to the foundation
                        break
                # Flip the last face-down card in the column (if any)
                if column and not column[-1].face_up:
                    column[-1].flip()
            else:
                break

    def is_full_sequence(self, cards):
        if len(cards) != 13:
            return False
        suit = cards[0].suit
        expected_rank = 13
        for c in cards:
            if c.suit != suit or c.rank != expected_rank:
                return False
            expected_rank -= 1
        return True



class SpiderSolitaireGUI(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spider Solitaire - Two Suit")
        self.setGeometry(100, 100, 1200, 800)
        self.game = SpiderSolitaire()
        self.game.add_wildcard_to_empty_columns()

        self.selected_column = None
        self.selected_index = None

        # Main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)

        # Top layout for undo/restart buttons and foundations
        top_layout = QHBoxLayout()
        self.init_top_layout(top_layout)
        self.main_layout.addLayout(top_layout)

        # Status label: Initialize before board layout
        self.status_label = QLabel("Moves: 0")
        self.status_label.setFont(QFont("Arial", 12))
        self.main_layout.addWidget(self.status_label)

        # Board layout for card columns
        self.board_layout = QGridLayout()
        self.init_board_layout(self.board_layout)
        self.main_layout.addLayout(self.board_layout)

    def card_click(self, column_index, card_index):
        """Handle card click events to highlight, move, or deselect cards."""
        if self.selected_column is None:
            # First click: Select the card
            self.selected_column = column_index
            self.selected_index = card_index
        elif self.selected_column == column_index and self.selected_index == card_index:
            # Clicking the same card again: Deselect it
            self.selected_column = None
            self.selected_index = None
        else:
            # Attempt to move to another column
            from_col = self.game.columns[self.selected_column]
            to_col = self.game.columns[column_index]

            if not to_col:  # If target column is empty
                self.game.move_sequence(from_col, self.selected_index, to_col)
                self.selected_column = None  # Clear selection after a valid move
                self.selected_index = None
            elif self.game.can_move_card(from_col, self.selected_index, to_col):
                # Move the sequence if valid
                self.game.move_sequence(from_col, self.selected_index, to_col)
                self.selected_column = None  # Clear selection after a valid move
                self.selected_index = None
            else:
                # Invalid move: Show warning and reset selection
                QMessageBox.warning(self, "Invalid Move", "You cannot move the selected card(s) here.")
                self.selected_column = None
                self.selected_index = None

        self.update_board()




    def init_top_layout(self, layout):
        # Undo Button
        undo_button = QPushButton("Undo")
        undo_button.clicked.connect(self.on_undo_click)
        layout.addWidget(undo_button)

        # Restart Button
        restart_button = QPushButton("Restart")
        restart_button.clicked.connect(self.on_restart_click)
        layout.addWidget(restart_button)

        # Draw Button
        draw_button = QPushButton("Draw")
        draw_button.clicked.connect(self.on_draw_click)  # Connect to draw action
        layout.addWidget(draw_button)

        # Foundation Placeholders
        self.foundation_widgets = []
        for i in range(8):
            foundation = QLabel("A♠" if i % 2 == 0 else "A♥")
            foundation.setAlignment(Qt.AlignCenter)
            foundation.setFixedSize(80, 100)
            foundation.setStyleSheet("border: 2px solid black; background-color: lightgray;")
            layout.addWidget(foundation)
            self.foundation_widgets.append(foundation)


    def init_board_layout(self, layout):
        self.column_widgets = []
        for col in range(10):
            column_widget = ColumnWidget(col, self)
            layout.addWidget(column_widget, 0, col)
            self.column_widgets.append(column_widget)
        self.update_board()

    def update_board(self):
        self.game.add_wildcard_to_empty_columns()
        for i, column in enumerate(self.game.columns):
            self.column_widgets[i].set_cards(column)
        
        # Update foundations
        for i, foundation in enumerate(self.game.foundations):
            if foundation:
                suit_symbol = "♠" if foundation[0].suit == "Spades" else "♥"
                self.foundation_widgets[i].setText(f"A{suit_symbol}")
            else:
                self.foundation_widgets[i].setText("")

        self.status_label.setText(f"Moves: {self.game.moves}")

    def on_undo_click(self):
        if self.game.undo_last_move():
            self.update_board()

    def on_restart_click(self):
        self.game = SpiderSolitaire()
        self.game.add_wildcard_to_empty_columns()
        self.update_board()
    def on_draw_click(self):
        """Handles the draw button click to deal a new row of cards."""
        if not self.game.deal_additional_row():
            QMessageBox.information(self, "No More Draws", "You cannot draw any more rows.")
        self.update_board()


class ColumnWidget(QFrame):
    FACE_DOWN_OVERLAP = 10
    FACE_UP_OVERLAP = 20

    def __init__(self, column_index, parent_widget):
        super().__init__()
        self.setStyleSheet("background-color: green; border:2px solid black; border-radius:5px;")
        self.setMinimumWidth(100 + 4)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.column_index = column_index
        self.parent_widget = parent_widget
        self.card_widgets = []

    def set_cards(self, cards, selected_index=None):
        """Display the cards in this column with optional highlighting."""
        # Clear previous card widgets
        for cw in self.card_widgets:
            cw.setParent(None)
            cw.deleteLater()
        self.card_widgets.clear()

        y_offset = 0
        if cards:
            for i, card in enumerate(cards):
                is_selected = (self.column_index == self.parent_widget.selected_column 
                            and i == self.parent_widget.selected_index)
                card_widget = CardWidget(card, self.column_index, i, is_selected)
                card_widget.clicked.connect(self.parent_widget.card_click)
                card_widget.setParent(self)
                card_widget.show()
                card_widget.move(0, y_offset)
                y_offset += self.FACE_UP_OVERLAP if card.face_up else self.FACE_DOWN_OVERLAP
                self.card_widgets.append(card_widget)




class CardWidget(QFrame):
    clicked = Signal(int, int)  # Signal will pass column index and card index

    card_width = 100
    card_height = 150

    def __init__(self, card, col_index, card_index, is_selected=False):
        super().__init__()
        self.card = card
        self.col_index = col_index
        self.card_index = card_index
        self.is_selected = is_selected
        self.update_appearance()

    def update_appearance(self):
        for child in self.children():
            child.deleteLater()

        if self.card.face_up:
            text = f"{self.card.display_rank}{self.card.display_suit}"
            text_color = "red" if self.card.suit == "Hearts" else "black"
            bg_color = "white"
        else:
            text = "Face Down"
            text_color = "black"
            bg_color = "lightgray"

        # Apply a blue highlight border if the card is selected
        if self.is_selected:
            border_color = "blue"
            bg_color = "lightblue"
        else:
            border_color = "black"

        self.setStyleSheet(f"""
            border: 2px solid {border_color};
            border-radius: 5px;
            background-color: {bg_color};
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        font_size = 20
        label = QLabel(text, self)
        label.setFont(QFont("Arial", font_size, QFont.Bold))
        label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        label.setStyleSheet(f"color: {text_color};")

        layout.addWidget(label)
        self.setLayout(layout)

        self.setFixedSize(self.card_width, self.card_height)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            print(f"Card {self.card.display_rank}{self.card.display_suit} clicked")
            self.clicked.emit(self.col_index, self.card_index)  # Emit the click signal with column and card index


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpiderSolitaireGUI()
    window.show()
    sys.exit(app.exec())
