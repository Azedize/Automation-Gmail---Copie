# ui_utils.py
# =============================================================================
# Module : ui_utils.py
# Rôle   : utilitaires d'interface graphique (PyQt6) de l'application
#          d'automatisation Gmail.
#
# Contenu du module :
#   - VerticalTabBar / VerticalTabWidget : barre d'onglets verticale dont le
#     rendu est entièrement dessiné à la main (y compris l'onglet « Result »
#     qui affiche les compteurs Completed / Not Completed en couleur).
#   - CustomTextDialog : petite boîte de dialogue d'édition de texte multi-lignes.
#   - UIManager : boîte à outils de méthodes statiques qui initialisent, stylisent
#     et mettent à jour les widgets de la fenêtre principale (onglets de résultats,
#     badges de notification, combobox, boutons, étapes du scénario, validation
#     des champs de saisie, etc.).
# =============================================================================
#
# --- Imports de la bibliothèque standard ---
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

# --- Résolution du dossier racine du projet ---
# __file__ = .../ui_utils/ui_utils.py -> on remonte de deux niveaux pour obtenir la
# racine du projet. Elle est insérée en tête de sys.path afin que les paquets
# « config » et « utils » soient importables quel que soit le dossier de lancement.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# --- Imports internes au projet ---
# Settings : configuration centrale (couleurs, polices, chemins, fonctions de log).
# ValidationUtils : fonctions de vérification (existence de chemins, validation
# des champs de saisie, manipulation des bordures d'erreur dans les styles).
# Sans ces deux dépendances le module ne peut pas fonctionner : en cas d'échec
# d'import, l'application s'arrête immédiatement avec le code de sortie 1
# (aucun message n'est affiché).
try:
    from config import Settings
    from utils.validation_utils import ValidationUtils
except ImportError as e:
    sys.exit(1)


# =============================================================================
# Classe VerticalTabBar
# -----------------------------------------------------------------------------
# Barre d'onglets personnalisée affichée verticalement sur le côté gauche.
# Le dessin natif de Qt est entièrement remplacé (paintEvent) pour obtenir :
#   - des onglets de taille fixe (180 x 60) avec des couleurs selon l'état
#     (sélectionné / survolé / normal) ;
#   - un rendu spécial pour l'onglet « Result » lorsqu'il porte des données
#     (tabData = dict avec les compteurs), avec un texte multicolore :
#     « Result (X Completed / Y Not Completed) » en vert et rouge.
# =============================================================================
class VerticalTabBar(QtWidgets.QTabBar):
    # Constructeur : configure l'orientation, le focus, le suivi de la souris
    # et initialise les marges internes utilisées par tabRect().
    def __init__(self, parent=None):
        super().__init__(parent)
        # RoundedWest : onglets placés à gauche du contenu (orientation verticale).
        self.setShape(QtWidgets.QTabBar.Shape.RoundedWest)
        # StrongFocus : la barre peut recevoir le focus au clavier (Tab) et au clic.
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # Suivi de la souris même sans bouton enfoncé : nécessaire pour détecter
        # le survol d'un onglet et le redessiner avec la couleur « hover ».
        self.setMouseTracking(True)
        # Marges (en pixels) appliquées au rectangle de chaque onglet dans tabRect().
        # Avec la valeur 0, le rectangle n'est pas réduit.
        self.tab_margin = 0
        self.left_margin = 0
        self.right_margin = 0

    # Clic souris : on conserve le comportement standard (changement d'onglet),
    # puis on force un redessin immédiat pour refléter la nouvelle sélection.
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.update()

    # Relâchement du clic : même logique, redessin pour garder l'affichage à jour.
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.update()

    # Taille suggérée pour chaque onglet.
    # En mode vertical, Qt calcule la taille comme pour un onglet horizontal :
    # transpose() échange largeur et hauteur, puis on impose une taille fixe
    # de 180 px de large et 60 px de haut pour tous les onglets.
    def tabSizeHint(self, index):
        size_hint = super().tabSizeHint(index)
        size_hint.transpose()
        size_hint.setWidth(180)
        size_hint.setHeight(60)
        return size_hint

    # Rectangle occupé par l'onglet d'index donné, réduit par les marges
    # configurées (adjust(gauche, haut, -droite, -bas)).
    def tabRect(self, index):
        rect = super().tabRect(index)
        rect.adjust(self.left_margin, self.tab_margin, -self.right_margin, -self.tab_margin)
        return rect

    # Dessin complet de la barre d'onglets (remplace le rendu natif de Qt).
    # Étapes :
    #   1. Création d'un QPainter avec anticrénelage.
    #   2. Détection de l'onglet actuellement survolé par la souris.
    #   3. Pour chaque onglet : calcul de l'état (sélectionné / survolé), puis
    #      a) onglet « Result » avec données -> texte multicolore sur fond transparent ;
    #      b) sinon -> fond coloré + bordures + texte aligné à gauche.
    #   4. Libération du painter.
    # Remarque : super().paintEvent() n'est pas appelé, donc Qt ne dessine rien
    # lui-même (ni texte, ni icône natifs).
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Position globale du curseur convertie en coordonnées locales de la barre,
        # puis conversion en index d'onglet (-1 si le curseur n'est sur aucun onglet).
        hovered_index = self.tabAt(self.mapFromGlobal(QtGui.QCursor.pos()))
        # Parcours de tous les onglets pour les dessiner un par un.
        for index in range(self.count()):
            tab_rect = self.tabRect(index)
            # Rectangle invalide (onglet non visible / non calculé) : rien à dessiner.
            if not tab_rect.isValid():
                continue
            # L'onglet est-il l'onglet courant ?
            selected = self.currentIndex() == index
            # L'effet de survol ne s'applique pas à l'onglet déjà sélectionné.
            hovered = hovered_index == index and not selected
            # Données arbitraires attachées à l'onglet (ici un dict de compteurs
            # déposé par UIManager.setCustomColoredTab).
            tab_data = self.tabData(index)
            text = self.tabText(index)

            # --- Cas a) : onglet « Result » avec compteurs ---
            # Le texte est dessiné morceau par morceau pour pouvoir colorer chaque partie.
            if isinstance(tab_data, dict) and text == "Result":
                # Fond totalement transparent (alpha = 0).
                bg_color = QtGui.QColor(0, 0, 0, 0)
                # Couleur du texte principal selon l'état de l'onglet :
                # blanc si sélectionné, couleur primaire si survolé, gris foncé sinon.
                if selected:
                    pen_color = QtGui.QColor("#ffffff")
                elif hovered:
                    pen_color = QtGui.QColor(Settings.PRIMARY_COLOR)
                else:
                    pen_color = QtGui.QColor("#333333")

                # save()/restore() isolent les réglages du painter (stylo, pinceau) pour ne
                # pas impacter le dessin suivant.
                painter.save()
                # Pas de contour : on ne remplit que le fond du rectangle.
                painter.setPen(QtCore.Qt.PenStyle.NoPen)
                painter.setBrush(QtGui.QBrush(bg_color))
                painter.drawRect(tab_rect)
                painter.restore()

                # Deuxième bloc isolé : dessin du texte.
                painter.save()
                font = QFont(Settings.FONT_FAMILY, 10)
                painter.setFont(font)
                # Zone de texte = rectangle de l'onglet avec 12 px de marge horizontale
                # et 8 px de marge verticale.
                text_rect = QtCore.QRect(tab_rect.left() + 12, tab_rect.top() + 8, tab_rect.width() - 24, tab_rect.height() - 16)

                # Métriques de police : permettent de mesurer la largeur de chaque segment
                # et de placer les morceaux de texte bout à bout.
                fm = painter.fontMetrics()
                # Les quatre segments du libellé. L'accès tab_data['completed'] suppose
                # que les clés sont présentes dans le dictionnaire.
                title_text = "Result "
                completed_text = f"({tab_data['completed']} Completed"
                separator_text = " / "
                not_completed_text = f"{tab_data['not_completed']} Not Completed)"

                # Point de départ du dessin. drawText(x, y, ...) utilise y comme ligne de
                # base : on la calcule pour centrer verticalement le texte dans la zone.
                x = text_rect.left()
                y = text_rect.center().y() + fm.ascent() // 2 - 2

                # Segment 1 : « Result » dans la couleur liée à l'état, puis on avance x
                # de la largeur du segment dessiné.
                painter.setPen(QtGui.QPen(pen_color))
                painter.drawText(x, y, title_text)
                x += fm.horizontalAdvance(title_text)
                # Segment 2 : nombre de « Completed » en vert.
                painter.setPen(QtGui.QPen(QtGui.QColor("#28a745")))
                painter.drawText(x, y, completed_text)
                x += fm.horizontalAdvance(completed_text)
                # Segment 3 : séparateur « / » dans la couleur liée à l'état.
                painter.setPen(QtGui.QPen(pen_color))
                painter.drawText(x, y, separator_text)
                x += fm.horizontalAdvance(separator_text)

                # Segment 4 : nombre de « Not Completed » en rouge.
                painter.setPen(QtGui.QPen(QtGui.QColor("#dc3545")))
                painter.drawText(x, y, not_completed_text)
                painter.restore()
            # --- Cas b) : onglet standard ---
            else:
                # Couleurs de fond et de texte selon l'état :
                #   - sélectionné : fond couleur primaire, texte blanc ;
                #   - survolé     : fond primaire éclairci de 40 % (lighter(140)), texte noir ;
                #   - normal      : fond gris clair, texte gris foncé.
                if selected:
                    bg_color = QtGui.QColor(Settings.PRIMARY_COLOR)
                    pen_color = QtGui.QColor("#ffffff")
                elif hovered:
                    bg_color = QtGui.QColor(Settings.PRIMARY_COLOR).lighter(140)
                    pen_color = QtGui.QColor("#000000")
                else:
                    bg_color = QtGui.QColor("#F5F5F5")
                    pen_color = QtGui.QColor("#333333")

                # Dessin du fond puis de deux bordures fines (bas et droite) de couleur
                # primaire, qui séparent les onglets entre eux et du contenu.
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

                # Dessin du texte, aligné à gauche et centré verticalement dans la zone.
                painter.save()
                font = QFont(Settings.FONT_FAMILY, 10)
                painter.setFont(font)
                painter.setPen(QtGui.QPen(pen_color))
                text_rect = QtCore.QRect(tab_rect.left() + 12, tab_rect.top() + 8, tab_rect.width() - 24, tab_rect.height() - 16)
                painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignLeft, text)
                painter.restore()
        # Fin du dessin : libération obligatoire du QPainter.
        painter.end()


# =============================================================================
# Classe VerticalTabWidget
# -----------------------------------------------------------------------------
# QTabWidget qui utilise la barre VerticalTabBar ci-dessus et place les onglets
# à gauche du contenu. Utilisé par UIManager.convertToVerticalTabs().
# =============================================================================
class VerticalTabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Remplacement de la barre d'onglets par défaut (doit être fait avant
        # l'ajout des onglets). Le QTabWidget devient parent de la barre.
        self.setTabBar(VerticalTabBar())
        # Position des onglets : côté ouest (gauche).
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)


