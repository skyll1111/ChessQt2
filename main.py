import json
import os
import sqlite3
import subprocess
import sys

import chess
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
                             QPushButton, QTabWidget, QComboBox, QTextEdit, QMessageBox, QFileDialog, QAction, QDialog,
                             QLineEdit, QLabel, QHBoxLayout)
from chess import svg


class ChessboardApp(QApplication):
    def __init__(self, sys_argv):
        super(ChessboardApp, self).__init__(sys_argv)
        self.main_window = ChessboardMainWindow()
        self.main_window.show()


def find_exe_file_in_app_root(file_name_part):
    app_root = os.path.dirname(os.path.abspath(__file__))

    for root, dirs, files in os.walk(app_root):
        for file in files:
            if file_name_part.lower() in file.lower() and file.endswith(".exe"):
                return os.path.join(root, file)

    return None


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Settings')
        self.setGeometry(600, 300, 450, 400)
        layout = QVBoxLayout()

        self.skill_level_edit = QLineEdit()
        self.skill_level_edit.setPlaceholderText('skill-level')
        self.analyse_skill_level_label = QLabel('analyse skill level(min:1, max:20)')
        self.hash_edit = QLineEdit()
        self.hash_edit.setPlaceholderText('analyse hash')
        self.analyse_hash_label = QLabel('analyze hash(mb)')
        self.threads_edit = QLineEdit()
        self.threads_edit.setPlaceholderText('threads')
        self.analyse_threads_label = QLabel('analyse threads')
        self.analyse_time_edit = QLineEdit()
        self.analyse_time_edit.setPlaceholderText('analyse time')
        self.analyse_time_label = QLabel('analyse time (ms)')
        self.bot_skill_level_edit = QLineEdit()
        self.bot_skill_level_edit.setPlaceholderText('bot skill')
        self.bot_skill_level_label = QLabel('bot skill level(min:1, max:20)')
        self.bot_hash_edit = QLineEdit()
        self.bot_hash_edit.setPlaceholderText('bot hash')
        self.bot_hash_label = QLabel('bot hash(mb)')
        self.bot_threads_edit = QLineEdit()
        self.bot_threads_edit.setPlaceholderText('bot threads')
        self.bot_threads_label = QLabel('bot threads')
        self.bot_move_time_edit = QLineEdit()
        self.bot_move_time_edit.setPlaceholderText('move time')
        self.bot_move_time_label = QLabel('bot move time')
        self.engine_path_edit = QLineEdit()
        self.engine_path_edit.setPlaceholderText('engine path')
        self.engine_path_label = QLabel('engine path')

        try:
            data = json.load(open("settings.json"))
        except Exception:
            data = {
                "analyse": {"skill level(min=1, max=20)": 20, "hash(mb)": 1024, "threads": 128, "analyse time": 3000},
                "bot": {"skill level(min=1, max=20)": 20, "hash(mb)": 1024, "threads": 128, "move time": 3000},
                "engine(stockfish)": {"path": "C:/PYTHON/ChessQT/stockfish/stockfish-windows-x86-64-avx2.exe"}}
        self.skill_level_edit.setText(str(data["analyse"]["skill level(min=1, max=20)"]))
        self.hash_edit.setText(str(data["analyse"]["hash(mb)"]))
        self.threads_edit.setText(str(data["analyse"]["threads"]))
        self.analyse_time_edit.setText(str(data["analyse"]["analyse time"]))
        self.bot_skill_level_edit.setText(str(data["bot"]["skill level(min=1, max=20)"]))
        self.bot_hash_edit.setText(str(data["bot"]["hash(mb)"]))
        self.bot_threads_edit.setText(str(data["bot"]["threads"]))
        self.bot_move_time_edit.setText(str(data["bot"]["move time"]))
        self.engine_path_edit.setText(data["engine(stockfish)"]["path"])

        ok_button = QPushButton('OK')
        ok_button.clicked.connect(self.accept)

        layout.addWidget(self.analyse_skill_level_label)
        layout.addWidget(self.skill_level_edit)

        layout.addWidget(self.analyse_hash_label)
        layout.addWidget(self.hash_edit)

        layout.addWidget(self.analyse_threads_label)
        layout.addWidget(self.threads_edit)

        layout.addWidget(self.analyse_time_label)
        layout.addWidget(self.analyse_time_edit)

        layout.addWidget(self.bot_skill_level_label)
        layout.addWidget(self.bot_skill_level_edit)

        layout.addWidget(self.bot_hash_label)
        layout.addWidget(self.bot_hash_edit)

        layout.addWidget(self.bot_threads_label)
        layout.addWidget(self.bot_threads_edit)

        layout.addWidget(self.bot_move_time_label)
        layout.addWidget(self.bot_move_time_edit)

        layout.addWidget(self.engine_path_label)
        layout.addWidget(self.engine_path_edit)
        layout.addWidget(ok_button)

        self.setLayout(layout)

    def get_settings(self):
        settings = {
            "analyse": {
                "skill level(min=1, max=20)": int(
                    self.skill_level_edit.text() if self.skill_level_edit.text().isdigit() else 20),
                "hash(mb)": int(self.hash_edit.text() if self.hash_edit.text().isdigit() else 1024),
                "threads": int(self.threads_edit.text() if self.threads_edit.text().isdigit() else 128),
                "analyse time": int(self.analyse_time_edit.text() if self.analyse_time_edit.text() else 3)
            },
            "bot": {
                "skill level(min=1, max=20)": int(
                    self.bot_skill_level_edit.text() if self.bot_skill_level_edit.text().isdigit() else 20),
                "hash(mb)": int(self.bot_hash_edit.text() if self.bot_hash_edit.text() else 1024),
                "threads": int(self.bot_threads_edit.text() if self.bot_threads_edit.text().isdigit() else 128),
                "move time": int(self.bot_move_time_edit.text() if self.bot_move_time_edit.text().isdigit() else 3)
            },
            "engine(stockfish)": {
                "path": self.engine_path_edit.text()
            }
        }
        return settings


