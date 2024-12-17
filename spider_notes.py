# Import required modules and classes for GUI, core logic, and randomization
import sys  # System-specific parameters and functions
import random  # For shuffling cards
from PySide6.QtWidgets import (  # Import QtWidgets for the GUI
    QApplication, QMainWindow, QHBoxLayout, QLabel, QPushButton, QWidget,
    QGridLayout, QFrame, QMessageBox, QSizePolicy, QVBoxLayout
)
from PySide6.QtCore import Qt, Signal  # Core Qt classes for alignment and signaling
from PySide6.QtGui import QFont  # GUI font management


class Card:
    """Class to define a playing card's attributes and behavior."""

    def __init__(self, rank, suit):
        # Initialize card with a rank, suit, and face-down state
        self.rank = rank
        self.suit = suit
        self.face_up = False  # Indicates if the card is face up

    def __repr__(self):
        # Return card's string representation (face up or face down)
        return f"{self.rank} of {self.suit}" if self.face_up else "Card Face Down"

    def flip(self):
        # Flip the card's face-up status
        self.face_up = not self.face_up

    @property
    def display_rank(self):
        # Map special ranks (1, 11, 12, 13) to their respective symbols
        rank_map = {1: "A", 11: "J", 12: "Q", 13: "K"}
        return rank_map.get(self.rank, str(self.rank))  # Default to numeric rank

    @property
    def display_suit(self):
        # Map suits to their symbols (♠ for Spades, ♥ for Hearts)
        if self.suit == "Spades":
            return "♠"
        elif self.suit == "Hearts":
            return "♥"
        return self.suit


class WildCard(Card):
    """Special card used as a placeholder for empty columns."""

    def __init__(self):
        # Initialize with a dummy rank and suit
        super().__init__(0, "Wildcard")
        self.face_up = True  # Wildcards are always face up

    def __repr__(self):
        # Return string representation for wildcards
        return "Wildcard"


class Deck:
    """Class to represent a deck of cards with two suits (Spades and Hearts)."""

    def __init__(self):
        # Create a deck with two suits, Spades and Hearts
        suits = ['Spades', 'Hearts', 'Spades', 'Hearts']
        ranks = list(range(1, 14))  # Ranks: 1 (Ace) to 13 (King)

        self.cards = []  # Initialize the deck
        for _ in range(2):  # Add two copies of each card (two decks)
            for suit in suits:
                for rank in ranks:
                    self.cards.append(Card(rank, suit))

        self.shuffle()  # Shuffle the deck

    def shuffle(self):
        # Shuffle the cards randomly
        random.shuffle(self.cards)

    def deal(self, num_cards):
        # Deal `num_cards` from the deck
        if num_cards > len(self.cards):
            raise ValueError(f"Cannot deal {num_cards} cards; only {len(self.cards)} cards remaining.")
        dealt_cards = self.cards[:num_cards]  # Take the top cards
        self.cards = self.cards[num_cards:]  # Remove dealt cards from the deck
        return dealt_cards


