def execute_command(command: str) -> str:
    import subprocess
    import sys
    from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                                 QPushButton, QLabel, QTextEdit)
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont, QPainter, QColor
    
    """Executes a shell command and returns the output."""
    
    class SmoothButton(QPushButton):
        def __init__(self, text, color_base, parent=None):
            super().__init__(text, parent)
            self.color_base = color_base
            self.is_hovered = False
            self.is_pressed = False
            
        def enterEvent(self, event):
            self.is_hovered = True
            self.update()
            super().enterEvent(event)
            
        def leaveEvent(self, event):
            self.is_hovered = False
            self.update()
            super().leaveEvent(event)
            
        def mousePressEvent(self, event):
            self.is_pressed = True
            self.update()
            super().mousePressEvent(event)
            
        def mouseReleaseEvent(self, event):
            self.is_pressed = False
            self.update()
            super().mouseReleaseEvent(event)
            
        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            
            # Color adjustments based on state
            alpha = 63  # Base alpha (0.25 * 255)
            border_alpha = 89  # Base border alpha
            
            if self.is_pressed:
                alpha = 89
                border_alpha = 127
            elif self.is_hovered:
                alpha = 76
                border_alpha = 114
                
            # Draw background
            bg_color = QColor(self.color_base[0], self.color_base[1], self.color_base[2], alpha)
            border_color = QColor(self.color_base[0], self.color_base[1], self.color_base[2], border_alpha)
            
            painter.setBrush(bg_color)
            painter.setPen(border_color)
            painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 14, 14)
            
            # Draw text
            painter.setPen(QColor(240, 240, 240, 220))
            painter.setFont(self.font())
            painter.drawText(self.rect(), Qt.AlignCenter, self.text())
    
    class CommandDialog(QWidget):
        def __init__(self, command):
            super().__init__()
            self.command = command
            self.user_choice = None
            self.app = QApplication.instance()
            self.init_ui()
            
        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            
            # More prominent background (0.1 + 0.15 = 0.25 alpha)
            painter.setBrush(QColor(20, 20, 30, 63))  # 0.25 alpha
            painter.setPen(QColor(160, 160, 160, 89))  # 0.35 alpha
            painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)
            
        def init_ui(self):
            self.setWindowTitle("Command Execution")
            self.setFixedSize(380, 140)
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.center_window()
            
            # Clean layout
            layout = QVBoxLayout()
            layout.setContentsMargins(12, 12, 12, 12)
            layout.setSpacing(8)
            
            # Simple question
            title = QLabel("Execute command?")
            title.setFont(QFont("system", 11))
            title.setStyleSheet("color: rgba(220, 220, 220, 200); margin: 0; padding: 2px;")
            title.setAlignment(Qt.AlignCenter)
            
            # Command display with more prominent background
            self.cmd_text = QTextEdit()
            self.cmd_text.setPlainText(self.command)
            self.cmd_text.setReadOnly(True)
            self.cmd_text.setFont(QFont("monospace", 9))
            self.cmd_text.setFixedHeight(50)
            self.cmd_text.setStyleSheet("""
                QTextEdit {
                    background: rgba(0, 0, 0, 63);
                    color: rgba(200, 200, 200, 220);
                    border: 1px solid rgba(140, 140, 140, 127);
                    border-radius: 8px;
                    padding: 6px;
                }
                QScrollBar { width: 0px; }
            """)
            
            # Smooth anti-aliased buttons
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(8)
            btn_layout.setContentsMargins(0, 4, 0, 0)
            
            # Red for cancel, Green for execute
            self.cancel_btn = SmoothButton("Cancel", (220, 80, 80))
            self.execute_btn = SmoothButton("Execute", (80, 180, 80))
            
            for btn in [self.cancel_btn, self.execute_btn]:
                btn.setFont(QFont("system", 10, QFont.Medium))
                btn.setFixedSize(70, 28)
                btn.setCursor(Qt.PointingHandCursor)
            
            self.cancel_btn.clicked.connect(self.reject)
            self.execute_btn.clicked.connect(self.accept)
            
            btn_layout.addStretch()
            btn_layout.addWidget(self.cancel_btn)
            btn_layout.addWidget(self.execute_btn)
            
            layout.addWidget(title)
            layout.addWidget(self.cmd_text)
            layout.addLayout(btn_layout)
            
            self.setLayout(layout)
            
        def center_window(self):
            screen = self.app.primaryScreen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
            
        def keyPressEvent(self, event):
            if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
                self.accept()
            elif event.key() == Qt.Key_Escape:
                self.reject()
                
        def accept(self):
            self.user_choice = True
            self.close()
            
        def reject(self):
            self.user_choice = False
            self.close()
    
    class ErrorDialog(QWidget):
        def __init__(self, error_message):
            super().__init__()
            self.error_message = error_message
            self.app = QApplication.instance()
            self.init_ui()
            
        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            # More prominent red-tinted background
            painter.setBrush(QColor(30, 20, 20, 63))  # 0.25 alpha
            painter.setPen(QColor(180, 120, 120, 114))  # 0.45 alpha
            painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)
            
        def init_ui(self):
            self.setWindowTitle("Command Error")
            self.setFixedSize(420, 200)
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.center_window()
            
            layout = QVBoxLayout()
            layout.setContentsMargins(12, 12, 12, 12)
            layout.setSpacing(8)
            
            title = QLabel("Command failed")
            title.setFont(QFont("system", 11))
            title.setStyleSheet("color: rgba(240, 180, 180, 200); margin: 0; padding: 2px;")
            title.setAlignment(Qt.AlignCenter)
            
            self.error_text = QTextEdit()
            self.error_text.setPlainText(self.error_message)
            self.error_text.setReadOnly(True)
            self.error_text.setFont(QFont("monospace", 9))
            self.error_text.setStyleSheet("""
                QTextEdit {
                    background: rgba(0, 0, 0, 63);
                    color: rgba(220, 180, 180, 220);
                    border: 1px solid rgba(180, 120, 120, 153);
                    border-radius: 8px;
                    padding: 6px;
                }
                QScrollBar:vertical {
                    background: transparent;
                    width: 6px;
                    border-radius: 3px;
                }
                QScrollBar::handle:vertical {
                    background: rgba(180, 120, 120, 140);
                    border-radius: 3px;
                }
                QScrollBar::handle:vertical:hover {
                    background: rgba(180, 120, 120, 190);
                }
            """)
            
            # Smooth close button
            self.close_btn = SmoothButton("Close", (180, 100, 100))
            self.close_btn.setFont(QFont("system", 10, QFont.Medium))
            self.close_btn.setFixedSize(60, 28)
            self.close_btn.setCursor(Qt.PointingHandCursor)
            self.close_btn.clicked.connect(self.close)
            
            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(0, 4, 0, 0)
            btn_layout.addStretch()
            btn_layout.addWidget(self.close_btn)
            
            layout.addWidget(title)
            layout.addWidget(self.error_text)
            layout.addLayout(btn_layout)
            self.setLayout(layout)
            
        def center_window(self):
            screen = self.app.primaryScreen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
            
        def keyPressEvent(self, event):
            if event.key() in [Qt.Key_Return, Qt.Key_Enter, Qt.Key_Escape]:
                self.close()
    
    # Run dialog
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    dialog = CommandDialog(command)
    dialog.show()
    app.exec_()
    
    if not dialog.user_choice:
        return "User aborted the command execution."
    
    # Execute command
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout
    else:
        error_dialog = ErrorDialog(result.stderr)
        error_dialog.show()
        app.exec_()
        return result.stderr

execute_command_description = "A simple tool to execute a linux shell command"