class ChessBoardEditor(QDialog):
    def __init__(self):
        super(ChessBoardEditor, self).__init__()
        self.setWindowTitle("Chess Board Editor")
        self.setGeometry(100, 100, 600, 600)

        layout = QVBoxLayout()

        self.board_widget = QSvgWidget(self)
        layout.addWidget(self.board_widget)
        layout.setAlignment(self.board_widget, Qt.AlignTop | Qt.AlignLeft)
        self.board_widget.setFixedSize(400, 400)

        self.piece_combo = QComboBox(self)
        self.piece_combo.addItems(
            ["Select a piece", "Pawn", "Rook", "Knight", "Bishop", "Queen", "King", "Remove piece"])
        layout.addWidget(self.piece_combo)

        self.color_combo = QComboBox(self)
        self.color_combo.addItems(["Select a color", "White", "Black"])
        layout.addWidget(self.color_combo)

        self.clear_button = QPushButton("Clear the board", self)
        layout.addWidget(self.clear_button)

        self.preset_combo = QComboBox(self)
        self.preset_combo.addItems(["Standard position", "Romanovsky's move", "Easy checkmate"])
        layout.addWidget(self.preset_combo)

        self.load_preset_button = QPushButton("Load preset", self)
        layout.addWidget(self.load_preset_button)

        self.save_fen_button = QPushButton("Save FEN", self)
        layout.addWidget(self.save_fen_button)

        self.setLayout(layout)

        self.board = chess.Board()
        self.update_board()

        self.clear_button.clicked.connect(self.clear_board)
        self.board_widget.mousePressEvent = self.set_piece
        self.load_preset_button.clicked.connect(self.load_preset)
        self.save_fen_button.clicked.connect(self.save_fen)

    def update_board(self):
        svg = chess.svg.board(self.board)
        self.board_widget.load(svg.encode('utf-8'))

    def clear_board(self):
        self.board.clear()
        self.update_board()

    def set_piece(self, event):
        print(event.x(), event.y())
        square_size = self.board_widget.size().width() // 8
        col = event.pos().x() // square_size
        row = 7 - event.pos().y() // square_size
        piece_text = self.piece_combo.currentText()
        color_text = self.color_combo.currentText()

        if piece_text == "Remove piece":
            self.board.remove_piece_at(chess.parse_square(f"{chr(col + 97)}{row + 1}"))
        elif piece_text != "Select a piece" and color_text != "Select a color":
            piece = {
                "Pawn": chess.PAWN,
                "Rook": chess.ROOK,
                "Knight": chess.KNIGHT,
                "Bishop": chess.BISHOP,
                "Queen": chess.QUEEN,
                "King": chess.KING
            }[piece_text]
            color = chess.WHITE if color_text == "White" else chess.BLACK
            self.board.set_piece_at(chess.parse_square(f"{chr(col + 97)}{row + 1}"), chess.Piece(piece, color))

        self.update_board()

    def load_preset(self):
        preset = self.preset_combo.currentText()
        if preset == "Standard position":
            self.board = chess.Board()
        elif preset == "Romanovsky's move":
            self.board.set_fen("2kr3r/ppp1qppp/2n1p3/2b1P3/2B5/8/PPP2PPP/3QK2R w K - 0 1")
        elif preset == "Easy checkmate":
            self.board.set_fen("4k3/8/8/3R4/8/3K4/8/8 b - - 0 1")

        self.update_board()

    def save_fen(self):
        file_dialog = QFileDialog.getSaveFileName(self, 'Save FEN File', '', 'FEN Files (*.fen)')
        file_path = file_dialog[0]
        if file_path:
            with open(file_path, 'w') as file:
                file.write(self.board.fen())


