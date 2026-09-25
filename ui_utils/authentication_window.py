import json
import os
import sys
import traceback

from PyQt6.QtGui import QColor, QGuiApplication, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
    QMainWindow,
)
from PyQt6 import uic

from config import Settings
from core import SessionManager
from ui_utils import UIManager
from ui_utils.entity_selection_dialog import EntitySelectionDialog
from utils import ValidationUtils


class AuthenticationWindow(QMainWindow):
    def __init__(
        self,
        main_window_class,
        stop_processes,
        start_extraction=None,
        runtime_state=None,
    ):
        super().__init__()
        self.main_window_class = main_window_class
        self.stop_processes = stop_processes
        self.start_extraction = start_extraction or getattr(
            main_window_class, "_default_start_extraction", None
        )
        self.runtime_state = runtime_state or getattr(
            main_window_class, "_default_runtime_state", None
        )
        self.ui_path = self.select_ui_file()
        uic.loadUi(self.ui_path, self)
        if "Auth.ui" in self.ui_path:
            self.initialize_login_ui()
            Settings.write_log_dev_file("Login UI initialized", "INFO")
        self.setWindowTitle("AutoMailPro")

    def select_ui_file(self) -> str:
        try:
            session_info = SessionManager.check_session()
            if session_info["valid"]:
                return Settings.INTERFACE_UI
        except Exception as error:
            Settings.write_log_dev_file(
                f"[SESSION ERROR] {error}\n{traceback.format_exc()}", "WARNING"
            )
            sys.exit()
        return Settings.AUTH_UI

    def initialize_login_ui(self):
        self.login_input = self.findChild(QLineEdit, "loginInput")
        self.password_input = self.findChild(QLineEdit, "passwordInput")
        self.login_button = self.findChild(QPushButton, "loginButton")
        self.title = self.findChild(QPushButton, "title")
        self.erreur_label = self.findChild(QLabel, "erreur")

        if self.erreur_label:
            Settings.write_log_dev_file(
                f"[INFO] Erreur label found: {self.erreur_label.text()}", "INFO"
            )
            self.erreur_label.hide()

        if self.title:
            self.title.clicked.connect(self.handle_show_session_date)
            Settings.write_log_dev_file(
                f"[INFO] Title label found: {self.title.text()}", "INFO"
            )
        if self.login_button:
            self.login_button.clicked.connect(self.handle_login)
            Settings.write_log_dev_file(
                f"[INFO] Login button found: {self.login_button.text()}", "INFO"
            )

        right_frame = self.findChild(QWidget, "rightFrame")
        if right_frame:
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(25)
            shadow.setXOffset(0)
            shadow.setYOffset(8)
            shadow.setColor(QColor(0, 0, 0, 80))
            right_frame.setGraphicsEffect(shadow)

        self.background_image_path = Settings.AUTH_BACKGROUND
        self.background_frame = self.findChild(QFrame, "background")
        if self.background_frame:
            self.background_label = QLabel(self.background_frame)
            self.background_label.setStyleSheet(
                "border-top-left-radius: 30px; border-bottom-left-radius: 30px; border-top-right-radius: 0px; border-bottom-right-radius: 0px; overflow: hidden;"
            )
            self.background_label.setScaledContents(True)
            self.background_label.lower()
            self.update_background_image()

            self.logoFrame = self.findChild(QFrame, "logoFrame")
            if self.logoFrame:
                self.logo_label = QLabel(self.logoFrame)
                self.logo_label.setScaledContents(True)
                pixmap = QPixmap(os.path.join(Settings.ICONS_DIR, "logo.jpg"))
                if not pixmap.isNull():
                    self.logo_label.setPixmap(pixmap)
                    self.logo_label.setGeometry(
                        0, 0, self.logoFrame.width(), self.logoFrame.height()
                    )
                    self.logo_label.show()

            self.UseFrame = self.findChild(QFrame, "userFrame")
            if self.UseFrame:
                self.user_label = QLabel(self.UseFrame)
                self.user_label.setScaledContents(True)
                user_pixmap = QPixmap(os.path.join(Settings.ICONS_DIR, "user.png"))
                if not user_pixmap.isNull():
                    self.user_label.setPixmap(user_pixmap)
                    self.user_label.setGeometry(
                        0, 0, self.UseFrame.width(), self.UseFrame.height()
                    )
                    self.user_label.show()

    def update_background_image(self):
        if hasattr(self, "background_frame") and hasattr(self, "background_label"):
            pixmap = QPixmap(self.background_image_path)
            if not pixmap.isNull():
                self.background_label.resize(self.background_frame.size())
                self.background_label.setPixmap(pixmap)

    def handle_login(self):
        UIManager.disableButton(self.login_button)
        username = (
            self.login_input.text().strip()
            if hasattr(self.login_input, "text")
            else str(self.login_input).strip()
        )
        password = (
            self.password_input.text().strip()
            if hasattr(self.password_input, "text")
            else str(self.password_input).strip()
        )

        if len(username) <= 4:
            Settings.write_log_dev_file(
                "❌ Username must contain more than 4 characters.", "WARNING"
            )
            UIManager.enableButton(self.login_button)
            self.erreur_label.setText("Username must contain more than 4 characters.")
            self.erreur_label.show()
            return

        if len(password) <= 4:
            Settings.write_log_dev_file(
                "❌ Password must contain more than 4 characters.", "WARNING"
            )
            UIManager.enableButton(self.login_button)
            self.erreur_label.setText("Password must contain more than 4 characters.")
            self.erreur_label.show()
            return

        Settings.write_log_dev_file("Calling check_api_credentials...", "INFO")
        auth_result = SessionManager.check_api_credentials(username, password)
        Settings.write_log_event(
            "authentication_response",
            "INFO",
            response_type=type(auth_result).__name__,
            success=not isinstance(auth_result, int) or auth_result == 0,
        )

        if isinstance(auth_result, int):
            UIManager.enableButton(self.login_button)
            messages = {
                -1: "Invalid credentials. Please try again.",
                -2: "This device is not authorized. Please contact support.",
                -3: "Unable to connect to the server. Please try again later.",
                -4: "Access to this application has been denied.",
                -5: "Unknown error occurred during authentication.",
            }
            error_message = messages.get(auth_result, "Unknown error occurred.")
            Settings.write_log_dev_file(
                f"Authentication error code: {auth_result} → {error_message}", "WARNING"
            )
            self.erreur_label.setText(error_message)
            self.erreur_label.show()
            return

        id_user, p_entity_Origine = auth_result
        if username == "rep.test":
            dialog = EntitySelectionDialog(
                pattern=r"^opm\d+$", default_entity=p_entity_Origine, parent=self
            )
            selected_entity = dialog.get_selected_entity()
            if selected_entity is None:
                UIManager.enableButton(self.login_button)
                Settings.write_log_dev_file(
                    "Entity selection canceled. Login aborted.", "WARNING"
                )
                self.erreur_label.setText(
                    "Entity selection is required for this user. Login aborted."
                )
                self.erreur_label.show()
                return
            p_entity_Nouveau = selected_entity
            Settings.write_log_dev_file(
                f"✅ Entity overridden to: {p_entity_Nouveau}", "INFO"
            )
        else:
            p_entity_Nouveau = p_entity_Origine

        try:
            valid_session = SessionManager.create_session(
                username, password, p_entity_Origine, p_entity_Nouveau, id_user
            )
            if not valid_session:
                Settings.write_log_dev_file(
                    "Failed to create user session for unknown reasons.", "ERROR"
                )
                UIManager.enableButton(self.login_button)
                self.erreur_label.setText("Failed to create user session.")
                self.erreur_label.show()
                return
        except Exception as error:
            UIManager.enableButton(self.login_button)
            Settings.write_log_dev_file(
                f"Exception during session creation: {error}\n{traceback.format_exc()}",
                "ERROR",
            )
            self.erreur_label.setText(
                f"Exception during session creation: {error}\n{traceback.format_exc()}"
            )
            self.erreur_label.show()
            return

        try:
            with open(Settings.FILE_ACTIONS_JSON, "r", encoding="utf-8") as file:
                json_data = json.load(file)
            if not json_data:
                Settings.write_log_dev_file(
                    f"Configuration file is empty: {Settings.FILE_ACTIONS_JSON}",
                    "WARNING",
                )
                raise ValueError("Fichier de configuration vide")

            Settings.write_log_dev_file(
                "Configuration file loaded successfully.", "INFO"
            )
            UIManager.enableButton(self.login_button)
            self.main_window = self.main_window_class(
                json_data,
                self.stop_processes,
                self.start_extraction,
                self.runtime_state,
            )
            self.main_window.setFixedSize(Settings.WINDOW_WIDTH, Settings.WINDOW_HEIGHT)
            self.main_window.setWindowTitle("AutoMailPro")
            self.main_window.stopButton.clicked.connect(
                lambda: self.stop_processes(self.main_window)
            )

            screen = QGuiApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.main_window.width()) // 2
            y = (screen_geometry.height() - self.main_window.height()) // 2
            self.main_window.move(x, y)
            self.main_window.show()
            self.close()
            Settings.write_log_dev_file(
                "Main window displayed, login completed successfully.", "INFO"
            )

        except Exception as error:
            UIManager.enableButton(self.login_button)
            Settings.write_log_dev_file(
                f"An error occurred while loading AutomationMainWindow: {error}\n{traceback.format_exc()}",
                "ERROR",
            )
            SessionManager.clear_session()
            self.erreur_label.setText("Unable to open the main application window.")
            self.erreur_label.show()

    def handle_show_session_date(self):
        if not ValidationUtils.pathExists(Settings.SESSION_PATH):
            Settings.write_log_dev_file(
                "Session file not found at expected path.", "WARNING"
            )
            self.erreur_label.setText("Session file not found .")
            self.erreur_label.show()
            return
        session_info = SessionManager.check_session()

        if session_info.get("valid"):
            session_data = (
                f"Username: {session_info.get('username')}\n"
                f"Entity: {session_info.get('p_entity_Nouveau')}\n"
                f"Session date: {session_info.get('date')}"
            )
            Settings.write_log_dev_file(
                "Session data retrieved without exposing credentials.", "INFO"
            )
            self.erreur_label.setText(f"Session data:\n{session_data}")
        else:
            Settings.write_log_dev_file(
                f"Session file is not valid: {session_info.get('error', 'Unknown error')}",
                "WARNING",
            )
            self.erreur_label.setText("Session file is not valid.")
        self.erreur_label.show()
