# ui_utils.py
import os
import traceback
import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QIcon, QColor
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6 import QtWidgets, QtGui, QtCore
import PyQt6
from collections import defaultdict
from functools import partial
import sys
from pathlib import Path
from PyQt6.QtGui import QTextCursor
from PyQt6.QtGui import QPainter
from PyQt6.QtGui import QPen

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from config import Settings
    from utils.validation_utils import ValidationUtils
except ImportError as e:
    sys.exit(1)  



class VerticalTabBar(QtWidgets.QTabBar):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setShape(QtWidgets.QTabBar.Shape.RoundedWest)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.tab_margin = 0
        self.left_margin = 0
        self.right_margin = 0

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.update()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.update()

    def tabSizeHint(self, index):
        size_hint = super().tabSizeHint(index)
        size_hint.transpose()
        size_hint.setWidth(180)
        size_hint.setHeight(60)
        return size_hint

    def tabRect(self, index):
        rect = super().tabRect(index)
        rect.adjust(self.left_margin, self.tab_margin, -self.right_margin, -self.tab_margin)
        return rect

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        hovered_index = self.tabAt(self.mapFromGlobal(QtGui.QCursor.pos()))
        for index in range(self.count()):
            tab_rect = self.tabRect(index)
            if not tab_rect.isValid():
                continue
            selected = self.currentIndex() == index
            hovered = hovered_index == index and not selected
            tab_data = self.tabData(index)
            text = self.tabText(index)

            if isinstance(tab_data, dict) and text == "Result":
                bg_color = QtGui.QColor(0, 0, 0, 0)
                if selected:
                    pen_color = QtGui.QColor("#ffffff")
                elif hovered:
                    pen_color = QtGui.QColor(Settings.PRIMARY_COLOR)
                else:
                    pen_color = QtGui.QColor("#333333")

                painter.save()
                painter.setPen(QtCore.Qt.PenStyle.NoPen)
                painter.setBrush(QtGui.QBrush(bg_color))
                painter.drawRect(tab_rect)
                painter.restore()

                painter.save()
                font = QFont(Settings.FONT_FAMILY, 10)
                painter.setFont(font)
                text_rect = QtCore.QRect(  tab_rect.left() + 12,  tab_rect.top() + 8, tab_rect.width() - 24,tab_rect.height() - 16 )

                fm = painter.fontMetrics()
                title_text = "Result "
                completed_text = f"({tab_data['completed']} Completed"
                separator_text = " / "
                not_completed_text = f"{tab_data['not_completed']} Not Completed)"

                x = text_rect.left()
                y = text_rect.center().y() + fm.ascent() // 2 - 2

                painter.setPen(QtGui.QPen(pen_color))
                painter.drawText(x, y, title_text)
                x += fm.horizontalAdvance(title_text)
                painter.setPen(QtGui.QPen(QtGui.QColor("#28a745")))
                painter.drawText(x, y, completed_text)
                x += fm.horizontalAdvance(completed_text)
                painter.setPen(QtGui.QPen(pen_color))
                painter.drawText(x, y, separator_text)
                x += fm.horizontalAdvance(separator_text)

                painter.setPen(QtGui.QPen(QtGui.QColor("#dc3545")))
                painter.drawText(x, y, not_completed_text)
                painter.restore()
            else:
                if selected:
                    bg_color = QtGui.QColor(Settings.PRIMARY_COLOR)
                    pen_color = QtGui.QColor("#ffffff")
                elif hovered:
                    bg_color = QtGui.QColor(Settings.PRIMARY_COLOR).lighter(140)
                    pen_color = QtGui.QColor("#000000")
                else:
                    bg_color = QtGui.QColor("#F5F5F5")
                    pen_color = QtGui.QColor("#333333")

                painter.save()
                painter.setPen(QtCore.Qt.PenStyle.NoPen)
                painter.setBrush(QtGui.QBrush(bg_color))
                painter.drawRect(tab_rect)
                border_pen = QtGui.QPen(QtGui.QColor(Settings.PRIMARY_COLOR))
                border_pen.setWidth(1)
                painter.setPen(border_pen)
                painter.drawLine(tab_rect.bottomLeft(), tab_rect.bottomRight())
                painter.drawLine(tab_rect.topRight(), tab_rect.bottomRight())
                painter.restore()

                painter.save()
                font = QFont(Settings.FONT_FAMILY, 10)
                painter.setFont(font)
                painter.setPen(QtGui.QPen(pen_color))
                text_rect = QtCore.QRect(  tab_rect.left() + 12,  tab_rect.top() + 8,  tab_rect.width() - 24, tab_rect.height() - 16 )
                painter.drawText(  text_rect,   QtCore.Qt.AlignmentFlag.AlignVCenter  | QtCore.Qt.AlignmentFlag.AlignLeft,   text )
                painter.restore()
        painter.end()


class VerticalTabWidget(QtWidgets.QTabWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabBar(VerticalTabBar())
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)


class CustomTextDialog(QDialog):

    def __init__(self, parent=None, texte_initial=""):
        super().__init__(parent)
        self.setWindowTitle("Update Text")
        self.setMinimumSize(500, 350)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        label = QLabel("📝 Please enter your text below:")
        layout.addWidget(label)
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(texte_initial)
        layout.addWidget(self.text_edit)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        self.btn_ok = QPushButton("Save")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.setStyleSheet(f"QDialog {{ background-color: #ffffff; font-family: {Settings.FONT_FAMILY}; }} QLabel {{ font-family: {Settings.FONT_FAMILY}; font-size: 14px; color: #2d2d2d; font-weight: 500; margin-bottom: 10px; }} QTextEdit {{ border: 1px solid #d0d0d0; border-radius: 10px; font-family: {Settings.FONT_FAMILY}; background-color: #fafafa; font-size: 12pt; padding: 5px; }} QTextEdit:focus {{ border: 2px solid #0078d7; background-color: #ffffff; }} QPushButton {{ font-family: {Settings.FONT_FAMILY}; padding: 8px 16px; text-align: center; font-size: 14px; font-weight: bold; min-width: 120px; }} QPushButton#btn_ok {{ background-color: #0078d7; border: none; color: white; }} QPushButton#btn_ok:hover {{ background-color: #005a9e; }} QPushButton#btn_cancel {{ background-color: #f0f0f0; border: 1px solid #cccccc; color: #333333; }} QPushButton#btn_cancel:hover {{ background-color: #e0e0e0; }}")
        self.btn_ok.setObjectName("btn_ok")
        self.btn_cancel.setObjectName("btn_cancel")

    def getText(self):
        return self.text_edit.toPlainText()