class SpiderSolitaire:
    """Class implementing the game logic for Spider Solitaire."""

    def __init__(self):
        # Initialize game with a deck and 10 columns of cards
        self.deck = Deck()  # Create a shuffled deck
        self.columns = []  # 10 columns where cards are placed
        for i in range(10):  # Deal cards into 10 columns
            if i < 6:
                pile = self.deck.deal(5)  # First 6 columns get 5 cards
            else:
                pile = self.deck.deal(6)  # Remaining columns get 6 cards
            for c in pile[:-1]:  # Face down all cards except the last in the column
                c.face_up = False
            pile[-1].face_up = True  # Last card is face up
            self.columns.append(pile)  # Add the pile to the columns

        self.foundations = [[] for _ in range(8)]  # Foundations to hold completed sequences
        self.moves = 0  # Move counter
        self.deal_count = 0  # Number of times new cards are dealt
        self.max_draws = 5  # Maximum number of additional draws allowed

        self.move_history = []  # Track move history for undo functionality

    def add_wildcard_to_empty_columns(self):
        # Add a wildcard to empty columns as placeholders
        for col in self.columns:
            if not col:  # If the column is empty
                col.append(WildCard())

    def deal_additional_row(self):
        # Deal an additional row of cards
        if self.deal_count >= self.max_draws:  # Stop if max draws are reached
            return False

        new_cards = self.deck.deal(10)  # Deal 10 cards (one for each column)
        for i, col in enumerate(self.columns):
            if isinstance(col[-1], WildCard):  # Remove wildcard before adding cards
                col.pop()
            col.append(new_cards[i])
            col[-1].face_up = True  # New cards are face up
        self.deal_count += 1  # Increment draw count
        self.move_history.append(('deal', new_cards))
        return True

    def can_move_card(self, from_col, card_index, to_col):
        # Check if a card sequence can be moved to another column
        if to_col and isinstance(to_col[-1], WildCard):  # Allow moves to empty columns
            return True

        # Check for valid sequences based on rank and suit
        movable_sequence = self.get_movable_sequence(from_col, card_index)
        if not movable_sequence:
            return False

        top_dest_card = to_col[-1]
        return movable_sequence[0].rank == top_dest_card.rank - 1  # Rank must decrease by 1

    def get_movable_sequence(self, col, start_index):
        # Return a valid card sequence starting at `start_index`
        if start_index < 0 or start_index >= len(col):  # Invalid index
            return []
        if not col[start_index].face_up:  # Cannot move face-down cards
            return []

        sequence = col[start_index:]
        for i in range(len(sequence) - 1):
            # Ensure cards in sequence are consecutive and same suit
            if sequence[i].suit != sequence[i + 1].suit or sequence[i].rank != sequence[i + 1].rank + 1:
                return []
        return sequence

    def move_sequence(self, from_col, card_index, to_col):
        # Move a valid card sequence to the target column
        if to_col and isinstance(to_col[-1], WildCard):  # Remove wildcard if moving into empty column
            to_col.pop()

        movable_sequence = self.get_movable_sequence(from_col, card_index)
        if not movable_sequence:  # If no valid sequence, allow a single card
            movable_sequence = [from_col[card_index]]

        # Move cards and update history
        self.move_history.append(('move', from_col, to_col, movable_sequence))
        moving_cards = from_col[card_index:]  # Cards to move
        del from_col[card_index:]  # Remove cards from the source column
        to_col.extend(moving_cards)  # Add to the destination column

        # Flip the last card in the source column
        if from_col and not from_col[-1].face_up:
            from_col[-1].flip()

        self.moves += 1
        self.add_wildcard_to_empty_columns()  # Add wildcards to empty columns
        self.check_for_complete_suits(to_col)

    def check_for_complete_suits(self, column):
        # Check if a full sequence (King to Ace) can be moved to the foundation
        while len(column) >= 13:
            last_13 = column[-13:]
            if self.is_full_sequence(last_13):
                for _ in range(13):  # Remove cards from column
                    column.pop()
                for f in self.foundations:  # Add to the foundation
                    if len(f) == 0:
                        f.extend(last_13)
                        break
            else:
                break

    def is_full_sequence(self, cards):
        # Check if the cards form a full sequence (King to Ace)
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
    """Main GUI class for Spider Solitaire game."""

    def __init__(self):
        # Initialize the main window and set its properties
        super().__init__()
        self.setWindowTitle("Spider Solitaire - Two Suit")
        self.setGeometry(100, 100, 1200, 800)  # Set window position and size
        self.game = SpiderSolitaire()  # Create a new game instance
        self.game.add_wildcard_to_empty_columns()  # Add placeholders for empty columns

        self.selected_column = None  # Track the column of the currently selected card
        self.selected_index = None  # Track the index of the selected card in the column

        # Main layout of the application
        self.main_widget = QWidget()  # Central widget
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)  # Vertical layout for the window

        # Top layout for buttons and foundations
        top_layout = QHBoxLayout()
        self.init_top_layout(top_layout)
        self.main_layout.addLayout(top_layout)  # Add the top layout to the main layout

        # Status label to show the number of moves
        self.status_label = QLabel("Moves: 0")
        self.status_label.setFont(QFont("Arial", 12))
        self.main_layout.addWidget(self.status_label)

        # Board layout for displaying columns of cards
        self.board_layout = QGridLayout()
        self.init_board_layout(self.board_layout)
        self.main_layout.addLayout(self.board_layout)

    def card_click(self, column_index, card_index):
        """
        Handle card click events to highlight, move, or deselect cards.
        - First click: Select the card.
        - Second click: Attempt to move the card to the target column.
        """
        if self.selected_column is None:
            # First click: Select a card
            self.selected_column = column_index
            self.selected_index = card_index
        elif self.selected_column == column_index and self.selected_index == card_index:
            # Clicking the same card deselects it
            self.selected_column = None
            self.selected_index = None
        else:
            # Attempt to move the sequence or card to another column
            from_col = self.game.columns[self.selected_column]
            to_col = self.game.columns[column_index]

            if not to_col:  # If the target column is empty
                self.game.move_sequence(from_col, self.selected_index, to_col)
            elif self.game.can_move_card(from_col, self.selected_index, to_col):
                # If move is valid, perform the move
                self.game.move_sequence(from_col, self.selected_index, to_col)
            else:
                # Invalid move: Show a warning
                QMessageBox.warning(self, "Invalid Move", "You cannot move the selected card(s) here.")

            # Clear the selection after attempting a move
            self.selected_column = None
            self.selected_index = None

        self.update_board()  # Refresh the board to reflect changes

    def init_top_layout(self, layout):
        """Initialize the top layout with undo, restart, and draw buttons."""

        # Undo button to reverse the last move
        undo_button = QPushButton("Undo")
        undo_button.clicked.connect(self.on_undo_click)  # Connect to undo logic
        layout.addWidget(undo_button)

        # Restart button to reset the game
        restart_button = QPushButton("Restart")
        restart_button.clicked.connect(self.on_restart_click)  # Connect to restart logic
        layout.addWidget(restart_button)

        # Draw button to deal a new row of cards
        draw_button = QPushButton("Draw")
        draw_button.clicked.connect(self.on_draw_click)  # Connect to deal logic
        layout.addWidget(draw_button)

        # Create placeholders for foundations (completed sequences)
        self.foundation_widgets = []
        for i in range(8):  # 8 Foundations
            foundation = QLabel("A♠" if i % 2 == 0 else "A♥")  # Alternating suit placeholder
            foundation.setAlignment(Qt.AlignCenter)
            foundation.setFixedSize(80, 100)  # Set size for foundation placeholders
            foundation.setStyleSheet("border: 2px solid black; background-color: lightgray;")
            layout.addWidget(foundation)  # Add foundation to the layout
            self.foundation_widgets.append(foundation)  # Save for later updates

    def init_board_layout(self, layout):
        """Initialize the board layout with 10 card columns."""
        self.column_widgets = []  # List to store column widgets
        for col in range(10):  # 10 columns in Spider Solitaire
            column_widget = ColumnWidget(col, self)  # Create a ColumnWidget
            layout.addWidget(column_widget, 0, col)  # Add it to the grid layout
            self.column_widgets.append(column_widget)  # Track it for updates
        self.update_board()  # Populate the board with initial cards

    def update_board(self):
        """Refresh the board and foundations to reflect the current game state."""
        self.game.add_wildcard_to_empty_columns()  # Ensure empty columns have wildcards

        # Update each column
        for i, column in enumerate(self.game.columns):
            self.column_widgets[i].set_cards(column)

        # Update foundations
        for i, foundation in enumerate(self.game.foundations):
            if foundation:
                suit_symbol = "♠" if foundation[0].suit == "Spades" else "♥"
                self.foundation_widgets[i].setText(f"A{suit_symbol}")
            else:
                self.foundation_widgets[i].setText("")

        # Update move count display
        self.status_label.setText(f"Moves: {self.game.moves}")

    def on_undo_click(self):
        """Handle undo button click to reverse the last move."""
        if self.game.undo_last_move():  # Check if undo is possible
            self.update_board()

    def on_restart_click(self):
        """Handle restart button click to reset the game."""
        self.game = SpiderSolitaire()  # Create a new game instance
        self.game.add_wildcard_to_empty_columns()
        self.update_board()  # Refresh the board

    def on_draw_click(self):
        """Handle draw button click to deal a new row of cards."""
        if not self.game.deal_additional_row():  # Attempt to deal cards
            QMessageBox.information(self, "No More Draws", "You cannot draw any more rows.")
        self.update_board()  # Refresh the board

