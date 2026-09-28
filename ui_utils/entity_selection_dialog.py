import os
import re

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from config import Settings


class EntitySelectionDialog(QDialog):
    # Cette classe représente une fenêtre de dialogue permettant à l'utilisateur
    # de saisir et de sélectionner une "Entity" pour la session courante.
    #
    # Elle hérite de QDialog, ce qui lui permet d'utiliser le comportement
    # standard d'une fenêtre de dialogue Qt :
    # - ouverture avec exec()
    # - fermeture acceptée avec accept()
    # - fermeture annulée avec reject()
    # - fonctionnement modal avec setModal()
    #
    # Le dialogue assure également la validation de la valeur saisie
    # avant d'autoriser la fermeture avec le bouton "Confirm".

    def __init__(self, pattern=None, default_entity=None, parent=None):
        # Le constructeur est appelé automatiquement lorsqu'une instance
        # de EntitySelectionDialog est créée.
        #
        # pattern :
        #   Expression régulière utilisée pour vérifier le format de l'Entity.
        #
        # default_entity :
        #   Valeur à afficher automatiquement dans le champ de saisie
        #   lorsqu'une Entity par défaut est disponible.
        #
        # parent :
        #   Widget parent de la fenêtre, généralement la fenêtre principale
        #   de l'application.

        # Initialise correctement la partie QDialog héritée de la classe parente.
        # Cette étape permet à Qt de configurer correctement la fenêtre,
        # son parent et son cycle de vie.
        super().__init__(parent)

        # Définit le titre affiché dans la barre de la fenêtre.
        self.setWindowTitle("Select Entity - AutoMailPro")

        # Rend la fenêtre modale.
        #
        # Cela signifie que l'utilisateur doit terminer cette fenêtre
        # (Confirm ou Cancel) avant de pouvoir continuer à interagir
        # normalement avec la fenêtre parent.
        self.setModal(True)

        # Définit une taille fixe pour la fenêtre :
        # largeur = 500 pixels
        # hauteur = 320 pixels
        #
        # L'utilisateur ne pourra pas redimensionner cette fenêtre.
        self.setFixedSize(500, 320)

        # Définit l'icône affichée dans la barre de la fenêtre.
        #
        # os.path.join() construit le chemin du fichier de manière compatible
        # avec le système d'exploitation.
        #
        # Exemple :
        # Settings.ICONS_DIR -> dossier contenant les icônes
        # "logo.jpg"         -> fichier de l'icône
        self.setWindowIcon(QIcon(os.path.join(Settings.ICONS_DIR, "logo.jpg")))

        # Conserve le pattern fourni par le code appelant.
        #
        # Cette valeur sera utilisée plus tard dans validate_and_accept()
        # afin de vérifier le format de l'Entity saisie.
        self.pattern = pattern

        # Crée le layout principal vertical de la fenêtre.
        #
        # QVBoxLayout signifie "Vertical Box Layout".
        # Les widgets seront donc placés verticalement les uns sous les autres.
        #
        # Le paramètre self indique que ce layout appartient directement
        # à cette fenêtre QDialog.
        main_layout = QVBoxLayout(self)

        # Définit les marges internes entre le contenu du layout
        # et les bords de la fenêtre.
        #
        # Ordre :
        # gauche, haut, droite, bas
        main_layout.setContentsMargins(25, 25, 25, 25)

        # Définit l'espace vertical entre les différents widgets
        # ajoutés au layout principal.
        main_layout.setSpacing(12)

        # Crée le titre principal de la fenêtre.
        #
        # QLabel est utilisé pour afficher du texte que l'utilisateur
        # ne doit pas modifier.
        title_label = QLabel("Entity Selection")

        # Définit l'apparence visuelle du titre.
        #
        # font-size      -> taille du texte
        # font-weight    -> texte en gras
        # color          -> couleur du texte
        # margin-bottom  -> espace sous le titre
        title_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #333; margin-bottom: 10px;"
        )

        # Ajoute le titre au layout principal.
        #
        # AlignCenter place le widget au centre horizontalement.
        main_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Crée le texte explicatif affiché au-dessus du champ de saisie.
        instruction_label = QLabel(
            "Please enter the entity you want to use for this session : "
        )

        # Définit le style visuel du texte d'instruction.
        instruction_label.setStyleSheet(
            "font-size: 14px; color: #555; margin-bottom: 5px;"
        )

        # Autorise QLabel à couper automatiquement le texte sur plusieurs lignes
        # si la largeur disponible n'est pas suffisante.
        instruction_label.setWordWrap(True)

        # Ajoute le texte d'instruction au layout principal.
        main_layout.addWidget(instruction_label)

        # Vérifie si un pattern de validation a été fourni.
        #
        # Si self.pattern existe, une information supplémentaire sera affichée
        # afin d'expliquer à l'utilisateur le format attendu.
        if self.pattern:
            # Crée un label expliquant le format attendu.
            #
            # Exemple :
            # opm74
            # opm19
            format_info = QLabel("Format: opm followed by digits (e.g., opm74, opm19)")

            # Définit le style du texte d'information.
            #
            # Le texte est plus petit et affiché en italique afin
            # de le distinguer de l'instruction principale.
            format_info.setStyleSheet(
                "font-size: 12px; color: #859cb5; "
                "margin-bottom: 10px; font-style: italic;"
            )

            # Ajoute l'information sur le format au layout.
            main_layout.addWidget(format_info)

        # Crée le champ dans lequel l'utilisateur pourra saisir l'Entity.
        #
        # QLineEdit est un champ de saisie permettant d'entrer une seule ligne
        # de texte.
        self.input_field = QLineEdit()

        # Définit le texte indicatif affiché lorsque le champ est vide.
        #
        # Ce texte disparaît automatiquement lorsque l'utilisateur commence
        # à saisir une valeur.
        self.input_field.setPlaceholderText("Enter entity (opm + number)...")

        # Vérifie si une Entity par défaut a été fournie.
        #
        # Si oui, elle est placée directement dans le champ de saisie.
        if default_entity:
            self.input_field.setText(default_entity)

        # Définit le style visuel du champ de saisie.
        #
        # QLineEdit :
        #   Style normal du champ.
        #
        # QLineEdit:hover :
        #   Style appliqué lorsque la souris passe au-dessus.
        #
        # QLineEdit:focus :
        #   Style appliqué lorsque le champ possède le focus clavier.
        self.input_field.setStyleSheet(
            "QLineEdit { "
            "font-size: 14px; "
            "padding: 8px; "
            "border: 2px solid #ccc; "
            "border-radius: 5px; "
            "background-color: #fff; "
            "min-width: 200px; "
            "} "
            "QLineEdit:hover { "
            "border-color: #0078d4; "
            "} "
            "QLineEdit:focus { "
            "border: 2px solid #0078d4; "
            "outline: none; "
            "}"
        )

        # Ajoute le champ de saisie au layout principal.
        #
        # AlignCenter permet de centrer le champ horizontalement.
        main_layout.addWidget(self.input_field, alignment=Qt.AlignmentFlag.AlignCenter)

        # Crée le label utilisé pour afficher les messages d'erreur
        # lors de la validation de l'Entity.
        self.error_label = QLabel()

        # Définit le style des messages d'erreur.
        #
        # Le texte est rouge afin d'indiquer clairement à l'utilisateur
        # qu'une erreur de validation s'est produite.
        self.error_label.setStyleSheet(
            "font-size: 12px; "
            "color: #d32f2f; "
            "margin-top: 8px; "
            "margin-bottom: 8px;"
        )

        # Permet au message d'erreur de passer sur plusieurs lignes
        # lorsque sa longueur dépasse la largeur disponible.
        self.error_label.setWordWrap(True)

        # Réserve une hauteur minimale pour le label.
        #
        # Cela évite que la disposition de la fenêtre change brutalement
        # lorsque le message d'erreur devient visible.
        self.error_label.setMinimumHeight(40)

        # Cache le message d'erreur au démarrage.
        #
        # Il sera affiché uniquement lorsqu'une validation échoue.
        self.error_label.hide()

        # Ajoute le label d'erreur au layout principal.
        main_layout.addWidget(self.error_label)

        # Ajoute un espace supplémentaire avant les boutons.
        #
        # Cela sépare visuellement la zone de saisie
        # de la zone contenant les boutons.
        main_layout.addSpacing(20)

        # Crée un layout horizontal pour les boutons.
        #
        # QHBoxLayout signifie "Horizontal Box Layout".
        #
        # Les boutons seront donc placés côte à côte :
        #
        # [ Cancel ] [ Confirm ]
        button_layout = QHBoxLayout()

        # Définit l'espace horizontal entre les boutons.
        button_layout.setSpacing(10)

        # Crée le bouton Cancel.
        self.cancel_button = QPushButton("Cancel")

        # Définit le style visuel du bouton Cancel.
        #
        # QPushButton :
        #   état normal
        #
        # QPushButton:hover :
        #   lorsque la souris passe dessus
        #
        # QPushButton:pressed :
        #   lorsque l'utilisateur clique dessus
        self.cancel_button.setStyleSheet(
            "QPushButton { "
            "font-size: 14px; "
            "padding: 10px 20px; "
            "background-color: #f3f2f1; "
            "border: 1px solid #ccc; "
            "border-radius: 5px; "
            "color: #333; "
            "text-align: center; "
            "} "
            "QPushButton:hover { "
            "background-color: #e1dfdd; "
            "} "
            "QPushButton:pressed { "
            "background-color: #c8c6c4; "
            "}"
        )

        # Connecte le signal "clicked" du bouton à la méthode reject().
        #
        # Lorsque l'utilisateur clique sur Cancel :
        #
        # clicked
        #    ↓
        # reject()
        #    ↓
        # Dialog fermé avec le résultat Rejected
        self.cancel_button.clicked.connect(self.reject)

        # Ajoute le bouton Cancel au layout horizontal.
        button_layout.addWidget(self.cancel_button)

        # Crée le bouton Confirm.
        self.confirm_button = QPushButton("Confirm")

        # Définit le style visuel du bouton Confirm.
        self.confirm_button.setStyleSheet(
            "QPushButton { "
            "font-size: 14px; "
            "padding: 10px 20px; "
            "background-color: #0078d4; "
            "border: none; "
            "border-radius: 5px; "
            "color: white; "
            "text-align: center; "
            "} "
            "QPushButton:hover { "
            "background-color: #106ebe; "
            "} "
            "QPushButton:pressed { "
            "background-color: #005a9e; "
            "}"
        )

        # Connecte le signal "clicked" du bouton Confirm
        # à notre méthode de validation.
        #
        # Contrairement à Cancel, Confirm ne ferme pas directement
        # la fenêtre.
        #
        # Le programme doit d'abord vérifier que l'Entity est valide.
        #
        # clicked
        #    ↓
        # validate_and_accept()
        #    ↓
        # validation
        #    ↓
        # accept() uniquement si la valeur est correcte
        self.confirm_button.clicked.connect(self.validate_and_accept)

        # Définit Confirm comme bouton par défaut.
        #
        # Dans Qt, cela permet notamment d'utiliser la touche Entrée
        # pour déclencher le bouton par défaut dans les situations appropriées.
        self.confirm_button.setDefault(True)

        # Ajoute le bouton Confirm au layout horizontal.
        button_layout.addWidget(self.confirm_button)

        # Ajoute le layout horizontal des boutons
        # au layout vertical principal.
        main_layout.addLayout(button_layout)

        # Définit la couleur de fond générale de la fenêtre.
        self.setStyleSheet("QDialog { background-color: #f8f8f8; }")

    def validate_and_accept(self):
        # Cette méthode est appelée lorsque l'utilisateur clique
        # sur le bouton "Confirm".
        #
        # Son rôle est de :
        # 1. récupérer la valeur saisie ;
        # 2. supprimer les espaces inutiles ;
        # 3. vérifier que la valeur n'est pas vide ;
        # 4. vérifier le format avec le pattern si nécessaire ;
        # 5. fermer le dialogue avec accept() uniquement si tout est valide.

        # Récupère le texte actuellement présent dans QLineEdit.
        #
        # text() récupère la valeur saisie par l'utilisateur.
        #
        # strip() supprime les espaces inutiles au début et à la fin.
        #
        # Exemple :
        # "   opm74   " -> "opm74"
        entity_text = self.input_field.text().strip()

        # Vérifie si l'utilisateur n'a rien saisi.
        #
        # Une chaîne vide est considérée comme False en Python.
        if not entity_text:
            # Affiche le message d'erreur approprié.
            self.error_label.setText("Entity name cannot be empty.")

            # Rend le label d'erreur visible.
            self.error_label.show()

            # Arrête immédiatement la méthode.
            #
            # Très important :
            # on ne doit pas appeler accept() lorsque la validation échoue.
            return

        # Vérifie le format de l'Entity lorsque self.pattern est disponible.
        #
        # Première condition :
        #     self.pattern
        #     -> un pattern a été fourni.
        #
        # Deuxième condition :
        #     not re.match(self.pattern, entity_text)
        #     -> l'Entity ne correspond pas au pattern.
        #
        # Exemple de pattern possible :
        #     ^opm\d+$
        #
        # Valeurs valides :
        #     opm74
        #     opm19
        #
        # Valeurs invalides :
        #     opmABC
        #     abc74
        #     opm
        if self.pattern and not re.match(self.pattern, entity_text):
            # Affiche le message indiquant que le format est incorrect.
            self.error_label.setText(
                "Invalid entity format. Expected format: "
                "opm followed by digits (e.g., opm74)"
            )

            # Rend le message d'erreur visible.
            self.error_label.show()

            # Arrête la validation.
            #
            # La fenêtre reste ouverte afin que l'utilisateur puisse
            # corriger la valeur saisie.
            return

        # Si cette ligne est atteinte, toutes les validations
        # précédentes ont réussi.
        #
        # On cache donc un éventuel ancien message d'erreur.
        self.error_label.hide()

        # Ferme le QDialog avec le résultat "Accepted".
        #
        # Le code qui a appelé exec() pourra alors détecter :
        #
        # QDialog.DialogCode.Accepted
        #
        # et récupérer la valeur saisie.
        self.accept()

    def get_selected_entity(self):
        # Cette méthode constitue le point d'entrée utilisé par le code
        # appelant pour afficher le dialogue et récupérer le résultat.
        #
        # Elle retourne :
        # - l'Entity saisie si l'utilisateur confirme avec succès ;
        # - None si l'utilisateur annule le dialogue.

        # Ouvre le dialogue et attend que l'utilisateur termine son interaction.
        #
        # exec() démarre la boucle d'événements du dialogue.
        #
        # La méthode attend jusqu'à ce que le dialogue soit fermé
        # avec accept() ou reject().
        if self.exec() == QDialog.DialogCode.Accepted:
            # Le dialogue a été validé avec Confirm.
            #
            # On récupère à nouveau le contenu du champ de saisie
            # et on supprime les espaces inutiles.
            return self.input_field.text().strip()

        # Si exec() ne retourne pas Accepted, cela signifie généralement
        # que l'utilisateur a annulé la fenêtre avec Cancel
        # ou qu'elle a été fermée sans validation.
        #
        # None indique donc qu'aucune Entity n'a été sélectionnée.
        return None
