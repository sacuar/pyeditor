from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QTabWidget,
    QVBoxLayout, QWidget, QAction, QFileDialog, QToolBar, QMenu
)
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter
from PyQt5.QtCore import Qt, QRegExp
from reportlab.pdfgen import canvas
from docx import Document
import sys, os

# ---------------- Syntax Highlighter ----------------
class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)
        self._highlighting_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#00ffff"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "def", "class", "if", "elif", "else", "while",
            "for", "in", "try", "except", "finally",
            "import", "from", "as", "return", "with", "pass",
            "break", "continue", "and", "or", "not", "is", "None", "True", "False"
        ]
        for word in keywords:
            pattern = QRegExp(r'\b' + word + r'\b')
            self._highlighting_rules.append((pattern, keyword_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ffa500"))
        self._highlighting_rules.append((QRegExp(r'"[^"]*"'), string_format))
        self._highlighting_rules.append((QRegExp(r"'[^']*'"), string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#888888"))
        self._highlighting_rules.append((QRegExp(r"#.*"), comment_format))

    def highlightBlock(self, text):
        for pattern, fmt in self._highlighting_rules:
            index = pattern.indexIn(text)
            while index >= 0:
                length = pattern.matchedLength()
                self.setFormat(index, length, fmt)
                index = pattern.indexIn(text, index + length)

# ---------------- Text Editor Widget ----------------
class Editor(QTextEdit):
    def __init__(self, file_path=None):
        super().__init__()
        self.file_path = file_path
        self.setFont(QFont("Consolas", 12))
        self.setStyleSheet("background:#1e1e1e; color:white; selection-background-color:#555555")
        self.highlighter = PythonHighlighter(self.document())

# ---------------- Main Window ----------------
class PyEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyEditor Dark Theme")
        self.resize(900, 600)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.setStyleSheet("""
            QTabBar::tab { background: #2d2d2d; color: white; padding: 6px; border-radius: 4px; margin-right:2px;}
            QTabBar::tab:selected { background: #444; font-weight:bold; }
            QTabWidget::pane { border:0; }
        """)
        self.setCentralWidget(self.tabs)

        self.new_tab()

        # Menus
        self.create_menus()

    # ---------------- Tabs ----------------
    def new_tab(self, file_path=None, content=""):
        editor = Editor(file_path)
        editor.setText(content)
        tab_name = os.path.basename(file_path) if file_path else "Untitled"
        self.tabs.addTab(editor, tab_name)
        self.tabs.setCurrentWidget(editor)

    def close_tab(self, index):
        self.tabs.removeTab(index)

    def current_editor(self):
        return self.tabs.currentWidget()

    # ---------------- Menus ----------------
    def create_menus(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("File")
        new_action = QAction("New", self)
        new_action.triggered.connect(lambda: self.new_tab())
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file)
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_file)
        save_as_action = QAction("Save As", self)
        save_as_action.triggered.connect(self.save_file_as)
        export_pdf_action = QAction("Export PDF", self)
        export_pdf_action.triggered.connect(self.export_pdf)
        export_docx_action = QAction("Export DOCX", self)
        export_docx_action.triggered.connect(self.export_docx)

        for a in [new_action, open_action, save_action, save_as_action, export_pdf_action, export_docx_action]:
            file_menu.addAction(a)

        # Edit Menu
        edit_menu = menubar.addMenu("Edit")
        cut_action = QAction("Cut", self)
        cut_action.triggered.connect(lambda: self.current_editor().cut())
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(lambda: self.current_editor().copy())
        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(lambda: self.current_editor().paste())
        undo_action = QAction("Undo", self)
        undo_action.triggered.connect(lambda: self.current_editor().undo())
        redo_action = QAction("Redo", self)
        redo_action.triggered.connect(lambda: self.current_editor().redo())

        for a in [cut_action, copy_action, paste_action, undo_action, redo_action]:
            edit_menu.addAction(a)

    # ---------------- File Operations ----------------
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*)")
        if path:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.new_tab(path, content)

    def save_file(self):
        editor = self.current_editor()
        if editor.file_path:
            with open(editor.file_path, "w", encoding="utf-8") as f:
                f.write(editor.toPlainText())
        else:
            self.save_file_as()

    def save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save File As", "", "All Files (*)")
        if path:
            editor = self.current_editor()
            editor.file_path = path
            with open(path, "w", encoding="utf-8") as f:
                f.write(editor.toPlainText())
            self.tabs.setTabText(self.tabs.currentIndex(), os.path.basename(path))

    # ---------------- Export ----------------
    def export_pdf(self):
        editor = self.current_editor()
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF Files (*.pdf)")
        if path:
            c = canvas.Canvas(path)
            text = editor.toPlainText().split('\n')
            y = 800
            for line in text:
                c.drawString(30, y, line)
                y -= 15
            c.save()

    def export_docx(self):
        editor = self.current_editor()
        path, _ = QFileDialog.getSaveFileName(self, "Export DOCX", "", "Word Files (*.docx)")
        if path:
            doc = Document()
            doc.add_paragraph(editor.toPlainText())
            doc.save(path)

# ---------------- Run App ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PyEditor()
    window.show()
    sys.exit(app.exec_())