class ChessboardMainWindow(QMainWindow):
    def __init__(self):
        super(ChessboardMainWindow, self).__init__()
        self.setWindowTitle("Chessboard with PyQt and chess.svg")
        self.setGeometry(100, 100, 418, 620)
        self.setFixedSize(418, 720)
        self.central_widget = ChessboardWidget()
        self.setCentralWidget(self.central_widget)

        menubar = self.menuBar()

        file_menu = menubar.addMenu('load/save FEN')

        new_action = QAction('New', self)
        new_action.triggered.connect(self.central_widget.new_game)
        file_menu.addAction(new_action)

        load_fen_action = QAction('Load FEN', self)
        load_fen_action.triggered.connect(self.central_widget.load_fen)
        file_menu.addAction(load_fen_action)

        save_fen_action = QAction('Save FEN', self)
        save_fen_action.triggered.connect(self.central_widget.save_fen)
        file_menu.addAction(save_fen_action)

        history_menu = menubar.addMenu('load/save game')

        save_game_action = QAction('Save game', self)
        save_game_action.triggered.connect(self.central_widget.save_game)
        history_menu.addAction(save_game_action)

        load_game_action = QAction('load game', self)
        load_game_action.triggered.connect(self.central_widget.load_game)
        history_menu.addAction(load_game_action)

        engine_menu = menubar.addMenu('Engine')

        search_engine_action = QAction('Search for Stockfish', self)
        search_engine_action.triggered.connect(self.search_stockfish)
        engine_menu.addAction(search_engine_action)

        choose_engine_action = QAction('Choose Engine', self)
        choose_engine_action.triggered.connect(self.central_widget.choose_engine)
        engine_menu.addAction(choose_engine_action)

        settings_action = QAction('Settings', self)
        settings_action.triggered.connect(self.show_settings_dialog)
        menubar.addAction(settings_action)

        chess_board_editor_menu = menubar.addMenu('Chess Board Editor')
        chess_board_editor_action = QAction('Chess Board Editor', self)
        chess_board_editor_action.triggered.connect(self.load_chess_board_editor)
        chess_board_editor_menu.addAction(chess_board_editor_action)

    @staticmethod
    def load_chess_board_editor():
        chess_board_editor_dialog = ChessBoardEditor()
        chess_board_editor_dialog.exec_()

    def show_settings_dialog(self):
        settings_dialog = SettingsDialog()
        result = settings_dialog.exec_()
        if result == QDialog.Accepted:
            new_settings = settings_dialog.get_settings()

            json.dump(new_settings, open('settings.json', 'w'))
            if new_settings["engine(stockfish)"]["path"] == "":
                self.search_stockfish()

    @staticmethod
    def search_stockfish():
        stockfish_path = find_exe_file_in_app_root("stockfish")

        if stockfish_path:
            msg = QMessageBox()
            msg.setWindowTitle("Stockfish Found")
            msg.setText(f"Stockfish found at and set:\n{stockfish_path}")
            try:
                with open("settings.json", "r") as f:
                    data = json.load(f)
                data["engine(stockfish)"]["path"] = str(stockfish_path).replace("\\", "/")
                json.dump(data, open("settings.json", "w"))
                f.close()
            except Exception:
                with open("settings.json", "w") as f:
                    data = {"analyse": {"skill level(min=1, max=20)": 20, "hash(mb)": 1024, "threads": 128,
                                        "analyse time": 3000},
                            "bot": {"skill level(min=1, max=20)": 20, "hash(mb)": 1024, "threads": 128,
                                    "move time": 3000}, "engine(stockfish)": {
                            "path": "C:/PYTHON/ChessQT/stockfish/stockfish-windows-x86-64-avx2.exe"}}
                    data["engine(stockfish)"]["path"] = str(stockfish_path).replace("\\", "/")
                    json.dump(data, f)
                f.close()
            msg.exec_()
        else:
            msg = QMessageBox()
            msg.setWindowTitle("Stockfish Not Found")
            msg.setText("Stockfish was not found in the application root or its subfolders.")
            msg.exec()


class ChessPieceDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Choose a Chess Piece')
        layout = QVBoxLayout()

        self.combo_box = QComboBox()
        self.combo_box.addItems(["pawn", "queen", "knight", "rook", "bishop"])
        layout.addWidget(self.combo_box)

        ok_button = QPushButton('OK')
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)

        self.setLayout(layout)


class ChessBoardDialog(QDialog):
    def __init__(self, move_list):
        super().__init__()

        self.setWindowTitle("Chessboard")
        self.setFixedSize(420, 500)

        layout = QVBoxLayout(self)
        self.svgWidget = QSvgWidget(self)
        self.svgWidget.setFixedSize(400, 400)
        layout.addWidget(self.svgWidget)

        control_layout = QHBoxLayout()
        self.control_button = QPushButton("Resume")
        self.control_button.clicked.connect(self.toggle_playback)
        control_layout.addWidget(self.control_button)

        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.play_previous_move)
        control_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.play_next_move)
        control_layout.addWidget(self.next_button)

        layout.addLayout(control_layout)

        self.board = chess.Board()
        try:
            data = json.load(open("set.json", "r"))
        except Exception:
            data = {"last fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "move history": [],
                    "start fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"}
            json.dump(data, open("set.json", "w"))
        self.board.set_fen(data["start fen"])
        self.moves = move_list

        self.move_index = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.play_next_move)
        self.playback_paused = True
        svg = chess.svg.board(board=self.board, size=250)
        self.svgWidget.load(svg.encode('utf-8'))

    def toggle_playback(self):
        if self.playback_paused:
            self.playback_paused = False
            self.control_button.setText("Stop")
            self.timer.start(2000)
        else:
            self.playback_paused = True
            self.control_button.setText("Resume")
            self.timer.stop()

    def play_next_move(self):
        if self.move_index < len(self.moves):
            move = self.moves[self.move_index]
            self.board.push(move)
            check_square = self.board.king(self.board.turn) if self.board.is_check() else None
            svg = chess.svg.board(board=self.board, size=250, lastmove=move, check=check_square)
            self.svgWidget.load(svg.encode('utf-8'))
            self.move_index += 1
        else:
            self.timer.stop()
            self.control_button.setDisabled(True)
            self.next_button.setDisabled(True)

    def play_previous_move(self):
        if self.move_index > 0:
            self.move_index -= 1
            self.board.pop()
            svg = chess.svg.board(board=self.board, size=250)
            self.svgWidget.load(svg.encode('utf-8'))
            self.control_button.setText("Stop")
            self.control_button.setDisabled(False)
            self.next_button.setDisabled(False)


