# ui_utils.py
import os
import json
import random
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIcon, QCursor, QColor, QPixmap
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6 import QtWidgets, QtGui, QtCore
import PyQt6
from collections import defaultdict

import sys


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from config import Settings
    from utils.validation_utils import ValidationUtils
except ImportError as e:
    raise ImportError(f"❌ Erreur d'importation: {e}")


class CustomTextDialog(QDialog):
    def __init__(self, parent=None, texte_initial=""):
        super().__init__(parent)
        self.setWindowTitle("Update Text")
        self.setMinimumSize(500, 350)

        # Layout principal
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Label d'instruction
        label = QLabel("📝 Please enter your text below:")
        layout.addWidget(label)

        # Zone de texte
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(texte_initial)
        layout.addWidget(self.text_edit)

        # Boutons Annuler / Enregistrer
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

        # 🌟 Style QSS compatible Qt
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                font-family: "Times", "Times New Roman", serif;
                font-size: 14px;
                color: #2d2d2d;
                font-weight: 500;
                margin-bottom: 10px;
            }
            QTextEdit {
                border: 1px solid #d0d0d0;
                border-radius: 10px;
                font-family: "Times", "Times New Roman", serif;
                background-color: #fafafa;
                font-size: 12pt;
                padding: 5px;
            }
            QTextEdit:focus {
                border: 2px solid #0078d7;
                background-color: #ffffff;
            }
            QPushButton {
                font-family: "Times", "Times New Roman", serif;
                padding: 8px 16px;
                text-align: center;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton#btn_ok {
                background-color: #0078d7;
                border: none;
                color: white;
            }
            QPushButton#btn_ok:hover {
                background-color: #005a9e;
            }
            QPushButton#btn_cancel {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                color: #333333;
            }
            QPushButton#btn_cancel:hover {
                background-color: #e0e0e0;
            }
        """)

        # IDs pour styles séparés
        self.btn_ok.setObjectName("btn_ok")
        self.btn_cancel.setObjectName("btn_cancel")

    def get_text(self):
        return self.text_edit.toPlainText()


class UIManager:
    
    # -------------------------
    # Personnalisation d'un onglet pour afficher le nombre d'emails complétés et non complétés
    # -----------------------------
    @staticmethod
    def Set_Custom_Colored_Tab( tab_widget, index, completed_count, not_completed_count):
        html_text = (
            f'<div style="text-align:center;margin:0;padding:0;">'
            f'<span style="font-family:\'Segoe UI\', sans-serif; font-size:14px;">Result ('
            f'<span style="color:#008000;">{completed_count} completed</span> / '
            f'<span style="color:#d90429;">{not_completed_count} not completed</span>)</span>'
            f'</div>'
        )

        # إزالة النص الافتراضي
        tab_widget.setTabText(index, "")

        # إنشاء QLabel
        label = QLabel()
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setText(html_text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # لف QLabel داخل QWidget لتوسيطه
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(label)

        # إزالة أي أزرار جانبية موجودة
        tab_widget.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, None)
        tab_widget.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)

        # إضافة الـ wrapper كزر التبويب (محاذاة مركزية)
        tab_widget.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, wrapper)









    # -----------------------------
    # Read email results and update the UI
    # -----------------------------
    @staticmethod
    def Read_Result_Update_List( window):
        # Vérifier si le fichier existe
        if not ValidationUtils.path_exists(Settings.RESULT_FILE_PATH):
            UIManager.Show_Critical_Message(
                window,
                "Information",
                "No emails have been processed yet.\nPlease check the filters or new data.",
                message_type="info"
            )
            return

        errors_dict = defaultdict(list)
        all_emails = []

        try:
            # Lire toutes les lignes non vides
            with open(Settings.RESULT_FILE_PATH , 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]

            # Vérification si le fichier est vide
            if not lines:
                UIManager.Show_Critical_Message(window, "Warning", "No results available.", message_type="warning")
                return

            completed_count = 0
            no_completed_count = 0

            # Parcourir chaque ligne et classer les emails par statut
            for line in lines:
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

            # Mise à jour du tab principal
            interface_tab_widget = window.findChild(QTabWidget, "interface_2")
            if interface_tab_widget:
                for i in range(interface_tab_widget.count()):
                    if interface_tab_widget.tabText(i).startswith("Result"):
                        UIManager.Set_Custom_Colored_Tab(interface_tab_widget, i, completed_count, no_completed_count)
                        break

            # Mise à jour des tabs secondaires
            result_tab_widget = window.findChild(QTabWidget, "tabWidgetResult")
            if not result_tab_widget:
                return

            for status in Settings.STATUS_LIST:
                tab_widget = result_tab_widget.findChild(QWidget, status)
                if not tab_widget:
                    continue

                list_widgets = tab_widget.findChildren(QListWidget)
                if not list_widgets:
                    continue

                list_widget = list_widgets[0]
                list_widget.clear()
                emails = errors_dict.get(status, [])
                if emails:
                    list_widget.addItems(emails)
                    list_widget.scrollToBottom()
                    # Ajouter un badge de notification
                    UIManager.Add_Notification_Badge(result_tab_widget, result_tab_widget.indexOf(tab_widget), len(emails))
                    # Supprimer le message "no data" si présent
                    message_label = tab_widget.findChild(QLabel, "no_data_message")
                    if message_label:
                        message_label.deleteLater()
                else:
                    list_widget.addItem("⚠ No email data available for this category currently.")
                    list_widget.show()

        except Exception as e:
            UIManager.Show_Critical_Message(window, "Error", f"An error occurred while displaying results: {e}")







    # -----------------------------
    # Gestion des badges de notification sur les onglets
    # -----------------------------

    @staticmethod
    def Remove_Notification( index , NOTIFICATION_BADGES):
        badge = NOTIFICATION_BADGES.pop(index, None)
        if badge:
            badge.deleteLater()





    @staticmethod
    def Add_Notification_Badge( tab_widget, tab_index, count , NOTIFICATION_BADGES):
        old_badge = NOTIFICATION_BADGES.get(tab_index)
        if old_badge:
            old_badge.deleteLater()

        tab_bar = tab_widget.tabBar()
        tab_rect = tab_bar.tabRect(tab_index)

        badge_x = tab_rect.right() - 14
        badge_y = tab_rect.top() + 2

        badge_label = QLabel(f"{count}", tab_widget)
        badge_label.setStyleSheet("""
            background-color: #d90429;
            color: white;
            font-size: 14px;
            padding: 3px;
            border-radius: 10px;
            min-width: 15px;
            text-align: center;
        """)
        badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        try:
            badge_label.setParent(tab_widget)
            badge_label.move(badge_x, badge_y)
            badge_label.show()
            NOTIFICATION_BADGES[tab_index] = badge_label
            tab_widget.update()
            tab_bar.update()
        except Exception as e:
            UIManager.Show_Critical_Message(tab_widget, "Error", f"Error adding notification badge: {e}")








    @staticmethod
    def Show_Critical_Message(window, title, message, message_type="critical"):
        """Affiche un QMessageBox stylé selon le type (critical, warning, info, success)."""
        dialog = QMessageBox(window)

        # Définition des styles pour chaque type
        colors = {
            "critical": {"accent": "#d32f2f", "start": "#d32f2f", "end": "#b71c1c", "bg": "#ffebee", "icon": QMessageBox.Icon.Critical},
            "warning": {"accent": "#ed6c02", "start": "#ed6c02", "end": "#e65100", "bg": "#fff3e0", "icon": QMessageBox.Icon.Warning},
            "info": {"accent": "#0288d1", "start": "#0288d1", "end": "#01579b", "bg": "#e1f5fe", "icon": QMessageBox.Icon.Information},
            "success": {"accent": "#2e7d32", "start": "#2e7d32", "end": "#1b5e20", "bg": "#e8f5e9", "icon": QMessageBox.Icon.Information}
        }

        c = colors.get(message_type, colors["info"])
        dialog.setIcon(c["icon"])
        dialog.setWindowTitle(title)
        dialog.setText(f"<h2 style='margin:0; font-weight:700; color:{c['accent']};'>{title}</h2>"
                    f"<p style='margin:0px; color:#37474f; line-height:1.5;'>{message}</p>")

        # Ombre
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 12)
        dialog.setGraphicsEffect(shadow)

        # Style global (fusionné et optimisé)
        dialog.setStyleSheet(f"""
            QMessageBox {{
                background-color: {c['bg']};
                color: #263238;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                font-size: 14px;
                padding: 20px;
                min-width: 480px;
                border-radius: 12px;
            }}
            QMessageBox QLabel#qt_msgbox_label {{
                padding: 15px;
                border-radius: 10px;
                background: {c['bg']};
            }}
            QMessageBox QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {c['start']}, stop:1 {c['end']});
                color: #fff;
                font-weight: 600;
                border-radius: 8px;
                padding: 10px 25px;
                min-width: 100px;
            }}
            QMessageBox QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {UIManager.Lighten_Color(c['start'], 12)}, stop:1 {UIManager.Lighten_Color(c['end'], 12)});
            }}
            QMessageBox QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {UIManager.Darken_Color(c['start'], 12)}, stop:1 {UIManager.Darken_Color(c['end'], 12)});
                padding: 11px 26px 9px 26px;
            }}
        """)

        if window:
            dialog.move(window.frameGeometry().center() - dialog.rect().center())

        return dialog.exec()


    # -----------------------------
    # Ajustement de la couleur HEX (assombrir / éclaircir)
    # -----------------------------


    @staticmethod
    def Darken_Color( hex_color, percent):
        r, g, b = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]
        factor = 1 - percent / 100
        r, g, b = [max(0, min(255, int(c * factor))) for c in (r, g, b)]
        return f"#{r:02x}{g:02x}{b:02x}"






    @staticmethod
    def Lighten_Color(hex_color, percent):
        r, g, b = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]
        r = min(255, int(r + (255 - r) * percent / 100))
        g = min(255, int(g + (255 - g) * percent / 100))
        b = min(255, int(b + (255 - b) * percent / 100))
        return f"#{r:02x}{g:02x}{b:02x}"





    @staticmethod
    def Set_Icon_For_Existing_Buttons(result_tab_widget):
        if not result_tab_widget:
            print("[DEBUG] ❌ tabWidgetResult introuvable. Vérifiez le nom.")
            return

        print("[DEBUG] ✅ tabWidgetResult trouvé.")

        for i in range(result_tab_widget.count()):
            tab_widget = result_tab_widget.widget(i)
            buttons = tab_widget.findChildren(QPushButton)

            for button in buttons:
                object_name = button.objectName()

                if object_name.startswith("copy"):
                    icon_path = os.path.join(Settings.ICONS_DIR, "copy.png")
                    button.setIcon(QIcon(icon_path))
                    button.setIconSize(QtCore.QSize(20, 20))
                    # print(f"[DEBUG] 🎯 Icône ajoutée au bouton '{object_name}' dans l'onglet {i}")

                    # ✅ ربط الزر بدالة النسخ (مرة واحدة)
                    try:
                        button.clicked.disconnect()
                    except Exception:
                        pass  # لم يكن هناك ربط سابق

                    button.clicked.connect(lambda _, idx=i: self.Copy_Result_From_Tab(idx))
                else:
                    print(f"[DEBUG] ⏭️ Bouton ignoré: '{object_name}'")




    @staticmethod
    def Copy_Result_From_Tab( tab_index , result_tab_widget):
        tab_widget = result_tab_widget.widget(tab_index)
        list_widgets = tab_widget.findChildren(QListWidget)

        if list_widgets:
            list_widget = list_widgets[0]
            items = [list_widget.item(i).text() for i in range(list_widget.count())]
            text_to_copy = "\n".join(items)
            clipboard = QApplication.clipboard()
            clipboard.setText(text_to_copy)
            print(f"[DEBUG] 📋 {len(items)} éléments copiés dans le presse-papiers.")
        else:
            print("[DEBUG] ⚠️ Aucun QListWidget trouvé dans cet onglet.")



    @staticmethod
    def Copy_Logs_To_Clipboard(self):
            log_box = self.findChild(QGroupBox, "log")
            if not log_box:
                print("[DEBUG] ❌ QGroupBox 'log' introuvable.")
                return

            labels = log_box.findChildren(QLabel)

            if not labels:
                print("[DEBUG] ⚠️ Aucun QLabel trouvé dans 'log'.")
                return

            log_lines = [label.text() for label in labels]
            text_to_copy = "\n".join(log_lines)

            QApplication.clipboard().setText(text_to_copy)
            print(f"[DEBUG] 📋 {len(log_lines)} lignes de LOGS copiées dans le presse-papiers.")


        #Ajoute une nouvelle ligne de log dans la zone de log (interface utilisateur).
    #Chaque log est stylisé pour rester lisible avec fond transparent.
    @staticmethod
    def Update_Logs_Display( log_entry ,log_layout):
        log_label = QLabel(log_entry)
        log_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                background-color: transparent;
                font-family: "Times", "Times New Roman", serif;
                padding: 2px;
            }
        """)
        log_layout.addWidget(log_label)

    

    


    # Met à jour dynamiquement le style de tous les widgets enfants dans le layout du scénario.
    # Différencie le dernier bloc des autres :
    # - Applique des styles personnalisés pour les QLabels, QSpinBox, QCheckBox, et QComboBox.
    # - Cache le dernier bouton dans chaque bloc sauf le dernier, où il devient visible et fonctionnel.
    # - Applique des styles conditionnels selon les icônes disponibles.
    @staticmethod
    def Update_Actions_Color_Handle_Last_Button( scenario_layout , Go_To_Previous_State):
        for i in range(scenario_layout.count()):
            widget = scenario_layout.itemAt(i).widget()

            if widget:
                if i != scenario_layout.count() - 1:
                    widget.setStyleSheet("background-color: #ffffff; border: 1px solid #b2cddd; border-radius: 8px;")
                    label_list = [child for child in widget.children() if isinstance(child, QLabel)]
                    if label_list:
                        first_label = label_list[0]

                        # 🖌️ Appliquer style par défaut à la première QLabel
                        first_label.setStyleSheet("""
                            QLabel {
                                color: #669bbc;
                                font-size: 16px;
                                border: none;
                                border-radius: 4px;
                                text-align: center;
                                background-color: transparent;
                                font-family: "Times", "Times New Roman", serif;
                                margin-left: 10px;
                            }
                        """)

                        # 🎯 Si elle commence par "Random", remplacer le style
                        if first_label.text().startswith("Random"):
                            first_label.setStyleSheet("""
                                QLabel {
                                    color: #669bbc;
                                    font-size: 9px;
                                    border: none;
                                    border-radius: 4px;
                                    background-color: transparent;
                                    font-family: "Monaco", monospace;
                                    padding: 0px;
                                    margin: 0px;
                                    border:None;
                                }
                            """)
                            print(f"[🎯] Style appliqué sur QLabel (index 0): '{first_label.text()}'")

                        # 🎨 Appliquer style aux autres QLabels
                        for label in label_list[1:]:
                            label.setStyleSheet("""
                                QLabel {
                                    color: #669bbc;
                                    font-size: 14px;
                                    border: none;
                                    border-radius: 4px;
                                    text-align: center;
                                    background-color: transparent;
                                    font-family: "Times", "Times New Roman", serif;
                                }
                            """)

                            # 🎯 S'il commence par "Random", on remplace
                            if label.text().startswith("Random"):
                                label.setStyleSheet("""
                                    QLabel {
                                        color: #669bbc;
                                        font-size: 9px;
                                        border: none;
                                        border-radius: 4px;
                                        background-color: transparent;
                                        font-family: "Monaco", monospace;
                                        padding: 0px;
                                        margin: 0px;
                                        border:None;
                                    }
                                """)
                                print(f"[🎯] Style appliqué sur QLabel: '{label.text()}'")


                    buttons = [child for child in widget.children() if isinstance(child, QPushButton)]
                    if buttons:
                        last_button = buttons[-1]
                        last_button.setVisible(False)  


                    spin_boxes = [child for child in widget.children() if isinstance(child, QSpinBox)]
                    if spin_boxes and Settings.DOWN_EXISTS and Settings.UP_EXISTS:
                        new_style = f"""
                            QSpinBox {{
                                padding: 2px; 
                                border: 1px solid #669bbc; 
                                color: black;
                            }}
                            QSpinBox::down-button {{
                                image: url("{Settings.ARROW_DOWN_PATH}");
                                width: 13px;
                                height: 13px;
                                padding: 2px;  
                                border-top-left-radius: 5px;
                                border-bottom-left-radius: 5px;
                            }}
                            QSpinBox::up-button {{
                                image: url("{Settings.ARROW_DOWN_PATH}");
                                width: 13px;
                                height: 13px;
                                padding: 2px;
                                border-top-left-radius: 5px;
                                border-bottom-left-radius: 5px;
                            }}
                        """
                        spin_boxes[0].setStyleSheet(new_style)  



                    QCheckBox_list = [child for child in widget.children() if isinstance(child, QCheckBox)]
                    if QCheckBox_list:  
                        checkbox = QCheckBox_list[0]                
                        if checkbox.isChecked():
                            additional_style = """
                                QCheckBox::indicator:checked  {
                                    background-color: #669bbc;
                                    border: 2px solid #669bbc;
                                }
                            """
                        else:
                            additional_style = """
                                QCheckBox::indicator {
                                    color: gray;
                                    background-color: #e0e0e0; 
                                    border: 1px solid #cccccc;
                                }
                            """

                        current_style = checkbox.styleSheet()
                        new_style = f"{current_style} {additional_style}" if current_style else additional_style
                        checkbox.setStyleSheet(new_style)

                    QComboBox_list = [child for child in widget.children() if isinstance(child, PyQt6.QtWidgets.QComboBox)]

                    if QComboBox_list:
                        QComboBox = QComboBox_list[0]
                        if Settings.DOWN_EXISTS:
                            old_style = QComboBox.styleSheet()
                            new_style = f"""
                                QComboBox::down-arrow {{
                                    image: url("{Settings.ARROW_DOWN_PATH}");
                                    width: 13px;
                                    height: 13px;
                                    border: 1px solid #669bbc; 
                                    background-color: white;
                                }}
                                QComboBox::drop-down {{
                                    border: 1px solid #669bbc; 
                                    width: 20px;
                                    outline: none;
                                }}
                                
                                QComboBox QAbstractItemView {{
                                    min-width: 90px; 
                                    border: 1px solid #669bbc; 
                                    background: white;
                                    selection-background-color: #669bbc;
                                    selection-color: white;
                                    padding: 3px; 
                                    margin: 0px;  
                                    alignment: center; 
                                }}
                                QComboBox {{
                                    padding-left: 10px; 
                                    font-size: 12px;
                                    font-family: "Times", "Times New Roman", serif;
                                    border: 1px solid #669bbc; 
                                }}
                                QComboBox QAbstractItemView::item {{
                                    padding: 5px; 
                                    font-size: 12px;
                                    color: #333;
                                    border: none; 
                                }}
                                QComboBox QAbstractItemView::item:selected {{
                                    background-color: #669bbc;
                                    color: white;
                                    border-radius: 3px;
                                }}
                                QComboBox:focus {{
                                    border: 1px solid #669bbc; 
                                }}
                            """
                            combined_style = old_style + new_style
                            QComboBox.setStyleSheet(combined_style)

                if i == scenario_layout.count() - 1:
                    widget.setStyleSheet("background-color: #669bbc; border-radius: 8px;")

                    label_list = [child for child in widget.children() if isinstance(child, QLabel)]

                    if label_list:
                        # 🎯 Première QLabel (souvent le titre)
                        label_list[0].setStyleSheet("""
                            QLabel {
                                color: white;
                                font-size: 16px;
                                border: none;
                                border-radius: 4px;
                                text-align: center;
                                background-color: #669bbc;
                                font-family: "Times", "Times New Roman", serif;
                                margin-left: 8px;
                            }
                        """)

                        # ➕ Vérifier si c’est un "Random"
                        if label_list[0].text().startswith("Random"):
                            label_list[0].setStyleSheet("""
                                QLabel {
                                    color: white;
                                    font-size: 9px;
                                    border: 1px dashed #ffffff;
                                    border-radius: 4px;
                                    background-color: transparent;
                                    font-family: "Monaco", monospace;
                                    padding: 0px;
                                    margin: 0px;
                                    border:None;
                                }
                            """)
                            print(f"[🎯] Dernier widget - QLabel (0) spéciale: '{label_list[0].text()}'")

                        # 🎨 Toutes les autres QLabels
                        for label in label_list[1:]:
                            label.setStyleSheet("""
                                QLabel {
                                    color: white;
                                    font-size: 16px;
                                    border: none;
                                    border-radius: 4px;
                                    text-align: center;
                                    background-color: #669bbc;
                                    font-family: "Times", "Times New Roman", serif;
                                }
                            """)

                            # 🎯 Appliquer style spécial si commence par "Random"
                            if label.text().startswith("Random"):
                                label.setStyleSheet("""
                                    QLabel {
                                        color: white;
                                        font-size: 9px;
                                        border: 1px dashed #ffffff;
                                        border-radius: 4px;
                                        background-color: transparent;
                                        font-family: "Monaco", monospace;
                                        padding: 0px;
                                        margin: 0px;
                                        border:None;
                                    }
                                """)
                                print(f"[🎯] Dernier widget - QLabel Random: '{label.text()}'")



                    buttons = [child for child in widget.children() if isinstance(child, QPushButton)]
                    if buttons:
                        last_button = buttons[0]
                        last_button.setVisible(True)
                        last_button.setCursor(Qt.CursorShape.PointingHandCursor)

                        try:
                            last_button.clicked.disconnect()
                        except TypeError:
                            pass  
                        last_button.clicked.connect(Go_To_Previous_State)
            
                    spin_boxes = [child for child in widget.children() if isinstance(child, QSpinBox)]
                    if spin_boxes and Settings.DOWN_EXISTS_W and Settings.UP_EXISTS_W:
                        new_style = f"""
                            QSpinBox {{
                                padding: 2px; 
                                border: 1px solid white; 
                                color: white;
                            }}
                            QSpinBox::down-button {{
                                image: url("{Settings.ARROW_DOWN_W_PATH}");
                                width: 13px;
                                height: 13px;
                                padding: 2px;  
                                border-top-left-radius: 5px;
                                border-bottom-left-radius: 5px;
                            }}
                            QSpinBox::up-button {{
                                image: url("{Settings.ARROW_UP_W_PATH}");
                                width: 13px;
                                height: 13px;
                                padding: 2px;
                                border-top-left-radius: 5px;
                                border-bottom-left-radius: 5px;
                            }}
                        """
                        spin_boxes[0].setStyleSheet(new_style)  



                    QCheckBox_list_last = [child for child in widget.children() if isinstance(child, QCheckBox)]
                    if QCheckBox_list_last:  
                        checkbox = QCheckBox_list_last[0]
                        
                        if checkbox.isChecked():
                            additional_style = """
                                QCheckBox::indicator:checked  {
                                    background-color: #669bbc;
                                    border: 2px solid #ffffff;
                                }
                            """
                        else:
                            additional_style = """
                                QCheckBox::indicator {
                                    color: gray;
                                    background-color: #e0e0e0; 
                                    border: 1px solid #cccccc;
                                }
                            """


                        current_style = checkbox.styleSheet()
                        new_style = f"{current_style} {additional_style}" if current_style else additional_style
                        checkbox.setStyleSheet(new_style)


                QComboBox_list = [child for child in widget.children() if isinstance(child, PyQt6.QtWidgets.QComboBox)]
                if QComboBox_list:
                    QComboBox = QComboBox_list[0]

                    if Settings.DOWN_EXISTS:
                        old_style = QComboBox.styleSheet()
                        new_style = f"""
                            QComboBox::down-arrow {{
                                image: url("{Settings.ARROW_DOWN_PATH}");
                                width: 13px;
                                height: 13px;
                                border: none;
                                background-color: white;
                            }}
                            QComboBox::drop-down {{
                                border: none;
                                width: 20px;
                                outline: none;
                            }}
                            
                            QComboBox QAbstractItemView {{
                                min-width: 90px; 
                                border: none; 
                                background: white;
                                selection-background-color: #669bbc;
                                selection-color: white;
                                padding: 3px; 
                                margin: 0px;  
                                alignment: center; 
                            }}
                            QComboBox {{
                                padding-left: 10px; 
                                font-size: 12px;
                                font-family: "Times", "Times New Roman", serif;
                                border: 1px solid #669bbc; 
                                outline: none; 
                            }}
                            QComboBox QAbstractItemView::item {{
                                padding: 5px; 
                                font-size: 12px;
                                color: #333;
                                border: none; 
                            }}
                            QComboBox QAbstractItemView::item:selected {{
                                background-color: #669bbc;
                                color: white;
                                border-radius: 3px;
                            }}
                            QComboBox:focus {{
                                border: 1px solid #669bbc; 
                            }}
                        """
                        combined_style = old_style + new_style
                        QComboBox.setStyleSheet(combined_style)

            




                # Récupérer tous les QTextEdit dans le widget
                QTextEdits = [child for child in widget.children() if isinstance(child, QTextEdit)]
                print(f"[🔍] Nombre de QTextEdit détectés : {len(QTextEdits)}")

                for idx, qtextedit in enumerate(QTextEdits):
                    print(f"[➡️] Préparation du QTextEdit numéro {idx}")

                    # ✅ إخفاء الـ scrollbars
                    qtextedit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                    qtextedit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)


                    def create_handler(te, index):
                        def handler(event):
                            print(f"[🖱️] Clic détecté sur le QTextEdit numéro {index}")
                            try:
                                dialog = CustomTextDialog(te, texte_initial=te.toPlainText())
                                if dialog.exec():  # Si l’utilisateur clique sur "Enregistrer"
                                    new_text = dialog.get_text()
                                    te.setPlainText(new_text)
                                    print(f"[✅] Nouveau texte saisi pour QTextEdit {index} :\n{new_text}")
                                else:
                                    print(f"[⚠️] Modification annulée (QTextEdit {index})")
                                # ✅ دايمًا ننحي الفوكس سواء سجل أو لغى
                                te.clearFocus()
                            except Exception as e:
                                print(f"[❌] Erreur lors de l’ouverture de la boîte de dialogue : {e}")
                        return handler

                    qtextedit.mousePressEvent = create_handler(qtextedit, idx)
                    print(f"[🔗] Gestionnaire de clic associé au QTextEdit numéro {idx}")




                                                    


                qlineedits = [child for child in widget.children() if isinstance(child, QLineEdit)]
                checkbox_qlineedit = None  # ⚠️ تخزين QLineEdit المرتبط بـ QCheckBox

                print("[🔍] Total QLineEdits détectés:", len(qlineedits))

                # إذا كان آخر QLineEdit داخل widget يحتوي على QCheckBox، نحذفه من القائمة
                if qlineedits:
                    last_qlineedit = qlineedits[-1]
                    parent_widget = last_qlineedit.parent()
                    if parent_widget:
                        contains_checkbox = any(isinstance(child, QCheckBox) for child in parent_widget.children())
                        print(f"[🧩] Dernier QLineEdit détecté. Contient QCheckBox ? {contains_checkbox}")
                        if contains_checkbox:
                            checkbox_qlineedit = last_qlineedit  # ✅ نحفظه ولكن لا نحذفه
                            qlineedits.pop()  # حذف العنصر الأخير
                            print("[📦] QLineEdit avec QCheckBox stocké séparément.")

                # ربط المحققين للـ QLineEdits العادية
                for idx, qlineedit in enumerate(qlineedits):
                    def create_validator(line_edit, default_val):
                        def validator():
                            print(f"[📝] Validation déclenchée pour QLineEdit[{idx}] avec valeur par défaut: {default_val}")
                            ValidationUtils.validate_qlineedit_with_range(line_edit, default_val)
                        return validator

                    if len(qlineedits) > 1 and idx == 0:
                        qlineedit.editingFinished.connect(create_validator(qlineedit, "50,50"))
                    else:
                        qlineedit.editingFinished.connect(create_validator(qlineedit, "1,1"))

                # ربط المحقق الخاص بـ QLineEdit مع QCheckBox
                if checkbox_qlineedit:
                    print("[🔗] Connexion du QLineEdit contenant QCheckBox à une validation personnalisée.")
                    def validate_checkbox_qlineedit():
                        print("[✅] Validation personnalisée déclenchée pour QLineEdit avec QCheckBox.")
                        UIManager.Validate_Checkbox_Linked_Qlineedit(checkbox_qlineedit)

                    checkbox_qlineedit.editingFinished.connect(validate_checkbox_qlineedit)
                # else:
                    # print("[⚠️] Aucun QLineEdit avec QCheckBox détecté.")





    @staticmethod
    def Validate_Checkbox_Linked_Qlineedit( qlineedit: QLineEdit):
        if qlineedit is None:
            print("[❌ ERREUR] Le QLineEdit est None. Validation ignorée.")
            return

        parent_widget = qlineedit.parent()
        full_state = parent_widget.property("full_state") if parent_widget else None

        text = qlineedit.text().strip()
        print(f"[🔍 INFO] Texte saisi dans QLineEdit associé à QCheckBox : '{text}'")

        old_style = qlineedit.styleSheet()
        cleaned_style = ValidationUtils.remove_border_from_style(old_style)

        # ✅ Vérification conditionnelle selon full_state
        if full_state and isinstance(full_state, dict):
            sub_id = full_state.get("id", "")
            sub_label = full_state.get("label", "Google")

            # Chercher le QCheckBox associé dans le même parent
            checkbox = next((child for child in parent_widget.children() if isinstance(child, QCheckBox)), None)

            if sub_id in ["open_spam", "open_inbox"]:
                if checkbox and checkbox.isChecked():
                    if text :
                        print("[✅ CONDITION VALIDE] Checkbox cochée et texte valide.")
                        def apply_ok():
                            qlineedit.setStyleSheet(cleaned_style)
                            qlineedit.setToolTip("")
                            print("[🔔 INFO] Bordure retirée et tooltip supprimé.")
                        QTimer.singleShot(0, apply_ok)
                        return
                    else:
                        print("[⚠️ TEXTE INVALIDE] Champ vide ou numérique malgré checkbox cochée.")
                        qlineedit.setText(sub_label or "Google")

                        def apply_error():
                            new_style = ValidationUtils.inject_border_into_style(cleaned_style)
                            qlineedit.setStyleSheet(new_style)
                            qlineedit.setToolTip("Texte invalide. Valeur remplacée par défaut depuis full_state.")
                            print("[🔔 INFO] Erreur appliquée avec bordure rouge.")
                        QTimer.singleShot(0, apply_error)
                        return

        # 🧾 Sinon: validation classique (ancienne logique)
        if text.isdigit() or len(text) < 4:
            print("[⚠️ INVALIDE] Le texte est un nombre ou trop court (<4).")
            qlineedit.setText("Google")

            def apply_error():
                new_style = ValidationUtils.inject_border_into_style(cleaned_style)
                qlineedit.setStyleSheet(new_style)
                qlineedit.setToolTip("Le texte est un nombre ou trop court, veuillez corriger la saisie.")
                print("[🔔 INFO] Bordure rouge appliquée et tooltip invitant à corriger la saisie.")
            QTimer.singleShot(0, apply_error)
        else:
            print("[✅ VALIDE] Texte non numérique et au moins 4 caractères.")

            def apply_ok():
                qlineedit.setStyleSheet(cleaned_style)
                qlineedit.setToolTip("")
                print("[🔔 INFO] Bordure retirée et tooltip supprimé.")
            QTimer.singleShot(0, apply_ok)





    # Supprime tous les boutons de réinitialisation liés aux blocs ajoutés *après* le dernier bloc contenant une checkbox.
    # Cette fonction :
    # - Identifie l'index du dernier bloc contenant une QCheckBox.
    # - Récupère les labels des blocs ajoutés après celui-ci.
    # - Compare avec les boutons existants dans le layout des options de reset.
    # - Supprime ceux qui sont déjà couverts par les labels détectés.
    @staticmethod
    def Remove_Copier(scenario_layout,reset_options_layout):
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
    def Remove_Initaile( scenario_layout,reset_options_layout):

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


        