# =============================================================================
# Classe CustomTextDialog
# -----------------------------------------------------------------------------
# Boîte de dialogue modale permettant de modifier un texte multi-lignes.
# Elle est ouverte lorsqu'on clique sur un QTextEdit d'une étape du scénario
# (voir updateActionsColorHandleLastButton) : l'utilisateur édite le texte
# dans une grande zone puis valide (Save) ou annule (Cancel).
# =============================================================================
class CustomTextDialog(QDialog):
    # Constructeur : texte_initial est le texte pré-rempli dans la zone d'édition.
    def __init__(self, parent=None, texte_initial=""):
        super().__init__(parent)
        self.setWindowTitle("Update Text")
        self.setMinimumSize(500, 350)

        # Layout vertical principal avec marges de 20 px et espacement de 15 px.
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        # Libellé d'invite affiché au-dessus de la zone de texte.
        label = QLabel("📝 Please enter your text below:")
        layout.addWidget(label)
        # Zone d'édition multi-lignes pré-remplie avec le texte actuel.
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(texte_initial)
        layout.addWidget(self.text_edit)
        # Ligne de boutons horizontale.
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        self.btn_ok = QPushButton("Save")
        self.btn_cancel = QPushButton("Cancel")
        # Signaux Qt : « Save » appelle accept() et « Cancel » appelle reject().
        # Les deux ferment la boîte ; exec() renverra alors 1 (accepté) ou 0 (rejeté).
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        # Ressort élastique : pousse les boutons vers la droite.
        button_layout.addStretch()
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        # Feuille de style (QSS) de la boîte de dialogue.
        # Dans la f-string, les doubles accolades {{ }} produisent des accolades
        # littérales. Les sélecteurs #btn_ok / #btn_cancel ciblent les boutons par
        # leur objectName.
        self.setStyleSheet(
            f"QDialog {{ background-color: #ffffff; font-family: {Settings.FONT_FAMILY}; }} QLabel {{ font-family: {Settings.FONT_FAMILY}; font-size: 14px; color: #2d2d2d; font-weight: 500; margin-bottom: 10px; }} QTextEdit {{ border: 1px solid #d0d0d0; border-radius: 10px; font-family: {Settings.FONT_FAMILY}; background-color: #fafafa; font-size: 12pt; padding: 5px; }} QTextEdit:focus {{ border: 2px solid #0078d7; background-color: #ffffff; }} QPushButton {{ font-family: {Settings.FONT_FAMILY}; padding: 8px 16px; text-align: center; font-size: 14px; font-weight: bold; min-width: 120px; }} QPushButton#btn_ok {{ background-color: #0078d7; border: none; color: white; }} QPushButton#btn_ok:hover {{ background-color: #005a9e; }} QPushButton#btn_cancel {{ background-color: #f0f0f0; border: 1px solid #cccccc; color: #333333; }} QPushButton#btn_cancel:hover {{ background-color: #e0e0e0; }}"
        )
        # Attribution des objectName utilisés par les sélecteurs QSS ci-dessus.
        # Le style n'est réellement appliqué qu'à l'affichage de la boîte, donc les
        # noms sont bien pris en compte même s'ils sont définis après setStyleSheet().
        self.btn_ok.setObjectName("btn_ok")
        self.btn_cancel.setObjectName("btn_cancel")

    # Retourne le texte saisi par l'utilisateur (texte brut, sans mise en forme).
    def getText(self):
        return self.text_edit.toPlainText()