class ColumnWidget(QFrame):
    """A widget representing a single column of cards in the game board."""

    FACE_DOWN_OVERLAP = 10  # Overlap for face-down cards
    FACE_UP_OVERLAP = 20  # Overlap for face-up cards

    def __init__(self, column_index, parent_widget):
        super().__init__()
        self.setStyleSheet("background-color: green; border:2px solid black; border-radius:5px;")
        self.setMinimumWidth(100 + 4)  # Set column width
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # Fixed width, expandable height
        self.column_index = column_index  # Column index
        self.parent_widget = parent_widget  # Parent GUI widget
        self.card_widgets = []  # List to store individual card widgets

    def set_cards(self, cards, selected_index=None):
        """Display cards in this column with optional highlighting."""
        # Clear any existing card widgets
        for cw in self.card_widgets:
            cw.setParent(None)
            cw.deleteLater()
        self.card_widgets.clear()

        # Add new card widgets to represent the column's cards
        y_offset = 0
        for i, card in enumerate(cards):
            is_selected = (self.column_index == self.parent_widget.selected_column 
                           and i == self.parent_widget.selected_index)
            card_widget = CardWidget(card, self.column_index, i, is_selected)
            card_widget.clicked.connect(self.parent_widget.card_click)
            card_widget.setParent(self)  # Set the parent to this column widget
            card_widget.show()
            card_widget.move(0, y_offset)  # Position the card in the column
            y_offset += self.FACE_UP_OVERLAP if card.face_up else self.FACE_DOWN_OVERLAP
            self.card_widgets.append(card_widget)