class UIManager:

    @staticmethod
    def resetResultTabLabel(tab_widget, index):
        """Reset a Result tab to its default plain state before Submit starts."""
        if tab_widget is None or index < 0 or index >= tab_widget.count():
            return

        tab_bar = tab_widget.tabBar()
        if tab_bar is None:
            return

        left_button = tab_bar.tabButton(index, QTabBar.ButtonPosition.LeftSide)
        right_button = tab_bar.tabButton(index, QTabBar.ButtonPosition.RightSide)
        if left_button is not None:
            left_button.deleteLater()
            tab_bar.setTabButton(index, QTabBar.ButtonPosition.LeftSide, None)
        if right_button is not None:
            right_button.deleteLater()
            tab_bar.setTabButton(index, QTabBar.ButtonPosition.RightSide, None)

        tab_widget.setTabText(index, "Result")

        if hasattr(tab_bar, "setTabData"):
            try:
                tab_bar.setTabData(index, None)
            except Exception as exc:
                Settings.write_log_event("ui_tab_reset_failed", "WARNING", index=index, exception_type=type(exc).__name__, error=str(exc))

        tab_bar.update()
        tab_widget.update()

    @staticmethod
    def logTabDebugInfo(tab_widget, prefix=""):
        """Log tab names, tabData and custom button states for debugging."""
        if tab_widget is None:
            return

        tab_bar = tab_widget.tabBar()
        if tab_bar is None:
            return

        tab_count = tab_widget.count()
        message = [f"{prefix} tabs={tab_count}"]

        for i in range(tab_count):
            tab_text = tab_widget.tabText(i)
            tab_data = tab_bar.tabData(i) if hasattr(tab_bar, "tabData") else None
            left_button = tab_bar.tabButton(i, QTabBar.ButtonPosition.LeftSide)
            right_button = tab_bar.tabButton(i, QTabBar.ButtonPosition.RightSide)
            message.append( f"index={i} text={tab_text!r} data={tab_data!r} left={type(left_button).__name__} right={type(right_button).__name__}"  )
        log_text = " | ".join(message)
        try:
            Settings.write_log_dev_file(f"[UI TRACE] {log_text}", "DEBUG")
        except Exception as exc:
            Settings.write_log_event("ui_tab_debug_failed", "WARNING", exception_type=type(exc).__name__, error=str(exc))

    

    @staticmethod
    def isResultTab(tab_widget, index):
        if tab_widget is None or index < 0 or index >= tab_widget.count():
            return False
        tab_bar = tab_widget.tabBar()
        if tab_bar is not None and hasattr(tab_bar, "tabData"):
            tab_data = tab_bar.tabData(index)
            if (  isinstance(tab_data, dict)   and "completed" in tab_data  and "not_completed" in tab_data ):
                return True

        tab_text = tab_widget.tabText(index)
        return isinstance(tab_text, str) and tab_text.startswith("Result")

    @staticmethod
    def setCustomColoredTab(tab_widget, index, completed_count, not_completed_count):
        main_color = Settings.PRIMARY_COLOR or "#669bbc"
        accent_color = Settings.ACCENT_COLOR or "#dc3545"

        html_text = (
            f'<div style="text-align:center; margin:0; padding:0;">'
            f"<span style=\"font-family:'Times', 'Times New Roman', serif; font-size:14px;\">Result ("
            f'<span style="color:#008000;">{completed_count} completed</span> / '
            f'<span style="color:{accent_color};">{not_completed_count} not completed</span>)</span>'
            f"</div>"
        )

        tab_widget.setTabText(index, "")

        label = QLabel()
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setText(html_text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)  
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        label.setStyleSheet(f"QLabel {{ background: transparent; color: {main_color}; font-family: 'Times', 'Times New Roman', serif; font-size: 14px; }} QLabel:hover {{ color:#2c3e50; }}")

        wrapper = QWidget()
        wrapper.setStyleSheet("QWidget { background: transparent; border: none; }")
        wrapper.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        wrapper.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        wrapper.setMouseTracking(True)

        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(label)

        wrapper.setSizePolicy( QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred )

        tab_rect = tab_widget.tabBar().tabRect(index)
        if tab_rect.isValid():
            wrapper.setMinimumWidth(tab_rect.width())
            wrapper.setFixedHeight(tab_rect.height())

        tab_bar = tab_widget.tabBar()
        tab_bar.setTabButton(index, QTabBar.ButtonPosition.LeftSide, None)
        tab_bar.setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
        tab_bar.setTabButton(index, QTabBar.ButtonPosition.LeftSide, wrapper)

        if hasattr(tab_bar, "setTabData"):
            try:
                tab_bar.setTabData( index, { "completed": completed_count, "not_completed": not_completed_count } )
            except Exception as exc:
                Settings.write_log_event("ui_tab_data_update_failed", "WARNING", index=index, exception_type=type(exc).__name__, error=str(exc))


    @staticmethod
    def clearResultFile():
        try:
            Path(Settings.RESULT_FILE_PATH).write_text("", encoding="utf-8")
            Settings.write_log_dev_file(f"Le fichier {Settings.RESULT_FILE_PATH} a été vidé avec succès", "INFO")

        except Exception as e:
            Settings.write_log_dev_file(  f"Error clearing result file: {e}\n{traceback.format_exc()}", "ERROR" )

 
    @staticmethod
    def readResultUpdateList(window, NOTIFICATION_BADGES):

        if not ValidationUtils.pathExists(Settings.RESULT_FILE_PATH):
            UIManager.showCriticalMessage( window, "Information", "No emails have been processed yet.\nPlease check the filters or new data.",  message_type="info" )
            return

        errors_dict = defaultdict(list)
        all_emails = []

        try:
            with open(Settings.RESULT_FILE_PATH, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]

            QApplication.processEvents()  
            if not lines:
                UIManager.showCriticalMessage(  window, "Warning", "No results available.", message_type="warning" )
                return

            completed_count = 0
            no_completed_count = 0

            for idx, line in enumerate(lines, start=1):
                parts = line.split(":")
                if len(parts) != 4:
                    continue
                _, _, email, status = [p.strip() for p in parts]
                all_emails.append(email)
                errors_dict[status].append(email)

                if status == "completed":
                    completed_count += 1
                else:
                    no_completed_count += 1

            errors_dict["all"] = all_emails
            QApplication.processEvents()

            interface_tab_widget = window.findChild(QTabWidget, "interface_2")
            if interface_tab_widget:
                UIManager.logTabDebugInfo( interface_tab_widget, prefix="Before Result update"  )
                found = False
                for i in range(interface_tab_widget.count()):
                    if UIManager.isResultTab(interface_tab_widget, i):
                        found = True
                        UIManager.setCustomColoredTab(  interface_tab_widget, i, completed_count, no_completed_count  )
                        break

                if not found:
                    try:
                        Settings.write_log_dev_file("Result tab non trouvé dans interface_2", "WARNING")
                        UIManager.logTabDebugInfo( interface_tab_widget, prefix="Result tab non trouvé")
                    except Exception:
                        Settings.write_log_dev_file("Result tab non trouvé et impossible de logger l'état des tabs", "ERROR")
                        pass
            else:
                try:
                    Settings.write_log_dev_file("[UI WARNING] interface_2 introuvable pour la mise à jour du tab Result", "WARNING")
                except Exception:
                    Settings.write_log_dev_file("Erreur lors de la mise à jour du tab Result", "ERROR")
                    pass
            QApplication.processEvents()     

            result_tab_widget = window.findChild(QTabWidget, "tabWidgetResult")
            if not result_tab_widget:
                Settings.write_log_dev_file("TabWidgetResult introuvable dans la fenêtre pour mise à jour des résultats", "ERROR")
                return

            for status in Settings.STATUS_LIST:
                tab_widget = result_tab_widget.findChild(QWidget, status)
                if not tab_widget:
                    Settings.write_log_dev_file(f"Tab pour le statut '{status}' introuvable dans tabWidgetResult", "WARNING")
                    continue

                list_widgets = tab_widget.findChildren(QListWidget)
                if not list_widgets:
                    Settings.write_log_dev_file(f"QListWidget introuvable dans le tab '{status}'", "WARNING")
                    continue

                list_widget = list_widgets[0]
                list_widget.clear()
                emails = errors_dict.get(status, [])

                if emails:
                    list_widget.addItems(emails)
                    list_widget.scrollToBottom()
                    UIManager.addNotificationBadge( result_tab_widget, result_tab_widget.indexOf(tab_widget), len(emails), NOTIFICATION_BADGES )
                    Settings.write_log_dev_file(f"{len(emails)} emails ajoutés au tab '{status}'", "INFO")
                    message_label = tab_widget.findChild(QLabel, "no_data_message")
                    if message_label:
                        message_label.deleteLater()
                else:
                    list_widget.addItem("⚠ No email data available for this category currently." )
                    list_widget.show()
            QApplication.processEvents()  
        except Exception as e:
            Settings.write_log_dev_file( f"Une erreur est survenue: {type(e).__name__} : {e}\n{traceback.format_exc()}","ERROR" )
        finally:
            UIManager.clearResultFile()



    @staticmethod
    def removeNotification(index, NOTIFICATION_BADGES):
        badge = NOTIFICATION_BADGES.pop(index, None)
        if badge:
            badge.deleteLater()

    @staticmethod
    def addNotificationBadge(tab_widget, tab_index, count, NOTIFICATION_BADGES):
        old_badge = NOTIFICATION_BADGES.get(tab_index)
        if old_badge:
            old_badge.deleteLater()

        tab_bar = tab_widget.tabBar()
        tab_rect = tab_bar.tabRect(tab_index)
        badge_x = tab_rect.right() - 14
        badge_y = tab_rect.top() + 2
        badge_label = QLabel(f"{count}", tab_widget)
        badge_label.setStyleSheet("background-color: #d90429; color: white; font-size: 14px; padding: 3px; border-radius: 10px; min-width: 15px; text-align: center;")
        badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        try:
            badge_label.setParent(tab_widget)
            badge_label.move(badge_x, badge_y)
            badge_label.show()
            NOTIFICATION_BADGES[tab_index] = badge_label
            tab_widget.update()
            tab_bar.update()
        except Exception as e:
            Settings.write_log_dev_file(  f"Error adding notification badge: {e}\n{traceback.format_exc()}", "ERROR" )



    @staticmethod
    def showCriticalMessage(window, title, message, message_type="critical"):
        dialog = QMessageBox(window)

        colors = {"critical": {"icon_bg": "#ffebee", "icon_color": "#d32f2f", "button_start": "#ef5350", "button_end": "#b71c1c", "icon": QMessageBox.Icon.Critical}, "warning": {"icon_bg": "#fff3e0", "icon_color": "#f57c00", "button_start": "#ffb74d", "button_end": "#e65100", "icon": QMessageBox.Icon.Warning}, "info": {"icon_bg": "#e1f5fe", "icon_color": "#0288d1", "button_start": "#4fc3f7", "button_end": "#01579b", "icon": QMessageBox.Icon.Information}, "success": {"icon_bg": "#e8f5e9", "icon_color": "#388e3c", "button_start": "#81c784", "button_end": "#1b5e20", "icon": QMessageBox.Icon.Information}}

        c = colors.get(message_type, colors["info"])
        dialog.setIcon(c["icon"])
        dialog.setWindowTitle(title)
        dialog.setText(f'<div style="background-color:{c["icon_bg"]}; padding:20px; color:{c["icon_color"]}; font-size:15px; font-weight:600; line-height:1.5; font-family: Segoe UI, Roboto, sans-serif; border: 1px solid {UIManager.darkenColor(c["icon_color"], 30)}">{message}</div>')
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        dialog.setGraphicsEffect(shadow)
        dialog.setStyleSheet(f"QMessageBox {{ background-color: {c['icon_bg']}; padding: 20px; min-width: 450px; font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif; font-size: 14px; }} QMessageBox QLabel#qt_msgbox_label {{ background-color: {c['icon_bg']}; padding: 20px; font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif; font-size: 15px; font-weight: 600; color: {c['icon_color']}; line-height: 1.5; }} QMessageBox QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {c['button_start']}, stop:1 {c['button_end']}); border: none; color: #fff; font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif; font-weight: 600; font-size: 14px; padding: 10px 25px; min-width: 100px; text-align: center; }} QMessageBox QPushButton:hover {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {UIManager.lightenColor(c['button_start'], 15)}, stop:1 {UIManager.lightenColor(c['button_end'], 15)}); }} QMessageBox QPushButton:pressed {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {UIManager.darkenColor(c['button_start'], 15)}, stop:1 {UIManager.darkenColor(c['button_end'], 15)}); padding: 11px 25px; }}")
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)

        button_box = dialog.findChild(QDialogButtonBox)
        if button_box:
            button_box.setCenterButtons(True)

        if window:
            geo = window.frameGeometry()
            center = geo.center()
            dialog.move(center - dialog.rect().center())

        return dialog.exec()



    @staticmethod
    def darkenColor(hex_color, percent):
        r, g, b = [int(hex_color[i : i + 2], 16) for i in (1, 3, 5)]
        factor = 1 - percent / 100
        r, g, b = [max(0, min(255, int(c * factor))) for c in (r, g, b)]
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def lightenColor(hex_color, percent):
        r, g, b = [int(hex_color[i : i + 2], 16) for i in (1, 3, 5)]
        r = min(255, int(r + (255 - r) * percent / 100))
        g = min(255, int(g + (255 - g) * percent / 100))
        b = min(255, int(b + (255 - b) * percent / 100))
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def copyResultFromTab(window, tab_index):
        tab_widget = window.result_tab_widget.widget(tab_index)
        list_widgets = tab_widget.findChildren(QListWidget)
        if list_widgets:
            list_widget = list_widgets[0]
            items = [list_widget.item(i).text() for i in range(list_widget.count())]
            text_to_copy = "\n".join(items)
            clipboard = QApplication.clipboard()
            clipboard.setText(text_to_copy)
            Settings.write_log_dev_file(f"[DEBUG] 📋 {len(items)} éléments copiés dans le presse-papiers.", "INFO")
        else:
            Settings.write_log_dev_file("[DEBUG] ⚠️ Aucun QListWidget rencontré dans cet onglet.", "INFO")





    @staticmethod
    def copyLogsToClipboard(self):
        log_box = self.findChild(QGroupBox, "log")
        if not log_box:
            Settings.write_log_dev_file("[DEBUG] ❌ QGroupBox 'log' introuvable.", "INFO")
            return
        labels = log_box.findChildren(QLabel)
        if not labels:
            Settings.write_log_dev_file("[DEBUG] ⚠️ Aucun QLabel rencontré dans 'log'.", "INFO")
            return
        log_lines = [label.text() for label in labels]
        text_to_copy = "\n".join(log_lines)
        QApplication.clipboard().setText(text_to_copy)
 




    @staticmethod
    def updateLogsDisplay(log_entry, log_text_edit):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_entry = f"[{timestamp}] {log_entry}"
        log_text_edit.appendPlainText(formatted_entry)
        log_text_edit.moveCursor(QtGui.QTextCursor.MoveOperation.End)

 
    @staticmethod
    def updateActionsColorHandleLastButton(scenario_layout, go_to_previous_state):
        for i in range(scenario_layout.count()):
            widget = scenario_layout.itemAt(i).widget()

            if widget:
                if i != scenario_layout.count() - 1:
                    widget.setStyleSheet( f"background-color: #ffffff; border: 1px solid {Settings.SECONDARY_COLOR}; border-radius: 8px;" )

                    label_list = [child for child in widget.children() if isinstance(child, QLabel)]
                    if label_list:
                        first_label = label_list[0]
                        first_label.setStyleSheet(f"QLabel {{ color: {Settings.PRIMARY_COLOR}; font-size: 16px; border: none; border-radius: 4px; text-align: center; background-color: transparent; font-family: {Settings.FONT_FAMILY}; margin-left: 10px; }}")
                        if first_label.text().startswith("Random"):
                            first_label.setStyleSheet(f"QLabel {{ color: {Settings.PRIMARY_COLOR}; font-size: 9px; border: none; border-radius: 4px; background-color: transparent; font-family: {Settings.FONT_FAMILY}; padding: 0px; margin: 0px; border:None; }}")
                        for label in label_list[1:]:
                            label.setStyleSheet(f"QLabel {{ color: {Settings.PRIMARY_COLOR}; font-size: 14px; border: none; border-radius: 4px; text-align: center; background-color: transparent; font-family: {Settings.FONT_FAMILY}; }}")
                            if label.text().startswith("Random"):
                                label.setStyleSheet(f"QLabel {{ color: {Settings.PRIMARY_COLOR}; ; font-size: 9px; border: none; border-radius: 4px; background-color: transparent; font-family: Monaco, monospace; padding: 0px; margin: 0px; border:None; }}")
                    buttons = [child for child in widget.children() if isinstance(child, QPushButton)]
                    if buttons:
                        last_button = buttons[-1]
                        last_button.setVisible(False)

                    spin_boxes = [child for child in widget.children() if isinstance(child, QSpinBox)]
                    if spin_boxes and Settings.DOWN_EXISTS and Settings.UP_EXISTS:
                        new_style = f"QSpinBox {{ padding: 2px; border: 1px solid {Settings.PRIMARY_COLOR}; color: black; }} QSpinBox::down-button {{ image: url(\"{Settings.ARROW_DOWN_PATH}\"); width: 13px; height: 13px; padding: 2px; border-top-left-radius: 5px; border-bottom-left-radius: 5px; }} QSpinBox::up-button {{ image: url(\"{Settings.ARROW_DOWN_PATH}\"); width: 13px; height: 13px; padding: 2px; border-top-left-radius: 5px; border-bottom-left-radius: 5px; }}"
                        spin_boxes[0].setStyleSheet(new_style)

                    QCheckBox_list = [child for child in widget.children() if isinstance(child, QCheckBox)]
                    if QCheckBox_list:
                        checkbox = QCheckBox_list[0]
                        if checkbox.isChecked():
                            additional_style = f"QCheckBox::indicator:checked {{ background-color: {Settings.PRIMARY_COLOR}; border: 2px solid {Settings.PRIMARY_COLOR}; }}"
                        else:
                            additional_style = "QCheckBox::indicator { color: gray; background-color: #e0e0e0; border: 1px solid #cccccc; }"

                        current_style = checkbox.styleSheet()
                        new_style = (  f"{current_style} {additional_style}" if current_style  else additional_style )
                        checkbox.setStyleSheet(new_style)

                    QComboBox_list = [child for child in widget.children()  if isinstance(child, PyQt6.QtWidgets.QComboBox)]

                    if QComboBox_list:
                        QComboBox = QComboBox_list[0]
                        if Settings.DOWN_EXISTS:
                            old_style = QComboBox.styleSheet()
                            new_style = f"QComboBox::down-arrow {{ image: url(\"{Settings.ARROW_DOWN_PATH}\"); width: 13px; height: 13px; border: 1px solid {Settings.PRIMARY_COLOR}; background-color: white; }} QComboBox::drop-down {{ border: 1px solid {Settings.PRIMARY_COLOR}; width: 20px; outline: none; }} QComboBox QAbstractItemView {{ min-width: 90px; border: 1px solid {Settings.PRIMARY_COLOR}; background: white; selection-background-color: {Settings.PRIMARY_COLOR}; selection-color: white; padding: 3px; margin: 0px; alignment: center; }} QComboBox {{ padding-left: 10px; font-size: 12px; font-family: {Settings.FONT_FAMILY}; border: 1px solid {Settings.PRIMARY_COLOR}; }} QComboBox QAbstractItemView::item {{ padding: 5px; font-size: 12px; color: #333; border: none; }} QComboBox QAbstractItemView::item:selected {{ background-color: {Settings.PRIMARY_COLOR}; color: white; border-radius: 3px; }} QComboBox:focus {{ border: 1px solid {Settings.PRIMARY_COLOR}; }}"
                            combined_style = old_style + new_style
                            QComboBox.setStyleSheet(combined_style)

                if i == scenario_layout.count() - 1:
                    widget.setStyleSheet(f"background-color: {Settings.PRIMARY_COLOR}; border-radius: 8px;")
                    label_list = [child for child in widget.children() if isinstance(child, QLabel)]
                    if label_list:
                        label_list[0].setStyleSheet(f"QLabel {{ color: white; font-size: 16px; border: none; border-radius: 4px; text-align: center; background-color: {Settings.PRIMARY_COLOR}; font-family: {Settings.FONT_FAMILY}; margin-left: 8px; }}")
                        if label_list[0].text().startswith("Random"):
                            label_list[0].setStyleSheet(f"QLabel {{ color: white; font-size: 9px; border: 1px dashed #ffffff; border-radius: 4px; background-color: transparent; font-family: {Settings.FONT_FAMILY}; padding: 0px; margin: 0px; border:None; }}")
                        for label in label_list[1:]:
                            label.setStyleSheet(f"QLabel {{ color: white; font-size: 16px; border: none; border-radius: 4px; text-align: center; background-color: {Settings.PRIMARY_COLOR}; font-family: {Settings.FONT_FAMILY}; }}")
                            if label.text().startswith("Random"):
                                label.setStyleSheet("QLabel { color: white; font-size: 9px; border: 1px dashed #ffffff; border-radius: 4px; background-color: transparent; font-family: \"Monaco\", monospace; padding: 0px; margin: 0px; border:None; }")

                    buttons = [child for child in widget.children() if isinstance(child, QPushButton)]
                    if buttons:
                        last_button = buttons[0]
                        last_button.setVisible(True)
                        last_button.setCursor(Qt.CursorShape.PointingHandCursor)
                        try:
                            last_button.clicked.disconnect()
                        except TypeError:
                            pass
                        last_button.clicked.connect(go_to_previous_state)

                    spin_boxes = [child for child in widget.children() if isinstance(child, QSpinBox)]
                    if spin_boxes and Settings.DOWN_EXISTS_W and Settings.UP_EXISTS_W:
                        new_style = f"QSpinBox {{ padding: 2px; border: 1px solid white; color: white; }} QSpinBox::down-button {{ image: url(\"{Settings.ARROW_DOWN_W_PATH}\"); width: 13px; height: 13px; padding: 2px; border-top-left-radius: 5px; border-bottom-left-radius: 5px; }} QSpinBox::up-button {{ image: url(\"{Settings.ARROW_UP_W_PATH}\"); width: 13px; height: 13px; padding: 2px; border-top-left-radius: 5px; border-bottom-left-radius: 5px; }}"
                        spin_boxes[0].setStyleSheet(new_style)

                    QCheckBox_list_last = [child for child in widget.children() if isinstance(child, QCheckBox)]
                    if QCheckBox_list_last:
                        checkbox = QCheckBox_list_last[0]
                        if checkbox.isChecked():
                            additional_style = f"QCheckBox::indicator:checked {{ background-color: {Settings.PRIMARY_COLOR}; border: 2px solid #ffffff; }}"
                        else:
                            additional_style = "QCheckBox::indicator { color: gray; background-color: #e0e0e0; border: 1px solid #cccccc; }"

                        current_style = checkbox.styleSheet()
                        new_style = (  f"{current_style} {additional_style}"  if current_style  else additional_style)
                        checkbox.setStyleSheet(new_style)

                QComboBox_list = [child for child in widget.children() if isinstance(child, PyQt6.QtWidgets.QComboBox)]
                if QComboBox_list:
                    QComboBox = QComboBox_list[0]

                    if Settings.DOWN_EXISTS:
                        old_style = QComboBox.styleSheet()
                        new_style = f"QComboBox::down-arrow {{ image: url(\"{Settings.ARROW_DOWN_PATH}\"); width: 13px; height: 13px; border: none; background-color: white; }} QComboBox::drop-down {{ border: none; width: 20px; outline: none; }} QComboBox QAbstractItemView {{ min-width: 90px; border: none; background: white; selection-background-color: {Settings.PRIMARY_COLOR}; selection-color: white; padding: 3px; margin: 0px; alignment: center; }} QComboBox {{ padding-left: 10px; font-size: 12px; font-family: {Settings.FONT_FAMILY}; border: 1px solid {Settings.PRIMARY_COLOR}; outline: none; }} QComboBox QAbstractItemView::item {{ padding: 5px; font-size: 12px; color: #333; border: none; }} QComboBox QAbstractItemView::item:selected {{ background-color: {Settings.PRIMARY_COLOR}; color: white; border-radius: 3px; }} QComboBox:focus {{ border: 1px solid {Settings.PRIMARY_COLOR}; }}"
                        combined_style = old_style + new_style
                        QComboBox.setStyleSheet(combined_style)

                QTextEdits = [child for child in widget.children() if isinstance(child, QTextEdit)]

                for idx, qtextedit in enumerate(QTextEdits):

                    qtextedit.setVerticalScrollBarPolicy( Qt.ScrollBarPolicy.ScrollBarAlwaysOff )
                    qtextedit.setHorizontalScrollBarPolicy( Qt.ScrollBarPolicy.ScrollBarAlwaysOff )

                    def create_handler(te, index):
                        def handler(event):
                            try:
                                dialog = CustomTextDialog(  te, texte_initial=te.toPlainText() )
                                if ( dialog.exec()  ): 
                                    new_text = dialog.get_text()
                                    te.setPlainText(new_text)

                                te.clearFocus()
                            except Exception as e:
                                Settings.write_log_dev_file(  f"[❌] Erreur lors de l’ouverture de la boîte de dialogue : {e}\n{traceback.format_exc()}",  "ERROR"  )

                        return handler
                    
                    qtextedit.mousePressEvent = create_handler(qtextedit, idx)
                qlineedits = [child for child in widget.children() if isinstance(child, QLineEdit)]
                checkbox_qlineedit = None  


                if qlineedits:
                    last_qlineedit = qlineedits[-1]
                    parent_widget = last_qlineedit.parent()
                    if parent_widget:
                        contains_checkbox = any(  isinstance(child, QCheckBox) for child in parent_widget.children() )
                        if contains_checkbox:
                            checkbox_qlineedit = ( last_qlineedit  )
                            qlineedits.pop()  

                for idx, qlineedit in enumerate(qlineedits):

                    def create_validator(line_edit, default_val):
                        def validator():
                            ValidationUtils.validate_qlineedit_with_range( line_edit, default_val )
                        return validator

                    if len(qlineedits) > 1 and idx == 0:
                        qlineedit.editingFinished.connect( create_validator(qlineedit, "50,50"))
                    else:
                        qlineedit.editingFinished.connect( create_validator(qlineedit, "1,1") )

                if checkbox_qlineedit:
                    def validate_checkbox_qlineedit():
                        UIManager.validateCheckboxLinkedQlineEdit(checkbox_qlineedit)

                    checkbox_qlineedit.editingFinished.connect( validate_checkbox_qlineedit)


    @staticmethod
    def validateCheckboxLinkedQlineEdit(qlineedit: QLineEdit):
        if qlineedit is None:
            Settings.write_log_dev_file( "Le QLineEdit est None. Validation ignorée.", "ERROR")
            return

        parent_widget = qlineedit.parent()
        full_state = parent_widget.property("full_state") if parent_widget else None
        text = qlineedit.text().strip()

        old_style = qlineedit.styleSheet()
        cleaned_style = ValidationUtils.remove_border_from_style(old_style)

        if full_state and isinstance(full_state, dict):
            sub_id = full_state.get("id", "")
            sub_label = full_state.get("label", "Google")

            checkbox = next((child for child in parent_widget.children() if isinstance(child, QCheckBox)), None)

            if sub_id in ["open_spam", "open_inbox"]:
                if checkbox and checkbox.isChecked():
                    if text:
                        def apply_ok():
                            qlineedit.setStyleSheet(cleaned_style)
                            qlineedit.setToolTip("")
                        QTimer.singleShot(0, apply_ok)
                        return
                    else:
                        qlineedit.setText(sub_label or "Google")
                        def apply_error():
                            new_style = ValidationUtils.inject_border_into_style(  cleaned_style)
                            qlineedit.setStyleSheet(new_style)
                            qlineedit.setToolTip( "Texte invalide. Valeur remplacée par défaut depuis full_state.")
                        QTimer.singleShot(0, apply_error)
                        return

        if text.isdigit() or len(text) < 4:
            qlineedit.setText("Google")

            def apply_error():
                new_style = ValidationUtils.inject_border_into_style(cleaned_style)
                qlineedit.setStyleSheet(new_style)
                qlineedit.setToolTip( "Le texte est un nombre ou trop court, veuillez corriger la saisie.")

            QTimer.singleShot(0, apply_error)
        else:
            def apply_ok():
                qlineedit.setStyleSheet(cleaned_style)
                qlineedit.setToolTip("")

            QTimer.singleShot(0, apply_ok)


    @staticmethod
    def removeCopier(scenario_layout, reset_options_layout):
        lastactionLoop = None
        scenarioContainertableauAdd = []
        resetOptionsContainertableauALL = []
        found_checkbox = False

        for i in range(scenario_layout.count()):
            widget = scenario_layout.itemAt(i).widget()
            if widget:
                for child in widget.children():
                    if isinstance(child, QCheckBox):
                        lastactionLoop = i
                        found_checkbox = True

        if not found_checkbox:
            return

        for i in range(lastactionLoop + 1, scenario_layout.count()):
            widget = scenario_layout.itemAt(i).widget()
            if widget:
                labels = [child.text() for child in widget.children() if isinstance(child, QLabel)]
                if labels:
                    scenarioContainertableauAdd.append(labels[0])

        for i in range(reset_options_layout.count()):
            widget = reset_options_layout.itemAt(i).widget()
            if widget and isinstance(widget, QPushButton):
                resetOptionsContainertableauALL.append(widget.text())

        diff_texts = [text for text in resetOptionsContainertableauALL if text not in scenarioContainertableauAdd]

        for i in reversed(range(reset_options_layout.count())):
            widget = reset_options_layout.itemAt(i).widget()
            if widget and isinstance(widget, QPushButton):
                if widget.text() not in diff_texts:
                    widget.deleteLater()
                    reset_options_layout.removeWidget(widget)

    @staticmethod
    def removeInitial(scenario_layout, reset_options_layout):
        scenarioContainertableauAdd = []
        resetOptionsContainertableauALL = []

        for i in range(scenario_layout.count()):
            widget = scenario_layout.itemAt(i).widget()
            if widget:
                sub_full_state = widget.property("full_state")
                sub_hidden_id = sub_full_state.get("INITAILE")
                if sub_hidden_id:
                    scenarioContainertableauAdd.append(sub_full_state.get("label"))

        for i in range(reset_options_layout.count()):
            widget = reset_options_layout.itemAt(i).widget()
            if widget and isinstance(widget, QPushButton):
                resetOptionsContainertableauALL.append(widget.text())

        diff_texts = [text for text in resetOptionsContainertableauALL if text not in scenarioContainertableauAdd]

        for i in reversed(range(reset_options_layout.count())):
            widget = reset_options_layout.itemAt(i).widget()
            if widget and isinstance(widget, QPushButton):
                if widget.text() not in diff_texts:
                    widget.deleteLater()
                    reset_options_layout.removeWidget(widget)



    @staticmethod
    def readFileContent(file_path):
        if not ValidationUtils.pathExists(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if not content:
                return None
            return content
        except Exception as exc:
            Settings.write_log_event("file_read_failed", "ERROR", file_path=file_path,  exception_type=type(exc).__name__, error=str(exc) )
            return None

    @staticmethod
    def findWidget(window, name, widget_type=None):
        """Find child widget with optional type"""
        return (  window.findChild(widget_type, name) if widget_type  else window.findChild(QWidget, name)  )

    @staticmethod
    def setupContainers(window):
        """Setup container widgets and layouts"""
        window.reset_options_container = UIManager.findWidget( window, "resetOptionsContainer" )
        if window.reset_options_container:
            window.reset_options_layout = QVBoxLayout(window.reset_options_container)
            window.reset_options_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        window.scenario_container = UIManager.findWidget(window, "scenarioContainer")
        if window.scenario_container:
            window.scenario_layout = QVBoxLayout(window.scenario_container)
            window.scenario_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    @staticmethod
    def setupTemplateWidgets(window):
        templates = {
            "template_button": "TemepleteButton",
            "Temeplete_Button_2": "TemepleteButton_2",
            "template_Frame1": "Template1",
            "template_Frame2": "Template2",
            "template_Frame3": "Template3",
            "template_Frame4": "Template4",
            "template_Frame5": "Template5",
        }

        for attr_name, widget_name in templates.items():
            widget = UIManager.findWidget(window, widget_name)
            setattr(window, attr_name, widget)
            if widget:
                widget.hide()

    @staticmethod
    def setupIconButton(  window, button_name, icon_file, callback, icon_size=None, button_size=None):
        """Helper to setup icon button with detailed debug output"""

        button = UIManager.findWidget(window, button_name, QPushButton)
        if not button:
            Settings.write_log_dev_file(f"Bouton '{button_name}' introuvable.", "ERROR")
            return None
        else:
            Settings.write_log_dev_file(f"Bouton '{button_name}' trouvé.", "DEBUG")
        icon_path = os.path.join(Settings.ICONS_DIR, icon_file).replace("\\", "/")
        Settings.write_log_dev_file(f"Chemin icône pour '{button_name}': {icon_path}", "DEBUG")

        if ValidationUtils.pathExists(icon_path):
            Settings.write_log_dev_file(f"Icône trouvée pour '{button_name}': {icon_path}", "DEBUG")
            icon = QIcon(icon_path)
            if icon_size:
                Settings.write_log_dev_file( f"Taille icône pour '{button_name}': {icon_size}", "DEBUG")
                button.setIconSize(QSize(*icon_size))
            button.setIcon(icon)
        else:
            Settings.write_log_dev_file(f"Icône introuvable pour '{button_name}': {icon_path}", "WARNING" )
        try:
            button.clicked.connect(callback)
            Settings.write_log_dev_file( f"Callback connecté pour '{button_name}'", "INFO" )
        except Exception as e:
            Settings.write_log_dev_file(
                f"Error connecting callback: {button_name}\n{traceback.format_exc()}","ERROR" )
        if button_size:
            Settings.write_log_dev_file( f"Taille bouton pour '{button_name}': {button_size}", "DEBUG" )
            button.setFixedSize(*button_size)
        if button_name in ("ClearButton", "CopyButton"):
            Settings.write_log_dev_file( f"Application style spéciale pour '{button_name}'", "DEBUG")
            button.setText("")
            button.setStyleSheet("QPushButton { border: none; background-color: transparent; padding: 0px; margin: 0px; }")
        Settings.write_log_dev_file( f"Bouton '{button_name}' configuré avec succès.", "SUCCESS")

        return button

    @staticmethod
    def setupButton(window, widget_name, callback):
        """Setup simple button with connection + debug"""
        button = UIManager.findWidget(window, widget_name, QPushButton)

        if not button:
            Settings.write_log_dev_file(f"Bouton '{widget_name}' introuvable.", "ERROR")
            return None
        else:
            Settings.write_log_dev_file(f"Bouton '{widget_name}' trouvé.", "DEBUG")

        if not callback:
            Settings.write_log_dev_file(  f"Aucun callback fourni pour '{widget_name}'", "WARNING")
            return button
        try:
            button.clicked.connect(callback)
            Settings.write_log_dev_file( f"Callback connecté pour '{widget_name}'", "SUCCESS" )
        except Exception as e:
            Settings.write_log_dev_file( f"Error connecting callback: {widget_name}\n{traceback.format_exc()}", "ERROR" )
        return button

    @staticmethod
    def setupBrowserCombobox(window):
        """Setup browser selection combobox with debug"""

        Settings.write_log_dev_file("Initialisation du QComboBox 'browsers'", "DEBUG")
        window.browser = UIManager.findWidget(window, "browsers", QComboBox)

        if window.browser is None:
            Settings.write_log_dev_file("QComboBox 'browsers' introuvable.", "ERROR")
            return
        else:
            Settings.write_log_dev_file("QComboBox trouvé.", "DEBUG")

        try:
            UIManager.applyComboboxStyle( window.browser)
            Settings.write_log_dev_file("Style appliqué au QComboBox.", "DEBUG")
        except Exception as e:
            Settings.write_log_dev_file( f"Error applying style to browsers combobox\n{traceback.format_exc()}","ERROR" )

        Settings.write_log_dev_file("[DEBUG] Nettoyage des anciens éléments...", "DEBUG")
        window.browser.clear()

        browsers = Settings.BROWSER_OPTIONS
        Settings.write_log_dev_file( f"Nombre de navigateurs à ajouter: {len(browsers)}", "DEBUG" )
        for name, icon_file in browsers:
            icon_path = os.path.join(Settings.ICONS_DIR, icon_file).replace("\\", "/")
            Settings.write_log_dev_file( f"Traitement: {name} | Icône: {icon_path}", "DEBUG" )

            if ValidationUtils.pathExists(icon_path):
                window.browser.addItem(QIcon(icon_path), name)
            else:
                Settings.write_log_dev_file( f"Icône introuvable pour {name}: {icon_path}", "WARNING" )
                window.browser.addItem(name)

        count = window.browser.count()
        Settings.write_log_dev_file( f"QComboBox configuré avec {count} éléments.", "SUCCESS")



    @staticmethod
    def applyComboboxStyle( combobox):
        """Apply custom arrow style to combobox"""
        if not ValidationUtils.pathExists(Settings.ARROW_DOWN_PATH):
            return

        style = f'QComboBox::down-arrow {{ image: url("{Settings.ARROW_DOWN_PATH}"); width: 16px; height: 16px; }}'
        old_style = combobox.styleSheet()
        combobox.setStyleSheet(old_style + style)

    @staticmethod
    def setupIspCombobox(window):
        """Setup ISP selection combobox"""
        window.Isp = UIManager.findWidget(window, "Isps", QComboBox)
        if window.Isp is None:
            return

        UIManager.applyComboboxStyle( window.Isp)
        window.Isp.clear()
        for name, icon_file in Settings.SERVICES.items():
            icon_path = os.path.join(Settings.ICONS_DIR, icon_file)
            if ValidationUtils.pathExists(icon_path):
                window.Isp.addItem(QIcon(icon_path), name)
            else:
                window.Isp.addItem(name)
        UIManager.setDefaultIsp(window)


    @staticmethod
    def setDefaultIsp(window):
        """Set the default ISP based on the content of FILE_ISP"""
        if not ValidationUtils.pathExists(Settings.FILE_ISP):
            return

        with open(Settings.FILE_ISP, "r", encoding="utf-8") as f:
            line = f.readline().strip().lower()

        if not hasattr(window, "Isp") or window.Isp is None:
            return

        for key, value in Settings.ISP_MAPPING.items():
            if key in line:
                index = window.Isp.findText(value)
                if index >= 0:
                    window.Isp.setCurrentIndex(index)
                break

    @staticmethod
    def setupScenarioCombobox(window):
        """Setup scenario selection combobox"""
        window.saveSanario = UIManager.findWidget(window, "saveSanario", QComboBox)
        if window.saveSanario is None:
            Settings.write_log_dev_file( "🔧 [DEBUG] Le save scenario not found", "DEBUG")
            return
        Settings.write_log_dev_file("🔧 [DEBUG] Le save scenario  found ", "DEBUG")
        UIManager.applyComboboxStyle( window.saveSanario)
        window.saveSanario.currentTextChanged.connect(window.scenario_changed)

    @staticmethod
    def setupLogoutButton(window, callback):
        button = UIManager.findWidget(window, "LogOut", QPushButton)
        if not button:
            return None
        button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        if callback:
            button.clicked.connect(callback)
        icon_path = os.path.join(Settings.ICONS_DIR, "LogOut4.png")
        if ValidationUtils.pathExists(icon_path):
            button.setIcon(QIcon(icon_path))
            button.setIconSize(QSize(18, 18))
        return button

    @staticmethod
    def setupResultTabWidget(window):
        """Setup result tab widget with vertical tabs"""
        window.tabWidgetResult = UIManager.findWidget( window, "tabWidgetResult", QTabWidget )
        if window.tabWidgetResult is None:
            return
        window.tabWidgetResult.tabBar().setCursor(Qt.CursorShape.PointingHandCursor)
        UIManager.setTabIcons(window, window.tabWidgetResult)
        try:
            window.tabWidgetResult.tabBar().tabBarClicked.connect( lambda index: UIManager.handleResultTabClicked(window, index) )
        except Exception:
            pass

        window.tabWidgetResult.currentChanged.connect( lambda index: UIManager.handleResultTabChanged(window, index) )
        UIManager.convertToVerticalTabs(window)
        UIManager.setIconsForExistingButtons(window)

    @staticmethod
    def handleResultTabClicked(window, index):
        if not hasattr(window, "tabWidgetResult") or window.tabWidgetResult is None:
            return
        if index < 0 or index >= window.tabWidgetResult.count():
            return
        window.tabWidgetResult.setCurrentIndex(index)

    @staticmethod
    def handleResultTabChanged(window, index):
        if not hasattr(window, "tabWidgetResult") or window.tabWidgetResult is None:
            return
        if index < 0 or index >= window.tabWidgetResult.count():
            return
        tab_text = window.tabWidgetResult.tabText(index)
        Settings.write_log_dev_file(f"Result tab switched to: {tab_text}", "INFO")

    @staticmethod
    def setIconsForExistingButtons(window):
        """Set copy icons for all copy buttons in result tabs"""
        if not hasattr(window, "tabWidgetResult") or window.tabWidgetResult is None:
            return
        tab_count = window.tabWidgetResult.count()

        for i in range(tab_count):
            tab_widget = window.tabWidgetResult.widget(i)
            if tab_widget is None:
                continue
            buttons = tab_widget.findChildren(QPushButton)
            for button in buttons:
                if button.objectName().startswith("copy"):
                    icon_path = os.path.join(Settings.ICONS_DIR, "copy.png")
                    if os.path.exists(icon_path):
                        button.setIcon(QIcon(icon_path))
                        button.setIconSize(QSize(20, 20))
                    try:
                        button.clicked.disconnect()
                    except TypeError:
                        Settings.write_log_dev_file( f"No signals to disconnect for copy button in tab {i}", "INFO" )
                    except Exception:
                        Settings.write_log_dev_file(  f"Unexpected error disconnecting copy button in tab {i}:\n{traceback.format_exc()}", "ERROR")
                    button.clicked.connect(  partial(UIManager.copyResultFromTab, window, i) )



    @staticmethod
    def setTabIcons(window, tab_widget):
        """Set icons for tabs based on tab text"""
        if not ValidationUtils.pathExists(Settings.ICONS_DIR):
            return
        icon_size = (40, 40)
        tab_count = tab_widget.count()
        for i in range(tab_count):
            tab_text = tab_widget.tabText(i)
            icon_name = tab_text.lower().replace(" ", "_") + ".png"
            icon_path = os.path.join(Settings.ICONS_DIR, icon_name)
            if ValidationUtils.pathExists(icon_path):
                icon = QIcon(icon_path)
                icon_pixmap = icon.pixmap(icon_size[0], icon_size[1])
                tab_widget.setTabIcon(i, QIcon(icon_pixmap))

    @staticmethod
    def convertToVerticalTabs(window):
        if not hasattr(window, "tabWidgetResult") or window.tabWidgetResult is None:
            return

        vertical_tab_widget = VerticalTabWidget()
        parent_widget = window.tabWidgetResult.parentWidget()
        geometry = window.tabWidgetResult.geometry()
        while window.tabWidgetResult.count() > 0:
            widget = window.tabWidgetResult.widget(0)
            text = window.tabWidgetResult.tabText(0)
            icon = window.tabWidgetResult.tabIcon(0)
            vertical_tab_widget.addTab(widget, icon, text)
            vertical_tab_widget.widget(vertical_tab_widget.count() - 1).setStyleSheet( widget.styleSheet())
            vertical_tab_widget.widget(vertical_tab_widget.count() - 1).setObjectName( widget.objectName() )
        window.tabWidgetResult.setParent(None)
        vertical_tab_widget.setParent(parent_widget)
        vertical_tab_widget.setObjectName("tabWidgetResult")
        vertical_tab_widget.setGeometry(geometry)
        vertical_tab_widget.show()
        window.tabWidgetResult = vertical_tab_widget
        window.tabWidgetResult.tabBar().setCursor(Qt.CursorShape.PointingHandCursor)
        try:
            window.tabWidgetResult.tabBar().tabBarClicked.connect( lambda index: UIManager.handleResultTabClicked(window, index))
        except Exception:
            pass
        window.tabWidgetResult.currentChanged.connect( lambda index: UIManager.handleResultTabChanged(window, index))


    @staticmethod
    def setupInterfaceTabWidget(window):
        """Setup main interface tab widget"""
        window.INTERFACE = UIManager.findWidget(window, "interface_2", QTabWidget)
        if window.INTERFACE is None:
            return
        try:
            window.INTERFACE.tabBar().setCursor(Qt.CursorShape.PointingHandCursor)
        except Exception:
            Settings.write_log_dev_file( f"Error setting cursor for TabBar\n{traceback.format_exc()}", "ERROR")
            pass

        for i in range(window.INTERFACE.count()):
            if UIManager.isResultTab(window.INTERFACE, i):
                tab_widget = window.INTERFACE.widget(i)
                if tab_widget is None:
                    continue
                frame = QFrame(tab_widget)
                frame.setStyleSheet(f"background-color: #F5F5F5; border-right: 1px solid {Settings.PRIMARY_COLOR};")
                frame.setGeometry(0, 660, 179, 300)
                frame.show()
                break

    @staticmethod
    def setupMiscellaneous(window):
        """Setup miscellaneous UI elements"""

        window.lineEdit_search = UIManager.findWidget( window, "lineEdit_search", QLineEdit)
        if window.lineEdit_search:
            window.lineEdit_search.hide()
        window.textEdit_3 = UIManager.findWidget(window, "textEdit_3", QTextEdit)
        if window.textEdit_3:
            window.textEdit_3.setPlaceholderText( "Please enter the data in the following format : \n Email* ; passwordEmail* ; ipAddress* ; port* ; login ; password ; recovery_email , new_recovery_email" )

        window.textEdit_4 = UIManager.findWidget(window, "textEdit_4", QTextEdit)
        if window.textEdit_4:
            window.textEdit_4.setPlaceholderText("Specify the maximum number of operations to process")

        tables = window.findChildren(QTableWidget)
        for table in tables:
            for col in range(table.columnCount()):
                table.horizontalHeader().setSectionResizeMode( col, QHeaderView.ResizeMode.Stretch )
        try:
            UIManager.styleSpinBoxes(window)
        except Exception:
            Settings.write_log_dev_file( f"Error styling spin boxes\n{traceback.format_exc()}", "ERROR" )
            pass

        window.result_tab_widget = UIManager.findWidget( window, "tabWidgetResult", QTabWidget )

    @staticmethod
    def styleSpinBoxes(window):
        if not (Settings.DOWN_EXISTS and Settings.UP_EXISTS):
            return
        for spin_box in window.findChildren(QSpinBox):
            old_style = spin_box.styleSheet()
            spin_box.setStyleSheet(old_style + f"QSpinBox::down-button {{ image: url(\"{Settings.ARROW_DOWN_PATH}\"); width: 13px; height: 13px; border-top-left-radius: 5px; border-bottom-left-radius: 5px; }} QSpinBox::up-button {{ image: url(\"{Settings.ARROW_UP_PATH}\"); width: 13px; height: 13px; border-top-left-radius: 5px; border-bottom-left-radius: 5px; }}")

    @staticmethod
    def updateScenario(window, template_name, state):
        template_frame = None
        if template_name == "Template1":
            template_frame = window.template_Frame1
        elif template_name == "Template2":
            template_frame = window.template_Frame2
        elif template_name == "Template3":
            template_frame = window.template_Frame3
        elif template_name == "Template4":
            template_frame = window.template_Frame4
        elif template_name == "Template5":
            template_frame = window.template_Frame5
        else:
            return

        if template_frame:
            new_template = QFrame()
            new_template.setStyleSheet(template_frame.styleSheet())
            new_template.setMaximumHeight(51)
            new_template.setMinimumHeight(51)
            new_template.setMaximumWidth(780)

            lineedits = []
            checkboxes = []
            first_label_updated = False

            for child in template_frame.children():
                if isinstance(child, QLabel):
                    new_label = QLabel(new_template)
                    if not first_label_updated:
                        new_label.setText(state.get("label", ""))
                        first_label_updated = True
                    else:
                        new_label.setText(child.text())
                    new_label.setStyleSheet(child.styleSheet())
                    new_label.setGeometry(child.geometry())
                elif isinstance(child, QPushButton):
                    new_button = QPushButton(child.text(), new_template)
                    new_button.setStyleSheet(child.styleSheet())
                    new_button.setGeometry(child.geometry())
                    new_button.clicked.connect(child.clicked)
                elif isinstance(child, QSpinBox):
                    new_spinbox = QSpinBox(new_template)
                    new_spinbox.setValue(child.value())
                    new_spinbox.setGeometry(child.geometry())
                    new_spinbox.setStyleSheet(child.styleSheet())
                elif isinstance(child, QLineEdit):
                    new_lineedit = QLineEdit(new_template)
                    new_lineedit.setText(child.text())
                    new_lineedit.setGeometry(child.geometry())
                    new_lineedit.setStyleSheet(child.styleSheet())
                    lineedits.append(new_lineedit)
                elif isinstance(child, QTextEdit):
                    new_textedit = QTextEdit(new_template)
                    new_textedit.setPlainText(child.toPlainText())
                    new_textedit.setGeometry(child.geometry())
                    new_textedit.setStyleSheet(child.styleSheet())
                    lineedits.append(new_textedit)
                elif isinstance(child, QCheckBox):
                    new_checkbox = QCheckBox(child.text(), new_template)
                    new_checkbox.setChecked(child.isChecked())
                    new_checkbox.setGeometry(child.geometry())
                    new_checkbox.setStyleSheet(child.styleSheet())
                    checkboxes.append(new_checkbox)
                elif isinstance(child, QComboBox):
                    new_combobox = QComboBox(new_template)
                    new_combobox.setCurrentIndex(child.currentIndex())
                    new_combobox.addItems( [child.itemText(i) for i in range(child.count())]  )
                    new_combobox.setGeometry(child.geometry())
                    new_combobox.setStyleSheet(child.styleSheet())

            for checkbox in checkboxes:
                if lineedits:
                    linked_lineedit = lineedits[-1]
                    linked_lineedit.hide()
                    checkbox.stateChanged.connect( lambda state, lineedit=linked_lineedit: (  UIManager.handleCheckboxState(state, lineedit) ) )
            new_template.setProperty("full_state", state)
            window.scenario_layout.addWidget(new_template)

    @staticmethod
    def handleCheckboxState(state, lineedit):
        if lineedit:
            if state == 2:
                lineedit.show()
            else:
                lineedit.hide()

    @staticmethod
    def displayStateStackAsTable(window):
        if not window.STATE_STACK:
            return

    @staticmethod
    def disableButton(button, disabled_style=None):
        """Désactive un bouton avec un style personnalisé"""
        Settings.write_log_dev_file("Attempting to disable button...", "INFO")
        if button is None:
            Settings.write_log_dev_file( "Attempted to disable a non-existent button", "WARNING")
            return
        if not button.isEnabled():
            Settings.write_log_dev_file("Attempted to disable an already disabled button", "WARNING")
            return
        button.setProperty("old_style", button.styleSheet())
        button.setEnabled(False)
        if disabled_style is None:
            disabled_style = "background-color: #cccccc; color: #666666; border: 1px solid #999999; text-align: center;"
        button.setStyleSheet(disabled_style)
        button.repaint()
        QApplication.processEvents()
        Settings.write_log_dev_file( f"Button '{button.objectName()}' disabled with style: {disabled_style}", "INFO" )


    @staticmethod
    def enableButton(button):
        """Réactive un bouton et restaure l'ancien style"""
        Settings.write_log_dev_file("Attempting to enable button...", "INFO")

        if button is None:
            Settings.write_log_dev_file( "Attempted to enable a non-existent button", "WARNING" )
            return
        
        button.setEnabled(True)
        old_style = button.property("old_style")

        if old_style:
            Settings.write_log_dev_file( f"Button '{button.objectName()}' enabled, restoring old style.", "INFO" )
            button.setStyleSheet(old_style)
        else:
            Settings.write_log_dev_file( f"Button '{button.objectName()}' enabled, but no old style found to restore.", "WARNING" )