# =============================================================================
# Classe UIManager
# -----------------------------------------------------------------------------
# Boîte à outils de l'interface : elle ne contient que des méthodes statiques
# (aucune instance n'est créée). Chaque méthode reçoit la fenêtre principale
# ou les widgets à manipuler en paramètre.
# Grands domaines couverts :
#   - onglet « Result » : compteurs colorés, réinitialisation, détection ;
#   - lecture du fichier de résultats et remplissage des listes par statut ;
#   - badges de notification, boîtes de message stylisées, presse-papiers ;
#   - styles et comportements des étapes du scénario (dernière étape active,
#     validation des champs, édition des textes) ;
#   - initialisation des widgets chargés depuis le fichier .ui (boutons,
#     combobox, onglets verticaux, conteneurs, templates).
# =============================================================================
class UIManager:
    @staticmethod
    # -------------------------------------------------------------------------
    # Remet l'onglet « Result » à son état d'origine (texte simple « Result »),
    # typiquement avant le lancement d'un nouveau traitement (Submit).
    # Étapes :
    #   1. Vérifie que le widget et l'index sont valides.
    #   2. Supprime les widgets personnalisés installés dans l'onglet
    #      (le QLabel HTML posé par setCustomColoredTab).
    #   3. Restaure le texte « Result » et efface les données (tabData) pour
    #      que la barre revienne à un rendu standard.
    #   4. Force le redessin.
    # -------------------------------------------------------------------------
    def resetResultTabLabel(tab_widget, index):
        """Reset a Result tab to its default plain state before Submit starts."""
        # Sécurité : widget absent ou index hors limites -> on ne fait rien.
        if tab_widget is None or index < 0 or index >= tab_widget.count():
            return

        tab_bar = tab_widget.tabBar()
        if tab_bar is None:
            return

        # Récupère les éventuels widgets placés à gauche et à droite du texte de l'onglet.
        left_button = tab_bar.tabButton(index, QTabBar.ButtonPosition.LeftSide)
        right_button = tab_bar.tabButton(index, QTabBar.ButtonPosition.RightSide)
        # deleteLater() programme la destruction du widget au prochain passage de la
        # boucle d'événements (plus sûr qu'une suppression immédiate), puis on retire
        # la référence dans l'onglet.
        if left_button is not None:
            left_button.deleteLater()
            tab_bar.setTabButton(index, QTabBar.ButtonPosition.LeftSide, None)
        if right_button is not None:
            right_button.deleteLater()
            tab_bar.setTabButton(index, QTabBar.ButtonPosition.RightSide, None)

        # Texte par défaut de l'onglet.
        tab_widget.setTabText(index, "Result")

        # Efface les compteurs stockés dans l'onglet. Le hasattr est une précaution ;
        # en cas d'erreur, on journalise un événement structuré sans interrompre l'UI.
        if hasattr(tab_bar, "setTabData"):
            try:
                tab_bar.setTabData(index, None)
            except Exception as exc:
                Settings.write_log_event("ui_tab_reset_failed", "WARNING", index=index, exception_type=type(exc).__name__, error=str(exc))

        # Redessin de la barre et du widget d'onglets pour appliquer les changements.
        tab_bar.update()
        tab_widget.update()

    @staticmethod
    # -------------------------------------------------------------------------
    # Écrit dans le log de développement l'état complet des onglets : texte,
    # données (tabData) et type des widgets gauche/droite de chaque onglet.
    # Outil de diagnostic utilisé notamment lors de la mise à jour de « Result ».
    # -------------------------------------------------------------------------
    def logTabDebugInfo(tab_widget, prefix=""):
        """Log tab names, tabData and custom button states for debugging."""
        if tab_widget is None:
            return

        tab_bar = tab_widget.tabBar()
        if tab_bar is None:
            return

        # Construction du message : un en-tête puis un bloc par onglet.
        tab_count = tab_widget.count()
        message = [f"{prefix} tabs={tab_count}"]

        # Pour chaque onglet : texte, données et type des boutons ({!r} = repr ;
        # type(None).__name__ donne « NoneType » quand il n'y a pas de bouton).
        for i in range(tab_count):
            tab_text = tab_widget.tabText(i)
            tab_data = tab_bar.tabData(i) if hasattr(tab_bar, "tabData") else None
            left_button = tab_bar.tabButton(i, QTabBar.ButtonPosition.LeftSide)
            right_button = tab_bar.tabButton(i, QTabBar.ButtonPosition.RightSide)
            message.append(f"index={i} text={tab_text!r} data={tab_data!r} left={type(left_button).__name__} right={type(right_button).__name__}")
        # Assemblage de toutes les parties sur une seule ligne séparée par « | ».
        log_text = " | ".join(message)
        # Écriture dans le log ; si l'écriture échoue, on enregistre un événement
        # d'avertissement plutôt que de lever une exception.
        try:
            Settings.write_log_dev_file(f"[UI TRACE] {log_text}", "DEBUG")
        except Exception as exc:
            Settings.write_log_event("ui_tab_debug_failed", "WARNING", exception_type=type(exc).__name__, error=str(exc))

    @staticmethod
    # -------------------------------------------------------------------------
    # Indique si l'onglet d'index donné est l'onglet « Result ».
    # Deux critères, dans cet ordre :
    #   1. l'onglet porte des données dict contenant « completed » et
    #      « not_completed » (cas où setCustomColoredTab a vidé le texte natif) ;
    #   2. sinon, le texte de l'onglet commence par « Result ».
    # -------------------------------------------------------------------------
    def isResultTab(tab_widget, index):
        # Widget absent ou index invalide : ce n'est pas un onglet Result.
        if tab_widget is None or index < 0 or index >= tab_widget.count():
            return False
        tab_bar = tab_widget.tabBar()
        # Critère 1 : présence des compteurs dans les données de l'onglet.
        if tab_bar is not None and hasattr(tab_bar, "tabData"):
            tab_data = tab_bar.tabData(index)
            if isinstance(tab_data, dict) and "completed" in tab_data and "not_completed" in tab_data:
                return True

        # Critère 2 : test sur le texte affiché.
        tab_text = tab_widget.tabText(index)
        return isinstance(tab_text, str) and tab_text.startswith("Result")

    @staticmethod
    # -------------------------------------------------------------------------
    # Affiche dans l'onglet « Result » un libellé HTML coloré :
    # « Result (X completed / Y not completed) ».
    # Étapes :
    #   1. Détermine les couleurs (valeurs de Settings ou couleurs par défaut).
    #   2. Construit le texte HTML (vert pour completed, couleur d'accent pour
    #      not completed).
    #   3. Vide le texte natif de l'onglet pour éviter un double affichage.
    #   4. Crée un QLabel RichText dans un conteneur transparent.
    #   5. Dimensionne le conteneur à la taille de l'onglet et l'installe comme
    #      bouton gauche de l'onglet.
    #   6. Stocke les compteurs dans tabData (utilisés par isResultTab et par
    #      VerticalTabBar.paintEvent).
    # -------------------------------------------------------------------------
    def setCustomColoredTab(tab_widget, index, completed_count, not_completed_count):
        # « or » fournit une couleur par défaut si le réglage est vide ou None.
        main_color = Settings.PRIMARY_COLOR or "#669bbc"
        accent_color = Settings.ACCENT_COLOR or "#dc3545"

        # Texte HTML centré, en police Times, avec deux parties colorées.
        html_text = (
            f'<div style="text-align:center; margin:0; padding:0;">'
            f"<span style=\"font-family:'Times', 'Times New Roman', serif; font-size:14px;\">Result ("
            f'<span style="color:#008000;">{completed_count} completed</span> / '
            f'<span style="color:{accent_color};">{not_completed_count} not completed</span>)</span>'
            f"</div>"
        )

        # Le texte natif est vidé : c'est le QLabel qui affiche désormais le libellé.
        tab_widget.setTabText(index, "")

        # QLabel en mode RichText pour interpréter le HTML, centré, extensible
        # horizontalement.
        label = QLabel()
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setText(html_text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Style du libellé : fond transparent, couleur principale, et couleur plus
        # foncée au survol (:hover).
        label.setStyleSheet(f"QLabel {{ background: transparent; color: {main_color}; font-family: 'Times', 'Times New Roman', serif; font-size: 14px; }} QLabel:hover {{ color:#2c3e50; }}")

        # Conteneur transparent sans bordure.
        # WA_StyledBackground : autorise la feuille de style à peindre le fond d'un
        # QWidget simple. WA_Hover + suivi de souris : génèrent les événements de
        # survol nécessaires au pseudo-état :hover.
        wrapper = QWidget()
        wrapper.setStyleSheet("QWidget { background: transparent; border: none; }")
        wrapper.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        wrapper.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        wrapper.setMouseTracking(True)

        # Layout sans marge ni espacement : le libellé occupe tout le conteneur.
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(label)

        wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Si le rectangle de l'onglet est connu, le conteneur en prend la largeur
        # minimale et la hauteur exacte.
        tab_rect = tab_widget.tabBar().tabRect(index)
        if tab_rect.isValid():
            wrapper.setMinimumWidth(tab_rect.width())
            wrapper.setFixedHeight(tab_rect.height())

        # On détache d'abord les éventuels widgets déjà installés à gauche et à
        # droite, puis on installe le nouveau conteneur à gauche de l'onglet.
        tab_bar = tab_widget.tabBar()
        tab_bar.setTabButton(index, QTabBar.ButtonPosition.LeftSide, None)
        tab_bar.setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
        tab_bar.setTabButton(index, QTabBar.ButtonPosition.LeftSide, wrapper)

        # Mémorisation des compteurs dans l'onglet ; échec journalisé sans bloquer.
        if hasattr(tab_bar, "setTabData"):
            try:
                tab_bar.setTabData(index, {"completed": completed_count, "not_completed": not_completed_count})
            except Exception as exc:
                Settings.write_log_event("ui_tab_data_update_failed", "WARNING", index=index, exception_type=type(exc).__name__, error=str(exc))

    @staticmethod
    # -------------------------------------------------------------------------
    # Vide le fichier de résultats (écrit une chaîne vide).
    # Appelée après chaque lecture pour que les mêmes résultats ne soient pas
    # retraités lors de la lecture suivante. Les erreurs sont journalisées
    # avec la pile d'appels mais ne sont pas propagées.
    # -------------------------------------------------------------------------
    def clearResultFile():
        try:
            Path(Settings.RESULT_FILE_PATH).write_text("", encoding="utf-8")
            Settings.write_log_dev_file(f"Le fichier {Settings.RESULT_FILE_PATH} a été vidé avec succès", "INFO")

        except Exception as e:
            Settings.write_log_dev_file(f"Error clearing result file: {e}\n{traceback.format_exc()}", "ERROR")

    @staticmethod
    # -------------------------------------------------------------------------
    # Lit le fichier de résultats et met à jour l'interface.
    # Paramètres :
    #   - window : fenêtre principale ;
    #   - NOTIFICATION_BADGES : dict {index d'onglet: QLabel badge} partagé,
    #     utilisé pour remplacer/supprimer les badges existants.
    # Format attendu de chaque ligne : « champ1:champ2:email:statut ».
    # Étapes :
    #   1. Vérifie l'existence du fichier (sinon message d'information).
    #   2. Lit les lignes non vides (sinon message d'avertissement).
    #   3. Analyse chaque ligne, élimine les doublons (email + statut),
    #      regroupe les emails par statut et compte completed / not completed.
    #   4. Met à jour le libellé de l'onglet « Result » dans « interface_2 ».
    #   5. Remplit la liste (QListWidget) de chaque onglet de statut dans
    #      « tabWidgetResult » et ajoute un badge avec le nombre d'emails.
    #   6. Dans tous les cas (bloc finally), vide le fichier de résultats.
    # -------------------------------------------------------------------------
    def readResultUpdateList(window, NOTIFICATION_BADGES):

        # Étape 1 : aucun fichier -> aucun email traité pour l'instant.
        if not ValidationUtils.pathExists(Settings.RESULT_FILE_PATH):
            UIManager.showCriticalMessage(window, "Information", "No emails have been processed yet.\nPlease check the filters or new data.", message_type="info")
            return

        # errors_dict : {statut: [emails]} ; defaultdict crée la liste automatiquement.
        # all_emails : liste de tous les emails uniques, pour l'onglet « all ».
        errors_dict = defaultdict(list)
        all_emails = []

        try:
            # Étape 2 : lecture en supprimant les espaces et en ignorant les lignes vides.
            with open(Settings.RESULT_FILE_PATH, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]

            # processEvents() laisse Qt traiter les événements en attente pour que
            # l'interface reste réactive pendant le traitement.
            QApplication.processEvents()
            # Fichier présent mais vide : rien à afficher.
            if not lines:
                UIManager.showCriticalMessage(window, "Warning", "No results available.", message_type="warning")
                return

            # Compteurs et ensemble des résultats déjà vus (dédoublonnage).
            completed_count = 0
            no_completed_count = 0
            seen_results = set()

            # Étape 3 : analyse ligne par ligne (idx n'est pas utilisé).
            for idx, line in enumerate(lines, start=1):
                # Découpage sur « : » ; toute ligne qui ne donne pas exactement 4 parties
                # est ignorée (par exemple si l'email ou le statut contient un « : »).
                parts = line.split(":")
                if len(parts) != 4:
                    continue
                # Les deux premiers champs ne sont pas utilisés ici ; statut en minuscules.
                _, _, email, status = [p.strip() for p in parts]
                status = status.lower()
                # Clé de dédoublonnage : email insensible à la casse (casefold) + statut.
                # Un même email avec le même statut n'est compté qu'une fois.
                result_key = (email.casefold(), status)
                if result_key in seen_results:
                    continue
                seen_results.add(result_key)
                # Ajout dans la liste globale et dans la liste du statut correspondant.
                all_emails.append(email)
                errors_dict[status].append(email)

                # Tout statut différent de « completed » est compté comme non terminé.
                if status == "completed":
                    completed_count += 1
                else:
                    no_completed_count += 1

            # Clé spéciale « all » : tous les emails uniques, quel que soit le statut.
            errors_dict["all"] = all_emails
            QApplication.processEvents()

            # Étape 4 : mise à jour du libellé de l'onglet « Result » dans le
            # widget d'onglets principal « interface_2 ».
            interface_tab_widget = window.findChild(QTabWidget, "interface_2")
            if interface_tab_widget:
                UIManager.logTabDebugInfo(interface_tab_widget, prefix="Before Result update")
                # Recherche du premier onglet Result, mise à jour des compteurs, arrêt.
                found = False
                for i in range(interface_tab_widget.count()):
                    if UIManager.isResultTab(interface_tab_widget, i):
                        found = True
                        UIManager.setCustomColoredTab(interface_tab_widget, i, completed_count, no_completed_count)
                        break

                # Onglet Result introuvable : journalisation + état des onglets pour diagnostic.
                if not found:
                    try:
                        Settings.write_log_dev_file("Result tab non trouvé dans interface_2", "WARNING")
                        UIManager.logTabDebugInfo(interface_tab_widget, prefix="Result tab non trouvé")
                    except Exception as exc:
                        Settings.write_log_dev_file("Result tab non trouvé et impossible de logger l'état des tabs " f"| exception={type(exc).__name__}: {exc}\n{traceback.format_exc()}", "ERROR")
                        pass
            # Le widget « interface_2 » lui-même est introuvable : simple avertissement.
            else:
                try:
                    Settings.write_log_dev_file("[UI WARNING] interface_2 introuvable pour la mise à jour du tab Result", "WARNING")
                except Exception as exc:
                    Settings.write_log_dev_file("Erreur lors de la mise à jour du tab Result " f"| exception={type(exc).__name__}: {exc}\n{traceback.format_exc()}", "ERROR")
                    pass
            QApplication.processEvents()

            # Étape 5 : widget d'onglets des résultats (version verticale créée par
            # convertToVerticalTabs, qui conserve le nom « tabWidgetResult »).
            # S'il est absent on s'arrête (le bloc finally videra quand même le fichier).
            result_tab_widget = window.findChild(QTabWidget, "tabWidgetResult")
            if not result_tab_widget:
                Settings.write_log_dev_file("TabWidgetResult introuvable dans la fenêtre pour mise à jour des résultats", "ERROR")
                return

            # Pour chaque statut connu, la page d'onglet porte le nom du statut
            # (objectName) : on la cherche et on remplit sa liste.
            for status in Settings.STATUS_LIST:
                tab_widget = result_tab_widget.findChild(QWidget, status)
                if not tab_widget:
                    Settings.write_log_dev_file(f"Tab pour le statut '{status}' introuvable dans tabWidgetResult", "WARNING")
                    continue

                # La première QListWidget trouvée dans la page reçoit les emails.
                list_widgets = tab_widget.findChildren(QListWidget)
                if not list_widgets:
                    Settings.write_log_dev_file(f"QListWidget introuvable dans le tab '{status}'", "WARNING")
                    continue

                # On vide la liste avant de la remplir avec les nouveaux résultats.
                list_widget = list_widgets[0]
                list_widget.clear()
                emails = errors_dict.get(status, [])

                # Des emails existent pour ce statut : ajout, défilement vers le bas,
                # badge de notification avec le nombre d'emails, et suppression de
                # l'éventuel libellé « no_data_message » (message « aucune donnée »).
                if emails:
                    list_widget.addItems(emails)
                    list_widget.scrollToBottom()
                    UIManager.addNotificationBadge(result_tab_widget, result_tab_widget.indexOf(tab_widget), len(emails), NOTIFICATION_BADGES)
                    Settings.write_log_dev_file(f"{len(emails)} emails ajoutés au tab '{status}'", "INFO")
                    message_label = tab_widget.findChild(QLabel, "no_data_message")
                    if message_label:
                        message_label.deleteLater()
                # Aucun email pour ce statut : élément d'information dans la liste.
                else:
                    list_widget.addItem("⚠ No email data available for this category currently.")
                    list_widget.show()
            QApplication.processEvents()
        # Toute erreur inattendue est journalisée avec la pile d'appels complète.
        except Exception as e:
            Settings.write_log_dev_file(f"Une erreur est survenue: {type(e).__name__} : {e}\n{traceback.format_exc()}", "ERROR")
        # Étape 6 : exécuté dans tous les cas (succès, erreur ou return anticipé
        # dans le try) : le fichier de résultats est vidé.
        finally:
            UIManager.clearResultFile()

    @staticmethod
    # -------------------------------------------------------------------------
    # Supprime le badge de notification associé à un index d'onglet.
    # pop(index, None) évite une KeyError si aucun badge n'existe.
    # -------------------------------------------------------------------------
    def removeNotification(index, NOTIFICATION_BADGES):
        badge = NOTIFICATION_BADGES.pop(index, None)
        if badge:
            badge.deleteLater()

    @staticmethod
    # -------------------------------------------------------------------------
    # Affiche un badge rouge arrondi contenant « count » en haut à droite d'un
    # onglet, et le mémorise dans NOTIFICATION_BADGES[tab_index].
    # Un éventuel ancien badge sur le même onglet est d'abord détruit.
    # -------------------------------------------------------------------------
    def addNotificationBadge(tab_widget, tab_index, count, NOTIFICATION_BADGES):
        # Suppression de l'ancien badge (s'il existe) pour éviter les superpositions.
        old_badge = NOTIFICATION_BADGES.get(tab_index)
        if old_badge:
            old_badge.deleteLater()

        # Position du badge : 14 px avant le bord droit et 2 px sous le haut
        # du rectangle de l'onglet.
        tab_bar = tab_widget.tabBar()
        tab_rect = tab_bar.tabRect(tab_index)
        badge_x = tab_rect.right() - 14
        badge_y = tab_rect.top() + 2
        # Création du QLabel badge (enfant du widget d'onglets) et de son style.
        badge_label = QLabel(f"{count}", tab_widget)
        badge_label.setStyleSheet("background-color: #d90429; color: white; font-size: 14px; padding: 3px; border-radius: 10px; min-width: 15px; text-align: center;")
        badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Placement et affichage du badge, puis enregistrement dans le dictionnaire
        # partagé ; les erreurs sont journalisées.
        try:
            badge_label.setParent(tab_widget)
            badge_label.move(badge_x, badge_y)
            badge_label.show()
            NOTIFICATION_BADGES[tab_index] = badge_label
            tab_widget.update()
            tab_bar.update()
        except Exception as e:
            Settings.write_log_dev_file(f"Error adding notification badge: {e}\n{traceback.format_exc()}", "ERROR")

    @staticmethod
    # -------------------------------------------------------------------------
    # Affiche une boîte de message modale stylisée et renvoie le résultat de
    # exec() (code du bouton cliqué).
    # message_type : « critical », « warning », « info » ou « success »
    # (toute autre valeur utilise le style « info »).
    # Étapes :
    #   1. Choix de la palette de couleurs et de l'icône selon le type.
    #   2. Titre + message HTML dans un bloc coloré.
    #   3. Ombre portée et feuille de style (boutons en dégradé, plus clairs au
    #      survol et plus foncés à l'appui).
    #   4. Bouton OK centré, puis centrage de la boîte sur la fenêtre parente.
    #   5. Affichage bloquant avec exec().
    # -------------------------------------------------------------------------
    def showCriticalMessage(window, title, message, message_type="critical"):
        dialog = QMessageBox(window)

        # Palette par type de message : fond, couleur du texte, dégradé des
        # boutons (début / fin) et icône standard de QMessageBox.
        colors = {
            "critical": {"icon_bg": "#ffebee", "icon_color": "#d32f2f", "button_start": "#ef5350", "button_end": "#b71c1c", "icon": QMessageBox.Icon.Critical},
            "warning": {"icon_bg": "#fff3e0", "icon_color": "#f57c00", "button_start": "#ffb74d", "button_end": "#e65100", "icon": QMessageBox.Icon.Warning},
            "info": {"icon_bg": "#e1f5fe", "icon_color": "#0288d1", "button_start": "#4fc3f7", "button_end": "#01579b", "icon": QMessageBox.Icon.Information},
            "success": {"icon_bg": "#e8f5e9", "icon_color": "#388e3c", "button_start": "#81c784", "button_end": "#1b5e20", "icon": QMessageBox.Icon.Information},
        }

        # Palette choisie, avec repli sur « info » si le type est inconnu.
        c = colors.get(message_type, colors["info"])
        dialog.setIcon(c["icon"])
        dialog.setWindowTitle(title)
        # RichText : le message est interprété comme du HTML.
        dialog.setTextFormat(Qt.TextFormat.RichText)
        # Message encadré dans un bloc coloré ; la bordure est une version
        # assombrie de 30 % de la couleur du texte.
        dialog.setText(
            f'<div style="background-color:{c["icon_bg"]}; padding:20px; '
            f"color:{c['icon_color']}; font-size:15px; font-weight:600; "
            f"line-height:1.5; font-family: Segoe UI, Roboto, sans-serif; "
            f'border: 1px solid {UIManager.darkenColor(c["icon_color"], 30)}">'
            f"{message}</div>"
        )
        # Ombre portée : flou de 20 px, noir semi-transparent, décalée de 5 px
        # vers le bas.
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        dialog.setGraphicsEffect(shadow)
        # Feuille de style de la boîte : fond, police, libellé, zone de boutons
        # et boutons en dégradé vertical (qlineargradient). Les variantes :hover et
        # :pressed utilisent lightenColor / darkenColor.
        dialog.setStyleSheet(
            f"QMessageBox {{ background-color: {c['icon_bg']}; padding: 20px; "
            f"min-width: 450px; font-family: 'Segoe UI', 'Roboto', "
            f"'Helvetica Neue', sans-serif; font-size: 14px; }} "
            f"QMessageBox QLabel, QMessageBox QLabel#qt_msgbox_label {{ "
            f"background-color: {c['icon_bg']}; padding: 20px; "
            f"font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif; "
            f"font-size: 15px; font-weight: 600; color: {c['icon_color']}; }} "
            f"QMessageBox QDialogButtonBox {{ padding-top: 12px; }} "
            f"QMessageBox QPushButton {{ background: qlineargradient(x1:0, y1:0, "
            f"x2:0, y2:1, stop:0 {c['button_start']}, stop:1 {c['button_end']}); "
            f"border: none; color: #fff; font-family: 'Segoe UI', 'Roboto', "
            f"'Helvetica Neue', sans-serif; font-weight: 600; font-size: 14px; "
            f"padding: 10px 25px; min-width: 100px; min-height: 18px; "
            f"text-align: center; border-radius: 4px; }} "
            f"QMessageBox QPushButton:hover {{ background: qlineargradient(x1:0, "
            f"y1:0, x2:0, y2:1, stop:0 {UIManager.lightenColor(c['button_start'], 15)}, "
            f"stop:1 {UIManager.lightenColor(c['button_end'], 15)}); }} "
            f"QMessageBox QPushButton:pressed {{ background: qlineargradient(x1:0, "
            f"y1:0, x2:0, y2:1, stop:0 {UIManager.darkenColor(c['button_start'], 15)}, "
            f"stop:1 {UIManager.darkenColor(c['button_end'], 15)}); }}"
        )
        # Un seul bouton : OK.
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)

        # Récupère la zone de boutons interne de QMessageBox pour centrer le bouton.
        button_box = dialog.findChild(QDialogButtonBox)
        if button_box:
            button_box.setCenterButtons(True)

        # Centrage de la boîte sur la fenêtre parente (centre du parent moins
        # la moitié de la taille de la boîte).
        if window:
            geo = window.frameGeometry()
            center = geo.center()
            dialog.move(center - dialog.rect().center())

        # Affichage modal (bloquant) ; renvoie le code du bouton cliqué.
        return dialog.exec()

    @staticmethod
    # -------------------------------------------------------------------------
    # Assombrit une couleur « #RRGGBB » d'un pourcentage donné.
    # Chaque composante est multipliée par (1 - percent/100), bornée entre 0
    # et 255, puis la couleur est reconvertie en hexadécimal.
    # -------------------------------------------------------------------------
    def darkenColor(hex_color, percent):
        # Extraction des composantes R, G, B (paires hexadécimales après « # »).
        r, g, b = [int(hex_color[i : i + 2], 16) for i in (1, 3, 5)]
        factor = 1 - percent / 100
        r, g, b = [max(0, min(255, int(c * factor))) for c in (r, g, b)]
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    # -------------------------------------------------------------------------
    # Éclaircit une couleur « #RRGGBB » : chaque composante est rapprochée de
    # 255 (blanc) d'un pourcentage donné de la distance restante.
    # -------------------------------------------------------------------------
    def lightenColor(hex_color, percent):
        r, g, b = [int(hex_color[i : i + 2], 16) for i in (1, 3, 5)]
        r = min(255, int(r + (255 - r) * percent / 100))
        g = min(255, int(g + (255 - g) * percent / 100))
        b = min(255, int(b + (255 - b) * percent / 100))
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    # -------------------------------------------------------------------------
    # Copie dans le presse-papiers tous les éléments de la liste (QListWidget)
    # de l'onglet de résultats d'index tab_index, un élément par ligne.
    # Utilise window.result_tab_widget, défini dans setupMiscellaneous().
    # -------------------------------------------------------------------------
    def copyResultFromTab(window, tab_index):
        tab_widget = window.result_tab_widget.widget(tab_index)
        list_widgets = tab_widget.findChildren(QListWidget)
        # Une liste est présente : on récupère le texte de chaque élément.
        if list_widgets:
            list_widget = list_widgets[0]
            items = [list_widget.item(i).text() for i in range(list_widget.count())]
            text_to_copy = "\n".join(items)
            # Copie du texte assemblé dans le presse-papiers système.
            clipboard = QApplication.clipboard()
            clipboard.setText(text_to_copy)
            Settings.write_log_dev_file(f"[DEBUG] 📋 {len(items)} éléments copiés dans le presse-papiers.", "INFO")
        # Aucune liste dans cet onglet : simple information dans le log.
        else:
            Settings.write_log_dev_file("[DEBUG] ⚠️ Aucun QListWidget rencontré dans cet onglet.", "INFO")

    @staticmethod
    # -------------------------------------------------------------------------
    # Copie tout le contenu de la zone de logs dans le presse-papiers.
    # Bien que la méthode soit statique, le paramètre s'appelle « self » :
    # il s'agit de la fenêtre principale, passée explicitement par l'appelant.
    # Recherche de la zone de logs :
    #   1. attribut log_text_edit de la fenêtre s'il existe ;
    #   2. sinon, le QPlainTextEdit contenu dans le widget nommé « log ».
    # -------------------------------------------------------------------------
    def copyLogsToClipboard(self):
        log_text_edit = getattr(self, "log_text_edit", None)
        if log_text_edit is None:
            log_container = self.findChild(QWidget, "log")
            log_text_edit = log_container.findChild(QPlainTextEdit) if log_container else None

        # Zone de logs introuvable : avertissement et arrêt.
        if log_text_edit is None:
            Settings.write_log_dev_file("[DEBUG] ❌ Widget de logs introuvable.", "WARNING")
            return
        text_to_copy = log_text_edit.toPlainText()
        # Rien à copier : information et arrêt.
        if not text_to_copy:
            Settings.write_log_dev_file("[DEBUG] ⚠️ Aucun log disponible à copier.", "INFO")
            return
        # Copie puis journalisation du nombre de lignes copiées.
        QApplication.clipboard().setText(text_to_copy)
        Settings.write_log_dev_file(f"[DEBUG] 📋 {len(text_to_copy.splitlines())} lignes de log copiées dans le presse-papiers.", "INFO")

    @staticmethod
    # -------------------------------------------------------------------------
    # Ajoute une entrée dans la zone de logs, préfixée par l'heure [HH:MM:SS],
    # puis place le curseur à la fin pour que l'affichage défile automatiquement
    # jusqu'à la dernière ligne.
    # -------------------------------------------------------------------------
    def updateLogsDisplay(log_entry, log_text_edit):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_entry = f"[{timestamp}] {log_entry}"
        log_text_edit.appendPlainText(formatted_entry)
        log_text_edit.moveCursor(QtGui.QTextCursor.MoveOperation.End)

    @staticmethod
    # -------------------------------------------------------------------------
    # Met à jour l'apparence et le comportement de toutes les étapes du scénario
    # (chaque étape est un cadre dans scenario_layout).
    #   - Toutes les étapes sauf la dernière : style « normal » (fond blanc,
    #     texte couleur primaire) et bouton de suppression masqué.
    #   - La dernière étape : style « active » (fond couleur primaire, texte
    #     blanc) et bouton visible, connecté à go_to_previous_state (retour à
    #     l'état précédent / retrait de la dernière étape).
    #   - Pour toutes les étapes :
    #       * les QTextEdit ouvrent CustomTextDialog au clic ;
    #       * les QLineEdit numériques sont validés (plages « min,max ») ;
    #       * le QLineEdit lié à une case à cocher est validé comme texte.
    # Remarque : widget.children() ne renvoie que les enfants directs du cadre.
    # -------------------------------------------------------------------------
    def updateActionsColorHandleLastButton(scenario_layout, go_to_previous_state):
        # Parcours de toutes les étapes du layout du scénario.
        for i in range(scenario_layout.count()):
            widget = scenario_layout.itemAt(i).widget()

            # Certains éléments du layout peuvent ne pas être des widgets (espaceurs).
            if widget:
                # === Étapes autres que la dernière : style normal ===
                if i != scenario_layout.count() - 1:
                    # Cadre : fond blanc, bordure couleur secondaire, coins arrondis.
                    widget.setStyleSheet(f"background-color: #ffffff; border: 1px solid {Settings.SECONDARY_COLOR}; border-radius: 8px;")

                    # Libellés : le premier (nom de l'étape) en 16 px avec marge à gauche ;
                    # les suivants en 14 px. Un libellé commençant par « Random » est affiché
                    # en petite taille (9 px).
                    label_list = [child for child in widget.children() if isinstance(child, QLabel)]
                    if label_list:
                        first_label = label_list[0]
                        first_label.setStyleSheet(
                            f"QLabel {{ color: {Settings.PRIMARY_COLOR}; font-size: 16px; border: none; border-radius: 4px; text-align: center; background-color: transparent; font-family: {Settings.FONT_FAMILY}; margin-left: 10px; }}"
                        )
                        if first_label.text().startswith("Random"):
                            first_label.setStyleSheet(
                                f"QLabel {{ color: {Settings.PRIMARY_COLOR}; font-size: 9px; border: none; border-radius: 4px; background-color: transparent; font-family: {Settings.FONT_FAMILY}; padding: 0px; margin: 0px; border:None; }}"
                            )
                        for label in label_list[1:]:
                            label.setStyleSheet(
                                f"QLabel {{ color: {Settings.PRIMARY_COLOR}; font-size: 14px; border: none; border-radius: 4px; text-align: center; background-color: transparent; font-family: {Settings.FONT_FAMILY}; }}"
                            )
                            if label.text().startswith("Random"):
                                label.setStyleSheet(
                                    f"QLabel {{ color: {Settings.PRIMARY_COLOR}; ; font-size: 9px; border: none; border-radius: 4px; background-color: transparent; font-family: Monaco, monospace; padding: 0px; margin: 0px; border:None; }}"
                                )
                    # Boutons : le dernier bouton du cadre (suppression) est masqué, car seule
                    # la dernière étape du scénario peut être retirée.
                    buttons = [child for child in widget.children() if isinstance(child, QPushButton)]
                    if buttons:
                        last_button = buttons[-1]
                        last_button.setVisible(False)

                    # QSpinBox : style avec flèches personnalisées si les images existent
                    # (ici les deux boutons utilisent l'image ARROW_DOWN_PATH).
                    spin_boxes = [child for child in widget.children() if isinstance(child, QSpinBox)]
                    if spin_boxes and Settings.DOWN_EXISTS and Settings.UP_EXISTS:
                        new_style = f'QSpinBox {{ padding: 2px; border: 1px solid {Settings.PRIMARY_COLOR}; color: black; }} QSpinBox::down-button {{ image: url("{Settings.ARROW_DOWN_PATH}"); width: 13px; height: 13px; padding: 2px; border-top-left-radius: 5px; border-bottom-left-radius: 5px; }} QSpinBox::up-button {{ image: url("{Settings.ARROW_DOWN_PATH}"); width: 13px; height: 13px; padding: 2px; border-top-left-radius: 5px; border-bottom-left-radius: 5px; }}'
                        spin_boxes[0].setStyleSheet(new_style)

                    # QCheckBox : style de l'indicateur selon qu'elle est cochée ou non.
                    # Le nouveau style est ajouté à la suite du style existant.
                    QCheckBox_list = [child for child in widget.children() if isinstance(child, QCheckBox)]
                    if QCheckBox_list:
                        checkbox = QCheckBox_list[0]
                        if checkbox.isChecked():
                            additional_style = f"QCheckBox::indicator:checked {{ background-color: {Settings.PRIMARY_COLOR}; border: 2px solid {Settings.PRIMARY_COLOR}; }}"
                        else:
                            additional_style = "QCheckBox::indicator { color: gray; background-color: #e0e0e0; border: 1px solid #cccccc; }"

                        current_style = checkbox.styleSheet()
                        new_style = f"{current_style} {additional_style}" if current_style else additional_style
                        checkbox.setStyleSheet(new_style)

                    # QComboBox : la variable locale nommée « QComboBox » (plus bas) masque la
                    # classe dans toute la fonction ; c'est pourquoi la classe est référencée
                    # ici via PyQt6.QtWidgets.QComboBox.
                    QComboBox_list = [child for child in widget.children() if isinstance(child, PyQt6.QtWidgets.QComboBox)]

                    # Ajout du style commun des combobox du scénario si l'image de flèche existe.
                    if QComboBox_list:
                        QComboBox = QComboBox_list[0]
                        if Settings.DOWN_EXISTS:
                            old_style = QComboBox.styleSheet()
                            new_style = UIManager.getScenarioComboboxStyle()
                            combined_style = old_style + new_style
                            QComboBox.setStyleSheet(combined_style)

                # === Dernière étape : style « actif » ===
                if i == scenario_layout.count() - 1:
                    # Cadre : fond couleur primaire, coins arrondis.
                    widget.setStyleSheet(f"background-color: {Settings.PRIMARY_COLOR}; border-radius: 8px;")
                    # Libellés en blanc ; les libellés « Random » en petite taille (9 px).
                    label_list = [child for child in widget.children() if isinstance(child, QLabel)]
                    if label_list:
                        label_list[0].setStyleSheet(
                            f"QLabel {{ color: white; font-size: 16px; border: none; border-radius: 4px; text-align: center; background-color: {Settings.PRIMARY_COLOR}; font-family: {Settings.FONT_FAMILY}; margin-left: 8px; }}"
                        )
                        if label_list[0].text().startswith("Random"):
                            label_list[0].setStyleSheet(
                                f"QLabel {{ color: white; font-size: 9px; border: 1px dashed #ffffff; border-radius: 4px; background-color: transparent; font-family: {Settings.FONT_FAMILY}; padding: 0px; margin: 0px; border:None; }}"
                            )
                        for label in label_list[1:]:
                            label.setStyleSheet(
                                f"QLabel {{ color: white; font-size: 16px; border: none; border-radius: 4px; text-align: center; background-color: {Settings.PRIMARY_COLOR}; font-family: {Settings.FONT_FAMILY}; }}"
                            )
                            if label.text().startswith("Random"):
                                label.setStyleSheet(
                                    'QLabel { color: white; font-size: 9px; border: 1px dashed #ffffff; border-radius: 4px; background-color: transparent; font-family: "Monaco", monospace; padding: 0px; margin: 0px; border:None; }'
                                )

                    # Bouton de l'étape : rendu visible avec un curseur main.
                    # Toutes les connexions précédentes du signal clicked sont retirées
                    # (PyQt6 lève TypeError s'il n'y en a aucune, d'où le except) afin d'éviter
                    # d'empiler plusieurs connexions, puis il est connecté à go_to_previous_state.
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

                    # QSpinBox : flèches blanches si les images correspondantes existent.
                    spin_boxes = [child for child in widget.children() if isinstance(child, QSpinBox)]
                    if spin_boxes and Settings.DOWN_EXISTS_W and Settings.UP_EXISTS_W:
                        new_style = f'QSpinBox {{ padding: 2px; border: 1px solid white; color: white; }} QSpinBox::down-button {{ image: url("{Settings.ARROW_DOWN_W_PATH}"); width: 13px; height: 13px; padding: 2px; border-top-left-radius: 5px; border-bottom-left-radius: 5px; }} QSpinBox::up-button {{ image: url("{Settings.ARROW_UP_W_PATH}"); width: 13px; height: 13px; padding: 2px; border-top-left-radius: 5px; border-bottom-left-radius: 5px; }}'
                        spin_boxes[0].setStyleSheet(new_style)

                    # QCheckBox : indicateur coché avec bordure blanche, sinon grisé.
                    QCheckBox_list_last = [child for child in widget.children() if isinstance(child, QCheckBox)]
                    if QCheckBox_list_last:
                        checkbox = QCheckBox_list_last[0]
                        if checkbox.isChecked():
                            additional_style = f"QCheckBox::indicator:checked {{ background-color: {Settings.PRIMARY_COLOR}; border: 2px solid #ffffff; }}"
                        else:
                            additional_style = "QCheckBox::indicator { color: gray; background-color: #e0e0e0; border: 1px solid #cccccc; }"

                        current_style = checkbox.styleSheet()
                        new_style = f"{current_style} {additional_style}" if current_style else additional_style
                        checkbox.setStyleSheet(new_style)

                    # QComboBox : style commun en variante « dernière étape ».
                    QComboBox_list = [child for child in widget.children() if isinstance(child, PyQt6.QtWidgets.QComboBox)]
                    if QComboBox_list and Settings.DOWN_EXISTS:
                        combo_box = QComboBox_list[0]
                        combo_box.setStyleSheet(combo_box.styleSheet() + UIManager.getScenarioComboboxStyle(last_step=True))

                # === Traitements communs à toutes les étapes ===
                # QTextEdit : barres de défilement masquées et clic remplacé par
                # l'ouverture de la boîte d'édition CustomTextDialog.
                QTextEdits = [child for child in widget.children() if isinstance(child, QTextEdit)]

                for idx, qtextedit in enumerate(QTextEdits):
                    qtextedit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                    qtextedit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

                    # Fabrique de gestionnaire (closure) : chaque handler capture SON propre
                    # QTextEdit « te », ce qui évite que tous les handlers créés dans la boucle
                    # pointent vers le dernier élément. « index » n'est pas utilisé.
                    def create_handler(te, index):
                        # Gestionnaire de clic : ouvre la boîte avec le texte actuel ; si
                        # l'utilisateur valide, le texte est remplacé ; le focus est ensuite retiré.
                        # Toute erreur est journalisée.
                        def handler(event):
                            try:
                                dialog = CustomTextDialog(te, texte_initial=te.toPlainText())
                                if dialog.exec():
                                    new_text = dialog.getText()
                                    te.setPlainText(new_text)
                                te.clearFocus()
                            except Exception as e:
                                Settings.write_log_dev_file(f"[❌] Erreur lors de l’ouverture de la boîte de dialogue : {e}\n{traceback.format_exc()}", "ERROR")

                        return handler

                    # Remplace la méthode mousePressEvent de cette instance de QTextEdit
                    # (le comportement de clic standard n'est donc plus exécuté).
                    qtextedit.mousePressEvent = create_handler(qtextedit, idx)
                # QLineEdit : si l'étape contient une case à cocher, le DERNIER QLineEdit
                # est le champ texte lié à cette case ; il est retiré de la liste des champs
                # numériques pour être validé séparément.
                qlineedits = [child for child in widget.children() if isinstance(child, QLineEdit)]
                checkbox_qlineedit = None

                if qlineedits:
                    last_qlineedit = qlineedits[-1]
                    parent_widget = last_qlineedit.parent()
                    if parent_widget:
                        contains_checkbox = any(isinstance(child, QCheckBox) for child in parent_widget.children())
                        if contains_checkbox:
                            checkbox_qlineedit = last_qlineedit
                            qlineedits.pop()

                # Validation des champs numériques au signal editingFinished (touche
                # Entrée ou perte du focus).
                for idx, qlineedit in enumerate(qlineedits):

                    # Fabrique de validateur (closure) : fige le champ et sa valeur par défaut.
                    def create_validator(line_edit, default_val):
                        def validator():
                            ValidationUtils.validate_qlineedit_with_range(line_edit, default_val)

                        return validator

                    # S'il y a plusieurs champs, le premier utilise la valeur par défaut
                    # « 50,50 », les autres « 1,1 ».
                    if len(qlineedits) > 1 and idx == 0:
                        qlineedit.editingFinished.connect(create_validator(qlineedit, "50,50"))
                    else:
                        qlineedit.editingFinished.connect(create_validator(qlineedit, "1,1"))

                # Validation spécifique du champ texte lié à la case à cocher.
                if checkbox_qlineedit:

                    def validate_checkbox_qlineedit():
                        UIManager.validateCheckboxLinkedQlineEdit(checkbox_qlineedit)

                    checkbox_qlineedit.editingFinished.connect(validate_checkbox_qlineedit)

    @staticmethod
    # -------------------------------------------------------------------------
    # Valide le texte d'un QLineEdit lié à une case à cocher et signale une
    # erreur par une bordure + une infobulle.
    # Règles :
    #   - Étape « open_spam » / « open_inbox » avec la case cochée :
    #       texte non vide -> valide ;
    #       texte vide     -> remplacé par le label de l'étape (ou « Google »)
    #                         et affiché en erreur.
    #   - Sinon (règle générale) : texte purement numérique ou de moins de
    #     4 caractères -> remplacé par « Google » et affiché en erreur ;
    #     autrement -> valide.
    # Les changements de style passent par QTimer.singleShot(0, ...) : ils sont
    # appliqués au prochain tour de la boucle d'événements, après que Qt a fini
    # de traiter editingFinished / le changement de focus.
    # -------------------------------------------------------------------------
    def validateCheckboxLinkedQlineEdit(qlineedit: QLineEdit):
        # Garde-fou : aucun champ fourni.
        if qlineedit is None:
            Settings.write_log_dev_file("Le QLineEdit est None. Validation ignorée.", "ERROR")
            return

        # full_state : dictionnaire d'état de l'étape stocké comme propriété Qt
        # sur le cadre parent (voir updateScenario).
        parent_widget = qlineedit.parent()
        full_state = parent_widget.property("full_state") if parent_widget else None
        text = qlineedit.text().strip()

        # Style actuel débarrassé de toute bordure d'erreur précédente.
        old_style = qlineedit.styleSheet()
        cleaned_style = ValidationUtils.remove_border_from_style(old_style)

        # Cas particulier : l'étape possède un état connu.
        if full_state and isinstance(full_state, dict):
            sub_id = full_state.get("id", "")
            sub_label = full_state.get("label", "Google")

            # Première case à cocher de l'étape (None s'il n'y en a pas).
            checkbox = next((child for child in parent_widget.children() if isinstance(child, QCheckBox)), None)

            # Uniquement pour les étapes d'ouverture de Spam / Inbox dont la case est cochée.
            if sub_id in ["open_spam", "open_inbox"]:
                if checkbox and checkbox.isChecked():
                    # Texte présent : style normal et infobulle vidée.
                    if text:

                        def apply_ok():
                            qlineedit.setStyleSheet(cleaned_style)
                            qlineedit.setToolTip("")

                        QTimer.singleShot(0, apply_ok)
                        return
                    # Texte vide : valeur par défaut issue de full_state + style d'erreur.
                    else:
                        qlineedit.setText(sub_label or "Google")

                        def apply_error():
                            new_style = ValidationUtils.inject_border_into_style(cleaned_style)
                            qlineedit.setStyleSheet(new_style)
                            qlineedit.setToolTip("Texte invalide. Valeur remplacée par défaut depuis full_state.")

                        QTimer.singleShot(0, apply_error)
                        return

        # Règle générale (aussi appliquée si la case open_spam/open_inbox n'est
        # pas cochée) : texte numérique ou trop court -> valeur « Google » + erreur.
        if text.isdigit() or len(text) < 4:
            qlineedit.setText("Google")

            def apply_error():
                new_style = ValidationUtils.inject_border_into_style(cleaned_style)
                qlineedit.setStyleSheet(new_style)
                qlineedit.setToolTip("Le texte est un nombre ou trop court, veuillez corriger la saisie.")

            QTimer.singleShot(0, apply_error)
        # Texte valide : style normal et infobulle vidée.
        else:

            def apply_ok():
                qlineedit.setStyleSheet(cleaned_style)
                qlineedit.setToolTip("")

            QTimer.singleShot(0, apply_ok)

    @staticmethod
    # -------------------------------------------------------------------------
    # Synchronise les boutons d'options (reset_options_layout) avec le scénario.
    # Étapes :
    #   1. Trouve l'index de la dernière étape contenant une QCheckBox
    #      (étape de type boucle). S'il n'y en a pas, on s'arrête.
    #   2. Relève le premier libellé de chaque étape située APRÈS cette étape.
    #   3. Relève le texte de tous les boutons d'options.
    #   4. diff_texts = boutons dont le texte n'apparaît pas dans ces étapes.
    #   5. Supprime les boutons dont le texte figure dans ces étapes.
    # -------------------------------------------------------------------------
    def removeCopier(scenario_layout, reset_options_layout):
        lastactionLoop = None
        scenarioContainertableauAdd = []
        resetOptionsContainertableauALL = []
        found_checkbox = False

        # Étape 1 : mémorise le dernier index d'étape contenant une case à cocher.
        for i in range(scenario_layout.count()):
            widget = scenario_layout.itemAt(i).widget()
            if widget:
                for child in widget.children():
                    if isinstance(child, QCheckBox):
                        lastactionLoop = i
                        found_checkbox = True

        if not found_checkbox:
            return

        # Étape 2 : libellés des étapes situées après cette étape.
        for i in range(lastactionLoop + 1, scenario_layout.count()):
            widget = scenario_layout.itemAt(i).widget()
            if widget:
                labels = [child.text() for child in widget.children() if isinstance(child, QLabel)]
                if labels:
                    scenarioContainertableauAdd.append(labels[0])

        # Étape 3 : textes de tous les boutons d'options.
        for i in range(reset_options_layout.count()):
            widget = reset_options_layout.itemAt(i).widget()
            if widget and isinstance(widget, QPushButton):
                resetOptionsContainertableauALL.append(widget.text())

        # Étape 4 : textes des boutons absents des étapes relevées.
        diff_texts = [text for text in resetOptionsContainertableauALL if text not in scenarioContainertableauAdd]

        # Étape 5 : parcours à l'envers pour que la suppression ne décale pas les
        # index restant à parcourir. Destruction différée + retrait du layout.
        for i in reversed(range(reset_options_layout.count())):
            widget = reset_options_layout.itemAt(i).widget()
            if widget and isinstance(widget, QPushButton):
                if widget.text() not in diff_texts:
                    widget.deleteLater()
                    reset_options_layout.removeWidget(widget)

    @staticmethod
    # -------------------------------------------------------------------------
    # Même principe que removeCopier, mais le critère porte sur les étapes dont
    # l'état (full_state) contient la clé « INITAILE » (orthographe du code) :
    # les boutons d'options portant le label de ces étapes sont supprimés.
    # Suppose que chaque étape possède une propriété full_state de type dict.
    # -------------------------------------------------------------------------
    def removeInitial(scenario_layout, reset_options_layout):
        scenarioContainertableauAdd = []
        resetOptionsContainertableauALL = []

        # Relève les labels des étapes marquées « INITAILE ».
        for i in range(scenario_layout.count()):
            widget = scenario_layout.itemAt(i).widget()
            if widget:
                sub_full_state = widget.property("full_state")
                sub_hidden_id = sub_full_state.get("INITAILE")
                if sub_hidden_id:
                    scenarioContainertableauAdd.append(sub_full_state.get("label"))

        # Textes de tous les boutons d'options.
        for i in range(reset_options_layout.count()):
            widget = reset_options_layout.itemAt(i).widget()
            if widget and isinstance(widget, QPushButton):
                resetOptionsContainertableauALL.append(widget.text())

        # Boutons dont le texte ne correspond à aucune étape marquée.
        diff_texts = [text for text in resetOptionsContainertableauALL if text not in scenarioContainertableauAdd]

        # Suppression (à l'envers) des boutons correspondant aux étapes marquées.
        for i in reversed(range(reset_options_layout.count())):
            widget = reset_options_layout.itemAt(i).widget()
            if widget and isinstance(widget, QPushButton):
                if widget.text() not in diff_texts:
                    widget.deleteLater()
                    reset_options_layout.removeWidget(widget)

    @staticmethod
    # -------------------------------------------------------------------------
    # Lit un fichier texte UTF-8 et renvoie son contenu sans espaces de début
    # et de fin. Renvoie None si le fichier n'existe pas, s'il est vide, ou en
    # cas d'erreur de lecture (erreur journalisée).
    # -------------------------------------------------------------------------
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
            Settings.write_log_event("file_read_failed", "ERROR", file_path=file_path, exception_type=type(exc).__name__, error=str(exc))
            return None

    @staticmethod
    # -------------------------------------------------------------------------
    # Recherche un widget enfant par son objectName. Si widget_type est fourni,
    # la recherche est restreinte à ce type ; sinon QWidget (tout widget).
    # Renvoie None si aucun widget ne correspond.
    # -------------------------------------------------------------------------
    def findWidget(window, name, widget_type=None):
        """Find child widget with optional type"""
        return window.findChild(widget_type, name) if widget_type else window.findChild(QWidget, name)

    @staticmethod
    # -------------------------------------------------------------------------
    # Récupère les conteneurs définis dans le fichier .ui et leur associe un
    # layout vertical aligné en haut (les éléments s'empilent depuis le haut) :
    #   - resetOptionsContainer -> window.reset_options_layout (boutons d'options) ;
    #   - scenarioContainer     -> window.scenario_layout (étapes du scénario).
    # Si un conteneur est absent, l'attribut de layout correspondant n'est pas créé.
    # -------------------------------------------------------------------------
    def setupContainers(window):
        """Setup container widgets and layouts"""
        window.reset_options_container = UIManager.findWidget(window, "resetOptionsContainer")
        if window.reset_options_container:
            window.reset_options_layout = QVBoxLayout(window.reset_options_container)
            window.reset_options_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        window.scenario_container = UIManager.findWidget(window, "scenarioContainer")
        if window.scenario_container:
            window.scenario_layout = QVBoxLayout(window.scenario_container)
            window.scenario_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    @staticmethod
    # -------------------------------------------------------------------------
    # Récupère les widgets « modèles » définis dans le fichier .ui, les
    # enregistre comme attributs de la fenêtre et les masque. Les cadres
    # Template1..5 sont ensuite clonés par updateScenario() pour créer les
    # étapes du scénario.
    # -------------------------------------------------------------------------
    def setupTemplateWidgets(window):
        # Correspondance : nom d'attribut sur la fenêtre -> objectName dans le .ui
        # (l'orthographe « Temeplete » est celle du fichier .ui).
        templates = {
            "template_button": "TemepleteButton",
            "Temeplete_Button_2": "TemepleteButton_2",
            "template_Frame1": "Template1",
            "template_Frame2": "Template2",
            "template_Frame3": "Template3",
            "template_Frame4": "Template4",
            "template_Frame5": "Template5",
        }

        # Pour chaque modèle : recherche, affectation (éventuellement None) et masquage.
        for attr_name, widget_name in templates.items():
            widget = UIManager.findWidget(window, widget_name)
            setattr(window, attr_name, widget)
            if widget:
                widget.hide()

    @staticmethod
    # -------------------------------------------------------------------------
    # Configure un bouton avec icône, avec journalisation détaillée.
    # Étapes :
    #   1. Recherche du bouton (None + log d'erreur s'il est introuvable).
    #   2. Construction du chemin de l'icône et application si le fichier
    #      existe (taille d'icône optionnelle).
    #   3. Connexion du callback au signal clicked.
    #   4. Taille fixe optionnelle du bouton.
    #   5. Pour « ClearButton » et « CopyButton » : bouton icône seule,
    #      transparent et sans texte.
    # Renvoie le bouton configuré.
    # -------------------------------------------------------------------------
    def setupIconButton(window, button_name, icon_file, callback, icon_size=None, button_size=None):
        """Helper to setup icon button with detailed debug output"""

        button = UIManager.findWidget(window, button_name, QPushButton)
        if not button:
            Settings.write_log_dev_file(f"Bouton '{button_name}' introuvable.", "ERROR")
            return None
        else:
            Settings.write_log_dev_file(f"Bouton '{button_name}' trouvé.", "DEBUG")
        # Chemin de l'icône avec des « / » (format accepté partout par Qt).
        icon_path = os.path.join(Settings.ICONS_DIR, icon_file).replace("\\", "/")
        Settings.write_log_dev_file(f"Chemin icône pour '{button_name}': {icon_path}", "DEBUG")

        # Icône trouvée : application, avec redimensionnement si demandé
        # (icon_size est un tuple (largeur, hauteur) décompressé par *).
        if ValidationUtils.pathExists(icon_path):
            Settings.write_log_dev_file(f"Icône trouvée pour '{button_name}': {icon_path}", "DEBUG")
            icon = QIcon(icon_path)
            if icon_size:
                Settings.write_log_dev_file(f"Taille icône pour '{button_name}': {icon_size}", "DEBUG")
                button.setIconSize(QSize(*icon_size))
            button.setIcon(icon)
        else:
            Settings.write_log_dev_file(f"Icône introuvable pour '{button_name}': {icon_path}", "WARNING")
        # Connexion du signal clicked au callback ; une erreur est journalisée
        # sans interrompre la configuration.
        try:
            button.clicked.connect(callback)
            Settings.write_log_dev_file(f"Callback connecté pour '{button_name}'", "INFO")
        except Exception as e:
            Settings.write_log_dev_file(f"Error connecting callback: {button_name}\n{traceback.format_exc()}", "ERROR")
        # Taille fixe du bouton si button_size est fourni.
        if button_size:
            Settings.write_log_dev_file(f"Taille bouton pour '{button_name}': {button_size}", "DEBUG")
            button.setFixedSize(*button_size)
        # Boutons « Effacer » et « Copier » : icône seule, fond transparent.
        if button_name in ("ClearButton", "CopyButton"):
            Settings.write_log_dev_file(f"Application style spéciale pour '{button_name}'", "DEBUG")
            button.setText("")
            button.setStyleSheet("QPushButton { border: none; background-color: transparent; padding: 0px; margin: 0px; }")
        Settings.write_log_dev_file(f"Bouton '{button_name}' configuré avec succès.", "SUCCESS")

        return button

    @staticmethod
    # -------------------------------------------------------------------------
    # Configure un bouton simple : recherche + connexion du callback.
    # Si aucun callback n'est fourni, le bouton est renvoyé sans connexion.
    # Renvoie None si le bouton est introuvable.
    # -------------------------------------------------------------------------
    def setupButton(window, widget_name, callback):
        """Setup simple button with connection + debug"""
        button = UIManager.findWidget(window, widget_name, QPushButton)

        if not button:
            Settings.write_log_dev_file(f"Bouton '{widget_name}' introuvable.", "ERROR")
            return None
        else:
            Settings.write_log_dev_file(f"Bouton '{widget_name}' trouvé.", "DEBUG")

        if not callback:
            Settings.write_log_dev_file(f"Aucun callback fourni pour '{widget_name}'", "WARNING")
            return button
        # Connexion du signal clicked ; erreur journalisée si elle échoue.
        try:
            button.clicked.connect(callback)
            Settings.write_log_dev_file(f"Callback connecté pour '{widget_name}'", "SUCCESS")
        except Exception as e:
            Settings.write_log_dev_file(f"Error connecting callback: {widget_name}\n{traceback.format_exc()}", "ERROR")
        return button

    @staticmethod
    # -------------------------------------------------------------------------
    # Initialise la liste déroulante « browsers » (choix du navigateur).
    # Étapes : recherche -> style de flèche -> vidage -> ajout de chaque
    # navigateur de Settings.BROWSER_OPTIONS (liste de tuples (nom, icône)),
    # avec son icône si le fichier existe, sinon texte seul.
    # -------------------------------------------------------------------------
    def setupBrowserCombobox(window):
        """Setup browser selection combobox with debug"""

        Settings.write_log_dev_file("Initialisation du QComboBox 'browsers'", "DEBUG")
        window.browser = UIManager.findWidget(window, "browsers", QComboBox)

        if window.browser is None:
            Settings.write_log_dev_file("QComboBox 'browsers' introuvable.", "ERROR")
            return
        else:
            Settings.write_log_dev_file("QComboBox trouvé.", "DEBUG")

        # Application du style de flèche personnalisé ; erreur journalisée.
        try:
            UIManager.applyComboboxStyle(window.browser)
            Settings.write_log_dev_file("Style appliqué au QComboBox.", "DEBUG")
        except Exception as e:
            Settings.write_log_dev_file(f"Error applying style to browsers combobox\n{traceback.format_exc()}", "ERROR")

        Settings.write_log_dev_file("[DEBUG] Nettoyage des anciens éléments...", "DEBUG")
        # Suppression des éléments éventuellement présents dans le .ui.
        window.browser.clear()

        browsers = Settings.BROWSER_OPTIONS
        Settings.write_log_dev_file(f"Nombre de navigateurs à ajouter: {len(browsers)}", "DEBUG")
        # Ajout de chaque navigateur, avec ou sans icône.
        for name, icon_file in browsers:
            icon_path = os.path.join(Settings.ICONS_DIR, icon_file).replace("\\", "/")
            Settings.write_log_dev_file(f"Traitement: {name} | Icône: {icon_path}", "DEBUG")

            if ValidationUtils.pathExists(icon_path):
                window.browser.addItem(QIcon(icon_path), name)
            else:
                Settings.write_log_dev_file(f"Icône introuvable pour {name}: {icon_path}", "WARNING")
                window.browser.addItem(name)

        count = window.browser.count()
        Settings.write_log_dev_file(f"QComboBox configuré avec {count} éléments.", "SUCCESS")

    @staticmethod
    # -------------------------------------------------------------------------
    # Ajoute au style existant d'une combobox une image de flèche personnalisée,
    # uniquement si le fichier de flèche existe.
    # -------------------------------------------------------------------------
    def applyComboboxStyle(combobox):
        """Apply custom arrow style to combobox"""
        if not ValidationUtils.pathExists(Settings.ARROW_DOWN_PATH):
            return

        style = f'QComboBox::down-arrow {{ image: url("{Settings.ARROW_DOWN_PATH}"); width: 16px; height: 16px; }}'
        old_style = combobox.styleSheet()
        combobox.setStyleSheet(old_style + style)

    @staticmethod
    # -------------------------------------------------------------------------
    # Renvoie la feuille de style commune aux combobox des étapes du scénario.
    # last_step=True : variante pour la dernière étape (fond coloré), avec
    # moins de bordures autour de la flèche et de la liste ; sinon bordures
    # de couleur primaire partout.
    # -------------------------------------------------------------------------
    def getScenarioComboboxStyle(last_step=False):
        """Return the shared style for scenario ComboBox widgets."""
        if last_step:
            arrow_style = "border: none; background-color: white;"
            dropdown_style = "border: none;"
            view_style = "border: none;"
            combo_style = "border: 1px solid {0}; outline: none;".format(Settings.PRIMARY_COLOR)
        else:
            arrow_style = f"border: 1px solid {Settings.PRIMARY_COLOR}; background-color: white;"
            dropdown_style = f"border: 1px solid {Settings.PRIMARY_COLOR};"
            view_style = f"border: 1px solid {Settings.PRIMARY_COLOR};"
            combo_style = f"border: 1px solid {Settings.PRIMARY_COLOR};"

        # Assemblage du QSS : flèche, zone déroulante, liste des choix, combobox,
        # éléments de la liste, élément sélectionné et état focus.
        return (
            f'QComboBox::down-arrow {{ image: url("{Settings.ARROW_DOWN_PATH}"); '
            f"width: 13px; height: 13px; {arrow_style} }} "
            f"QComboBox::drop-down {{ {dropdown_style} width: 20px; outline: none; }} "
            f"QComboBox QAbstractItemView {{ min-width: 90px; {view_style} "
            f"background: white; selection-background-color: {Settings.PRIMARY_COLOR}; "
            f"selection-color: white; padding: 3px; margin: 0px; }} "
            f"QComboBox {{ padding-left: 10px; font-size: 12px; "
            f"font-family: {Settings.FONT_FAMILY}; {combo_style} }} "
            f"QComboBox QAbstractItemView::item {{ padding: 5px; font-size: 12px; "
            f"color: #333; border: none; }} "
            f"QComboBox QAbstractItemView::item:selected {{ background-color: {Settings.PRIMARY_COLOR}; "
            f"color: white; border-radius: 3px; }} "
            f"QComboBox:focus {{ border: 1px solid {Settings.PRIMARY_COLOR}; }}"
        )

    @staticmethod
    # -------------------------------------------------------------------------
    # Initialise la liste déroulante « Isps » (fournisseurs de messagerie) à
    # partir de Settings.SERVICES ({nom: fichier icône}), puis sélectionne le
    # fournisseur par défaut via setDefaultIsp().
    # -------------------------------------------------------------------------
    def setupIspCombobox(window):
        """Setup ISP selection combobox"""
        window.Isp = UIManager.findWidget(window, "Isps", QComboBox)
        if window.Isp is None:
            return

        UIManager.applyComboboxStyle(window.Isp)
        window.Isp.clear()
        # Ajout de chaque fournisseur, avec ou sans icône.
        for name, icon_file in Settings.SERVICES.items():
            icon_path = os.path.join(Settings.ICONS_DIR, icon_file)
            if ValidationUtils.pathExists(icon_path):
                window.Isp.addItem(QIcon(icon_path), name)
            else:
                window.Isp.addItem(name)
        UIManager.setDefaultIsp(window)

    @staticmethod
    # -------------------------------------------------------------------------
    # Sélectionne le fournisseur par défaut d'après la première ligne du fichier
    # Settings.FILE_ISP (en minuscules). La première clé de Settings.ISP_MAPPING
    # contenue dans cette ligne détermine l'élément à sélectionner ; la boucle
    # s'arrête sur cette première correspondance, que l'élément soit trouvé
    # ou non dans la combobox.
    # -------------------------------------------------------------------------
    def setDefaultIsp(window):
        """Set the default ISP based on the content of FILE_ISP"""
        if not ValidationUtils.pathExists(Settings.FILE_ISP):
            return

        with open(Settings.FILE_ISP, "r", encoding="utf-8") as f:
            line = f.readline().strip().lower()

        # La combobox doit exister sur la fenêtre.
        if not hasattr(window, "Isp") or window.Isp is None:
            return

        for key, value in Settings.ISP_MAPPING.items():
            if key in line:
                index = window.Isp.findText(value)
                if index >= 0:
                    window.Isp.setCurrentIndex(index)
                break

    @staticmethod
    # -------------------------------------------------------------------------
    # Initialise la combobox « saveSanario » (scénarios sauvegardés) : style de
    # flèche et connexion du signal currentTextChanged à
    # window.scenario_changed pour charger le scénario choisi.
    # -------------------------------------------------------------------------
    def setupScenarioCombobox(window):
        """Setup scenario selection combobox"""
        window.saveSanario = UIManager.findWidget(window, "saveSanario", QComboBox)
        if window.saveSanario is None:
            Settings.write_log_dev_file("🔧 [DEBUG] Le save scenario not found", "DEBUG")
            return
        Settings.write_log_dev_file("🔧 [DEBUG] Le save scenario  found ", "DEBUG")
        UIManager.applyComboboxStyle(window.saveSanario)
        window.saveSanario.currentTextChanged.connect(window.scenario_changed)

    @staticmethod
    # -------------------------------------------------------------------------
    # Configure le bouton de déconnexion « LogOut » : icône placée à droite du
    # texte (RightToLeft), callback connecté si fourni, icône 18 x 18.
    # -------------------------------------------------------------------------
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
    # -------------------------------------------------------------------------
    # Initialise le widget d'onglets des résultats « tabWidgetResult ».
    # Étapes :
    #   1. Recherche du widget ; curseur main sur la barre d'onglets.
    #   2. Icônes des onglets déduites de leur texte.
    #   3. Connexion des signaux tabBarClicked et currentChanged.
    #   4. Remplacement par une version à onglets verticaux
    #      (convertToVerticalTabs, qui reconnecte les signaux sur le nouveau
    #      widget).
    #   5. Icônes et connexions des boutons de copie.
    # -------------------------------------------------------------------------
    def setupResultTabWidget(window):
        """Setup result tab widget with vertical tabs"""
        window.tabWidgetResult = UIManager.findWidget(window, "tabWidgetResult", QTabWidget)
        if window.tabWidgetResult is None:
            return
        window.tabWidgetResult.tabBar().setCursor(Qt.CursorShape.PointingHandCursor)
        UIManager.setTabIcons(window, window.tabWidgetResult)
        try:
            # tabBarClicked : émis à chaque clic sur un onglet (même déjà actif).
            # Le lambda transmet la fenêtre en plus de l'index cliqué.
            window.tabWidgetResult.tabBar().tabBarClicked.connect(lambda index: UIManager.handleResultTabClicked(window, index))
        except Exception:
            pass

        # currentChanged : émis quand l'onglet courant change.
        window.tabWidgetResult.currentChanged.connect(lambda index: UIManager.handleResultTabChanged(window, index))
        UIManager.convertToVerticalTabs(window)
        UIManager.setIconsForExistingButtons(window)

    @staticmethod
    # -------------------------------------------------------------------------
    # Clic sur un onglet de résultats : après vérification de l'index, rend
    # cet onglet courant.
    # -------------------------------------------------------------------------
    def handleResultTabClicked(window, index):
        if not hasattr(window, "tabWidgetResult") or window.tabWidgetResult is None:
            return
        if index < 0 or index >= window.tabWidgetResult.count():
            return
        window.tabWidgetResult.setCurrentIndex(index)

    @staticmethod
    # -------------------------------------------------------------------------
    # Changement d'onglet de résultats : journalise le nom du nouvel onglet.
    # -------------------------------------------------------------------------
    def handleResultTabChanged(window, index):
        if not hasattr(window, "tabWidgetResult") or window.tabWidgetResult is None:
            return
        if index < 0 or index >= window.tabWidgetResult.count():
            return
        tab_text = window.tabWidgetResult.tabText(index)
        Settings.write_log_dev_file(f"Result tab switched to: {tab_text}", "INFO")

    @staticmethod
    # -------------------------------------------------------------------------
    # Pour chaque onglet de résultats, configure les boutons dont l'objectName
    # commence par « copy » : icône copy.png (20 x 20), suppression des
    # anciennes connexions puis connexion à copyResultFromTab pour cet onglet.
    # -------------------------------------------------------------------------
    def setIconsForExistingButtons(window):
        """Set copy icons for all copy buttons in result tabs"""
        if not hasattr(window, "tabWidgetResult") or window.tabWidgetResult is None:
            return
        tab_count = window.tabWidgetResult.count()

        # Parcours des pages d'onglets et de tous leurs boutons.
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
                    # Déconnexion préalable pour éviter les connexions multiples.
                    # PyQt6 lève TypeError quand aucun slot n'est connecté (cas normal).
                    try:
                        button.clicked.disconnect()
                    except TypeError:
                        Settings.write_log_dev_file(f"No signals to disconnect for copy button in tab {i}", "INFO")
                    except Exception:
                        Settings.write_log_dev_file(f"Unexpected error disconnecting copy button in tab {i}:\n{traceback.format_exc()}", "ERROR")
                    # partial fige la fenêtre et l'index i au moment de la connexion : chaque
                    # bouton copie bien le contenu de SON onglet.
                    button.clicked.connect(partial(UIManager.copyResultFromTab, window, i))

    @staticmethod
    # -------------------------------------------------------------------------
    # Associe à chaque onglet une icône dont le nom est dérivé de son texte :
    # « Not Completed » -> « not_completed.png ». L'icône est convertie en
    # pixmap 40 x 40 avant d'être appliquée. Le paramètre window n'est pas utilisé.
    # -------------------------------------------------------------------------
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
    # -------------------------------------------------------------------------
    # Remplace « tabWidgetResult » (onglets horizontaux issus du .ui) par un
    # VerticalTabWidget (onglets verticaux dessinés à la main).
    # Étapes :
    #   1. Création du nouveau widget ; mémorisation du parent et de la géométrie.
    #   2. Transfert de toutes les pages avec leur texte, icône, style et
    #      objectName.
    #   3. Détachement de l'ancien widget ; placement du nouveau au même endroit
    #      avec le même objectName (findChild le retrouvera donc toujours).
    #   4. Mise à jour de window.tabWidgetResult et reconnexion des signaux.
    # -------------------------------------------------------------------------
    def convertToVerticalTabs(window):
        if not hasattr(window, "tabWidgetResult") or window.tabWidgetResult is None:
            return

        vertical_tab_widget = VerticalTabWidget()
        parent_widget = window.tabWidgetResult.parentWidget()
        geometry = window.tabWidgetResult.geometry()
        # addTab() reprend la page à l'ancien widget : son nombre d'onglets diminue
        # à chaque itération, d'où la boucle « tant qu'il reste des onglets » qui
        # prend toujours l'onglet d'index 0.
        while window.tabWidgetResult.count() > 0:
            widget = window.tabWidgetResult.widget(0)
            text = window.tabWidgetResult.tabText(0)
            icon = window.tabWidgetResult.tabIcon(0)
            vertical_tab_widget.addTab(widget, icon, text)
            # Recopie du style et du nom d'objet sur la page ajoutée (dernier index).
            vertical_tab_widget.widget(vertical_tab_widget.count() - 1).setStyleSheet(widget.styleSheet())
            vertical_tab_widget.widget(vertical_tab_widget.count() - 1).setObjectName(widget.objectName())
        # L'ancien widget est retiré de l'arborescence de la fenêtre.
        window.tabWidgetResult.setParent(None)
        # Le nouveau widget prend sa place (même parent, nom et géométrie) puis
        # est affiché.
        vertical_tab_widget.setParent(parent_widget)
        vertical_tab_widget.setObjectName("tabWidgetResult")
        vertical_tab_widget.setGeometry(geometry)
        vertical_tab_widget.show()
        # La fenêtre référence désormais le widget vertical.
        window.tabWidgetResult = vertical_tab_widget
        # Même configuration de curseur et de signaux que dans setupResultTabWidget.
        window.tabWidgetResult.tabBar().setCursor(Qt.CursorShape.PointingHandCursor)
        try:
            window.tabWidgetResult.tabBar().tabBarClicked.connect(lambda index: UIManager.handleResultTabClicked(window, index))
        except Exception:
            pass
        window.tabWidgetResult.currentChanged.connect(lambda index: UIManager.handleResultTabChanged(window, index))

    @staticmethod
    # -------------------------------------------------------------------------
    # Initialise le widget d'onglets principal « interface_2 » : curseur main
    # sur la barre d'onglets, puis ajout d'un cadre décoratif gris dans la page
    # de l'onglet « Result » (position fixe x=0, y=660, taille 179 x 300, bordure
    # droite couleur primaire), qui prolonge visuellement la colonne d'onglets.
    # -------------------------------------------------------------------------
    def setupInterfaceTabWidget(window):
        """Setup main interface tab widget"""
        window.INTERFACE = UIManager.findWidget(window, "interface_2", QTabWidget)
        if window.INTERFACE is None:
            return
        try:
            window.INTERFACE.tabBar().setCursor(Qt.CursorShape.PointingHandCursor)
        except Exception:
            Settings.write_log_dev_file(f"Error setting cursor for TabBar\n{traceback.format_exc()}", "ERROR")
            pass

        # Recherche du premier onglet Result et ajout du cadre, puis arrêt.
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
    # -------------------------------------------------------------------------
    # Réglages divers de l'interface :
    #   - masque le champ de recherche « lineEdit_search » ;
    #   - textes d'aide (placeholder) des zones textEdit_3 (format des données
    #     d'entrée) et textEdit_4 (nombre maximum d'opérations) ;
    #   - colonnes de tous les QTableWidget étirées sur toute la largeur ;
    #   - style des QSpinBox ;
    #   - référence window.result_tab_widget utilisée par copyResultFromTab.
    # -------------------------------------------------------------------------
    def setupMiscellaneous(window):
        """Setup miscellaneous UI elements"""

        window.lineEdit_search = UIManager.findWidget(window, "lineEdit_search", QLineEdit)
        if window.lineEdit_search:
            window.lineEdit_search.hide()
        window.textEdit_3 = UIManager.findWidget(window, "textEdit_3", QTextEdit)
        if window.textEdit_3:
            window.textEdit_3.setPlaceholderText(
                "Please enter the data in the following format : \n Email* ; passwordEmail* ; ipAddress* ; port* ; login ; password ; recovery_email , new_recovery_email"
            )

        window.textEdit_4 = UIManager.findWidget(window, "textEdit_4", QTextEdit)
        if window.textEdit_4:
            window.textEdit_4.setPlaceholderText("Specify the maximum number of operations to process")

        # Toutes les colonnes de chaque tableau se partagent la largeur disponible.
        tables = window.findChildren(QTableWidget)
        for table in tables:
            for col in range(table.columnCount()):
                table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        # Style des spinbox ; une erreur est journalisée sans bloquer la suite.
        try:
            UIManager.styleSpinBoxes(window)
        except Exception:
            Settings.write_log_dev_file(f"Error styling spin boxes\n{traceback.format_exc()}", "ERROR")
            pass

        window.result_tab_widget = UIManager.findWidget(window, "tabWidgetResult", QTabWidget)

    @staticmethod
    # -------------------------------------------------------------------------
    # Ajoute des images de flèches haut/bas personnalisées à tous les QSpinBox
    # de la fenêtre, uniquement si les deux fichiers d'images existent.
    # -------------------------------------------------------------------------
    def styleSpinBoxes(window):
        if not (Settings.DOWN_EXISTS and Settings.UP_EXISTS):
            return
        for spin_box in window.findChildren(QSpinBox):
            old_style = spin_box.styleSheet()
            spin_box.setStyleSheet(
                old_style
                + f'QSpinBox::down-button {{ image: url("{Settings.ARROW_DOWN_PATH}"); width: 13px; height: 13px; border-top-left-radius: 5px; border-bottom-left-radius: 5px; }} QSpinBox::up-button {{ image: url("{Settings.ARROW_UP_PATH}"); width: 13px; height: 13px; border-top-left-radius: 5px; border-bottom-left-radius: 5px; }}'
            )

    @staticmethod
    # -------------------------------------------------------------------------
    # Ajoute une nouvelle étape au scénario en clonant un cadre modèle.
    # Paramètres :
    #   - template_name : « Template1 » à « Template5 » (sinon rien n'est fait) ;
    #   - state : dict décrivant l'étape (au minimum « label ») ; il est stocké
    #     sur le cadre créé dans la propriété « full_state ».
    # Étapes :
    #   1. Sélection du cadre modèle.
    #   2. Création d'un nouveau QFrame de même style (hauteur fixe 51 px,
    #      largeur max 780 px).
    #   3. Clonage de chaque enfant direct du modèle selon son type, en
    #      conservant texte/valeur, position et style. Le premier QLabel reçoit
    #      le label de l'étape.
    #   4. Chaque case à cocher masque le dernier champ texte et l'affiche
    #      uniquement lorsqu'elle est cochée.
    #   5. Stockage de l'état et ajout du cadre dans scenario_layout.
    # -------------------------------------------------------------------------
    def updateScenario(window, template_name, state):
        # Étape 1 : choix du modèle selon son nom ; nom inconnu -> sortie.
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

        # Étape 2 : création du cadre de la nouvelle étape.
        if template_frame:
            new_template = QFrame()
            new_template.setStyleSheet(template_frame.styleSheet())
            new_template.setMaximumHeight(51)
            new_template.setMinimumHeight(51)
            new_template.setMaximumWidth(780)

            # Champs de saisie (QLineEdit et QTextEdit) et cases à cocher clonés,
            # conservés pour l'étape 4.
            lineedits = []
            checkboxes = []
            first_label_updated = False

            # Étape 3 : clonage de chaque enfant direct du modèle.
            for child in template_frame.children():
                # QLabel : le premier prend le label de l'étape, les autres gardent le texte
                # du modèle.
                if isinstance(child, QLabel):
                    new_label = QLabel(new_template)
                    if not first_label_updated:
                        new_label.setText(state.get("label", ""))
                        first_label_updated = True
                    else:
                        new_label.setText(child.text())
                    new_label.setStyleSheet(child.styleSheet())
                    new_label.setGeometry(child.geometry())
                # QPushButton : le signal clicked du clone est connecté au signal clicked
                # du modèle (connexion signal -> signal) : cliquer sur le clone réémet le
                # signal du bouton modèle et déclenche donc ses propres slots.
                elif isinstance(child, QPushButton):
                    new_button = QPushButton(child.text(), new_template)
                    new_button.setStyleSheet(child.styleSheet())
                    new_button.setGeometry(child.geometry())
                    new_button.clicked.connect(child.clicked)
                # QSpinBox : même valeur, position et style.
                elif isinstance(child, QSpinBox):
                    new_spinbox = QSpinBox(new_template)
                    new_spinbox.setValue(child.value())
                    new_spinbox.setGeometry(child.geometry())
                    new_spinbox.setStyleSheet(child.styleSheet())
                # QLineEdit : même texte ; ajouté à la liste des champs de saisie.
                elif isinstance(child, QLineEdit):
                    new_lineedit = QLineEdit(new_template)
                    new_lineedit.setText(child.text())
                    new_lineedit.setGeometry(child.geometry())
                    new_lineedit.setStyleSheet(child.styleSheet())
                    lineedits.append(new_lineedit)
                # QTextEdit : même texte ; ajouté lui aussi à la liste des champs de saisie.
                elif isinstance(child, QTextEdit):
                    new_textedit = QTextEdit(new_template)
                    new_textedit.setPlainText(child.toPlainText())
                    new_textedit.setGeometry(child.geometry())
                    new_textedit.setStyleSheet(child.styleSheet())
                    lineedits.append(new_textedit)
                # QCheckBox : même texte et même état coché.
                elif isinstance(child, QCheckBox):
                    new_checkbox = QCheckBox(child.text(), new_template)
                    new_checkbox.setChecked(child.isChecked())
                    new_checkbox.setGeometry(child.geometry())
                    new_checkbox.setStyleSheet(child.styleSheet())
                    checkboxes.append(new_checkbox)
                # QComboBox : recopie de tous les choix et de l'élément sélectionné.
                elif isinstance(child, QComboBox):
                    new_combobox = QComboBox(new_template)
                    new_combobox.addItems([child.itemText(i) for i in range(child.count())])
                    new_combobox.setCurrentIndex(child.currentIndex())
                    new_combobox.setGeometry(child.geometry())
                    new_combobox.setStyleSheet(child.styleSheet())

            # Étape 4 : le dernier champ de saisie est masqué par défaut ; il apparaît
            # quand la case est cochée (signal stateChanged). L'argument par défaut
            # lineedit=linked_lineedit fige le champ au moment de la création du lambda.
            for checkbox in checkboxes:
                if lineedits:
                    linked_lineedit = lineedits[-1]
                    linked_lineedit.hide()
                    checkbox.stateChanged.connect(lambda state, lineedit=linked_lineedit: (UIManager.handleCheckboxState(state, lineedit)))
            # Étape 5 : état complet mémorisé sur le cadre (lu notamment par
            # validateCheckboxLinkedQlineEdit et removeInitial), puis ajout au scénario.
            new_template.setProperty("full_state", state)
            window.scenario_layout.addWidget(new_template)

    @staticmethod
    # -------------------------------------------------------------------------
    # Affiche ou masque le champ lié à une case à cocher.
    # state vient du signal stateChanged : 2 correspond à Qt.CheckState.Checked.
    # -------------------------------------------------------------------------
    def handleCheckboxState(state, lineedit):
        if lineedit:
            if state == 2:
                lineedit.show()
            else:
                lineedit.hide()

    @staticmethod
    # -------------------------------------------------------------------------
    # Désactive un bouton et lui applique un style « grisé ».
    # Étapes :
    #   1. Ignore un bouton inexistant ou déjà désactivé (ce second contrôle
    #      évite d'écraser le style d'origine déjà sauvegardé).
    #   2. Sauvegarde le style actuel dans la propriété dynamique « old_style ».
    #   3. Désactive le bouton et applique disabled_style (gris par défaut).
    #   4. Force le redessin et traite les événements en attente pour que le
    #      changement soit visible immédiatement, même pendant un traitement long.
    # -------------------------------------------------------------------------
    def disableButton(button, disabled_style=None):
        """Désactive un bouton avec un style personnalisé"""
        Settings.write_log_dev_file("Attempting to disable button...", "INFO")
        if button is None:
            Settings.write_log_dev_file("Attempted to disable a non-existent button", "WARNING")
            return
        if not button.isEnabled():
            Settings.write_log_dev_file("Attempted to disable an already disabled button", "WARNING")
            return
        # Sauvegarde du style actuel pour le restaurer dans enableButton().
        button.setProperty("old_style", button.styleSheet())
        button.setEnabled(False)
        if disabled_style is None:
            disabled_style = "background-color: #cccccc; color: #666666; border: 1px solid #999999; text-align: center;"
        button.setStyleSheet(disabled_style)
        # Redessin immédiat + traitement des événements en attente.
        button.repaint()
        QApplication.processEvents()
        Settings.write_log_dev_file(f"Button '{button.objectName()}' disabled with style: {disabled_style}", "INFO")

    @staticmethod
    # -------------------------------------------------------------------------
    # Réactive un bouton et restaure le style sauvegardé par disableButton()
    # (propriété « old_style ») s'il existe ; sinon un avertissement est journalisé.
    # -------------------------------------------------------------------------
    def enableButton(button):
        """Réactive un bouton et restaure l'ancien style"""
        Settings.write_log_dev_file("Attempting to enable button...", "INFO")

        if button is None:
            Settings.write_log_dev_file("Attempted to enable a non-existent button", "WARNING")
            return

        button.setEnabled(True)
        # Lecture du style sauvegardé lors de la désactivation.
        old_style = button.property("old_style")

        if old_style:
            Settings.write_log_dev_file(f"Button '{button.objectName()}' enabled, restoring old style.", "INFO")
            button.setStyleSheet(old_style)
        else:
            Settings.write_log_dev_file(f"Button '{button.objectName()}' enabled, but no old style found to restore.", "WARNING")
