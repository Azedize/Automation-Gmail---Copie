import base64
import copy
import json
import os
import sys
import time
import traceback

from PyQt6 import uic
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor, QGuiApplication, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QInputDialog,
    QListWidget,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QWidget,
)

from api import API_MANAGER
from config import Settings
from core import EncryptionService, SessionManager
from core.runtime_state import runtime_state as default_runtime_state
from models import BrowserManager
from services import JsonManager
from ui_utils import UIManager
from ui_utils.authentication_window import AuthenticationWindow
from ui_utils.log_display_thread import ApplicationLogDisplayThread
from Update import UpdateManager
from utils import ValidationUtils


class AutomationMainWindow(QMainWindow):
    def __init__(self, json_data, stop_processes, start_extraction, runtime_state=None):
        super(AutomationMainWindow, self).__init__()
        self.stop_processes = stop_processes
        self.start_extraction = start_extraction
        self.runtime_state = runtime_state or default_runtime_state
        self.logs = self.runtime_state.logs
        self.notification_badges = self.runtime_state.notification_badges
        type(self)._default_start_extraction = start_extraction
        type(self)._default_runtime_state = self.runtime_state
        self._init_ui()
        self._init_data(json_data)
        self._setup_ui_components()
        self._load_initial_state()

    def _init_ui(self):
        Settings.write_log_dev_file("Initializing user interface...", "INFO")
        uic.loadUi(Settings.INTERFACE_UI, self)

    def _init_data(self, json_data):
        self.states = json_data
        self.STATE_STACK = []

    def _setup_ui_components(self):
        self._setup_containers()
        self._setup_template_widgets()
        self._setup_buttons()
        self._setup_comboboxes()
        self._setup_tab_widgets()
        self._setup_log_system()
        self._setup_miscellaneous()

    def _find_widget(self, name, widget_type=None):
        widget = (
            self.findChild(widget_type, name)
            if widget_type
            else self.findChild(QWidget, name)
        )
        Settings.write_log_dev_file(
            f"Searching for widget: {name} (type: {widget_type})", "INFO"
        )
        return widget

    def _setup_containers(self):
        UIManager.setupContainers(self)

    def _setup_template_widgets(self):
        UIManager.setupTemplateWidgets(self)

    def _setup_buttons(self):
        self.Button_Initaile_state = self._setup_button(
            "Button_Initaile_state", self.load_initial_options
        )
        self.submit_button = self._setup_button(
            "submitButton", lambda: self.submit_button_clicked(self)
        )
        self.ClearButton = self._setup_icon_button(
            "ClearButton",
            "clear.png",
            self.clear_button_clicked,
            icon_size=(32, 32),
            button_size=(36, 36),
        )
        self.CopyButton = self._setup_icon_button(
            "CopyButton",
            "copyLog.png",
            self.copy_logs_to_clipboard,
            icon_size=(26, 26),
            button_size=(38, 38),
        )
        self.SaveButton = self._setup_icon_button(
            "saveButton", "save.png", self.handle_save, icon_size=(16, 16)
        )
        self.log_out_Button = UIManager.setupLogoutButton(self, self.log_out)

    def _setup_icon_button(
        self, button_name, icon_file, callback, icon_size=None, button_size=None
    ):
        return UIManager.setupIconButton(
            self, button_name, icon_file, callback, icon_size, button_size
        )

    def _setup_button(self, widget_name, callback):
        return UIManager.setupButton(self, widget_name, callback)

    def _setup_comboboxes(self):
        self._setup_browser_combobox()
        self._setup_isp_combobox()
        self._setup_scenario_combobox()

    def _setup_browser_combobox(self):
        UIManager.setupBrowserCombobox(self)

    def _setup_isp_combobox(self):
        UIManager.setupIspCombobox(self)

    def _setup_scenario_combobox(self):
        UIManager.setupScenarioCombobox(self)

    def _setup_tab_widgets(self):
        UIManager.setupResultTabWidget(self)
        UIManager.setupInterfaceTabWidget(self)

    def _setup_log_system(self):
        self.log_container = self._find_widget("log", QWidget)
        if self.log_container is not None:
            self.log_text_edit = QPlainTextEdit(self.log_container)
            self.log_text_edit.setReadOnly(True)  # Lecture seule pour les logs
            self.log_text_edit.setStyleSheet(
                "QPlainTextEdit { background-color: #161a1d; color: #ffffff; font-size: 14px; font-family: 'Segoe UI'; border: none; padding: 8px; }"
            )
            self.log_text_edit.setFrameShape(QFrame.Shape.NoFrame)
            self.log_text_edit.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            self.log_text_edit.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            self.log_text_edit.document().setMaximumBlockCount(1000)

            rect = self.log_container.rect()
            width = rect.width() if rect.width() > 0 else 1600
            height = rect.height() if rect.height() > 0 else 9000
            margin_top = 60
            margin_side = 10
            self.log_text_edit.setGeometry(
                margin_side,
                margin_top,
                max(0, width - 2 * margin_side),
                max(0, height - margin_top - margin_side),
            )

        self.LOGS_THREAD = ApplicationLogDisplayThread(
            self.logs,
            lambda: self.runtime_state.logs_running,
        )
        self.LOGS_THREAD.log_signal.connect(self.update_logs_display)

    def _setup_miscellaneous(self):
        UIManager.setupMiscellaneous(self)

    def _load_initial_state(self):
        self.load_scenarios_into_combobox()
        self.load_initial_options()

    def save_process(self, params):
        return API_MANAGER.saveProcess(params)

    def handle_save(self):
        Settings.write_log_dev_file(
            f"Checking STATE_STACK: {len(self.STATE_STACK) if self.STATE_STACK else 0} items",
            "INFO",
        )
        if not self.STATE_STACK:
            UIManager.showCriticalMessage(
                self,
                "No Data",
                "No actions to save. Please add actions before saving.",
                message_type="critical",
            )
            Settings.write_log_dev_file(
                "No actions to save. Please add actions before saving.", "ERROR"
            )
            return

        scenario_name, ok = QInputDialog.getText(
            self, "Save Scenario", "Enter scenario name:"
        )

        if not ok:
            Settings.write_log_dev_file("User cancelled scenario name input", "INFO")
            return

        scenario_name = scenario_name.strip()
        Settings.write_log_dev_file(f"Scenario name entered: '{scenario_name}'", "INFO")

        if not scenario_name:
            Settings.write_log_dev_file("Scenario name cannot be empty", "ERROR")
            UIManager.showCriticalMessage(
                self,
                "Invalid Name",
                "Scenario name cannot be empty.",
                message_type="critical",
            )
            return

        Settings.write_log_dev_file(
            "Scenario name is valid, checking session file", "INFO"
        )
        if not ValidationUtils.pathExists(Settings.SESSION_PATH):
            Settings.write_log_dev_file(
                f"Session file not found at: {Settings.SESSION_PATH}", "ERROR"
            )
            UIManager.showCriticalMessage(
                self,
                "Session Not Found",
                "[❌] Your session file is missing. Please restart the application.",
                message_type="critical",
            )
            Settings.write_log_dev_file(
                "Your session file is missing. Please restart the application.", "ERROR"
            )
            return

        Settings.write_log_dev_file(
            "Session file exists, checking session validity", "INFO"
        )
        session_info = SessionManager.check_session()
        Settings.write_log_event(
            "session_checked", "INFO", valid=session_info.get("valid")
        )

        if not session_info["valid"]:
            Settings.write_log_dev_file("Session is invalid, exiting", "ERROR")
            sys.exit()
            return False

        Settings.write_log_dev_file("Session is valid, encrypting session info", "INFO")
        encrypted_String = EncryptionService.encrypt_message(
            f"{session_info['Id_User']}::{session_info['username']}::{session_info['date']}::IT",
            Settings.KEY,
        )
        Settings.write_log_dev_file(
            f"Encrypted string generated (length: {len(encrypted_String)})", "INFO"
        )
        Settings.write_log_dev_file("Preparing payload", "INFO")

        try:
            state_json = json.dumps(self.STATE_STACK[-1], ensure_ascii=False)
            state_stack_json = json.dumps(self.STATE_STACK, ensure_ascii=False)
            state_b64 = base64.b64encode(state_json.encode("utf-8")).decode("utf-8")
            state_stack_b64 = base64.b64encode(state_stack_json.encode("utf-8")).decode(
                "utf-8"
            )

        except Exception as e:
            Settings.write_log_dev_file(
                f"Error encoding state for saving: {e}\n{traceback.format_exc()}",
                "ERROR",
            )
            return

        payload = {
            "user_id": session_info["Id_User"],
            "encrypted": encrypted_String,
            "name": scenario_name,
            "state": state_b64,
            "state_stack": state_stack_b64,
        }
        Settings.write_log_dev_file(f"Complete payload prepared for API call", "INFO")

        Settings.write_log_dev_file("Building API URL", "INFO")
        Api_Url = (
            f"{Settings.SCENARIO_API}?rv4=1&entity=IT&action=add&l={encrypted_String}"
        )

        Settings.write_log_dev_file(f"API URL: {Api_Url}", "INFO")
        Settings.write_log_dev_file("Calling API...", "INFO")

        try:
            result = API_MANAGER.handleSaveScenario(payload, Api_Url)
            Settings.write_log_event(
                "save_scenario_response_received",
                "INFO",
                response_type=type(result).__name__,
                success=result.get("status") if isinstance(result, dict) else None,
            )

            if result.get("status") is False:
                Settings.write_log_dev_file(
                    "API returned status=False, showing error message", "INFO"
                )
                UIManager.showCriticalMessage(
                    self,
                    "Action Not Saved",
                    " The action could not be saved.\n\n"
                    "Your session may have expired, or this name already exists.\n Please verify your session and make sure the name is unique, then try again.",
                    message_type="critical",
                )
                Settings.write_log_dev_file(
                    "Save failed: session expired or action name already exists.",
                    "ERROR",
                )
                return

            if result.get("status"):
                Settings.write_log_dev_file(
                    "API returned status=True, scenario saved successfully", "INFO"
                )
                self.load_scenarios_into_combobox()
                UIManager.showCriticalMessage(
                    self,
                    "Success",
                    "The scenario has been saved successfully.",
                    message_type="success",
                )
                Settings.write_log_dev_file(
                    "The scenario has been saved successfully.", "INFO"
                )
            else:
                Settings.write_log_dev_file(
                    "API returned status=None or unexpected, showing API error", "INFO"
                )
                UIManager.showCriticalMessage(
                    self,
                    "API Error",
                    "An error occurred while saving the scenario.",
                    message_type="critical",
                )
                Settings.write_log_dev_file(
                    "An error occurred while saving the scenario.", "ERROR"
                )

        except Exception as e:
            Settings.write_log_dev_file(f"Exception during API call: {e}", "ERROR")
            UIManager.showCriticalMessage(
                self,
                "Error",
                "An error occurred while saving the scenario.",
                message_type="critical",
            )
            Settings.write_log_dev_file(
                f"An error occurred while saving the scenario: {str(e)}\n{traceback.format_exc()}",
                "ERROR",
            )

        Settings.write_log_dev_file("handle_save function completed", "INFO")

    def load_scenarios_into_combobox(self):
        Settings.write_log_dev_file("Starting load_scenarios_into_combobox()", "INFO")

        if self.saveSanario is None:
            Settings.write_log_dev_file("saveSanario is None", "ERROR")
            return

        if self.saveSanario is None:
            Settings.write_log_dev_file("saveSanario is None", "ERROR")
            return

        if not ValidationUtils.pathExists(Settings.SESSION_PATH):
            Settings.write_log_dev_file("Session file not found", "ERROR")
            return

        Settings.write_log_dev_file("Session file exists", "INFO")
        session_info = SessionManager.check_session()
        Settings.write_log_event(
            "session_checked", "INFO", valid=session_info.get("valid")
        )

        if not session_info.get("valid"):
            Settings.write_log_dev_file(
                "Session invalid. Redirecting to login.", "ERROR"
            )
            sys.exit()
            return False

        encrypted_String = EncryptionService.encrypt_message(
            f"{session_info['Id_User']}::{session_info['username']}::{session_info['date']}::IT",
            Settings.KEY,
        )
        Settings.write_log_dev_file(f"Encrypted string: {encrypted_String}", "INFO")
        Api_Url = (
            f"{Settings.SCENARIO_API}?rv4=1&action=get&entity=IT&l={encrypted_String}"
        )

        try:
            result = API_MANAGER.fetchScenarios(Api_Url)
            if isinstance(result, dict) and result.get("status") is False:
                Settings.write_log_dev_file(
                    f"API returned error: {result.get('error', 'Unknown error')}",
                    "ERROR",
                )
                self.saveSanario.clear()
                self.saveSanario.addItem("None")
                return

            scenarios = result if isinstance(result, list) else []
            Settings.write_log_dev_file(
                f"Number of scenarios loaded: {len(scenarios)}", "INFO"
            )

            self.saveSanario.clear()
            self.saveSanario.addItem("None")

            if scenarios:
                for index, scenario in enumerate(scenarios, 1):
                    name = scenario.get("name", f"Scénario {index}")
                    Settings.write_log_dev_file(
                        f"Adding scenario {index}: {name}", "INFO"
                    )
                    self.saveSanario.addItem(name)
            else:
                Settings.write_log_dev_file(
                    "No scenarios found, added 'None' only", "INFO"
                )
            Settings.write_log_dev_file("Combobox updated successfully", "INFO")
        except Exception as e:
            Settings.write_log_dev_file(
                f"An error occurred while loading scenarios: {str(e)}\n{traceback.format_exc()}",
                "CRITICAL",
            )

    def copy_logs_to_clipboard(self):
        UIManager.copyLogsToClipboard(self)

    def log_out(self):
        try:
            SessionManager.clear_session()
            if self.runtime_state.selected_browser:
                self.stop_processes(self)

            self.login_window = AuthenticationWindow(type(self), self.stop_processes)
            self.login_window.setFixedSize(
                Settings.WINDOW_WIDTH, Settings.WINDOW_HEIGHT
            )
            screen = QGuiApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.login_window.width()) // 2
            y = (screen_geometry.height() - self.login_window.height()) // 2
            self.login_window.move(x, y)
            self.login_window.show()
            self.close()

        except Exception as e:
            Settings.write_log_dev_file(
                f"An error occurred while logging out: {str(e)}\n{traceback.format_exc()}",
                "ERROR",
            )

    def update_logs_display(self, log_entry):
        UIManager.updateLogsDisplay(log_entry, self.log_text_edit)

    def extraction_finished(self, window):
        self.LOGS_THREAD.stopThread()
        self.LOGS_THREAD.wait()
        Settings.write_log_dev_file("Extraction Finished", "INFO")
        QTimer.singleShot(
            100,
            lambda: UIManager.readResultUpdateList(
                window, self.notification_badges
            ),
        )

    def verify_required_paths(self):
        Settings.write_log_dev_file("Starting required path verification", "INFO")

        paths = [
            (Settings.CONFIG_PROFILE, False),
            (Settings.EXTENTION_EX3_CHROMIUM, False),
            (Settings.SECURE_PREFERENCES_TEMPLATE, True),
            (Settings.FICHIER_LOCAL_STATE, True),
            (Settings.FICHIER_VARIATIONS, True),
        ]

        invalid_paths = []

        for path, is_file in paths:
            path_type = "file" if is_file else "directory"
            normalized_path = os.path.normpath(path) if path else path
            exists = os.path.exists(path)
            type_ok = os.path.isfile(path) if is_file else os.path.isdir(path)

            detail_msg = f"Path check: {normalized_path} | expected={path_type} | exists={exists} | type_ok={type_ok}"
            Settings.write_log_dev_file(detail_msg, "INFO")
            valid = ValidationUtils.validate_path(
                path, must_exist=True, is_file=is_file
            )

            if not valid:
                reason = (
                    "missing"
                    if not exists
                    else ("wrong type" if not type_ok else "unknown")
                )
                Settings.write_log_dev_file(
                    f"❌ Invalid path: {normalized_path} | expected={path_type} | exists={exists} | type_ok={type_ok} | reason={reason}",
                    "ERROR",
                )
                invalid_paths.append(
                    f"❌ Invalid path: {normalized_path} | expected={path_type} | exists={exists} | type_ok={type_ok} | reason={reason}"
                )

        if invalid_paths:
            Settings.write_log_dev_file(
                f"Required path verification failed: {len(invalid_paths)} invalid path(s)",
                "ERROR",
            )
        else:
            Settings.write_log_dev_file("All required paths are valid", "SUCCESS")
        return len(invalid_paths) == 0, invalid_paths

    def submit_button_clicked(self, window):
        UIManager.disableButton(self.submitButton)
        session_info = SessionManager.check_session()
        if not session_info["valid"]:
            self.login_window = AuthenticationWindow(type(self), self.stop_processes)
            self.login_window.setFixedSize(
                Settings.WINDOW_WIDTH, Settings.WINDOW_HEIGHT
            )

            screen = QGuiApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.login_window.width()) // 2
            y = (screen_geometry.height() - self.login_window.height()) // 2
            self.login_window.move(x, y)
            self.login_window.show()
            self.close()

            try:
                with open(Settings.SESSION_PATH, "w", encoding="utf-8") as f:
                    f.write("")
            except Exception as e:
                Settings.write_log_dev_file(
                    f"An error occurred while cleaning the session: {str(e)}\n{traceback.format_exc()}",
                    "ERROR",
                )
            UIManager.enableButton(self.submitButton)
            return

        auth_result = SessionManager.check_api_credentials(
            session_info.get("username"), session_info.get("password")
        )

        if isinstance(auth_result, int):
            messages = {
                -1: "Invalid credentials. Please login again.",
                -2: "This device is not authorized.",
                -3: "Unable to connect to the server.",
                -4: "Access denied for this application.",
                -5: "Unknown authentication error.",
            }

            self.erreur_label.setText(
                messages.get(auth_result, "Authentication failed.")
            )
            self.erreur_label.show()
            UIManager.enableButton(self.submitButton)
            return
        else:
            Settings.write_log_dev_file("Authentication successful", "INFO")

        is_valid, errors = self.verify_required_paths()
        if is_valid:
            Settings.write_log_dev_file("All required paths are valid.", "INFO")
        else:
            Settings.write_log_dev_file("Error with required paths.", "ERROR")
            error_details = "\n".join(errors)
            UIManager.showCriticalMessage(
                window,
                "Invalid Paths",
                f"The following paths are invalid:\n\n{error_details}",
                message_type="critical",
            )
            UIManager.enableButton(self.submitButton)
            return

        try:
            Settings.write_log_dev_file("Start badge cleanup", "INFO")
            if self.result_tab_widget:
                Settings.write_log_dev_file(
                    f"Number of tabs in result_tab_widget = {self.result_tab_widget.count()}",
                    "INFO",
                )

                for tab_index, badge in self.notification_badges.items():
                    if badge:
                        Settings.write_log_dev_file(
                            f"Badge removed tab_index={tab_index}", "INFO"
                        )
                        badge.deleteLater()

                self.notification_badges.clear()
                Settings.write_log_dev_file(
                    "All existing badges removed and dictionary cleared", "INFO"
                )

                for i in range(self.result_tab_widget.count()):
                    tab = self.result_tab_widget.widget(i)
                    if tab:
                        list_widgets = tab.findChildren(QListWidget)
                        for lw_index, lw in enumerate(list_widgets):
                            lw.clear()

            else:
                Settings.write_log_dev_file("result_tab_widget is None", "WARNING")

        except Exception as e:
            Settings.write_log_dev_file(
                f"An error occurred while removing badges: {str(e)}\n{traceback.format_exc()}",
                "ERROR",
            )
            UIManager.enableButton(self.submitButton)
            return

        update_result = UpdateManager.checkAndUpdate(window=self)
        if update_result is False:
            Settings.write_log_dev_file(
                "Mise à jour détectée : checkV3.py lancé et AppV2 fermé.", "INFO"
            )
            QApplication.instance().quit()
            return
        if update_result is None:
            Settings.write_log_dev_file(
                "Aucune mise à jour appliquée ou vérification indisponible; poursuite normale.",
                "WARNING",
            )

        selected_Browser = self.browser.currentText()
        QApplication.processEvents()

        browser_path = BrowserManager.get_browser_executable_path(selected_Browser)

        if browser_path is None:
            Settings.write_log_dev_file(
                f"Unable to find path for browser: {selected_Browser}", "ERROR"
            )
            UIManager.showCriticalMessage(
                window,
                "Browser Not Found",
                f"Unable to find the path for the selected browser: {selected_Browser}.\n\nPlease ensure the browser is installed and try again.",
                message_type="critical",
            )
            UIManager.enableButton(self.submitButton)
            return

        # browser_check_version = UpdateManager.checkExtensionVersion(window, selected_Browser.lower())
        # if browser_check_version is False:
        #     Settings.write_log_dev_file(f"Extension check bloqué pour le navigateur sélectionné: {selected_Browser}","ERROR")
        #     UIManager.enableButton(self.submitButton)
        #     return

        # if browser_check_version is not True:
        #     remote_version = browser_check_version if isinstance(browser_check_version, str) else None
        #     if remote_version is not None:
        #         valid_extension = UpdateManager.validateBrowserExtensionVersion(  selected_Browser, remote_version,  target_name="EX3",  window=window)
        #         if not valid_extension:
        #             UIManager.enableButton(self.submitButton)
        #             return
        #     elif selected_Browser:
        #         installed_version = UpdateManager.getInstalledBrowserExtensionVersion(selected_Browser.lower(), "EX3")
        #         if installed_version is None:
        #             UIManager.showCriticalMessage( window, "Extension not detected",  f"The EX3 extension could not be found in {selected_Browser}. Please contact support to validate the installation before continuing.",  message_type="warning")
        #             UIManager.enableButton(self.submitButton)
        #             return

        if self.INTERFACE:
            for i in range(self.INTERFACE.count()):
                if UIManager.isResultTab(self.INTERFACE, i):
                    UIManager.resetResultTabLabel(self.INTERFACE, i)
        self.runtime_state.logs_running = True

        if self.scenario_layout.count() == 0:
            UIManager.showCriticalMessage(
                window,
                "Empty Scenario",
                "No actions have been added. Please add actions before submitting.",
                message_type="warning",
            )
            UIManager.enableButton(self.submitButton)
            Settings.write_log_dev_file(
                "No actions have been added. Please add actions before submitting.",
                "WARNING",
            )
            return

        try:
            result = ValidationUtils.generateUserInputData(window)

            if not isinstance(result, dict):
                Settings.write_log_dev_file(
                    "Invalid result format returned from ValidationUtils.generateUserInputData",
                    "ERROR",
                )
                UIManager.enableButton(self.submitButton)
                return

            if not result.get("valid"):
                Settings.write_log_dev_file(
                    "❌ [DATA ERROR] Input or proxy validation failed before browser processes were started.",
                    "ERROR",
                )

                title, detail_text = (
                    result.get("error", "Unknown error").split(":", 1)
                    if ":" in result.get("error", "Unknown error")
                    else (
                        result.get("error", "Unknown error"),
                        result.get("error", "Unknown error"),
                    )
                )

                Settings.write_log_dev_file(
                    f"Data error: {result.get('error', 'Unknown error')}", "ERROR"
                )
                Settings.write_log_dev_file(
                    f"Title: {title.strip()} | Detail: {detail_text.strip()}", "ERROR"
                )
                Settings.write_log_dev_file(
                    f"Generate_User_Input_Data failed: {result.get('error', 'Unknown error')}",
                    "ERROR",
                )
                UIManager.showCriticalMessage(
                    window, title.strip(), detail_text.strip(), message_type="warning"
                )
                UIManager.enableButton(self.submitButton)
                return

            data_list = result.get("data") or []
            entered_number = result.get("entered_number")

            if not isinstance(data_list, list):
                Settings.write_log_dev_file("Data list is not a list", "ERROR")
                UIManager.enableButton(self.submitButton)
                return

            Settings.write_log_dev_file(
                f"User input processed successfully | Records: {len(data_list)} | Entered number: {entered_number}",
                "INFO",
            )

        except Exception as e:
            Settings.write_log_dev_file(
                f"Processing error: {e}\n{traceback.format_exc()}", "ERROR"
            )
            UIManager.showCriticalMessage(
                window,
                "Unexpected Error",
                "Something went wrong while processing your request.\n\nPlease try again or contact support.",
                message_type="critical",
            )
            UIManager.enableButton(self.submitButton)
            return

        Settings.write_log_dev_file("Final JSON:", "INFO")
        result_json = JsonManager.generateJson(self.scenario_layout, selected_Browser)
        Settings.write_log_dev_file(
            f"Final JSON generated. Data: {json.dumps(result_json, indent=2, ensure_ascii=False)}",
            "INFO",
        )
        Settings.write_log_dev_file("The final JSON has been generated.", "INFO")
        QApplication.processEvents()

        if not result_json or result_json == []:
            UIManager.showCriticalMessage(
                window,
                "Error - Save Configuration",
                "No valid actions could be generated or an error occurred while saving the configuration file.\n\nIf the problem persists, contact Support.",
                message_type="critical",
            )
            Settings.write_log_dev_file(
                "No valid actions could be generated or an error occurred while saving the configuration file.",
                "ERROR",
            )
            UIManager.enableButton(self.submitButton)
            return

        QApplication.processEvents()
        try:
            with open(Settings.FILE_ISP, "w", encoding="utf-8") as f:
                f.write(self.Isp.currentText().strip())
        except Exception as e:
            UIManager.enableButton(self.submitButton)

            Settings.write_log_dev_file(
                f"Error writing to Isp.txt: {e}\n{traceback.format_exc()}", "ERROR"
            )

        QApplication.processEvents()
        json_string = json.dumps(result_json)

        parameters = {
            "p_owner": session_info["username"],
            "p_entity": session_info["p_entity_Origine"],
            "p_isp": self.Isp.currentText(),
            "p_action_name": json_string,
            "p_app": "V4",
            "p_python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
            "p_browser": self.browser.currentText(),
        }

        unique_id = self.save_process(parameters)
        if unique_id == -1:
            UIManager.showCriticalMessage(
                window,
                "Error - Process Save",
                "Failed to save the process in the database.\n\nPlease check your connection and try again.",
                message_type="critical",
            )
            Settings.write_log_dev_file(
                "Failed to save the process in the database.", "ERROR"
            )
            UIManager.enableButton(self.submitButton)
            return

        QApplication.processEvents()

        self.start_extraction(
            window,
            data_list,
            entered_number,
            selected_Browser,
            self.Isp.currentText(),
            unique_id,
            result_json,
            session_info["username"],
        )
        self.LOGS_THREAD.start()
        QApplication.processEvents()

    def load_initial_options(self):
        while self.reset_options_layout.count() > 0:
            item = self.reset_options_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for key, state in self.states.items():
            if state.get("showOnInit", False):
                self.create_option_button(state)

    def create_option_button(self, state):
        default_icon_path = os.path.join(Settings.ICONS_DIR, "icon.png")
        default_icon_path_Templete2 = os.path.join(Settings.ICONS_DIR, "next.png")
        is_multi = state.get("isMultiSelect", False)

        if is_multi:
            template_button = self.Temeplete_Button_2
            icon_path = default_icon_path_Templete2
        else:
            template_button = self.template_button
            icon_path = default_icon_path
        button = QPushButton(
            state.get("label", "Unnamed"), self.reset_options_container
        )
        button.setStyleSheet(template_button.styleSheet())
        button.setFixedSize(template_button.size())
        button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        button.clicked.connect(lambda _, s=state: self.load_state(s))
        if ValidationUtils.pathExists(icon_path):
            button.setIcon(QIcon(icon_path))
        else:
            Settings.write_log_dev_file(
                f"[Warning] Icon not found at: {icon_path}", "WARNING"
            )
        self.reset_options_layout.addWidget(button)

    def load_state(self, state):
        is_multi = state.get("isMultiSelect", False)
        if not is_multi:
            self.STATE_STACK.append(state)

        if not is_multi:
            template = state.get("Template", "")
            UIManager.updateScenario(self, template, state)

        actions = state.get("actions", [])
        self.update_reset_options(actions)
        self.update_actions_color_handle_last_button()
        UIManager.removeCopier(self.scenario_layout, self.reset_options_layout)
        UIManager.removeInitial(self.scenario_layout, self.reset_options_layout)

    def update_actions_color_handle_last_button(self):
        UIManager.updateActionsColorHandleLastButton(
            self.scenario_layout, self.go_to_previous_state
        )

    def update_reset_options(self, actions):
        count = self.reset_options_layout.count()
        for i in reversed(range(count)):
            widget = self.reset_options_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        if not actions:
            self.load_initial_options()
            return
        for action_key in actions:
            state = self.states.get(action_key)
            if state:
                label = state.get("label", action_key)
                self.create_option_button(state)

    def go_to_previous_state(self):
        if len(self.STATE_STACK) > 1:
            if self.scenario_layout.count() > 0:
                last_item = self.scenario_layout.takeAt(
                    self.scenario_layout.count() - 1
                )
                if last_item.widget():
                    last_item.widget().deleteLater()

            self.STATE_STACK.pop()
            previous_state = self.STATE_STACK[-1]
            self.update_reset_options(previous_state.get("actions", []))
        else:
            self.STATE_STACK.clear()
            while self.scenario_layout.count() > 0:
                last_item = self.scenario_layout.takeAt(0)
                if last_item.widget():
                    last_item.widget().deleteLater()
            self.load_initial_options()
        self.update_actions_color_handle_last_button()
        UIManager.removeCopier(self.scenario_layout, self.reset_options_layout)

    def clear_button_clicked(self):
        self.log_text_edit.clear()
        self.logs.clear()

    def scenario_changed(self, name_selected):
        session_info = SessionManager.check_session()
        if not session_info.get("valid"):
            Settings.write_log_dev_file(
                "Session invalid. Redirecting to login.", "ERROR"
            )
            sys.exit()
            return False

        encrypted_string = EncryptionService.encrypt_message(
            f"{session_info['Id_User']}::{session_info['username']}::{session_info['date']}::IT",
            Settings.KEY,
        )
        api_url = (
            f"{Settings.SCENARIO_API}?rv4=1&action=get&entity=IT&l={encrypted_string}"
        )

        try:
            raw_result = API_MANAGER.fetchScenarios(
                api_url, params={"name": name_selected}
            )
        except Exception as e:
            Settings.write_log_dev_file(
                f"API call failed: {e} \n {traceback.format_exc()}", "ERROR"
            )
            return

        if isinstance(raw_result, dict) and raw_result.get("status") is False:
            Settings.write_log_dev_file(
                f"API returned error: {raw_result.get('error', 'Unknown API error')}",
                "ERROR",
            )
            return

        if isinstance(raw_result, list):
            data_list = raw_result
        elif isinstance(raw_result, dict) and "data" in raw_result:
            data_list = raw_result["data"]
        else:
            Settings.write_log_dev_file(
                f"Unexpected API result format: {type(raw_result)}", "ERROR"
            )
            return

        if not data_list:
            Settings.write_log_dev_file("No scenario returned from API.", "WARNING")
            return

        scenario = next(
            (item for item in data_list if item.get("name") == name_selected),
            None,
        )
        if scenario is None:
            Settings.write_log_dev_file(
                f"Scenario not found in API response: {name_selected}",
                "WARNING",
            )
            return

        for i in reversed(range(self.scenario_layout.count())):
            item = self.scenario_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget_name = (
                        widget.objectName()
                        if widget.objectName()
                        else widget.__class__.__name__
                    )
                    Settings.write_log_dev_file(
                        f"🗑️ Removing widget: {widget_name}", "INFO"
                    )
                    widget.deleteLater()

        state_stack = scenario.get("state_stack", [])
        if isinstance(state_stack, str):
            state_stack = state_stack.strip()
            try:
                state_stack = json.loads(state_stack)
            except json.JSONDecodeError:
                try:
                    state_stack = json.loads(
                        base64.b64decode(state_stack).decode("utf-8")
                    )
                except Exception as e:
                    Settings.write_log_dev_file(
                        f"Failed to parse state_stack: {e}\n{traceback.format_exc()}",
                        "WARNING",
                    )
                    return

        if not isinstance(state_stack, list):
            Settings.write_log_dev_file(
                "Scenario state_stack has an invalid format.", "WARNING"
            )
            return

        self.STATE_STACK = state_stack
        Settings.write_log_dev_file(
            f"📥 Scenario loaded with {len(self.STATE_STACK)} states.", "INFO"
        )

        state_stack_copy = copy.deepcopy(self.STATE_STACK)

        for index, state in enumerate(state_stack_copy, start=1):
            try:
                pretty = json.dumps(state, indent=2, ensure_ascii=False, default=str)
            except Exception:
                pretty = repr(state)

            try:
                t0 = time.time()
                self.load_state(state)
                t1 = time.time()
                Settings.write_log_dev_file(
                    f"✅ load_state for #{index} succeeded in {t1 - t0:.3f}s", "INFO"
                )
                try:
                    self.update_actions_color_handle_last_button()
                except Exception as e:
                    Settings.write_log_dev_file(
                        f"⚠️ update_actions_color_handle_last_button failed after state #{index}: {e} \n {traceback.format_exc()}",
                        "WARNING",
                    )
            except Exception as e:
                Settings.write_log_dev_file(
                    f"❌ Error during load_state() for state #{index}: {e}\n{traceback.format_exc()}",
                    "WARNING",
                )
                continue

        try:
            unique_states = []
            seen = set()
            for state in self.STATE_STACK:
                try:
                    state_key = json.dumps(
                        state, sort_keys=True, ensure_ascii=False, default=str
                    )
                except Exception:
                    state_key = repr(state)
                if state_key not in seen:
                    seen.add(state_key)
                    unique_states.append(state)
            self.STATE_STACK = unique_states
        except Exception as e:
            Settings.write_log_dev_file(
                f"⚠️ Failed to deduplicate STATE_STACK: {e}\n{traceback.format_exc()}",
                "ERROR",
            )



