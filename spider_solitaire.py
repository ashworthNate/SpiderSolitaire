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


Curent Bugs:
    - Can grab cards from bellow the top card or decending suits
    - Draw Button doesn't work, always returns that there is no more moves left

Wish List:
    - Cleaner GUI (To-Do: remove face down text and change the culumn color to something other than green. Maybe add a colored background.)
    - Auto Move (Ie, simply pressing on a card will move it to a any posibly move location, instead of the curerent click then choose method)
"""

import sys
import random
from functools import partial
from PyQt5.QtWidgets import (
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
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


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


class Deck:
    """Class to create card decks (2 decks of 52 cards, total 104)"""
    def __init__(self):
        self.cards = []
        suits = ["Spades", "Hearts"]
        ranks = list(range(1, 14))
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
    """Class for the game logic of Spider Solitaire (Two Suit Version)"""
    def __init__(self):
        self.deck = Deck()
        # Initial deal: Ten piles of five cards each
        # For each pile: first four face down, fifth card face up
        self.columns = []
        for _ in range(10):
            pile = self.deck.deal(5)
            for c in pile[:4]:
                c.face_up = False
            pile[-1].face_up = True
            self.columns.append(pile)

        self.foundations = [[] for _ in range(8)]
        self.moves = 0
        self.deal_count = 0  # Track how many times we've dealt rows from the stock

    def deal_additional_row(self):
        # Before dealing, no empty column should exist.
        if self.has_empty_column():
            return False

        if len(self.deck.cards) == 0:
            return False

        if len(self.deck.cards) >= 10:
            # Deal 10 cards face up
            new_cards = self.deck.deal(10)
            for c in new_cards:
                c.face_up = True
            for i, col in enumerate(self.columns):
                col.append(new_cards[i])
            self.deal_count += 1
            return True
        else:
            # If less than 10 but at least 4 cards remain, deal 4 cards to first four piles
            if len(self.deck.cards) >= 4:
                new_cards = self.deck.deal(4)
                for c in new_cards:
                    c.face_up = True
                for i in range(4):
                    self.columns[i].append(new_cards[i])
                self.deal_count += 1
                return True

            # If fewer than 4 remain, no deal possible
            return False

    def has_empty_column(self):
        return any(len(col) == 0 for col in self.columns)

    def can_move_card(self, from_col, card_index, to_col):
        movable_sequence = self.get_movable_sequence(from_col, card_index)
        if not movable_sequence:
            return False

        top_moved_card = movable_sequence[0]
        # According to the new requirement: If column is empty, any card or sequence can be placed there.
        if not to_col:
            return True
        else:
            # If not empty, must follow standard rank rule (top_moved_card one less than destination top)
            top_dest_card = to_col[-1]
            return top_moved_card.rank == top_dest_card.rank - 1

    def get_movable_sequence(self, col, start_index):
        if start_index < 0 or start_index >= len(col):
            return []
        seq = [col[start_index]]
        if not col[start_index].face_up:
            return []

        for i in range(start_index+1, len(col)):
            prev_card = seq[-1]
            curr_card = col[i]
            if curr_card.face_up and curr_card.suit == prev_card.suit and curr_card.rank == prev_card.rank - 1:
                seq.append(curr_card)
            else:
                break
        return seq

    def move_sequence(self, from_col, card_index, to_col):
        movable_sequence = self.get_movable_sequence(from_col, card_index)
        if not movable_sequence:
            return

        length = len(movable_sequence)
        moving_cards = from_col[card_index:card_index+length]
        del from_col[card_index:card_index+length]
        to_col.extend(moving_cards)

        if from_col and not from_col[-1].face_up:
            from_col[-1].flip()
        self.moves += 1
        self.check_for_complete_suits(to_col)

    def check_for_complete_suits(self, column):
        # If a complete suit (A to K) is formed, remove it to foundations.
        while len(column) >= 13:
            last_13 = column[-13:]
            if self.is_full_sequence(last_13):
                for _ in range(13):
                    column.pop()
                for f in self.foundations:
                    if len(f) == 0:
                        f.extend(last_13)
                        break
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

    def is_game_won(self):
        completed_suits = sum(1 for f in self.foundations if len(f) == 13)
        return completed_suits == 8


class CardWidget(QFrame):
    clicked = pyqtSignal()

    card_width = 60
    card_height = 90

    def __init__(self, card):
        super().__init__()
        self.card = card
        self.update_appearance()

    def update_appearance(self):
        for child in self.children():
            child.deleteLater()

        if self.card.face_up:
            text = f"{self.card.display_rank}{self.card.display_suit}"
            if self.card.suit == "Hearts":
                text_color = "red"
            else:
                text_color = "black"
            bg_color = "white"
        else:
            text = "Face Down"
            text_color = "black"
            bg_color = "lightgray"

        self.setStyleSheet(f"""
            border: 1px solid black;
            border-radius: 5px;
            background-color: {bg_color};
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        font_size = 12
        label = QLabel(text, self)
        label.setFont(QFont("Arial", font_size, QFont.Bold))
        label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        label.setStyleSheet(f"color: {text_color};")

        layout.addWidget(label)
        self.setLayout(layout)

        self.setFixedSize(self.card_width, self.card_height)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()


