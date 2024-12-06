"""
Tristen, Nathan
Spider_solitaire
12-03-24 - Created File/Started Basic Structure
12-05-24 - (Nathan) Started Work on GUI
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
from PyQt5.QtCore import Qt


class Card:
    """Class to define cards and suits"""
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.face_up = False

    def __repr__(self):
        return f"{self.rank} of {self.suit}" if self.face_up else "Card Face Down"


class Deck:
    """Class to create card decks"""
    def __init__(self):
        self.cards = []
        suits = ["Spades", "Hearts"]
        ranks = list(range(1, 14))  # 1 for Ace, 11 for Jack, etc.
        for suit in suits:
            for rank in ranks:
                self.cards.append(Card(rank, suit))
        self.cards *= 4  # Spider Solitaire uses two full decks

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, num_cards):
        dealt_cards = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt_cards


class SpiderSolitaire:
    """Class for the game logic of Spider Solitaire"""
    def __init__(self):
        self.deck = Deck()
        self.deck.shuffle()
        # First 4 columns get 6 cards, the remaining 6 columns get 5 cards
        self.columns = [self.deck.deal(6) for _ in range(4)] + [self.deck.deal(5) for _ in range(6)]
        self.foundations = [[] for _ in range(4)]

    def move_card(self, from_column, to_column):
        # Placeholder for logic to move cards between columns
        pass

    def is_game_won(self):
        # Placeholder to check if the game is won
        return all(len(foundation) == 13 for foundation in self.foundations)


class SpiderSolitaireGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spider Solitaire - Two Suit")
        self.setGeometry(100, 100, 1200, 800)
        self.game = SpiderSolitaire()
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
        board_layout = QGridLayout()
        self.init_board_layout(board_layout)
        main_layout.addLayout(board_layout)

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
            column = QVBoxLayout()
            placeholder = self.create_card_placeholder(f"Column {col+1}")
            column.addWidget(placeholder)

            # Add cards placeholder frame for each column
            card_stack = self.create_card_stack()
            column.addWidget(card_stack)
            layout.addLayout(column, 0, col)

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

    def create_card_stack(self):
        # Create a frame to represent a stack of cards
        stack_frame = QFrame()
        stack_frame.setFixedSize(100, 400)
        stack_frame.setStyleSheet("""
            border: 2px dashed gray;
            background-color: white;
        """)
        return stack_frame

    def on_draw_click(self):
        # Logic to handle drawing cards
        print("Draw pile clicked")
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpiderSolitaireGUI()
    window.show()
    sys.exit(app.exec_())
