"""
Tristen, Nathan Boyd
Spider_solitaire
Proffessor Ordonez
Fundamentals of Software Design

12-03-24 - (Nathan) Created File/Started Basic Structure
12-05-24 - (Nathan) Started Work on GUI
12-09-24 - (Nathan) Implemented card display, card interactions, draw logic, and basic move logic.
"""

import sys
import random
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
    QGridLayout,
    QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QPoint, QRect
from PyQt5.QtGui import QFont, QPalette, QColor


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
        # Convert numeric ranks to typical card symbols
        rank_map = {1: "A", 11: "J", 12: "Q", 13: "K"}
        return rank_map.get(self.rank, str(self.rank))

    @property
    def display_suit(self):
        # We can use simple unicode symbols or just text
        if self.suit == "Spades":
            return "♠"
        elif self.suit == "Hearts":
            return "♥"
        return self.suit


class Deck:
    """Class to create card decks"""
    def __init__(self):
        self.cards = []
        suits = ["Spades", "Hearts"]
        ranks = list(range(1, 14))  # 1 for Ace, 11 for Jack, etc.
        # Two full decks of two suits -> 2 decks * 2 suits * 13 ranks = 52 cards * 2 = 104 cards
        for _ in range(2):
            for suit in suits:
                for rank in ranks:
                    self.cards.append(Card(rank, suit))
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, num_cards):
        if num_cards > len(self.cards):
            num_cards = len(self.cards)
        dealt_cards = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt_cards


class SpiderSolitaire:
    """Class for the game logic of Spider Solitaire"""
    def __init__(self):
        self.deck = Deck()
        # First 4 columns get 6 cards, the remaining 6 columns get 5 cards
        self.columns = [self.deck.deal(6) for _ in range(4)] + [self.deck.deal(5) for _ in range(6)]
        self.foundations = [[] for _ in range(4)]
        # Flip the last card in each column face up
        for col in self.columns:
            if col:
                col[-1].face_up = True

    def deal_additional_row(self):
        # Deal one card to each column if deck is not empty
        if len(self.deck.cards) < 10:
            return False
        new_cards = self.deck.deal(10)
        for i, col in enumerate(self.columns):
            col.append(new_cards[i])
            col[-1].flip()  # Immediately flip them face up
        return True

    def can_move_card(self, from_col, card_index, to_col):
        # Basic move logic:
        # - You can only move a sequence of face-up cards in descending order
        #   matching suit.
        # For simplicity, let's only consider moving the top face-up card or
        # a valid sequence. We'll implement a minimal rule:
        #
        # Check that the sequence from card_index to the end of from_col is descending
        # and same suit.
        moving_sequence = from_col[card_index:]
        if not all(card.face_up for card in moving_sequence):
            return False
        # Check descending order by rank and same suit
        for i in range(len(moving_sequence) - 1):
            if not (moving_sequence[i].rank == moving_sequence[i+1].rank + 1 and
                    moving_sequence[i].suit == moving_sequence[i+1].suit):
                return False

        # Check if we can place on to_col
        if not to_col:
            # Empty column can only accept King sequences (if top card is a King)
            if moving_sequence[0].rank == 13:
                return True
            else:
                return False
        else:
            top_card = to_col[-1]
            # Must place onto a card exactly one rank higher and same suit
            if (top_card.face_up and
                top_card.suit == moving_sequence[0].suit and
                top_card.rank == moving_sequence[0].rank + 1):
                return True
        return False

    def move_sequence(self, from_col, card_index, to_col):
        # Move the sequence of cards
        moving_sequence = from_col[card_index:]
        del from_col[card_index:]
        to_col.extend(moving_sequence)
        # Flip the new top card of from_col, if any
        if from_col and not from_col[-1].face_up:
            from_col[-1].flip()

    def is_game_won(self):
        # Check if all foundations are complete
        return all(len(foundation) == 13 for foundation in self.foundations)


