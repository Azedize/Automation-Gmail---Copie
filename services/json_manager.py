import random
import os
import sys
import traceback

from PyQt6.QtWidgets import QCheckBox, QLineEdit, QComboBox


# Récupère le chemin absolu du dossier racine du projet.
#
# __file__ représente le fichier Python actuellement exécuté.
# abspath() transforme ce chemin en chemin absolu.
# dirname() remonte d'un niveau dans l'arborescence.
#
# Exemple :
# C:\AutoMailPro\utils\json_manager.py
#                    ↓ dirname()
# C:\AutoMailPro\utils
#                    ↓ dirname()
# C:\AutoMailPro
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Vérifie que le dossier racine du projet est présent dans sys.path.
#
# sys.path contient les chemins dans lesquels Python recherche
# les modules lors des instructions import.
#
# insert(0, ...) place ROOT_DIR au début de la liste afin que
# Python recherche en priorité les modules dans le projet.
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


try:
    # Settings contient les constantes et configurations globales
    # utilisées par l'application.
    from config import Settings

    # ValidationUtils contient les fonctions utilisées pour valider
    # et convertir les valeurs saisies dans l'interface graphique.
    from utils import ValidationUtils

except ImportError as error:
    # Journalise le détail complet si la configuration est déjà disponible.
    if "Settings" in globals():
        Settings.write_log_event("json_manager_import_failed", "ERROR", file=__file__, exception_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
    else:
        # Utilise la console si l’import de Settings est lui-même en échec.
        print(f"❌ Erreur d'importation dans file {__file__}: {error}\n" f"{traceback.format_exc()}")

    # Arrête immédiatement l'application avec un code d'erreur.
    sys.exit(1)


class JsonManager:
    @staticmethod
    def parseRandomRange(text: str) -> int:
        # Cette méthode sert de passerelle vers ValidationUtils.
        #
        # Elle reçoit une valeur texte représentant généralement
        # une valeur numérique ou une plage aléatoire.
        #
        # Exemple :
        # "5"     -> 5
        # "2-5"   -> une valeur comprise dans la plage selon
        #            l'implémentation de parse_random_range().
        #
        # La conversion réelle est déléguée à ValidationUtils
        # afin de centraliser la logique de validation.
        return ValidationUtils.parse_random_range(text)

    @staticmethod
    def getChildWidgets(widget, cls):
        # Récupère tous les widgets enfants du widget fourni
        # correspondant au type demandé.
        #
        # Exemple :
        #
        # widget
        # ├── QLabel
        # ├── QLineEdit
        # ├── QLineEdit
        # └── QCheckBox
        #
        # getChildWidgets(widget, QLineEdit)
        # retourne les deux QLineEdit.
        #
        # isinstance(c, cls) vérifie si l'objet c est une instance
        # du type demandé.
        return [c for c in widget.children() if isinstance(c, cls)]

    @staticmethod
    def generateJson(scenario_layout):
        # Cette méthode constitue le point principal de génération
        # du scénario JSON à partir des widgets présents dans
        # scenario_layout.
        #
        # Elle parcourt les éléments de l'interface graphique,
        # récupère leurs informations internes, lit les valeurs
        # des champs et construit progressivement le JSON.
        #
        # Initialise le JSON avec l'action de connexion.
        #
        # Le scénario commence donc toujours par :
        #
        # {
        #     "process": "login",
        #     "sleep": 1
        # }
        output_json = [{"process": "login", "sleep": 1}]

        # Si le layout ne contient aucun élément, il n'y a aucun
        # scénario à générer.
        if scenario_layout.count() == 0:
            return []

        # Index utilisé pour parcourir les éléments du layout.
        i = 0

        # Parcourt tous les éléments du scénario dans leur ordre
        # d'apparition dans l'interface.
        while i < scenario_layout.count():
            # Récupère le widget situé à la position i.
            #
            # itemAt(i) récupère l'élément du layout.
            # widget() récupère ensuite le QWidget associé.
            widget = scenario_layout.itemAt(i).widget()

            # Il est possible qu'un élément du layout ne corresponde
            # pas directement à un QWidget.
            #
            # Dans ce cas, on ignore l'élément et on passe au suivant.
            if not widget:
                i += 1
                continue

            # Récupère la propriété Qt personnalisée "full_state".
            #
            # Cette propriété contient généralement les informations
            # internes du scénario, par exemple :
            #
            # {
            #     "id": "open_inbox",
            #     "showOnInit": True
            # }
            #
            # Si la propriété n'existe pas, on utilise un dictionnaire vide
            # afin d'éviter une erreur lors des appels à .get().
            full_state = widget.property("full_state") or {}

            # Récupère l'identifiant interne de l'action.
            #
            # Exemple :
            # "open_inbox"
            # "delete"
            # "youtube_video"
            hidden_id = full_state.get("id")

            # Indique si l'élément est une action principale affichée
            # dès l'initialisation du scénario.
            #
            # Si la propriété n'existe pas, False est utilisé.
            show_on_init = full_state.get("showOnInit", False)

            # Recherche le premier QCheckBox présent dans le widget.
            #
            # getChildWidgets() retourne une liste de QCheckBox.
            # iter() transforme cette liste en itérateur.
            # next(..., None) récupère le premier élément.
            #
            # Si aucun QCheckBox n'existe, checkbox vaut None.
            checkbox = next(iter(JsonManager.getChildWidgets(widget, QCheckBox)), None)

            # Récupère tous les QLineEdit présents dans le widget.
            #
            # Leur position dans la liste est importante dans la logique
            # actuelle car le code utilise qlineedits[0], qlineedits[1]
            # ou qlineedits[-1] selon le type d'action.
            qlineedits = JsonManager.getChildWidgets(widget, QLineEdit)

            # ---------------------------------------------------------
            # CAS 1 :
            # Action normale, non principale et non Google/YouTube.
            # ---------------------------------------------------------
            #
            # Conditions :
            #
            # 1. hidden_id existe.
            # 2. showOnInit est False.
            # 3. L'action ne commence pas par le préfixe Google.
            # 4. L'action ne commence pas par le préfixe YouTube.
            #
            # Exemple :
            #
            # hidden_id = "delete"
            # show_on_init = False
            #
            # Cette action sera traitée comme une action classique.
            if hidden_id and not show_on_init and not hidden_id.startswith((Settings.GOOGLE_PREFIX, Settings.YOUTUBE_PREFIX)):
                # Si le widget contient au moins deux champs texte,
                # le premier représente la limite et le second
                # représente le temps d'attente.
                if len(qlineedits) > 1:
                    # Convertit la première valeur en nombre
                    # ou en valeur aléatoire selon le format fourni.
                    limit = ValidationUtils.parse_random_range(qlineedits[0].text())

                    # Convertit la deuxième valeur en temps d'attente.
                    sleep = ValidationUtils.parse_random_range(qlineedits[1].text())

                    # Ajoute l'action au scénario JSON.
                    output_json.append({"process": hidden_id, "limit": limit, "sleep": sleep})

                # Si un seul QLineEdit existe, il est utilisé comme
                # valeur de sleep.
                elif qlineedits:
                    # Lit et convertit la valeur du champ.
                    sleep = ValidationUtils.parse_random_range(qlineedits[0].text())

                    # Ajoute l'action au JSON.
                    output_json.append({"process": hidden_id, "sleep": sleep})

                # L'élément actuel a été complètement traité.
                # On avance vers le prochain élément du layout.
                i += 1
                continue

            # ---------------------------------------------------------
            # CAS 2 :
            # Action YouTube nécessitant une vérification de connexion.
            # ---------------------------------------------------------
            #
            # Exemple :
            # hidden_id = "youtube_video"
            #
            # Avant l'action YouTube, le scénario ajoute automatiquement
            # CheckLoginYoutube.
            if hidden_id and not show_on_init and hidden_id.startswith(Settings.YOUTUBE_PREFIX):
                # Si deux QLineEdit existent :
                # qlineedits[0] = limite
                # qlineedits[1] = sleep
                #
                # Sinon, les valeurs par défaut sont 0.
                limit = ValidationUtils.parse_random_range(qlineedits[0].text()) if len(qlineedits) > 1 else 0

                sleep = ValidationUtils.parse_random_range(qlineedits[1].text()) if len(qlineedits) > 1 else 0

                # Ajoute une vérification de connexion YouTube
                # avant l'exécution de l'action YouTube.
                #
                # randint(1, 3) produit aléatoirement 1, 2 ou 3.
                output_json.append({"process": "CheckLoginYoutube", "sleep": random.randint(1, 3)})

                # Ajoute ensuite l'action YouTube elle-même.
                output_json.append({"process": hidden_id, "limit": limit, "sleep": sleep})

                # Passe à l'élément suivant.
                i += 1
                continue

            # ---------------------------------------------------------
            # CAS 3 :
            # Action principale avec Checkbox.
            # ---------------------------------------------------------
            #
            # Ce cas représente une action principale pouvant contenir
            # plusieurs sous-actions.
            #
            # Exemple conceptuel :
            #
            # open_inbox
            # ├── select_all
            # ├── delete
            # └── next
            #
            # Le Checkbox permet généralement d'activer une recherche
            # ou un comportement supplémentaire.
            if show_on_init and checkbox:
                # Ajoute l'action principale.
                #
                # Le temps d'attente initial est volontairement aléatoire
                # entre 1 et 3 secondes.
                output_json.append({"process": hidden_id, "sleep": random.randint(1, 3)})

                # Vérifie si le Checkbox est activé.
                if checkbox.isChecked():
                    # Si des QLineEdit existent, utilise le dernier
                    # comme valeur de recherche.
                    #
                    # S'il n'y en a aucun, utilise une chaîne vide.
                    search_value = qlineedits[-1].text() if qlineedits else ""

                    # Cas spécial pour la boîte Spam.
                    #
                    # Le préfixe "in:spam" permet de limiter la recherche
                    # aux messages présents dans le dossier Spam.
                    if hidden_id == "open_spam":
                        search_value = f"in:spam {search_value}"

                    # Ajoute l'action de recherche au scénario.
                    output_json.append({"process": "search", "value": search_value})

                # Liste contenant les actions secondaires
                # appartenant à l'action principale actuelle.
                sub_process = []

                # Passe au widget suivant afin de commencer à rechercher
                # les sous-actions.
                i += 1

                # -----------------------------------------------------
                # Recherche des sous-actions.
                # -----------------------------------------------------
                while i < scenario_layout.count():
                    # Récupère le widget suivant.
                    sub_widget = scenario_layout.itemAt(i).widget()

                    # Si aucun widget n'est trouvé, on arrête la recherche
                    # des sous-actions.
                    if not sub_widget:
                        break

                    # Récupère l'état interne du sous-widget.
                    sub_state = sub_widget.property("full_state") or {}

                    # Récupère son identifiant.
                    #
                    # Si aucun ID n'est défini, une chaîne vide est utilisée.
                    sub_id = sub_state.get("id") or ""

                    # Si le sous-widget est lui-même une action principale
                    # ou une action Google/YouTube, il ne fait plus partie
                    # des sous-actions du widget actuel.
                    #
                    # On arrête donc la boucle interne.
                    if sub_state.get("showOnInit") or sub_id.startswith((Settings.GOOGLE_PREFIX, Settings.YOUTUBE_PREFIX)):
                        break

                    # Recherche le premier QLineEdit du sous-widget.
                    #
                    # Si aucun QLineEdit n'existe, "0" est utilisé.
                    sleep_txt = next((c.text() for c in JsonManager.getChildWidgets(sub_widget, QLineEdit)), "0")

                    # Convertit la valeur de sleep.
                    sleep = ValidationUtils.parse_random_range(sleep_txt)

                    # Ajoute la sous-action avec son temps d'attente.
                    sub_process.append({"process": sub_id, "sleep": sleep})

                    # Passe au widget suivant.
                    i += 1

                # -----------------------------------------------------
                # Détermine l'action finale du groupe.
                # -----------------------------------------------------

                # Recherche le premier QComboBox du widget principal.
                combo = next(iter(JsonManager.getChildWidgets(widget, QComboBox)), None)

                # Si le ComboBox existe et que l'utilisateur a choisi
                # "Return back", l'action finale sera "return_back".
                #
                # Dans tous les autres cas, l'action sera "next".
                action = "return_back" if combo and combo.currentText() == "Return back" else "next"

                # Si des sous-actions existent, ajoute l'action finale
                # à la fin de la liste.
                #
                # Exemple :
                #
                # [
                #     {"process": "select_all", "sleep": 1},
                #     {"process": "delete", "sleep": 2},
                #     {"process": "next"}
                # ]
                if sub_process:
                    sub_process.append({"process": action})

                # Récupère la limite du loop.
                #
                # qlineedits[0] représente la limite lorsque deux champs
                # sont présents.
                limit_loop = ValidationUtils.parse_random_range(qlineedits[0].text()) if len(qlineedits) > 1 else 0

                # Récupère la valeur de départ du loop.
                start_loop = ValidationUtils.parse_random_range(qlineedits[1].text()) if len(qlineedits) > 1 else 0

                # Ajoute le loop complet au JSON.
                #
                # "check" indique la condition utilisée par le moteur
                # d'exécution pour contrôler le loop.
                output_json.append({"process": "loop", "check": "is_empty_folder", "limit_loop": limit_loop, "start": start_loop, "sub_process": sub_process})

                # Le widget et ses sous-widgets ont déjà été traités.
                continue

            # ---------------------------------------------------------
            # CAS 4 :
            # Action principale sans Checkbox.
            # ---------------------------------------------------------
            if show_on_init and not checkbox:
                # Récupère le temps d'attente depuis le premier QLineEdit.
                #
                # S'il n'existe aucun QLineEdit, utilise 0.
                sleep = ValidationUtils.parse_random_range(qlineedits[0].text()) if qlineedits else 0

                # Ajoute l'action principale au JSON.
                output_json.append({"process": hidden_id, "sleep": sleep})

                # Passe au widget suivant.
                i += 1
                continue

            # ---------------------------------------------------------
            # CAS 5 :
            # Action Google ou YouTube.
            # ---------------------------------------------------------
            if hidden_id and hidden_id.startswith((Settings.GOOGLE_PREFIX, Settings.YOUTUBE_PREFIX)):
                # Récupère le sleep depuis le premier QLineEdit.
                #
                # Si aucun champ n'existe, utilise 0.
                sleep = ValidationUtils.parse_random_range(qlineedits[0].text()) if qlineedits else 0

                # Construit l'action de base.
                action = {"process": hidden_id, "sleep": sleep}

                # Si un Checkbox existe et qu'il est activé,
                # ajoute la valeur de recherche.
                if checkbox and checkbox.isChecked():
                    # Avec plusieurs QLineEdit, le deuxième champ
                    # représente la recherche.
                    #
                    # Avec un seul QLineEdit, le premier est utilisé.
                    action["search"] = qlineedits[1].text() if len(qlineedits) > 1 else qlineedits[0].text()

                # Ajoute l'action finale au JSON.
                output_json.append(action)

                # Passe au widget suivant.
                i += 1
                continue

            # ---------------------------------------------------------
            # Aucun des cas précédents ne correspond.
            # ---------------------------------------------------------
            #
            # On avance simplement vers l'élément suivant afin d'éviter
            # de rester bloqué sur le même index.
            i += 1

        # -------------------------------------------------------------
        # POST-TRAITEMENT DU JSON
        # -------------------------------------------------------------
        #
        # La première étape organise les éléments en sections et
        # applique certaines règles aux loops.
        output_json = JsonManager.splitJsonIntoProcesses(output_json)

        # La deuxième étape traite certaines règles liées aux derniers
        # éléments des loops.
        output_json = JsonManager.handleLastJsonElement(output_json)

        # La dernière étape modifie certains loops selon la présence
        # préalable d'une action open_message.
        output_json = JsonManager.modifyJsonProcesses(output_json)

        # Retourne le scénario JSON final.
        return output_json

    @staticmethod
    def splitJsonIntoProcesses(input_json):
        # Cette méthode organise le JSON en sections.
        #
        # Une nouvelle section commence notamment avec :
        #
        # - open_inbox
        # - open_spam
        #
        # Elle applique également certaines règles aux loops
        # et supprime les loops sans sous-actions.

        # output  = résultat final.
        # section = section actuellement en construction.
        # current = nom du process principal de la section courante.
        output, section, current = [], [], None

        def flush():
            # Si une section contient des éléments, les ajoute au résultat.
            #
            # extend() ajoute tous les éléments de section à output.
            if section:
                output.extend(section)

        # Parcourt tous les éléments du JSON d'entrée.
        for el in input_json:
            # Si un loop ne contient aucune sous-action,
            # il n'a aucune utilité et est donc ignoré.
            if el.get("process") == "loop" and not el.get("sub_process"):
                continue

            # ---------------------------------------------------------
            # Début d'une nouvelle section.
            # ---------------------------------------------------------
            #
            # open_inbox et open_spam servent de points de séparation
            # entre les différentes sections du scénario.
            if el.get("process") in ("open_inbox", "open_spam"):
                # Ajoute l'ancienne section au résultat avant
                # d'en commencer une nouvelle.
                flush()

                # Commence une nouvelle section avec l'élément actuel.
                section = [el]

                # Mémorise le process principal de la section.
                current = el["process"]

                continue

            # ---------------------------------------------------------
            # Traitement spécial des loops.
            # ---------------------------------------------------------
            if el.get("process") == "loop":
                # Récupère la liste des opérations autorisées
                # pour la section actuelle.
                #
                # Si aucune configuration n'existe pour current,
                # une collection vide est utilisée.
                allowed = Settings.ALLOWED_ITEMS.get(current, ())

                # Récupère les sous-actions du loop.
                sub = el["sub_process"]

                # Vérifie si le loop contient :
                #
                # - select_all
                # OU
                # - au moins une action autorisée dans la section.
                if any(s["process"] == "select_all" for s in sub) or any(s["process"] in allowed for s in sub):
                    # Dans ce cas, les actions de contrôle
                    # next / return_back sont supprimées.
                    #
                    # Cela permet d'éviter certaines actions finales
                    # incompatibles avec les opérations présentes
                    # dans le loop.
                    sub = [s for s in sub if s["process"] not in ("next", "return_back")]

                # Remplace les sous-actions originales par la version
                # éventuellement nettoyée.
                el["sub_process"] = sub

                # Ajoute le loop à la section courante.
                section.append(el)

                continue

            # ---------------------------------------------------------
            # Élément normal.
            # ---------------------------------------------------------
            #
            # Si l'élément n'est ni une nouvelle section ni un loop,
            # il est simplement ajouté à la section courante.
            section.append(el)

        # Après avoir parcouru tous les éléments, ajoute la dernière
        # section au résultat.
        flush()

        # Retourne le JSON organisé.
        return output

    @staticmethod
    def handleLastJsonElement(input_json):
        # Cette méthode applique des règles spéciales aux derniers
        # éléments des loops et supprime certaines opérations exclues.

        # Liste contenant le résultat final.
        output = []

        # Parcourt chaque élément du JSON.
        for el in input_json:
            # ---------------------------------------------------------
            # Suppression des processes exclus.
            # ---------------------------------------------------------
            #
            # EXCLUDED_PROCESSES est défini dans Settings.
            #
            # Si le process actuel est présent dans cette collection,
            # il n'est pas ajouté au résultat.
            if el.get("process") in Settings.EXCLUDED_PROCESSES:
                continue

            # ---------------------------------------------------------
            # Traitement spécifique des loops.
            # ---------------------------------------------------------
            if el.get("process") == "loop":
                # Récupère les sous-actions du loop.
                #
                # Si sub_process n'existe pas, utilise une liste vide.
                sub = el.get("sub_process", [])

                # Continue uniquement si le loop contient des sous-actions.
                if sub:
                    # Récupère le process de la dernière sous-action.
                    #
                    # [-1] signifie le dernier élément de la liste.
                    last = sub[-1]["process"]

                    # -------------------------------------------------
                    # Cas où le dernier process est "next".
                    # -------------------------------------------------
                    if last == "next":
                        # Ajoute automatiquement une action
                        # open_message après le loop.
                        #
                        # Le sleep est aléatoire entre 1 et 3 secondes.
                        output.append({"process": "open_message", "sleep": random.randint(1, 3)})

                    # -------------------------------------------------
                    # Cas où le dernier process n'est pas une action
                    # finale spécifique.
                    # -------------------------------------------------
                    elif last not in ("delete", "archive", "not_spam", "report_spam"):
                        # Parcourt toutes les sous-actions.
                        for s in sub:
                            # Si une action open_message existe,
                            # elle est remplacée par une version spéciale
                            # permettant apparemment de traiter les messages
                            # un par un.
                            if s["process"] == "open_message":
                                s["process"] = "OPEN_MESSAGE_ONE_BY_ONE"

                # Met à jour les sous-actions du loop après les
                # éventuelles modifications.
                el["sub_process"] = sub

            # Ajoute l'élément courant au résultat.
            output.append(el)

        # Retourne le JSON après traitement.
        return output

    @staticmethod
    def modifyJsonProcesses(input_json):
        # Cette méthode applique une dernière règle contextuelle.
        #
        # Elle surveille la présence d'un process "open_message".
        # Si un loop apparaît ensuite et contient "next",
        # la propriété "check" du loop est supprimée.

        # Liste contenant le résultat final.
        output = []

        # Indique si un process "open_message" a déjà été rencontré.
        found = False

        # Parcourt tous les éléments du JSON.
        for el in input_json:
            # ---------------------------------------------------------
            # Détection de open_message.
            # ---------------------------------------------------------
            if el.get("process") == "open_message":
                # À partir de maintenant, les règles qui dépendent
                # de la présence de open_message peuvent être appliquées.
                found = True

            # ---------------------------------------------------------
            # Recherche d'un loop après open_message.
            # ---------------------------------------------------------
            elif el.get("process") == "loop" and found:
                # Vérifie si le loop contient une sous-action "next".
                if any(s["process"] == "next" for s in el.get("sub_process", [])):
                    # Supprime la propriété "check" si elle existe.
                    #
                    # Le deuxième argument None évite une exception
                    # si la clé "check" n'existe pas.
                    el.pop("check", None)

            # Ajoute l'élément au résultat.
            output.append(el)

        # Retourne le JSON final après toutes les modifications.
        return output


# Création d'une instance de JsonManager.
#
# Toutes les méthodes actuelles sont des @staticmethod, donc cette
# instance n'est pas nécessaire pour les appeler.
#
# Elle peut cependant être conservée pour compatibilité avec le reste
# de l'application si d'autres fichiers utilisent :
#
#     json_manager.generateJson(...)
json_manager = JsonManager()