class ColumnWidget(QFrame):
    FACE_DOWN_OVERLAP = 10
    FACE_UP_OVERLAP = 20

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: green; border:2px solid black; border-radius:5px;")
        self.setMinimumWidth(CardWidget.card_width + 4)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.card_widgets = []

    def set_cards(self, cards):
        for cw in self.card_widgets:
            cw.setParent(None)
            cw.deleteLater()
        self.card_widgets.clear()

        # Find first face-up card from bottom
        face_up_start_index = None
        for i, cw in enumerate(cards):
            if cw.card.face_up:
                face_up_start_index = i
                break

        if face_up_start_index is None:
            face_up_start_index = len(cards)  # no face-up cards

        y_offset = 0
        # Place face-down cards
        for i in range(face_up_start_index):
            cw = cards[i]
            cw.setParent(self)
            cw.show()
            cw.move(0, y_offset)
            y_offset += self.FACE_DOWN_OVERLAP
            self.card_widgets.append(cw)

        # Place face-up cards
        for i in range(face_up_start_index, len(cards)):
            cw = cards[i]
            cw.setParent(self)
            cw.show()
            cw.move(0, y_offset)
            y_offset += self.FACE_UP_OVERLAP
            self.card_widgets.append(cw)

        self.setMinimumHeight(y_offset + CardWidget.card_height)


class SpiderSolitaireGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spider Solitaire - Two Suit")
        self.setGeometry(100, 100, 1200, 800)
        self.game = SpiderSolitaire()

        self.selected_column = None
        self.selected_index = None
        self.selected_widgets = []

        self.status_label = QLabel()

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)

        top_layout = QHBoxLayout()
        self.init_top_layout(top_layout)
        self.main_layout.addLayout(top_layout)

        self.board_layout = QGridLayout()
        self.board_layout.setHorizontalSpacing(5)
        self.board_layout.setVerticalSpacing(5)
        self.init_board_layout(self.board_layout)
        self.main_layout.addLayout(self.board_layout)

        status_layout = QHBoxLayout()
        self.status_label = QLabel("Moves: 0")
        self.status_label.setFont(QFont("Arial", 12))
        status_layout.addWidget(self.status_label)
        self.main_layout.addLayout(status_layout)

    def init_top_layout(self, layout):
        for i in range(8):
            foundation = self.create_card_placeholder("Foundation")
            layout.addWidget(foundation)

        layout.addStretch(1)

        draw_pile = QPushButton("Draw")
        draw_pile.clicked.connect(self.on_draw_click)
        layout.addWidget(draw_pile)

    def init_board_layout(self, layout):
        self.column_widgets = []
        for col in range(10):
            column_layout = QVBoxLayout()
            placeholder = self.create_card_placeholder(f"Column {col+1}")
            column_layout.addWidget(placeholder)

            column_widget = ColumnWidget()
            column_layout.addWidget(column_widget)
            self.column_widgets.append(column_widget)

            layout.addLayout(column_layout, 0, col)

        self.refresh_board()

    def create_card_placeholder(self, text):
        placeholder = QLabel(text)
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("""
            border: 2px solid black;
            border-radius: 5px;
            background-color: lightgray;
            font-size: 14px;
        """)
        placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        placeholder.setFixedHeight(100)
        return placeholder

    def on_draw_click(self):
        # Before dealing, no empty column should exist to deal new cards.
        # This rule remains as per standard Spider, but we allow moving any card to empty column before that.
        if self.game.has_empty_column():
            self.show_message("Cannot deal: fill all empty spaces first.")
            return

        success = self.game.deal_additional_row()
        if success:
            self.clear_selection()
            self.refresh_board()
        else:
            self.show_message("No more cards to draw.")

    def handle_card_click(self, col_index, card_index):
        columns = self.game.columns
        if not (0 <= col_index < len(columns)) or not (0 <= card_index < len(columns[col_index])):
            return

        card = columns[col_index][card_index]

        if not card.face_up:
            self.clear_selection()
            return

        if self.selected_column is None:
            self.selected_column = col_index
            self.selected_index = card_index
            self.highlight_selection(col_index, card_index)
        else:
            from_col = self.game.columns[self.selected_column]
            to_col = self.game.columns[col_index]
            if self.game.can_move_card(from_col, self.selected_index, to_col):
                self.game.move_sequence(from_col, self.selected_index, to_col)
                self.clear_selection()
                self.refresh_board()
                self.update_status()
                if self.game.is_game_won():
                    self.win_message()
            else:
                self.show_message("Invalid Move!")
                self.clear_selection()

    def clear_selection(self):
        self.selected_column = None
        self.selected_index = None
        self.selected_widgets = []
        self.refresh_board()

    def highlight_selection(self, col_index, card_index):
        col_data = self.game.columns[col_index]
        seq_length = len(col_data) - card_index
        col_widget = self.column_widgets[col_index]
        for i in range(card_index, card_index + seq_length):
            if 0 <= i < len(col_widget.card_widgets):
                cw = col_widget.card_widgets[i]
                cw.setStyleSheet("""
                    border: 2px solid blue;
                    border-radius: 5px;
                    background-color: white;
                """)
                self.selected_widgets.append(cw)

    def refresh_board(self):
        for col_index, col_widget in enumerate(self.column_widgets):
            col_data = self.game.columns[col_index]
            cards = []
            for i, card_obj in enumerate(col_data):
                cw = CardWidget(card_obj)
                cw.clicked.connect(partial(self.handle_card_click, col_index, i))
                cards.append(cw)
            col_widget.set_cards(cards)

    def update_status(self):
        self.status_label.setText(f"Moves: {self.game.moves}")

    def show_message(self, message):
        msg = QMessageBox(self)
        msg.setWindowTitle("Spider Solitaire")
        msg.setText(message)
        msg.setIcon(QMessageBox.Information)
        msg.exec_()

    def win_message(self):
        self.show_message("You won the game! Congratulations!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpiderSolitaireGUI()
    window.show()
    sys.exit(app.exec_())
