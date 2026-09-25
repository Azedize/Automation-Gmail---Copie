import os
import re

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from config import Settings


class EntitySelectionDialog(QDialog):
    def __init__(self, pattern=None, default_entity=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Entity - AutoMailPro")
        self.setModal(True)
        self.setFixedSize(500, 320)
        self.setWindowIcon(QIcon(os.path.join(Settings.ICONS_DIR, "logo.jpg")))
        self.pattern = pattern
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(12)
        title_label = QLabel("Entity Selection")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333; margin-bottom: 10px;")
        main_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        instruction_label = QLabel("Please enter the entity you want to use for this session : ")
        instruction_label.setStyleSheet("font-size: 14px; color: #555; margin-bottom: 5px;")
        instruction_label.setWordWrap(True)
        main_layout.addWidget(instruction_label)

        if self.pattern:
            format_info = QLabel("Format: opm followed by digits (e.g., opm74, opm19)")
            format_info.setStyleSheet("font-size: 12px; color: #859cb5; margin-bottom: 10px; font-style: italic;")
            main_layout.addWidget(format_info)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter entity (opm + number)...")
        if default_entity:
            self.input_field.setText(default_entity)
        self.input_field.setStyleSheet("QLineEdit { font-size: 14px; padding: 8px; border: 2px solid #ccc; border-radius: 5px; background-color: #fff; min-width: 200px; } QLineEdit:hover { border-color: #0078d4; } QLineEdit:focus { border: 2px solid #0078d4; outline: none; }")
        main_layout.addWidget(self.input_field, alignment=Qt.AlignmentFlag.AlignCenter)

        self.error_label = QLabel()
        self.error_label.setStyleSheet("font-size: 12px; color: #d32f2f; margin-top: 8px; margin-bottom: 8px;")
        self.error_label.setWordWrap(True)
        self.error_label.setMinimumHeight(40)
        self.error_label.hide()
        main_layout.addWidget(self.error_label)

        main_layout.addSpacing(20)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("QPushButton { font-size: 14px; padding: 10px 20px; background-color: #f3f2f1; border: 1px solid #ccc; border-radius: 5px; color: #333; text-align: center; } QPushButton:hover { background-color: #e1dfdd; } QPushButton:pressed { background-color: #c8c6c4; }")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.setStyleSheet("QPushButton { font-size: 14px; padding: 10px 20px; background-color: #0078d4; border: none; border-radius: 5px; color: white; text-align: center; } QPushButton:hover { background-color: #106ebe; } QPushButton:pressed { background-color: #005a9e; }")
        self.confirm_button.clicked.connect(self.validate_and_accept)
        self.confirm_button.setDefault(True)
        button_layout.addWidget(self.confirm_button)
        main_layout.addLayout(button_layout)
        self.setStyleSheet("QDialog { background-color: #f8f8f8; }")

    def validate_and_accept(self):
        entity_text = self.input_field.text().strip()
        if not entity_text:
            self.error_label.setText("Entity name cannot be empty.")
            self.error_label.show()
            return

        if self.pattern and not re.match(self.pattern, entity_text):
            self.error_label.setText("Invalid entity format. Expected format: opm followed by digits (e.g., opm74)")
            self.error_label.show()
            return

        self.error_label.hide()
        self.accept()

    def get_selected_entity(self):
        if self.exec() == QDialog.DialogCode.Accepted:
            return self.input_field.text().strip()
        return None