class ChessboardWidget(QWidget):
    def __init__(self):
        super(ChessboardWidget, self).__init__()
        self.bot_playing = False
        self.bot_thread = None
        self.engine_path = "C:/PYTHON/ChessQT/stockfish/stockfish-windows-x86-64-avx2.exe"
        self.bot_side = chess.WHITE
        self.board = chess.Board()
        self.selected_square = None
        self.possible_moves = set()
        self.last_move = None
        self.move_history = []
        self.arrows = []
        self.current_game_id = None
        self.init_ui()
        self.last_analyse_move = None
        self.busy = False
        self.start_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

        try:
            data = json.load(open("set.json", "r"))
            self.board.set_fen(data["start fen"])
            self.move_history = [chess.Move.from_uci(i) for i in data["move history"]]
            for i in self.move_history:
                self.board.push(i)
            for i in data["move history"]:
                item = i
                self.move_list.addItem(item)

        except Exception:
            data = {"last fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "move history": [],
                    "start fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"}
            self.board.set_fen(data["last fen"])
            self.move_history = [chess.Move.from_uci(i) for i in data["move history"]]
        self.update_svg()

    def save_game(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getSaveFileName(self, "Сохранить партию", "",
                                                   "SQLite Database (*.db);;All Files (*)",
                                                   options=options)
        if file_name:
            try:
                conn = sqlite3.connect(file_name)
                cursor = conn.cursor()

                cursor.execute("CREATE TABLE IF NOT EXISTS games (id INTEGER PRIMARY KEY, fen TEXT, moves TEXT)")

                fen = self.board.fen()
                moves = " ".join([str(move) for move in self.move_history])

                cursor.execute("SELECT id FROM games ORDER BY id DESC LIMIT 1")
                row = cursor.fetchone()

                if row:
                    latest_id = row[0]
                    cursor.execute("UPDATE games SET fen = ?, moves = ? WHERE id = ?", (fen, moves, latest_id))
                else:
                    cursor.execute("INSERT INTO games (fen, moves) VALUES (?, ?)", (fen, moves))

                conn.commit()
                conn.close()
            except Exception:
                pass

    def load_game(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "Загрузить партию", "",
                                                   "SQLite Database (*.db);;All Files (*)",
                                                   options=options)
        if file_name:
            try:
                conn = sqlite3.connect(file_name)
                cursor = conn.cursor()

                cursor.execute("SELECT fen, moves FROM games ORDER BY id DESC LIMIT 1")
                row = cursor.fetchone()

                if row:
                    fen, moves_str = row
                    self.board.set_fen(fen)
                    moves = moves_str.split()
                    self.load_game_moves([chess.Move.from_uci(move) for move in moves])
                    self.update_svg()

                conn.close()
            except Exception:
                self.update_svg()

    def save_fen(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getSaveFileName(self, "Save FEN", "", "FEN Files (*.fen);;All Files (*)",
                                                   options=options)
        if file_name:
            try:
                with open(file_name, 'w') as fen_file:
                    fen_file.write(self.board.fen())
            except Exception:
                pass

    def update_last_move(self):
        try:
            with open("set.json", "r") as f:
                data = json.load(f)
            data["last fen"] = str(self.board.fen())
            data["move history"] = [i.uci() for i in self.move_history]
            json.dump(data, open("set.json", "w"))
            f.close()
        except Exception:
            data = {"last fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "move history": [],
                    "start fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"}
            with open("set.json", "w") as f:
                json.dump(data, f)
            f.close()

    def init_ui(self):
        self.setGeometry(10, 10, 600, 600)
        layout = QVBoxLayout(self)
        board_size = 400

        self.svg_widget = QSvgWidget(self)
        self.svg_widget.setFixedSize(board_size, board_size)
        layout.addWidget(self.svg_widget)

        self.move_list = QListWidget(self)
        layout.addWidget(self.move_list)

        undo_button = QPushButton('Undo', self)
        undo_button.clicked.connect(self.undo_move)
        layout.addWidget(undo_button)

        self.tab_widget = QTabWidget(self)
        layout.addWidget(self.tab_widget)

        bot_tab = QWidget()
        bot_tab.layout = QVBoxLayout()

        self.bot_side_combobox = QComboBox()
        self.bot_side_combobox.addItem("Bot as White", chess.WHITE)
        self.bot_side_combobox.addItem("Bot as Black", chess.BLACK)
        bot_tab.layout.addWidget(self.bot_side_combobox)

        self.start_button = QPushButton('Start Bot / Stop Bot', self)
        self.start_button.clicked.connect(self.toggle_bot)
        bot_tab.layout.addWidget(self.start_button)
        bot_tab.setLayout(bot_tab.layout)
        self.tab_widget.addTab(bot_tab, "Bot")

        analysis_tab = QWidget()
        analysis_tab.layout = QVBoxLayout()

        self.analyze_button = QPushButton('Analyze', self)
        self.analyze_button.clicked.connect(self.analyze)
        analysis_tab.layout.addWidget(self.analyze_button)

        self.analysis_textedit = QTextEdit(self)
        self.analysis_textedit.setReadOnly(True)
        analysis_tab.layout.addWidget(self.analysis_textedit)

        analysis_tab.setLayout(analysis_tab.layout)
        self.tab_widget.addTab(analysis_tab, "Analysis")

        self.setMouseTracking(True)

    def toggle_bot(self):
        self.bot_playing = not self.bot_playing
        self.bot_side = self.bot_side_combobox.currentData()
        if self.bot_playing:
            self.bot_thread = BotThread(self.board.copy(), self.bot_side)
            self.bot_thread.move_ready.connect(self.bot_move_ready)
            self.bot_thread.start()
            self.start_button.setDisabled(True)
        else:
            if self.bot_thread:
                self.bot_thread.terminate()
            self.start_button.setDisabled(False)
        self.update_svg()

    def bot_move_ready(self, move):
        self.check_for_checkmate()
        self.update_svg()
        self.clear_arrows()
        self.board.push(move)
        self.add_move_to_list(move.uci())
        self.last_move = move
        self.move_history.append(move)
        self.update_svg()
        self.bot_thread = None
        self.start_button.setDisabled(False)
        self.busy = False

    def update_analyse(self, move):
        for i in range(3):
            if move != self.last_analyse_move:
                self.clear_arrows()
                self.analysis_textedit.append(f"{move}")
                self.arrows.append(svg.Arrow(move.from_square, move.to_square))
            self.last_analyse_move = move
            self.update_svg()
        self.busy = False

    def clear_arrows(self):
        self.arrows = []

    def update_svg(self):
        self.check_for_checkmate()
        board_svg = self.create_custom_svg()
        self.svg_widget.load(board_svg.encode())
        self.update_last_move()

    def create_custom_svg(self):
        custom_svg = svg.board(
            self.board,
            fill=self.get_fill_dict(),
            arrows=self.arrows,
            squares=self.get_square_set(),
            size=400,
            coordinates=True,
            check=self.board.king(self.board.turn) if self.board.is_check() else None
        )
        return custom_svg

    def get_fill_dict(self):
        fill_dict = {}
        if self.selected_square is not None:
            fill_dict[self.selected_square] = "#ffa50077"
            for square in self.possible_moves:
                fill_dict[square] = "#ff000044"
        if self.last_move is not None:
            fill_dict[self.last_move.from_square] = "#00ff0077"
            fill_dict[self.last_move.to_square] = "#00ff0077"
        return fill_dict

    @staticmethod
    def get_square_set():
        square_set = chess.SquareSet()
        return square_set

    def mousePressEvent(self, event):
        if not self.busy:
            if event.button() == Qt.LeftButton:
                if 24 <= event.x() <= 392 and 24 <= event.y() <= 392:
                    corrected_x = event.x() - 24
                    corrected_y = event.y() - 24
                    col = corrected_x * 8 // (392 - 24) if corrected_x * 8 // (392 - 24) <= 7 else 7
                    row = 7 - corrected_y * 8 // (392 - 24) if 7 - corrected_y * 8 // (392 - 24) <= 7 else 7

                    square = chess.square(col, row)
                    self.update_svg()

                    if self.selected_square is None:
                        piece = self.board.piece_at(square)

                        if piece is not None and piece.color == self.board.turn:
                            self.selected_square = square
                            self.possible_moves = self.get_possible_moves(square)
                        else:
                            self.selected_square = None
                            self.possible_moves.clear()
                        self.update_svg()
                    else:
                        move = chess.Move(self.selected_square, square)

                        prom_move = chess.Move(self.selected_square, square, promotion=chess.QUEEN)
                        if prom_move in self.board.legal_moves:
                            dialog = ChessPieceDialog()
                            result = dialog.exec_()
                            if result == QDialog.Accepted:
                                selected_piece = dialog.combo_box.currentText()
                                if selected_piece == "queen":
                                    selected_piece = chess.QUEEN
                                if selected_piece == "knight":
                                    selected_piece = chess.KNIGHT
                                if selected_piece == "rook":
                                    selected_piece = chess.ROOK
                                if selected_piece == "bishop":
                                    selected_piece = chess.BISHOP
                                prom_move = chess.Move(self.selected_square, square, promotion=selected_piece)
                                self.board.push(prom_move)
                        elif move in self.board.legal_moves:
                            if (self.board.turn == chess.WHITE and self.board.piece_at(
                                    move.from_square) == chess.PAWN and
                                    move.from_uci()[1] == '7' or
                                    self.board.turn == chess.BLACK and self.board.piece_at(
                                        move.from_square) == chess.PAWN and
                                    move.from_uci()[1] == '2'):
                                self.board.push(chess.Move(self.selected_square, square, promotion=chess.QUEEN))
                            else:
                                self.board.push(move)
                            self.clear_arrows()
                            self.update_svg()
                            self.add_move_to_list(move.uci())
                            print(move)
                            self.last_move = move
                            self.move_history.append(move)
                            if self.bot_playing:
                                self.bot_side = self.bot_side_combobox.currentData()
                                self.bot_thread = BotThread(self.board.copy(), self.bot_side)
                                self.bot_thread.move_ready.connect(self.bot_move_ready)
                                self.bot_thread.start()
                                self.busy = True
                            self.analysis_textedit.clear()
                        self.selected_square = None
                        self.possible_moves.clear()
                        self.update_svg()

    def undo_move(self):
        try:
            if self.move_history:
                self.board.pop()
                self.clear_arrows()

                self.last_move = None
                self.update_svg()
                self.clear_move_list()
                self.update_last_move()
        except Exception:
            pass

    def clear_move_list(self):
        self.move_list.clear()
        for move in self.board.move_stack:
            self.add_move_to_list(move.uci())
        self.update_last_move()

    def get_possible_moves(self, square):
        legal_moves = self.board.legal_moves
        return set(move.to_square for move in legal_moves if move.from_square == square)

    def add_move_to_list(self, move):
        move_text = move
        item = QListWidgetItem(move_text)

        self.move_list.addItem(item)
        self.update_last_move()

    @staticmethod
    def piece_to_text(piece):
        if piece is not None:
            if piece.symbol() == 'P':
                return 'Pawn'
            if piece.symbol() == 'N':
                return 'Knight'
            if piece.symbol() == 'B':
                return 'Bishop'
            if piece.symbol() == 'R':
                return 'Rook'
            if piece.symbol() == 'Q':
                return 'Queen'
            if piece.symbol() == 'K':
                return 'King'
        return ''

    def new_game(self):
        self.board.reset()
        self.selected_square = None
        self.possible_moves.clear()
        self.last_move = None
        self.move_history = []
        self.clear_arrows()
        self.update_svg()
        self.clear_move_list()
        self.current_game_id = None

    def analyze(self):
        currnt_board = self.board
        self.clear_arrows()
        try:
            self.analyze_thread = AnalyzeThread(currnt_board)
            self.analyze_thread.analyze_ready.connect(self.update_analyse)
            self.analyze_thread.start()
            self.busy = True
        except Exception:
            pass
        self.update_svg()

    def check_for_checkmate(self):
        if self.board.is_checkmate():
            winner = "White" if self.board.turn == chess.BLACK else "Black"
            msg = QMessageBox()
            msg.setWindowTitle("Game Over")
            msg.setText(f"Checkmate! {winner} wins!")
            msg.exec_()
            dialog = ChessBoardDialog(self.move_history)
            dialog.exec_()

    def load_game_moves(self, moves):
        self.board.reset()

        self.selected_square = None
        self.possible_moves.clear()
        self.last_move = None
        self.move_history = []
        self.clear_arrows()
        try:
            data = json.load(open("set.json", "r"))
            self.board.set_fen(data["start fen"])
        except Exception:
            data = {"last fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "move history": [],
                    "start fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"}
            json.dump(data, open("set.json", "w"))
            self.board.set_fen(data["start fen"])
        for move in moves:
            self.board.push(move)
            self.add_move_to_list(move.uci())
            self.last_move = move
            self.move_history.append(move)

        self.update_svg()

    def load_fen(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "Load FEN", "", "FEN Files (*.fen);;All Files (*)",
                                                   options=options)
        if file_name:
            with open(file_name, 'r') as fen_file:
                fen = fen_file.read()
                self.board.set_fen(fen)
                self.load_game_moves(self.board.move_stack)
                self.board.set_fen(fen)
                self.update_svg()
                self.clear_move_list()
                try:
                    data = json.load(open("set.json", "r"))
                    data["start fen"] = fen
                    json.dump(data, open("set.json", "w"))
                except Exception:
                    try:
                        data = {"last fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                                "move history": [],
                                "start fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"}
                        json.dump(data, open("set.json", "w"))
                    except Exception:
                        pass

    def choose_engine(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        engine_path, _ = QFileDialog.getOpenFileName(self, "Choose Engine", "",
                                                     "Executable Files (*.exe);;All Files (*)",
                                                     options=options)
        if engine_path:
            self.engine_path = engine_path
            try:
                with open("settings.json", "r") as f:
                    data = json.load(f)
                data["engine(stockfish)"]["path"] = str(engine_path)
                json.dump(data, open("settings.json", "w"))
                f.close()
            except Exception:
                with open("settings.json", "w") as f:
                    data = {"analyse": {"skill level(min=1, max=20)": 20, "hash(mb)": 1024, "threads": 128,
                                        "analyse time": 3000},
                            "bot": {"skill level(min=1, max=20)": 20, "hash(mb)": 1024, "threads": 128,
                                    "move time": 3000}, "engine(stockfish)": {
                            "path": "C:/PYTHON/ChessQT/stockfish/stockfish-windows-x86-64-avx2.exe"}}
                data["engine(stockfish)"]["path"] = str(engine_path)
                f.close()
                json.dump(data, open("settings.json", "w"))

            self.update_svg()


class BotThread(QThread):
    move_ready = pyqtSignal(chess.Move)

    def __init__(self, board, bot_side):
        super(BotThread, self).__init__()
        self.board = board

        self.bot_side = bot_side
        self.bot_depth = 32
        self.bot_time = 5000
        self.running = True
        self.data = None
        try:
            self.data = json.load(open("settings.json", "r"))
        except Exception:
            self.data = {
                "analyse": {"skill level(min=1, max=20)": 20, "hash(mb)": 1024, "threads": 128, "analyse time": 3000},
                "bot": {"skill level(min=1, max=20)": 20, "hash(mb)": 1024, "threads": 128, "move time": 3000},
                "engine(stockfish)": {"path": find_exe_file_in_app_root("stockfish")}}
        self.engine_path = self.data["engine(stockfish)"]["path"]

    def stop(self):
        self.running = False

    def run(self):
        if self.bot_side == self.board.turn:
            try:
                stockfish_process = subprocess.Popen(
                    [self.engine_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    shell=True,
                )

                stockfish_process.stdin.write("uci\n")
                stockfish_process.stdin.write(
                    f"setoption name Skill Level value {self.data['bot']['skill level(min=1, max=20)']}\n")
                stockfish_process.stdin.write(f"setoption name hash value {self.data['bot']['hash(mb)']}\n")
                stockfish_process.stdin.write(f"setoption name threads value {self.data['bot']['threads']}\n")
                stockfish_process.stdin.write(f"position fen {self.board.fen()}\n")
                stockfish_process.stdin.write(f"go movetime {self.data['bot']['move time']}\n")

                stockfish_process.stdin.flush()

                result = None
                for line in stockfish_process.stdout:
                    if line.startswith("bestmove"):
                        result = chess.Move.from_uci(line.split()[1])
                        break

                stockfish_process.kill()
                if result:
                    self.move_ready.emit(result)
            except Exception:
                pass


class AnalyzeThread(QThread):
    analyze_ready = pyqtSignal(chess.Move)

    def __init__(self, board):
        super(AnalyzeThread, self).__init__()
        self.board = board

        self.analysis_depth = 20
        self.analysis_time = 6000
        self.data = None
        try:
            self.data = json.load(open("settings.json", "r"))
        except Exception:
            self.data = {
                "analyse": {"skill level(min=1, max=20)": 20, "hash(mb)": 1024, "threads": 128, "analyse time": 3000},
                "bot": {"skill level(min=1, max=20)": 20, "hash(mb)": 1024, "threads": 128, "move time": 3000},
                "engine(stockfish)": {"path": find_exe_file_in_app_root("stockfish")}}

        self.engine_path = self.data["engine(stockfish)"]["path"]

    def run(self):
        try:
            stockfish_process = subprocess.Popen(
                [self.engine_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                shell=True,
            )
            stockfish_process.stdin.write("uci\n")
            stockfish_process.stdin.write(
                f"setoption name Skill Level value {self.data['analyse']['skill level(min=1, max=20)']}\n")
            stockfish_process.stdin.write(f"setoption name hash value {self.data['analyse']['hash(mb)']}\n")
            stockfish_process.stdin.write(f"setoption name threads value {self.data['analyse']['threads']}\n")
            stockfish_process.stdin.write(f"position fen {self.board.fen()}\n")
            stockfish_process.stdin.write(f"go movetime {self.data['analyse']['analyse time']}\n")
            info = []
            stockfish_process.stdin.flush()
            for line in stockfish_process.stdout:
                if line.startswith("info"):
                    if "pv" in line:
                        ind = line.index(" pv ")
                        info.append(chess.Move.from_uci(line[ind + 4: ind + 8]))
                        self.analyze_ready.emit(chess.Move.from_uci(line[ind + 4: ind + 8]))
                if line.startswith("bestmove"):
                    line = line.split()
                    info.append(chess.Move.from_uci(line[1]))
            stockfish_process.kill()
        except Exception:
            pass


if __name__ == '__main__':
    app = ChessboardApp(sys.argv)
    sys.exit(app.exec_())
