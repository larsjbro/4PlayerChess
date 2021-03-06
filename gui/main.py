#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of the Four-Player Chess project, a four-player chess GUI.
#
# Copyright (C) 2018, GammaDeltaII
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from PyQt5.QtWidgets import QWidget, QMainWindow, QSizePolicy, QLayout, QListWidget, QListWidgetItem, QListView, \
    QFrame, QAbstractItemView, QFileDialog, QPushButton, QLineEdit
from PyQt5.QtCore import Qt, QObject, QSize, QRect, QPoint, pyqtSignal, QEvent
from PyQt5.QtGui import QPainter, QPalette, QIcon, QColor, QFont, QFontMetrics
from collections import deque
from datetime import date
from ui.mainwindow import Ui_mainWindow


class MainWindow(QMainWindow, Ui_mainWindow):
    """The GUI main window."""
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Create view and algorithm instances
        self.view = View()
        self.gridLayout.addWidget(self.view, 0, 0, 3, 1)
        self.algorithm = Teams()

        # Set piece icons
        pieces = ['rP', 'rN', 'rR', 'rB', 'rQ', 'rK',
                  'bP', 'bN', 'bR', 'bB', 'bQ', 'bK',
                  'yP', 'yN', 'yR', 'yB', 'yQ', 'yK',
                  'gP', 'gN', 'gR', 'gB', 'gQ', 'gK']
        for piece in pieces:
            self.view.setPiece(piece, QIcon('resources/img/pieces/'+piece+'.svg'))

        # Set view size based on board square size
        self.view.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.view.setSquareSize(QSize(50, 50))
        self.layout().setSizeConstraint(QLayout.SetFixedSize)

        # Connect signals
        self.view.clicked.connect(self.viewClicked)
        self.algorithm.boardChanged.connect(self.view.setBoard)  # If algorithm changes board, view must update board
        self.algorithm.currentPlayerChanged.connect(self.view.highlightPlayer)
        self.algorithm.fen4Generated.connect(self.fenField.setPlainText)
        self.algorithm.pgn4Generated.connect(self.pgnField.setPlainText)
        self.algorithm.moveTreeChanged.connect(self.updateMoveTree)
        self.algorithm.moveTreeChanged.connect(self.algorithm.updateMoves)
        self.algorithm.removeHighlight.connect(self.view.removeHighlightsOfColor)
        self.view.playerNameEdited.connect(self.algorithm.updatePlayerNames)
        self.algorithm.addHighlight.connect(self.addHighlight)

        # Connect actions
        self.actionQuit.triggered.connect(self.close)
        self.actionNew_Game.triggered.connect(self.algorithm.newGame)
        self.actionNew_Game.triggered.connect(self.moveListWidget.clear)
        self.actionCopy_FEN4.triggered.connect(self.fenField.selectAll)
        self.actionCopy_FEN4.triggered.connect(self.fenField.copy)
        self.actionPaste_FEN4.triggered.connect(self.fenField.clear)
        self.actionPaste_FEN4.triggered.connect(self.fenField.paste)

        self.boardResetButton.clicked.connect(self.algorithm.newGame)
        self.boardResetButton.clicked.connect(self.view.repaint)  # Forced repaint
        self.boardResetButton.clicked.connect(self.moveListWidget.clear)
        self.boardResetButton.clicked.connect(self.resetMoves)
        self.getFenButton.clicked.connect(self.algorithm.getBoardState)
        self.getFenButton.clicked.connect(self.fenField.repaint)
        self.setFenButton.clicked.connect(self.setFen4)
        self.getPgnButton.clicked.connect(self.algorithm.getPgn4)
        self.savePgnButton.clicked.connect(self.saveFileDialog)
        self.prevMoveButton.clicked.connect(self.algorithm.prevMove)
        self.prevMoveButton.clicked.connect(self.view.repaint)
        self.nextMoveButton.clicked.connect(self.algorithm.nextMove)
        self.nextMoveButton.clicked.connect(self.view.repaint)
        self.firstMoveButton.clicked.connect(self.algorithm.firstMove)
        self.firstMoveButton.clicked.connect(self.view.repaint)
        self.lastMoveButton.clicked.connect(self.algorithm.lastMove)
        self.lastMoveButton.clicked.connect(self.view.repaint)

        # Start new game
        self.algorithm.newGame()

        # Initialize variables
        self.clickPoint = QPoint()
        self.selectedSquare = 0
        self.moveHighlight = 0
        self.moves = []

    def resetMoves(self):
        """Clears the list of moves if the board is reset."""
        self.moves = []

    def addHighlight(self, fromFile, fromRank, toFile, toRank, color):
        fromSquare = self.view.SquareHighlight(fromFile, fromRank, color)
        self.view.addHighlight(fromSquare)
        toSquare = self.view.SquareHighlight(toFile, toRank, color)
        self.view.addHighlight(toSquare)

    def viewClicked(self, square):
        """Handles user click event to move clicked piece to clicked square."""
        if self.algorithm.currentPlayer == self.algorithm.Red:
            color = QColor('#66bf3b43')
        elif self.algorithm.currentPlayer == self.algorithm.Blue:
            color = QColor('#664185bf')
        elif self.algorithm.currentPlayer == self.algorithm.Yellow:
            color = QColor('#66c09526')
        elif self.algorithm.currentPlayer == self.algorithm.Green:
            color = QColor('#664e9161')
        else:
            color = QColor('#00000000')
        if self.clickPoint.isNull():
            squareData = self.view.board.getData(square.x(), square.y())
            if squareData != ' ' and squareData[0] == self.algorithm.currentPlayer:
                self.clickPoint = square
                self.selectedSquare = self.view.SquareHighlight(square.x(), square.y(), color)
                self.view.addHighlight(self.selectedSquare)
        else:
            moved = False
            if square != self.clickPoint:
                moved = self.algorithm.makeMove(self.clickPoint.x(), self.clickPoint.y(), square.x(), square.y())
            self.clickPoint = QPoint()
            if not moved:
                self.view.removeHighlight(self.selectedSquare)
            else:
                self.moveHighlight = self.view.SquareHighlight(square.x(), square.y(), color)
                self.view.addHighlight(self.moveHighlight)
                # Remove highlights of next player
                if self.algorithm.currentPlayer == self.algorithm.Red:
                    color = QColor('#66bf3b43')
                elif self.algorithm.currentPlayer == self.algorithm.Blue:
                    color = QColor('#664185bf')
                elif self.algorithm.currentPlayer == self.algorithm.Yellow:
                    color = QColor('#66c09526')
                elif self.algorithm.currentPlayer == self.algorithm.Green:
                    color = QColor('#664e9161')
                else:
                    color = QColor('#00000000')
                self.view.removeHighlightsOfColor(color)
                self.moveHighlight = 0
            self.selectedSquare = 0

    def keyPressEvent(self, event):
        """Handles arrow key press events to go to previous, next, first or last move."""
        if event.key() == Qt.Key_Left:
            self.algorithm.prevMove()
        if event.key() == Qt.Key_Right:
            self.algorithm.nextMove()
        if event.key() == Qt.Key_Up:
            self.algorithm.firstMove()
        if event.key() == Qt.Key_Down:
            self.algorithm.lastMove()

    def saveFileDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        # noinspection PyTypeChecker,PyCallByClass
        fileName, _ = QFileDialog.getSaveFileName(self, "Save Game", "data/games/",
                                                  "PGN4 Files (*.pgn4)", options=options)
        if fileName:
            with open(fileName + '.pgn4', 'w') as file:
                pgn4 = self.pgnField.toPlainText()
                file.writelines(pgn4)

    def setFen4(self):
        """Gets FEN4 from the text field to set the board accordingly."""
        fen4 = self.fenField.toPlainText()
        self.algorithm.setBoardState(fen4)
        self.view.repaint()  # Forced repaint

    def updateMoveTree(self, node):
        """Constructs the move list based on the move tree."""
        # Custom QListWidget class for rows in main list
        class Row(QListWidget):
            def __init__(self):
                super().__init__()
                self.setFlow(QListView.LeftToRight)
                self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.setWrapping(True)
                self.setFrameShape(QFrame.NoFrame)
                self.setSelectionMode(QAbstractItemView.NoSelection)
                self.setFocusPolicy(Qt.NoFocus)
                self.setStyleSheet("color: rgb(0, 0, 0); font-family: Arial; font-weight: bold; font-size: 12; "
                                   "padding: 2px; margin: 0px;")

            def sizeHint(self):
                """Overrides sizeHint() method."""
                fm = QFontMetrics(QFont('Arial', 12))  # 12pt = 16px
                spacing = 17  # Guess
                rowWidth = sum(fm.width(self.item(index).text()) + spacing for index in range(self.count()))
                width = 295
                height = 22 * (rowWidth // width + 1)
                return QSize(width, height)

        # List moves with move number and variation root and number (tuple), i.e. [(moveNum, move, rootNum, root, var)]
        moves = self.traverse(node, self.moves)
        self.moves = moves
        self.moveListWidget.clear()
        mainLineRoot = (0, 'root')
        mainline = [move[:2] for move in moves if move[-3:] == (mainLineRoot[0], mainLineRoot[1], 0)]
        prevVar = 0
        prevRoot = mainLineRoot
        roots = [prevRoot]
        row = Row()
        for move in moves:
            root = move[-3:-1]
            var = move[-1]
            # Same variation root
            if root == prevRoot:
                # Same variation number
                if var == prevVar:
                    flag = (move[0] - 1) % 4
                    if flag == 0:
                        moveNum = str((move[0] - 1) // 4 + 1) + '. '
                    else:
                        moveNum = ''
                    if root == mainLineRoot and var == 0:
                        sep = ' '
                    else:
                        # Remove closing bracket from previous move, if present
                        if row.item(row.count() - 1).text()[-2] == ')':
                            row.item(row.count() - 1).setText(row.item(row.count() - 1).text()[:-2] + ' ')
                        sep = ') '
                    moveItem = QListWidgetItem(moveNum + move[1] + sep)
                    row.addItem(moveItem)
                # Higher variation number = new variation from same root
                elif var > prevVar:
                    item = QListWidgetItem(self.moveListWidget)
                    item.setSizeHint(row.sizeHint())
                    self.moveListWidget.addItem(item)
                    self.moveListWidget.setItemWidget(item, row)
                    # Start of variation -> prepend opening bracket and add 1, 2 or 3 dots, depending on current player
                    flag = ((move[0] - 1) % 4)
                    if flag == 0:  # Red's move
                        moveNum = str((move[0] - 1) // 4 + 1) + '. '
                    elif flag == 1:  # Blue's move, add one dot
                        moveNum = str((move[0] - 1) // 4 + 1) + '. . '
                    elif flag == 2:  # Yellow's move, add two dots
                        moveNum = str((move[0] - 1) // 4 + 1) + '. .. '
                    else:  # Green's move, add three dots
                        moveNum = str((move[0] - 1) // 4 + 1) + '. ... '
                    if root == mainLineRoot and var == 0:
                        sep = ' '
                    else:
                        sep = ') '
                    moveItem = QListWidgetItem('(' + moveNum + move[1] + sep)
                    row = Row()
                    if root in mainline or root == mainLineRoot:
                        row.setStyleSheet("color: rgb(100, 100, 100); font-weight: bold; font-size: 12; "
                                          "background-color: rgb(240, 240, 240); padding: 2px; margin: 0px;")
                    else:
                        row.setStyleSheet("color: rgb(150, 150, 150); font-weight: bold; font-size: 12; "
                                          "background-color: rgb(240, 240, 240); padding: 2px; margin: 0px;")
                    row.addItem(moveItem)
                # Lower variation number = returning to previous variation with same root
                elif var < prevVar:
                    item = QListWidgetItem(self.moveListWidget)
                    item.setSizeHint(row.sizeHint())
                    self.moveListWidget.addItem(item)
                    self.moveListWidget.setItemWidget(item, row)
                    flag = ((move[0] - 1) % 4 == 0)
                    if flag:
                        moveNum = str((move[0] - 1) // 4 + 1) + '. '
                    else:
                        moveNum = ''
                    if root == mainLineRoot and var == 0:
                        sep = ' '
                    else:
                        sep = ') '
                    moveItem = QListWidgetItem(moveNum + move[1] + sep)
                    row = Row()
                    if root == mainLineRoot:
                        pass
                    elif root in mainline:
                        row.setStyleSheet("color: rgb(100, 100, 100); font-weight: bold; font-size: 12; "
                                          "background-color: rgb(240, 240, 240); padding: 2px; margin: 0px;")
                    else:
                        row.setStyleSheet("color: rgb(150, 150, 150); font-weight: bold; font-size: 12; "
                                          "background-color: rgb(240, 240, 240); padding: 2px; margin: 0px;")
                    row.addItem(moveItem)
            # Different variation root
            else:
                if root not in roots:
                    roots.append(root)
                    roots.sort()
                # If variation root has higher move number than previous, start new variation
                if root[0] > prevRoot[0]:
                    # Remove closing bracket from previous move, if present
                    if row.item(row.count() - 1).text()[-2] == ')':
                        row.item(row.count() - 1).setText(row.item(row.count() - 1).text()[:-2] + ' ')
                    item = QListWidgetItem(self.moveListWidget)
                    item.setSizeHint(row.sizeHint())
                    self.moveListWidget.addItem(item)
                    self.moveListWidget.setItemWidget(item, row)
                    # Start of variation -> prepend opening bracket and add 1, 2 or 3 dots, depending on current player
                    flag = ((move[0] - 1) % 4)
                    if flag == 0:  # Red's move
                        moveNum = str((move[0] - 1) // 4 + 1) + '. '
                    elif flag == 1:  # Blue's move, add one dot
                        moveNum = str((move[0] - 1) // 4 + 1) + '. . '
                    elif flag == 2:  # Yellow's move, add two dots
                        moveNum = str((move[0] - 1) // 4 + 1) + '. .. '
                    else:  # Green's move, add three dots
                        moveNum = str((move[0] - 1) // 4 + 1) + '. ... '
                    moveItem = QListWidgetItem('(' + moveNum + move[1] + ') ')
                    row = Row()
                    if root in mainline:
                        row.setStyleSheet("color: rgb(100, 100, 100); font-weight: bold; font-size: 12; "
                                          "background-color: rgb(240, 240, 240); padding: 2px; margin: 0px;")
                    else:
                        row.setStyleSheet("color: rgb(150, 150, 150); font-weight: bold; font-size: 12; "
                                          "background-color: rgb(240, 240, 240); padding: 2px; margin: 0px;")
                    row.addItem(moveItem)
                # If variation root has lower move number than previous, return to previous variation
                else:
                    # Add closing bracket(s) if moving out of multiple variations
                    step = roots.index(prevRoot) - roots.index(root)
                    if step > 1 and roots.index(root) != 0:
                        row.item(row.count() - 1).setText(row.item(row.count() - 1).text()[:-1] + ')'*(step - 1) + ' ')
                    item = QListWidgetItem(self.moveListWidget)
                    item.setSizeHint(row.sizeHint())
                    self.moveListWidget.addItem(item)
                    self.moveListWidget.setItemWidget(item, row)
                    flag = ((move[0] - 1) % 4 == 0)
                    if flag:
                        moveNum = str((move[0] - 1) // 4 + 1) + '. '
                    else:
                        moveNum = ''
                    if root == mainLineRoot and var == 0:
                        sep = ' '
                    else:
                        sep = ') '
                    moveItem = QListWidgetItem(moveNum + move[1] + sep)
                    row = Row()
                    if root == mainLineRoot:
                        pass
                    elif root in mainline:
                        row.setStyleSheet("color: rgb(100, 100, 100); font-weight: bold; font-size: 12; "
                                          "background-color: rgb(240, 240, 240); padding: 2px; margin: 0px;")
                    else:
                        row.setStyleSheet("color: rgb(150, 150, 150); font-weight: bold; font-size: 12; "
                                          "background-color: rgb(240, 240, 240); padding: 2px; margin: 0px;")
                    row.addItem(moveItem)
                prevRoot = root
            prevVar = var
        # End of move list -> append rest of main line moves
        item = QListWidgetItem(self.moveListWidget)
        item.setSizeHint(row.sizeHint())
        self.moveListWidget.addItem(item)
        self.moveListWidget.setItemWidget(item, row)

    def traverse(self, node, moves=None, moveNum=0, rootNum=0, root=None, var=0, rootNode=None):
        """Traverses move tree to create list of moves, sorted by move number and variation (incl. variation root)."""
        # The tree is represented as a nested list with move strings, i.e. node = ['parent', [children]]
        parent = node[0]
        if not root:
            root = parent
        if not rootNode:
            rootNode = node
        if not moves:
            moves = self.moves
        children = node[1]
        if children:
            for child in children:
                self.traverse(child, moves, moveNum + 1, rootNum, root, var, rootNode)
                var += 1
                # Root should be first element of previous level -> go back to previous node with multiple children
                root = parent  # FIXME root of variation is not necessarily previous move
                rootNum = moveNum
        elif not moves.count((moveNum, parent, rootNum, root, var)):
            moves.append((moveNum, parent, rootNum, root, var))
        # Sort moves: insert variations after the main move
        prevVars = []
        i = 0
        while i < len(moves):
            varMoves = [var for var in moves if var[-2] == moves[i][1]]
            varMoves = sorted(varMoves, key=lambda element: (element[-1], element[0]))
            if prevVars:
                shift = 2 + len(prevVars)
            else:
                shift = 2
            moves = moves[:i+shift] + varMoves + moves[i+shift:]
            # Remove duplicate elements from the back
            moves.reverse()
            for move in moves:
                while moves.count(move) > 1:
                    moves.remove(move)
            moves.reverse()
            prevVars = varMoves
            i += 1
        return moves


class Board(QObject):
    """The Board is the actual chess board and is the data structure shared between the View and the Algorithm."""
    boardReset = pyqtSignal()
    dataChanged = pyqtSignal(int, int)

    def __init__(self, files, ranks):
        super().__init__()
        self.files = files
        self.ranks = ranks
        self.boardData = []
        self.initBoard()

    def initBoard(self):
        """Initializes board with empty squares."""
        self.boardData = [' '] * self.files * self.ranks
        self.boardReset.emit()

    def getData(self, file, rank):
        """Gets board data from square (file, rank)."""
        return self.boardData[file+rank*self.files]

    def setData(self, file, rank, data):
        """Sets board data at square (file, rank) to data."""
        index = file+rank*self.files
        if self.boardData[index] == data:
            return
        self.boardData[index] = data
        self.dataChanged.emit(file, rank)

    def movePiece(self, fromFile, fromRank, toFile, toRank):
        """Moves piece from square (fromFile, fromRank) to square (toFile, toRank)."""
        self.setData(toFile, toRank, self.getData(fromFile, fromRank))
        self.setData(fromFile, fromRank, ' ')

    def setFen4(self, fen4):
        """Sets board position according to the FEN4 string fen4."""
        index = 0
        skip = 0
        for rank in reversed(range(self.ranks)):
            for file in range(self.files):
                if skip > 0:
                    char = ' '
                    skip -= 1
                else:
                    # Pieces are always two characters, skip value can be single or double digit
                    char = fen4[index]
                    index += 1
                    if char.isdigit():
                        # Check if next is also digit. If yes, treat as single number
                        next_ = fen4[index]
                        if next_.isdigit():
                            char += next_
                            index += 1
                        skip = int(char)
                        char = ' '
                        skip -= 1
                    # If not digit, then it is a two-character piece. Add next character
                    else:
                        char += fen4[index]
                        index += 1
                self.setData(file, rank, char)
            next_ = fen4[index]
            if next_ != '/' and next_ != ' ':
                # If no slash or space after rank, the FEN4 is invalid, so reset board
                self.initBoard()
                return
            else:  # Skip the slash
                index += 1
        self.boardReset.emit()

    def getFen4(self):
        """Generates FEN4 from current board state."""
        fen4 = ''
        skip = 0
        prev = ' '
        for rank in reversed(range(self.ranks)):
            for file in range(self.files):
                char = self.getData(file, rank)
                # If current square is empty, increment skip value
                if char == ' ':
                    skip += 1
                    prev = char
                else:
                    # If current square is not empty, but previous square was empty, append skip value to FEN4 string,
                    # unless the previous square was on the previous rank
                    if prev == ' ' and file != 0:
                        fen4 += str(skip)
                        skip = 0
                    # Append algebraic piece name to FEN4 string
                    fen4 += char
                    prev = char
            # If skip is non-zero at end of rank, append skip and reset to zero
            if skip > 0:
                fen4 += str(skip)
                skip = 0
            # Append slash at end of rank and append space after last rank
            if rank == 0:
                fen4 += ' '
            else:
                fen4 += '/'
        return fen4


class Algorithm(QObject):
    """The Algorithm is the underlying logic responsible for changing the current state of the board."""
    boardChanged = pyqtSignal(Board)
    gameOver = pyqtSignal(str)
    currentPlayerChanged = pyqtSignal(str)
    fen4Generated = pyqtSignal(str)
    pgn4Generated = pyqtSignal(str)
    moveTreeChanged = pyqtSignal(list)
    removeHighlight = pyqtSignal(QColor)
    addHighlight = pyqtSignal(int, int, int, int, QColor)

    NoResult, Team1Wins, Team2Wins, Draw = ['*', '1-0', '0-1', '1/2-1/2']  # Results
    NoPlayer, Red, Blue, Yellow, Green = ['?', 'r', 'b', 'y', 'g']  # Players
    playerQueue = deque([Red, Blue, Yellow, Green])

    def __init__(self):
        super().__init__()
        self.variant = '?'
        self.board = Board(14, 14)
        self.result = self.NoResult
        self.currentPlayer = self.NoPlayer
        self.moveNumber = 0
        self.currentMove = self.Node('root', [], None)
        self.moves = []
        self.redName = self.NoPlayer
        self.blueName = self.NoPlayer
        self.yellowName = self.NoPlayer
        self.greenName = self.NoPlayer

    class Node:
        """Generic node class. Basic element of a tree."""
        def __init__(self, name, children, parent):
            self.name = name
            self.children = children
            self.parent = parent

        def add(self, node):
            """Adds node to children."""
            self.children.append(node)

        def pop(self):
            """Removes last child from node."""
            self.children.pop()

        def getRoot(self):
            """Backtracks tree and returns root node."""
            if self.parent is None:
                return self
            return self.parent.getRoot()

        def getTree(self):
            """Returns the (sub)tree starting from the current node."""
            tree = [self.name, [child.getTree() for child in self.children]]
            return tree

    def updatePlayerNames(self, red, blue, yellow, green):
        self.redName = red if not (red == 'Player Name' or red == '') else '?'
        self.blueName = blue if not (blue == 'Player Name' or blue == '') else '?'
        self.yellowName = yellow if not (yellow == 'Player Name' or yellow == '') else '?'
        self.greenName = green if not (green == 'Player Name' or green == '') else '?'

    def resetMoves(self):
        """Resets current move to root and move number to zero."""
        self.moveNumber = 0
        self.currentMove = self.Node('root', [], None)
        self.moves = []

    def setResult(self, value):
        """Updates game result, if changed."""
        if self.result == value:
            return
        if self.result == self.NoResult:
            self.result = value
            self.gameOver.emit(self.result)
        else:
            self.result = value

    def setCurrentPlayer(self, value):
        """Updates current player, if changed."""
        if self.currentPlayer == value:
            return
        self.currentPlayer = value
        self.setPlayerQueue(self.currentPlayer)
        self.currentPlayerChanged.emit(self.currentPlayer)

    def setPlayerQueue(self, currentPlayer):
        """Rotates player queue such that the current player is the first in the queue."""
        while self.playerQueue[0] != currentPlayer:
            self.playerQueue.rotate(-1)

    def setBoard(self, board):
        """Updates board, if changed."""
        if self.board == board:
            return
        self.board = board
        self.boardChanged.emit(self.board)

    def setupBoard(self):
        """Initializes board."""
        self.setBoard(Board(14, 14))

    def newGame(self):
        """Initializes board and sets starting position."""
        self.setupBoard()
        # Set starting position from FEN4
        self.board.setFen4('3yRyNyByKyQyByNyR3/3yPyPyPyPyPyPyPyP3/14/bRbP10gPgR/bNbP10gPgN/bBbP10gPgB/bKbP10gPgQ/'
                           'bQbP10gPgK/bBbP10gPgB/bNbP10gPgN/bRbP10gPgR/14/3rPrPrPrPrPrPrPrP3/3rRrNrBrQrKrBrNrR3 '
                           'r rKrQbKbQyKyQgKgQ - 0 1')
        self.setResult(self.NoResult)
        self.setCurrentPlayer(self.Red)
        self.setPlayerQueue(self.currentPlayer)
        self.resetMoves()

    def getBoardState(self):
        """Gets FEN4 from current board state."""
        fen4 = self.board.getFen4()
        # Append character for current player
        fen4 += self.currentPlayer + ' '
        # TODO implement castling availability and en passant target square
        fen4 += '- '  # "K" if kingside castling available, "Q" if queenside, "-" if no player can castle
        fen4 += '- '  # En passant target square
        fen4 += str(self.moveNumber) + ' '  # Number of quarter-moves
        fen4 += str(self.moveNumber // 4 + 1) + ' '  # Number of full moves, starting from 1
        self.fen4Generated.emit(fen4)
        return fen4

    def setBoardState(self, fen4):
        """Sets board according to FEN4."""
        if not fen4:
            return
        self.board.setFen4(fen4)
        self.setCurrentPlayer(fen4.split(' ')[1])

    def treeToAlgebraic(self, tree):
        if tree[0] == 'root':
            newTree = ['root', [self.treeToAlgebraic(subtree) for subtree in tree[1]]]
        else:
            newTree = [self.toAlgebraic(tree[0]), [self.treeToAlgebraic(subtree) for subtree in tree[1]]]
        return newTree

    def toAlgebraic(self, moveString):
        """Converts move string to algebraic notation."""
        # moveString = moveString[1:]
        moveString = moveString.split()
        if moveString[0][1] == 'P':
            moveString.pop(0)
            if len(moveString) == 3:
                moveString[0] = moveString[0][0]
                moveString[1] = 'x'
            else:
                moveString.pop(0)
        elif len(moveString) == 4:
            # Castling move
            if moveString[0][1] == 'K' and moveString[2][1] == 'R' and moveString[0][0] == moveString[2][0]:
                fromFile = ord(moveString[1][0]) - 97
                fromRank = int(moveString[1][1]) - 1
                toFile = ord(moveString[3][0]) - 97
                toRank = int(moveString[3][1]) - 1
                if fromRank == toRank:
                    # Kingside
                    if abs(toFile - fromFile) == 3:
                        moveString = 'O-O'
                    # Queenside
                    elif abs(toFile - fromFile) == 4:
                        moveString = 'O-O-O'
                elif fromFile == toFile:
                    # Kingside
                    if abs(toRank - fromRank) == 3:
                        moveString = 'O-O'
                    # Queenside
                    elif abs(toRank - fromRank) == 4:
                        moveString = 'O-O-O'
            else:
                moveString[0] = moveString[0][1]
                moveString[2] = 'x'
                moveString.remove(moveString[1])
        else:
            moveString.remove(moveString[1])
            if moveString != 'O-O' and moveString != 'O-O-O':
                moveString[0] = moveString[0][1]
        moveString = ''.join(moveString)
        return moveString

    def strMove(self, fromFile, fromRank, toFile, toRank):
        """Returns move in string form, separated by spaces, i.e. '<piece> <from> <captured piece> <to>'."""
        piece: str = self.board.getData(fromFile, fromRank)
        target: str = self.board.getData(toFile, toRank)
        char = (piece + ' ' + chr(97+fromFile) + str(fromRank+1) + ' ' + target*(target != ' ') + ' ' + chr(97+toFile) +
                str(toRank+1))  # chr(97) = 'a'
        return char

    def prevMove(self):
        """Sets board state to previous move."""
        if self.currentMove.name == 'root':
            return
        moveString = self.currentMove.name
        moveString = moveString.split()
        piece = moveString[0]
        fromFile = ord(moveString[1][0]) - 97  # chr(97) = 'a'
        fromRank = int(moveString[1][1:]) - 1
        if len(moveString) == 4:
            target = moveString[2]
            toFile = ord(moveString[3][0]) - 97
            toRank = int(moveString[3][1:]) - 1
        else:
            target = ' '
            toFile = ord(moveString[2][0]) - 97
            toRank = int(moveString[2][1:]) - 1
        self.board.setData(fromFile, fromRank, piece)
        self.board.setData(toFile, toRank, target)
        self.currentMove = self.currentMove.parent
        self.moveNumber -= 1
        self.playerQueue.rotate(1)
        self.setCurrentPlayer(self.playerQueue[0])
        # Signal View to remove last move highlight
        if self.currentPlayer == self.Red:
            color = QColor('#66bf3b43')
        elif self.currentPlayer == self.Blue:
            color = QColor('#664185bf')
        elif self.currentPlayer == self.Yellow:
            color = QColor('#66c09526')
        elif self.currentPlayer == self.Green:
            color = QColor('#664e9161')
        else:
            color = QColor('#00000000')
        self.removeHighlight.emit(color)

    def nextMove(self):
        """Sets board state to next move."""
        if not self.currentMove.children:
            return
        moveString = self.currentMove.children[-1].name  # Take last variation
        moveString = moveString.split()
        piece = moveString[0]
        fromFile = ord(moveString[1][0]) - 97  # chr(97) = 'a'
        fromRank = int(moveString[1][1:]) - 1
        if len(moveString) == 4:
            toFile = ord(moveString[3][0]) - 97
            toRank = int(moveString[3][1:]) - 1
        else:
            toFile = ord(moveString[2][0]) - 97
            toRank = int(moveString[2][1:]) - 1
        self.board.setData(fromFile, fromRank, ' ')
        self.board.setData(toFile, toRank, piece)
        self.currentMove = self.currentMove.children[-1]
        self.moveNumber += 1
        # Signal View to add move highlight and remove highlights of next player
        if self.currentPlayer == self.Red:
            color = QColor('#66bf3b43')
        elif self.currentPlayer == self.Blue:
            color = QColor('#664185bf')
        elif self.currentPlayer == self.Yellow:
            color = QColor('#66c09526')
        elif self.currentPlayer == self.Green:
            color = QColor('#664e9161')
        else:
            color = QColor('#00000000')
        self.addHighlight.emit(fromFile, fromRank, toFile, toRank, color)
        self.playerQueue.rotate(-1)
        self.setCurrentPlayer(self.playerQueue[0])
        if self.currentPlayer == self.Red:
            color = QColor('#66bf3b43')
        elif self.currentPlayer == self.Blue:
            color = QColor('#664185bf')
        elif self.currentPlayer == self.Yellow:
            color = QColor('#66c09526')
        elif self.currentPlayer == self.Green:
            color = QColor('#664e9161')
        else:
            color = QColor('#00000000')
        self.removeHighlight.emit(color)

    def firstMove(self):
        while self.currentMove.name != 'root':
            self.prevMove()

    def lastMove(self):
        while self.currentMove.children:
            self.nextMove()

    def makeMove(self, fromFile, fromRank, toFile, toRank):
        """This method must be overridden to define the proper logic corresponding to the game type (Teams or FFA)."""
        return False

    def getPgn4(self):
        """Generates PGN4 from current game."""
        pgn4 = ''

        # Standard tags, ("?" if data unknown, "-" if not applicable)
        pgn4 += '[Event "Four-Player Chess ' + self.variant + '"]\n'
        pgn4 += '[Site "chess.com"]\n'
        pgn4 += '[Date "' + date.today().strftime('%Y.%m.%d') + '"]\n'
        # pgn4 += '[Round "-"]\n'
        pgn4 += '[Red "' + self.redName + '"]\n'
        pgn4 += '[Blue "' + self.blueName + '"]\n'
        pgn4 += '[Yellow "' + self.yellowName + '"]\n'
        pgn4 += '[Green "' + self.greenName + '"]\n'
        pgn4 += '[Result "' + self.result + '"]\n'  # 1-0 (r & y win), 0-1 (b & g win), 1/2-1/2 (draw), * (no result)

        # Supplemental tags
        # pgn4 += '[RedElo "?"]\n'
        # pgn4 += '[BlueElo "?"]\n'
        # pgn4 += '[YellowElo "?"]\n'
        # pgn4 += '[GreenElo "?"]\n'
        pgn4 += '[PlyCount "' + str(self.moveNumber) + '"]\n'  # Total number of quarter-moves
        pgn4 += '[TimeControl "60 d15"]\n'  # 60 seconds sudden death with 15 seconds delay per move
        pgn4 += '[Mode "ICS"]\n'  # ICS = Internet Chess Server, OTB = Over-The-Board
        pgn4 += '[CurrentPosition "' + self.getBoardState() + '"]\n'
        pgn4 += '\n'

        # Movetext
        moves = self.moves
        moveList = []
        row = []
        prev = 0
        i = 0
        while i < len(moves):
            # Same variation -> continue
            if moves[i][-1] == prev:
                flag = (moves[i][0] - 1) % 4
                if flag == 0:
                    moveNum = str((moves[i][0] - 1) // 4 + 1) + '. '
                else:
                    moveNum = ''
                move = moveNum + moves[i][1] + ' '
                row.append(move)
            # New variation
            elif moves[i][-1] > prev:
                moveList.append(row)
                # Start of variation -> prepend opening bracket and add 1, 2 or 3 dots, depending on current player
                flag = ((moves[i][0] - 1) % 4)
                if flag == 0:  # Red's move
                    moveNum = str((moves[i][0] - 1) // 4 + 1) + '. '
                elif flag == 1:  # Blue's move, add one dot
                    moveNum = str((moves[i][0] - 1) // 4 + 1) + '. . '
                elif flag == 2:  # Yellow's move, add two dots
                    moveNum = str((moves[i][0] - 1) // 4 + 1) + '. .. '
                else:  # Green's move, add three dots
                    moveNum = str((moves[i][0] - 1) // 4 + 1) + '. ... '
                move = '(' + moveNum + moves[i][1] + ' '
                row = list()
                row.append(move)
            # End of variation, returning to previous variation
            elif moves[i][-1] < prev:
                # End of variation -> remove last space and append closing brackets
                row[-1] = row[-1][:-1] + ') ' * (prev - moves[i][-1])
                moveList.append(row)
                flag = ((moves[i][0] - 1) % 4 == 0)
                if flag:
                    moveNum = str((moves[i][0] - 1) // 4 + 1) + '. '
                else:
                    moveNum = ''
                move = moveNum + moves[i][1] + ' '
                row = list()
                row.append(move)
            # End of move list -> append rest of main line moves
            if i + 1 == len(moves):
                moveList.append(row)
            prev = moves[i][-1]
            i += 1
        for sublist in moveList:
            for move in sublist:
                pgn4 += move
        # Append result
        pgn4 += self.result
        self.pgn4Generated.emit(pgn4)

    def updateMoves(self, tree):
        moves = self.traverse(tree)
        self.moves = moves

    # TODO copied from MainWindow class -> possible to integrate and get rid of duplicate method?
    def traverse(self, node, moves=None, moveNum=0, root=None, var=0):
        """Traverses move tree to create list of moves, sorted by move number and variation (incl. variation root)."""
        # The tree is represented as a nested list with move strings, i.e. node = ['parent', [children]]
        parent = node[0]
        if not root:
            root = parent
        if not moves:
            moves = self.moves
        children = node[1]
        if children:
            for child in children:
                self.traverse(child, moves, moveNum + 1, root, var)
                var += 1
                root = parent
        elif not moves.count((moveNum, parent, root, var)):
            moves.append((moveNum, parent, root, var))
        # Sort moves: insert variations after the main line move
        i = 0
        while i < len(moves):
            variations = [var for var in moves if var[2] == moves[i][1]]
            # Sort variations by move and variation number
            variations = sorted(variations, key=lambda element: (element[-1], element[0]))
            moves = moves[:i+2] + variations + moves[i+2:]
            # Remove duplicate elements from the back
            moves.reverse()
            for move in moves:
                while moves.count(move) > 1:
                    moves.remove(move)
            moves.reverse()
            i += 1
        return moves


class Teams(Algorithm):
    """A subclass of Algorithm for the 4-player chess Teams variant."""
    def __init__(self):
        super().__init__()
        self.variant = 'Teams'

    def makeMove(self, fromFile, fromRank, toFile, toRank):
        """Moves piece from square (fromFile, fromRank) to square (toFile, toRank), if the move is valid."""
        if self.currentPlayer == self.NoPlayer:
            return False
        # Check if square contains piece of current player. (A player may only move his own pieces.)
        fromData = self.board.getData(fromFile, fromRank)
        if self.currentPlayer == self.Red and fromData[0] != 'r':
            return False
        if self.currentPlayer == self.Blue and fromData[0] != 'b':
            return False
        if self.currentPlayer == self.Yellow and fromData[0] != 'y':
            return False
        if self.currentPlayer == self.Green and fromData[0] != 'g':
            return False

        # Check if move is within board
        if toFile < 0 or toFile > (self.board.files-1):
            return False
        if toRank < 0 or toRank > (self.board.ranks-1):
            return False
        if ((toFile < 3 and toRank < 3) or (toFile < 3 and toRank > 10) or
                (toFile > 10 and toRank < 3) or (toFile > 10 and toRank > 10)):
            return False

        # Check if target square is not occupied by friendly piece. (Castling move excluded.)
        toData = self.board.getData(toFile, toRank)
        if self.currentPlayer == self.Red and (toData[0] == 'r' or toData[0] == 'y'):
            if not (fromData == 'rK' and toData == 'rR'):
                return False
        if self.currentPlayer == self.Blue and (toData[0] == 'b' or toData[0] == 'g'):
            if not (fromData == 'bK' and toData == 'bR'):
                return False
        if self.currentPlayer == self.Yellow and (toData[0] == 'y' or toData[0] == 'r'):
            if not (fromData == 'yK' and toData == 'yR'):
                return False
        if self.currentPlayer == self.Green and (toData[0] == 'g' or toData[0] == 'b'):
            if not (fromData == 'gK' and toData == 'gR'):
                return False

        # TODO check if move is legal

        # If move already exists (in case of variations), do not change the move tree
        moveString = self.strMove(fromFile, fromRank, toFile, toRank)
        if not (self.currentMove.children and (moveString in (child.name for child in self.currentMove.children))):
            # Make move child of current move and update current move (i.e. previous move is parent of current move)
            move = self.Node(moveString, [], self.currentMove)
            self.currentMove.add(move)
            self.currentMove = move

            # Send signal to update the move list and pass the tree with moves in algebraic notation
            tree = self.treeToAlgebraic(self.currentMove.getRoot().getTree())
            self.moveTreeChanged.emit(tree)
        else:
            # Update current move, but do not change the move tree
            for child in self.currentMove.children:
                if child.name == moveString:
                    self.currentMove = child

        # Make the move
        if fromData[1] == 'K' and toData != ' ':
            if toData[1] == 'R' and fromData[0] == toData[0]:
                # Castling move
                if fromRank == toRank:
                    if abs(toFile - fromFile) == 3:  # Kingside
                        kingFile = toFile - 1 if toFile > fromFile else toFile + 1
                        rookFile = fromFile + 1 if toFile > fromFile else fromFile - 1
                        self.board.movePiece(fromFile, fromRank, kingFile, toRank)
                        self.board.movePiece(toFile, fromRank, rookFile, toRank)
                    elif abs(toFile - fromFile) == 4:  # Queenside
                        kingFile = toFile + 2 if toFile < fromFile else toFile - 2
                        rookFile = fromFile - 1 if toFile < fromFile else fromFile + 1
                        self.board.movePiece(fromFile, fromRank, kingFile, toRank)
                        self.board.movePiece(toFile, fromRank, rookFile, toRank)
                elif fromFile == toFile:
                    if abs(toRank - fromRank) == 3:  # Kingside
                        kingRank = toRank - 1 if toRank > fromRank else toRank + 1
                        rookRank = fromRank + 1 if toRank > fromRank else fromRank - 1
                        self.board.movePiece(fromFile, fromRank, toFile, kingRank)
                        self.board.movePiece(fromFile, toRank, toFile, rookRank)
                    elif abs(toRank - fromRank) == 4:  # Queenside
                        kingRank = toRank + 2 if toRank < fromRank else toRank - 2
                        rookRank = fromRank - 1 if toRank < fromRank else fromRank + 1
                        self.board.movePiece(fromFile, fromRank, toFile, kingRank)
                        self.board.movePiece(fromFile, toRank, toFile, rookRank)
            else:
                self.board.movePiece(fromFile, fromRank, toFile, toRank)
        else:
            self.board.movePiece(fromFile, fromRank, toFile, toRank)

        # Increment move number
        self.moveNumber += 1

        # Rotate player queue and get next player from the queue (first element)
        self.playerQueue.rotate(-1)
        self.setCurrentPlayer(self.playerQueue[0])

        return True


class FFA(Algorithm):
    """A subclass of Algorithm for the 4-player chess Free-For-All (FFA) variant."""
    # TODO implement FFA class
    def __init__(self):
        super().__init__()
        self.variant = 'Free-For-All'


class View(QWidget):
    """The View is responsible for rendering the current state of the board and signalling user interaction to the
    underlying logic."""
    clicked = pyqtSignal(QPoint)
    squareSizeChanged = pyqtSignal(QSize)
    playerNameEdited = pyqtSignal(str, str, str, str)

    def __init__(self):
        super().__init__()
        self.squareSize = QSize(50, 50)
        self.board = Board(14, 14)
        self.pieces = {}
        self.highlights = []
        self.playerHighlights = {'r': self.PlayerHighlight(12, 1, QColor('#bf3b43')),
                                 'b': self.PlayerHighlight(1, 1, QColor('#4185bf')),
                                 'y': self.PlayerHighlight(1, 12, QColor('#c09526')),
                                 'g': self.PlayerHighlight(12, 12, QColor('#4e9161'))}
        self.redName = None
        self.redNameEdit = None
        self.blueName = None
        self.blueNameEdit = None
        self.yellowName = None
        self.yellowNameEdit = None
        self.greenName = None
        self.greenNameEdit = None
        self.createPlayerLabels()

    class SquareHighlight:
        """A square highlight type."""
        Type = 1

        def __init__(self, file, rank, color):
            self.file = file
            self.rank = rank
            self.color = color

    class PlayerHighlight(SquareHighlight):
        """A player highlight type. Same as square highlight, just renamed for convenience (unaltered subclass)."""
        pass

    def setBoard(self, board):
        """Updates board, if changed. Disconnects signals from old board and connects them to new board."""
        if self.board == board:
            return
        if self.board:
            try:
                self.board.disconnect()
            # If there are no signal-slot connections, TypeError is raised
            except TypeError:
                pass
        self.board = board
        if board:
            board.dataChanged.connect(self.update)
            board.boardReset.connect(self.update)
            board.boardReset.connect(self.resetHighlights)
        self.updateGeometry()

    def setSquareSize(self, size):
        """Sets size of board squares and updates geometry accordingly."""
        if self.squareSize == size:
            return
        self.squareSize = size
        self.squareSizeChanged.emit(size)
        self.updateGeometry()

    def sizeHint(self):
        """Overrides QWidget sizeHint() method. Computes and returns size based on size of board squares."""
        return QSize(self.squareSize.width()*self.board.files, self.squareSize.height()*self.board.ranks)

    def squareRect(self, file, rank):
        """Returns square of type QRect at position (file, rank)."""
        sqSize = self.squareSize
        return QRect(QPoint(file*sqSize.width(), (self.board.ranks-(rank+1))*sqSize.height()), sqSize)

    def paintEvent(self, event):
        """Overrides QWidget paintEvent() method. Draws squares and pieces on the board."""
        painter = QPainter()
        painter.begin(self)
        # First draw squares, then highlights, then pieces
        for rank in range(self.board.ranks):
            for file in range(self.board.files):
                # Do not paint 3x3 sub-grids at the corners
                if not ((file < 3 and rank < 3) or (file < 3 and rank > 10) or
                        (file > 10 and rank < 3) or (file > 10 and rank > 10)):
                    self.drawSquare(painter, file, rank)
        self.drawHighlights(painter)
        painter.fillRect(self.squareRect(12, 1), QColor('#40bf3b43'))
        painter.fillRect(self.squareRect(1, 1), QColor('#404185bf'))
        painter.fillRect(self.squareRect(1, 12), QColor('#40c09526'))
        painter.fillRect(self.squareRect(12, 12), QColor('#404e9161'))
        for rank in range(self.board.ranks):
            for file in range(self.board.files):
                self.drawPiece(painter, file, rank)
        painter.end()

    def drawSquare(self, painter, file, rank):
        """Draws dark or light square at position (file, rank) using painter."""
        rect = self.squareRect(file, rank)
        fillColor = self.palette().color(QPalette.Midlight) if (file+rank) % 2 else self.palette().color(QPalette.Mid)
        painter.fillRect(rect, fillColor)

    def setPiece(self, char, icon):
        """Sets piece icon corresponding to algebraic piece name."""
        self.pieces[char] = icon
        self.update()

    def piece(self, char):
        """Returns piece icon corresponding to algebraic piece name."""
        return self.pieces[char]

    def drawPiece(self, painter, file, rank):
        """Draws piece at square (file, rank) using painter."""
        rect = self.squareRect(file, rank)
        char = self.board.getData(file, rank)
        if char != ' ':
            icon = self.piece(char)
            if not icon.isNull():
                icon.paint(painter, rect, Qt.AlignCenter)

    def squareAt(self, point):
        """Returns square (file, rank) of type QPoint that contains point."""
        sqSize = self.squareSize
        file = point.x() / sqSize.width()
        rank = point.y() / sqSize.height()
        if (file < 0) or (file > self.board.files) or (rank < 0) or (rank > self.board.ranks):
            return QPoint()
        return QPoint(file, self.board.ranks-rank)

    def mouseReleaseEvent(self, event):
        """Overrides QWidget mouseReleaseEvent() method. Emits signal with clicked square of type QPoint as value."""
        point = self.squareAt(event.pos())
        if point.isNull():
            return
        self.clicked.emit(point)

    def addHighlight(self, highlight):
        """Adds highlight to the list and redraws view."""
        self.highlights.append(highlight)
        self.update()

    def removeHighlight(self, highlight):
        """Removes highlight from the list and redraws view."""
        self.highlights.remove(highlight)
        self.update()

    def removeHighlightsOfColor(self, color):
        """Removes all highlights of color."""
        # NOTE: Need to loop through the reversed list, otherwise an element will be skipped if an element was removed
        # in the previous iteration.
        for highlight in reversed(self.highlights):
            if highlight.color == color:
                self.removeHighlight(highlight)

    def drawHighlights(self, painter):
        """Draws all recognized highlights stored in the list."""
        for highlight in self.highlights:
            if highlight.Type == self.SquareHighlight.Type:
                rect = self.squareRect(highlight.file, highlight.rank)
                painter.fillRect(rect, highlight.color)

    def highlightPlayer(self, player):
        """Adds highlight for player to indicate turn. Removes highlights for other players if they exist."""
        self.addHighlight(self.playerHighlights[player])
        for otherPlayer in self.playerHighlights:
            if otherPlayer != player:
                try:
                    self.removeHighlight(self.playerHighlights[otherPlayer])
                except ValueError:
                    pass

    def resetHighlights(self):
        """Clears list of highlights and redraws view."""
        self.highlights = []
        self.update()

    class PlayerName(QPushButton):
        def __init__(self):
            super().__init__()
            self.setFixedSize(150, 50)
            # self.setFlat(True)
            self.setText('Player Name')
            self.setStyleSheet("""
            QPushButton {border: none; font-weight: bold;}
            QPushButton[player='red'] {color: #bf3b43;}
            QPushButton[player='blue'] {color: #4185bf;}
            QPushButton[player='yellow'] {color: #c09526;}
            QPushButton[player='green'] {color: #4e9161;}
            """)

    class PlayerNameEdit(QLineEdit):
        focusOut = pyqtSignal()

        def __init__(self):
            super().__init__()
            self.setFixedSize(150, 50)
            self.setAlignment(Qt.AlignCenter)
            self.setFrame(False)
            self.setAttribute(Qt.WA_MacShowFocusRect, 0)
            self.installEventFilter(self)
            self.setStyleSheet("""
            QLineEdit {font-weight: bold;}
            QLineEdit[player='red'] {color: #bf3b43;}
            QLineEdit[player='blue'] {color: #4185bf;}
            QLineEdit[player='yellow'] {color: #c09526;}
            QLineEdit[player='green'] {color: #4e9161;}
            """)

        def eventFilter(self, object, event):
            if event.type() == QEvent.FocusOut:
                self.focusOut.emit()
            return False

    def createPlayerLabels(self):
        # Red player
        self.redName = self.PlayerName()
        self.redName.setProperty('player', 'red')
        self.redName.move(550, 650)
        self.redName.setParent(self)
        self.redName.show()
        self.redName.clicked.connect(lambda: self.editPlayerName(self.redNameEdit))
        self.redNameEdit = self.PlayerNameEdit()
        self.redNameEdit.setProperty('player', 'red')
        self.redNameEdit.move(550, 650)
        self.redNameEdit.setParent(self)
        self.redNameEdit.show()
        self.redNameEdit.setHidden(True)
        self.redNameEdit.returnPressed.connect(lambda: self.setPlayerName(self.redName))
        self.redNameEdit.focusOut.connect(lambda: self.setPlayerName(self.redName))
        # Blue player
        self.blueName = self.PlayerName()
        self.blueName.setProperty('player', 'blue')
        self.blueName.move(0, 650)
        self.blueName.setParent(self)
        self.blueName.show()
        self.blueName.clicked.connect(lambda: self.editPlayerName(self.blueNameEdit))
        self.blueNameEdit = self.PlayerNameEdit()
        self.blueNameEdit.setProperty('player', 'blue')
        self.blueNameEdit.move(0, 650)
        self.blueNameEdit.setParent(self)
        self.blueNameEdit.show()
        self.blueNameEdit.setHidden(True)
        self.blueNameEdit.returnPressed.connect(lambda: self.setPlayerName(self.blueName))
        self.blueNameEdit.focusOut.connect(lambda: self.setPlayerName(self.blueName))
        # Yellow player
        self.yellowName = self.PlayerName()
        self.yellowName.setProperty('player', 'yellow')
        self.yellowName.move(0, 0)
        self.yellowName.setParent(self)
        self.yellowName.show()
        self.yellowName.clicked.connect(lambda: self.editPlayerName(self.yellowNameEdit))
        self.yellowNameEdit = self.PlayerNameEdit()
        self.yellowNameEdit.setProperty('player', 'yellow')
        self.yellowNameEdit.move(0, 0)
        self.yellowNameEdit.setParent(self)
        self.yellowNameEdit.show()
        self.yellowNameEdit.setHidden(True)
        self.yellowNameEdit.returnPressed.connect(lambda: self.setPlayerName(self.yellowName))
        self.yellowNameEdit.focusOut.connect(lambda: self.setPlayerName(self.yellowName))
        # Green player
        self.greenName = self.PlayerName()
        self.greenName.setProperty('player', 'green')
        self.greenName.move(550, 0)
        self.greenName.setParent(self)
        self.greenName.show()
        self.greenName.clicked.connect(lambda: self.editPlayerName(self.greenNameEdit))
        self.greenNameEdit = self.PlayerNameEdit()
        self.greenNameEdit.setProperty('player', 'green')
        self.greenNameEdit.move(550, 0)
        self.greenNameEdit.setParent(self)
        self.greenNameEdit.show()
        self.greenNameEdit.setHidden(True)
        self.greenNameEdit.returnPressed.connect(lambda: self.setPlayerName(self.greenName))
        self.greenNameEdit.focusOut.connect(lambda: self.setPlayerName(self.greenName))

    def editPlayerName(self, nameEdit):
        name = self.sender()
        name.setHidden(True)
        nameEdit.setHidden(False)
        nameEdit.setFocus(True)

    def setPlayerName(self, name):
        nameEdit = self.sender()
        name.setText(nameEdit.text())
        nameEdit.setHidden(True)
        name.setHidden(False)
        self.playerNameEdited.emit(self.redName.text(), self.blueName.text(), self.yellowName.text(),
                                   self.greenName.text())