class CardWidget(QFrame):
    """A widget representing a single card."""

    clicked = Signal(int, int)  # Signal emitted when the card is clicked

    card_width = 100  # Fixed width for card display
    card_height = 150  # Fixed height for card display

    def __init__(self, card, col_index, card_index, is_selected=False):
        super().__init__()
        self.card = card  # Card object
        self.col_index = col_index  # Column index
        self.card_index = card_index  # Card's position in the column
        self.is_selected = is_selected  # Whether the card is highlighted
        self.update_appearance()  # Update the card's visual appearance

    def update_appearance(self):
        """Update the visual appearance of the card based on its state."""
        for child in self.children():
            child.deleteLater()

        # Determine card text and colors
        if self.card.face_up:
            text = f"{self.card.display_rank}{self.card.display_suit}"
            text_color = "red" if self.card.suit == "Hearts" else "black"
            bg_color = "white"
        else:
            text = "Face Down"
            text_color = "black"
            bg_color = "lightgray"

        # Apply selection highlight
        if self.is_selected:
            border_color = "blue"
            bg_color = "lightblue"
        else:
            border_color = "black"

        # Apply styles and layout
        self.setStyleSheet(f"""
            border: 2px solid {border_color};
            border-radius: 5px;
            background-color: {bg_color};
        """)
        layout = QVBoxLayout(self)
        label = QLabel(text, self)
        label.setFont(QFont("Arial", 20, QFont.Bold))
        label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        label.setStyleSheet(f"color: {text_color};")
        layout.addWidget(label)
        self.setFixedSize(self.card_width, self.card_height)

    def mousePressEvent(self, event):
        """Handle mouse click event."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.col_index, self.card_index)  # Emit signal with column and card index

if __name__ == "__main__":
    app = QApplication(sys.argv)  # Create the application
    window = SpiderSolitaireGUI()  # Instantiate the main GUI window
    window.show()  # Show the GUI
    sys.exit(app.exec())  # Execute the application event loop