class CardWidget(QFrame):
    clicked = pyqtSignal()  # Signal emitted when this card is clicked

    def __init__(self, card):
        super().__init__()
        self.card = card
        self.setFixedSize(80, 120)
        self.update_appearance()

    def update_appearance(self):
        palette = self.palette()
        if self.card.face_up:
            # Different suit colors: Hearts (red), Spades (black)
            if self.card.suit == "Hearts":
                palette.setColor(QPalette.WindowText, Qt.red)
            else:
                palette.setColor(QPalette.WindowText, Qt.black)

            text = f"{self.card.display_rank}{self.card.display_suit}"
            self.setStyleSheet("""
                border: 2px solid black;
                border-radius: 5px;
                background-color: white;
            """)
        else:
            text = "Face Down"
            palette.setColor(QPalette.WindowText, Qt.black)
            self.setStyleSheet("""
                border: 2px solid black;
                border-radius: 5px;
                background-color: lightgray;
            """)

        label = QLabel(text, self)
        label.setFont(QFont("Arial", 14, QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        # Manually position label (center)
        label.setGeometry(QRect(0, 0, self.width(), self.height()))
        self.setPalette(palette)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()


class SpiderSolitaireGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spider Solitaire - Two Suit")
        self.setGeometry(100, 100, 1200, 800)
        self.game = SpiderSolitaire()

        self.selected_column = None
        self.selected_index = None
        self.selected_widgets = []

        self.initUI()

    def initUI(self):
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Top layout: Foundations and draw pile
        top_layout = QHBoxLayout()
        self.init_top_layout(top_layout)
        main_layout.addLayout(top_layout)

        # Game board layout: Columns of cards
        self.board_layout = QGridLayout()
        self.init_board_layout(self.board_layout)
        main_layout.addLayout(self.board_layout)

    def init_top_layout(self, layout):
        # Add foundation placeholders
        for i in range(4):
            foundation = self.create_card_placeholder("Foundation")
            layout.addWidget(foundation)

        # Add spacing
        layout.addStretch(1)

        # Add draw pile
        draw_pile = QPushButton("Draw")
        draw_pile.clicked.connect(self.on_draw_click)
        layout.addWidget(draw_pile)

    def init_board_layout(self, layout):
        # Create 10 columns for the Spider Solitaire game board
        for col in range(10):
            column_layout = QVBoxLayout()
            placeholder = self.create_card_placeholder(f"Column {col+1}")
            column_layout.addWidget(placeholder)
            # Add cards for each column
            self.add_cards_to_column(column_layout, col)
            layout.addLayout(column_layout, 0, col)

    def add_cards_to_column(self, column_layout, col_index):
        # Clear existing cards in the layout if any
        # Not strictly necessary here, but good practice if we refresh
        for i in reversed(range(column_layout.count())):
            item = column_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), CardWidget):
                widget = item.widget()
                column_layout.removeWidget(widget)
                widget.deleteLater()

        # Add current cards from self.game.columns[col_index]
        for i, card in enumerate(self.game.columns[col_index]):
            cw = CardWidget(card)
            cw.clicked.connect(lambda _, c=col_index, idx=i: self.handle_card_click(c, idx))
            column_layout.addWidget(cw)

    def create_card_placeholder(self, text):
        placeholder = QLabel(text)
        placeholder.setFixedSize(100, 140)
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("""
            border: 2px solid black;
            border-radius: 5px;
            background-color: lightgray;
            font-size: 14px;
        """)
        return placeholder

    def on_draw_click(self):
        # Logic to handle drawing cards (deal a new row if possible)
        success = self.game.deal_additional_row()
        if success:
            self.refresh_board()
        else:
            print("No more cards to draw.")

    def handle_card_click(self, col_index, card_index):
        # If no card selected, select this one (if it is face up)
        columns = self.game.columns
        card = columns[col_index][card_index]
        if not card.face_up:
            # Can't select a face-down card
            return

        if self.selected_column is None:
            # Try selecting a sequence starting at card_index
            # We'll just highlight this choice
            self.selected_column = col_index
            self.selected_index = card_index
            self.highlight_selection(col_index, card_index)
        else:
            # Attempt move
            if (col_index, card_index) == (self.selected_column, self.selected_index):
                # Same card clicked again, deselect
                self.clear_selection()
                return
            # If clicking on another column (on a card or empty space):
            # We'll treat clicking on any card in target column as an attempt
            # to move onto its top card.
            if self.game.can_move_card(self.game.columns[self.selected_column],
                                       self.selected_index,
                                       self.game.columns[col_index]):
                self.game.move_sequence(self.game.columns[self.selected_column],
                                        self.selected_index,
                                        self.game.columns[col_index])
                self.clear_selection()
                self.refresh_board()
                # Check for win
                if self.game.is_game_won():
                    self.win_message()
            else:
                # Invalid move
                self.clear_selection()

    def clear_selection(self):
        self.selected_column = None
        self.selected_index = None
        # Clear any highlighting
        self.selected_widgets = []
        self.refresh_board()

    def highlight_selection(self, col_index, card_index):
        # Highlight the selected sequence
        # We will highlight all cards from card_index to end
        column_layout = self.get_column_layout(col_index)
        seq_length = len(self.game.columns[col_index]) - card_index
        # Style them slightly differently
        for i in range(card_index, card_index + seq_length):
            cw = column_layout.itemAt(i+1).widget()  # +1 for the placeholder at top
            cw.setStyleSheet("""
                border: 2px solid blue;
                border-radius: 5px;
                background-color: white;
            """)
            self.selected_widgets.append(cw)

    def get_column_layout(self, col_index):
        # board_layout item at (0, col_index) is a layout that includes placeholder and cards
        # We know each column is a QVBoxLayout added to board_layout
        item = self.board_layout.itemAtPosition(0, col_index)
        return item

    def refresh_board(self):
        for col in range(10):
            col_layout = self.get_column_layout(col)
            # First item: placeholder
            # Remove all card widgets and re-add
            while col_layout.count() > 1:
                w = col_layout.itemAt(col_layout.count() - 1).widget()
                col_layout.removeWidget(w)
                w.deleteLater()
            # Add updated cards
            self.add_cards_to_column(col_layout, col)

    def win_message(self):
        # Just print a message for now
        print("You won the game!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpiderSolitaireGUI()
    window.show()
    sys.exit(app.exec_())
