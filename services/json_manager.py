"""
JSON Manager - Gestion optimisée du traitement JSON pour l'application AutoMailPro
Version refactorisée avec méthodes statiques pour une meilleure modularité
"""

import json
import random
import os
import sys
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from config import Settings
    from utils.validation_utils import ValidationUtils
except ImportError as e:
    raise ImportError(f"❌ Erreur d'importation: {e}")

# Constantes pour une meilleure lisibilité
class ProcessTypes:
    """Types de processus constants pour éviter les chaînes magiques"""
    LOGIN = "login"
    LOOP = "loop"
    OPEN_INBOX = "open_inbox"
    OPEN_SPAM = "open_spam"
    OPEN_MESSAGE = "open_message"
    SELECT_ALL = "select_all"
    ARCHIVE = "archive"
    DELETE = "delete"
    NOT_SPAM = "not_spam"
    REPORT_SPAM = "report_spam"
    NEXT = "next"
    NEXT_PAGE = "next_page"
    RETURN_BACK = "return_back"
    SEARCH = "search"
    REPLY_MESSAGE = "reply_message"
    CHECK_LOGIN_YOUTUBE = "CheckLoginYoutube"
    GOOGLE_MAPS_ACTIONS = "google_maps_actions"
    SAVE_LOCATION = "save_location"
    SEARCH_ACTIVITIES = "search_activities"

class JsonManager:
    """Gestionnaire optimisé pour la transformation et validation des structures JSON"""
    
    # Constantes statiques
    GOOGLE_PREFIX = "google"
    YOUTUBE_PREFIX = "youtube"
    
    EXCLUDED_PROCESSES = {
        ProcessTypes.GOOGLE_MAPS_ACTIONS,
        ProcessTypes.SAVE_LOCATION,
        ProcessTypes.SEARCH_ACTIVITIES
    }
    
    ALLOWED_ITEMS_MAP = {
        ProcessTypes.OPEN_INBOX: {
            ProcessTypes.REPORT_SPAM,
            ProcessTypes.DELETE,
            ProcessTypes.ARCHIVE
        },
        ProcessTypes.OPEN_SPAM: {
            ProcessTypes.NOT_SPAM,
            ProcessTypes.DELETE,
            ProcessTypes.REPORT_SPAM
        }
    }
    
    def __init__(self):
        """Initialise le gestionnaire JSON"""
        pass
    
    @staticmethod
    def create_initial_json() -> List[Dict[str, Any]]:
        """
        Crée la structure JSON initiale avec l'action de login
        
        Returns:
            Liste contenant l'action de login initiale
        """
        return [{
            "process": ProcessTypes.LOGIN,
            "sleep": 1
        }]
    
    @staticmethod
    def _extract_widget_data(widget) -> Dict[str, Any]:
        """
        Extrait les données d'un widget de manière structurée
        
        Args:
            widget: Le widget à analyser
            
        Returns:
            Dictionnaire contenant toutes les données extraites
        """
        if not widget:
            return {}
        
        data = {
            "widget": widget,
            "full_state": widget.property("full_state") if hasattr(widget, 'property') else {},
            "children": {}
        }
        
        if not data["full_state"]:
            return data
        
        # Récupérer l'ID caché
        data["hidden_id"] = data["full_state"].get("id")
        data["show_on_init"] = data["full_state"].get("showOnInit", False)
        
        # Extraire les enfants par type
        for child in widget.children():
            child_type = type(child).__name__
            if child_type not in data["children"]:
                data["children"][child_type] = []
            data["children"][child_type].append(child)
        
        return data
    
    @staticmethod
    def _parse_sleep_value(sleep_text: str, default: int = 0) -> int:
        try:
            return ValidationUtils.Parse_Random_Range(sleep_text)
        except (ValueError, AttributeError):
            return default
    
    @staticmethod
    def _process_youtube_action(hidden_id: str, limit_value: int, sleep_value: int) -> List[Dict[str, Any]]:
        """
        Traite une action YouTube spéciale
        
        Args:
            hidden_id: ID de l'action
            limit_value: Valeur de limite
            sleep_value: Valeur de sleep
            
        Returns:
            Liste d'actions pour YouTube
        """
        actions = []
        
        # Ajouter le check de login YouTube uniquement si c'est une action YouTube
        if hidden_id.startswith(JsonManager.YOUTUBE_PREFIX):
            actions.append({
                "process": ProcessTypes.CHECK_LOGIN_YOUTUBE,
                "sleep": random.randint(1, 3)
            })
        
        # Ajouter l'action principale
        actions.append({
            "process": hidden_id,
            "limit": limit_value,
            "sleep": sleep_value
        })
        
        return actions
    
    @staticmethod
    def _process_show_on_init_with_checkbox(widget_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite un widget avec showOnInit=True et checkbox
        
        Args:
            widget_data: Données du widget
            
        Returns:
            Dictionnaire contenant l'action et les sous-processus
        """
        hidden_id = widget_data["hidden_id"]
        
        # Chercher la checkbox
        checkbox = next((child for child in widget_data["children"].get("QCheckBox", [])), None)
        
        if not checkbox:
            return {"action": None, "sub_process": []}
        
        # Action principale
        action = {
            "process": hidden_id,
            "sleep": random.randint(1, 3)
        }
        
        # Gestion de la recherche si checkbox cochée
        sub_process = []
        if checkbox.isChecked():
            qlineedits = widget_data["children"].get("QLineEdit", [])
            search_value = qlineedits[-1].text() if qlineedits else ""
            
            search_action = {
                "process": ProcessTypes.SEARCH,
                "value": search_value
            }
            
            # Ajouter le filtre spam si nécessaire
            if hidden_id == ProcessTypes.OPEN_SPAM:
                search_action["value"] = f"in:spam {search_value}"
            
            sub_process.append(search_action)
        
        return {"action": action, "sub_process": sub_process}
    
    @staticmethod
    def _process_sub_widgets(layout, start_index: int, widget_data: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Traite les sous-widgets récursivement
        
        Args:
            layout: Layout contenant les widgets
            start_index: Index de départ
            widget_data: Données du widget parent
            
        Returns:
            Tuple (sous-processus, nouvel index)
        """
        sub_process = []
        i = start_index
        
        while i < layout.count():
            sub_widget = layout.itemAt(i).widget()
            if not sub_widget:
                break
            
            sub_data = JsonManager._extract_widget_data(sub_widget)
            sub_hidden_id = sub_data.get("hidden_id")
            
            # Arrêter si on rencontre un nouveau widget principal
            if (sub_data.get("show_on_init") or 
                (sub_hidden_id and (sub_hidden_id.startswith(JsonManager.GOOGLE_PREFIX) or 
                                    sub_hidden_id.startswith(JsonManager.YOUTUBE_PREFIX)))):
                break
            
            # Récupérer le sleep
            qlineedits = sub_data["children"].get("QLineEdit", [])
            sleep_text = qlineedits[0].text() if qlineedits else "0"
            wait_process = JsonManager._parse_sleep_value(sleep_text)
            
            # Traiter selon le type d'action
            if sub_hidden_id == ProcessTypes.REPLY_MESSAGE:
                qtextedits = sub_data["children"].get("QTextEdit", [])
                message_text = qtextedits[0].toPlainText() if qtextedits else ""
                
                sub_process.append({
                    "process": sub_hidden_id,
                    "sleep": wait_process,
                    "value": message_text
                })
            else:
                sub_process.append({
                    "process": sub_hidden_id,
                    "sleep": wait_process
                })
            
            i += 1
        
        # Ajouter l'action de retour/next
        combobox = next((child for child in widget_data["children"].get("QComboBox", [])), None)
        action_type = ProcessTypes.RETURN_BACK if combobox and combobox.currentText() == "Return back" else ProcessTypes.NEXT
        
        if sub_process:
            sub_process.append({"process": action_type})
        
        return sub_process, i
    
    @staticmethod
    def _process_special_platform_action(widget_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite les actions spéciales (Google/YouTube)
        
        Args:
            widget_data: Données du widget
            
        Returns:
            Dictionnaire d'action
        """
        hidden_id = widget_data["hidden_id"]
        qlineedits = widget_data["children"].get("QLineEdit", [])
        
        # Récupérer le sleep
        sleep_text = qlineedits[0].text() if qlineedits else "0"
        wait_process = JsonManager._parse_sleep_value(sleep_text)
        
        # Chercher checkbox
        checkbox = next((child for child in widget_data["children"].get("QCheckBox", [])), None)
        
        action = {
            "process": hidden_id,
            "sleep": wait_process
        }
        
        # Ajouter la recherche si checkbox cochée
        if checkbox and checkbox.isChecked():
            search_value = ""
            if len(qlineedits) > 1:
                search_value = qlineedits[1].text()
            elif len(qlineedits) == 1:
                search_value = qlineedits[0].text()
            
            action["search"] = search_value
        
        return action
    
    @staticmethod
    def process_widget_data(scenario_layout: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Traite les données des widgets pour construire le JSON final
        
        Args:
            scenario_layout: Layout contenant les widgets
            
        Returns:
            JSON construit à partir des widgets
        """
        output_json = []
        i = 0
        
        while i < scenario_layout.count():
            widget = scenario_layout.itemAt(i).widget()
            if not widget:
                i += 1
                continue
            
            # Extraire les données du widget
            widget_data = JsonManager._extract_widget_data(widget)
            hidden_id = widget_data.get("hidden_id")
            
            if not hidden_id:
                i += 1
                continue
            
            show_on_init = widget_data.get("show_on_init", False)
            
            # Cas 1: showOnInit=False et pas Google/YouTube
            if not show_on_init and not (hidden_id.startswith(JsonManager.GOOGLE_PREFIX) or 
                                       hidden_id.startswith(JsonManager.YOUTUBE_PREFIX)):
                qlineedits = widget_data["children"].get("QLineEdit", [])
                
                if len(qlineedits) >= 2:
                    limit_value = JsonManager._parse_sleep_value(qlineedits[0].text())
                    sleep_value = JsonManager._parse_sleep_value(qlineedits[1].text())
                    
                    if hidden_id.startswith(JsonManager.YOUTUBE_PREFIX):
                        output_json.extend(
                            JsonManager._process_youtube_action(hidden_id, limit_value, sleep_value)
                        )
                    else:
                        output_json.append({
                            "process": hidden_id,
                            "limit": limit_value,
                            "sleep": sleep_value
                        })
                elif qlineedits:
                    sleep_value = JsonManager._parse_sleep_value(qlineedits[0].text())
                    output_json.append({
                        "process": hidden_id,
                        "sleep": sleep_value
                    })
                
                i += 1
                continue
            
            # Cas 2: showOnInit=True avec checkbox
            if show_on_init and widget_data["children"].get("QCheckBox"):
                result = JsonManager._process_show_on_init_with_checkbox(widget_data)
                
                if result["action"]:
                    output_json.append(result["action"])
                
                # Traiter les sous-widgets
                sub_process, new_i = JsonManager._process_sub_widgets(
                    scenario_layout, i + 1, widget_data
                )
                i = new_i
                
                # Récupérer les valeurs de loop
                qlineedits = widget_data["children"].get("QLineEdit", [])
                limit_loop = JsonManager._parse_sleep_value(
                    qlineedits[0].text() if len(qlineedits) > 1 else "0"
                )
                start_loop = JsonManager._parse_sleep_value(
                    qlineedits[1].text() if len(qlineedits) > 1 else "0"
                )
                
                # Ajouter la loop
                if sub_process:
                    output_json.append({
                        "process": ProcessTypes.LOOP,
                        "check": "is_empty_folder",
                        "limit_loop": limit_loop,
                        "start": start_loop,
                        "sub_process": sub_process
                    })
                
                continue
            
            # Cas 3: showOnInit=True sans checkbox
            if show_on_init and not widget_data["children"].get("QCheckBox"):
                qlineedits = widget_data["children"].get("QLineEdit", [])
                sleep_text = qlineedits[0].text() if qlineedits else "0"
                wait_process = JsonManager._parse_sleep_value(sleep_text)
                
                output_json.append({
                    "process": hidden_id,
                    "sleep": wait_process
                })
                
                i += 1
                continue
            
            # Cas 4: Google/YouTube avec checkbox
            if (hidden_id.startswith(JsonManager.GOOGLE_PREFIX) or 
                hidden_id.startswith(JsonManager.YOUTUBE_PREFIX)):
                action = JsonManager._process_special_platform_action(widget_data)
                output_json.append(action)
                
                i += 1
                continue
            
            i += 1
        
        return output_json
    
    @staticmethod
    def split_json_sections(input_json: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Divise le JSON en sections basées sur open_inbox/open_spam
        
        Args:
            input_json: JSON d'entrée
            
        Returns:
            JSON avec sections séparées
        """
        output_json = []
        current_section = []
        
        def finalize_section():
            """Finalise et ajoute la section courante à l'output"""
            if current_section:
                output_json.extend(current_section)
        
        for element in input_json:
            process_type = element.get("process")
            
            # Ignorer les loops vides
            if process_type == ProcessTypes.LOOP and not element.get("sub_process"):
                continue
            
            # Nouvelle section détectée
            if process_type in {ProcessTypes.OPEN_INBOX, ProcessTypes.OPEN_SPAM}:
                finalize_section()
                current_section = [element]
                continue
            
            # Traitement des loops
            if process_type == ProcessTypes.LOOP:
                sub_process = element.get("sub_process", [])
                allowed_items = JsonManager.ALLOWED_ITEMS_MAP.get(
                    current_section[0].get("process") if current_section else None, 
                    set()
                )
                
                # Filtrer les sous-processus si nécessaire
                has_select_all = any(sp.get("process") == ProcessTypes.SELECT_ALL for sp in sub_process)
                has_allowed_item = any(sp.get("process") in allowed_items for sp in sub_process)
                
                if has_select_all or has_allowed_item:
                    sub_process = [
                        sp for sp in sub_process
                        if sp.get("process") not in {ProcessTypes.RETURN_BACK, ProcessTypes.NEXT}
                    ]
                
                element["sub_process"] = sub_process
                current_section.append(element)
                continue
            
            # Élément normal
            current_section.append(element)
        
        # Finaliser la dernière section
        finalize_section()
        return output_json
    
    @staticmethod
    def handle_last_element(input_json: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Gère les derniers éléments des boucles
        
        Args:
            input_json: JSON d'entrée
            
        Returns:
            JSON avec derniers éléments traités
        """
        output_json = []
        
        for element in input_json:
            process_type = element.get("process")
            
            # Ignorer certains processus
            if process_type in JsonManager.EXCLUDED_PROCESSES:
                continue
            
            # Traitement des boucles
            if process_type == ProcessTypes.LOOP and "sub_process" in element:
                sub_process = element["sub_process"]
                
                if sub_process:
                    last_process = sub_process[-1].get("process")
                    
                    # Cas 1: Dernière action = "next"
                    if last_process == ProcessTypes.NEXT:
                        output_json.append({
                            "process": ProcessTypes.OPEN_MESSAGE,
                            "sleep": random.randint(1, 3)
                        })
                        
                        # Supprimer open_message de la boucle
                        sub_process = [
                            sp for sp in sub_process
                            if sp.get("process") != ProcessTypes.OPEN_MESSAGE
                        ]
                    
                    # Cas 2: Pas d'action finale
                    elif last_process not in {
                        ProcessTypes.DELETE, 
                        ProcessTypes.ARCHIVE, 
                        ProcessTypes.NOT_SPAM, 
                        ProcessTypes.REPORT_SPAM
                    }:
                        # Forcer l'ouverture message par message
                        for sp in sub_process:
                            if sp.get("process") == ProcessTypes.OPEN_MESSAGE:
                                sp["process"] = "OPEN_MESSAGE_ONE_BY_ONE"
                    
                    # Vérifier si besoin d'ajouter next_page
                    has_select_all = any(
                        sp.get("process") == ProcessTypes.SELECT_ALL 
                        for sp in sub_process
                    )
                    has_archive = any(
                        sp.get("process") == ProcessTypes.ARCHIVE 
                        for sp in sub_process
                    )
                    has_next_page = any(
                        sp.get("process") == ProcessTypes.NEXT_PAGE 
                        for sp in sub_process
                    )
                    
                    if has_select_all and not has_archive and not has_next_page:
                        sub_process.append({
                            "process": ProcessTypes.NEXT_PAGE,
                            "sleep": 2
                        })
                
                element["sub_process"] = sub_process
            
            output_json.append(element)
        
        return output_json
    
    @staticmethod
    def modify_json_structure(input_json: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Modifie la structure JSON finale
        
        Args:
            input_json: JSON d'entrée
            
        Returns:
            JSON modifié
        """
        output_json = []
        current_section = []
        found_open_message = False
        
        def finalize_section():
            """Finalise la section courante"""
            if current_section:
                output_json.extend(current_section)
        
        for element in input_json:
            process_type = element.get("process")
            
            if process_type == ProcessTypes.OPEN_MESSAGE:
                found_open_message = True
            
            if process_type == ProcessTypes.LOOP:
                if found_open_message:
                    sub_process = element.get("sub_process", [])
                    if any(sp.get("process") == ProcessTypes.NEXT for sp in sub_process):
                        element.pop("check", None)
                current_section.append(element)
                continue
            
            current_section.append(element)
        
        finalize_section()
        return output_json
    
    @staticmethod
    def save_json_to_file(
        json_data: List[Dict[str, Any]],
        selected_browser: str
    ) -> str:
        """
        Sauvegarde le JSON dans le fichier approprié selon le navigateur
        
        Args:
            json_data: Données JSON à sauvegarder
            selected_browser: "firefox", "chrome", ou autre
            
        Returns:
            "SUCCESS", "SUCCESS_FAMILY", ou "ERROR"
        """
        # Déterminer le répertoire cible
        browser_lower = selected_browser.lower()
        
        if browser_lower == "firefox":
            template_dir = Settings.TEMPLATE_DIRECTORY_FIREFOX
        elif browser_lower == "chrome":
            template_dir = Settings.EXTENTION_EX3
        else:
            template_dir = Settings.TEMPLATE_DIRECTORY_FAMILY_CHROME
        
        traitement_file = os.path.join(template_dir, 'traitement.json')
        
        try:
            # Créer le répertoire si nécessaire
            os.makedirs(template_dir, exist_ok=True)
            
            # Sauvegarder le fichier
            with open(traitement_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            
            # Retourner le statut approprié
            if template_dir == Settings.EXTENTION_EX3:
                return "SUCCESS_FAMILY"
            return "SUCCESS"
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde du fichier {traitement_file}: {e}")
            return "ERROR"
    
    def process_complete_pipeline(
        self, 
        scenario_layout: List[Dict[str, Any]], 
        selected_browser: str
    ) -> str:
        """
        Pipeline complet de traitement des données
        
        Args:
            scenario_layout: Layout des widgets
            selected_browser: Navigateur cible
            
        Returns:
            Statut de l'opération
        """
        try:
            # Étape 1: Traitement des widgets
            json_data = self.process_widget_data(scenario_layout)
            
            # Étape 2: Division en sections
            json_data = self.split_json_sections(json_data)
            
            # Étape 3: Gestion des derniers éléments
            json_data = self.handle_last_element(json_data)
            
            # Étape 4: Modification finale
            json_data = self.modify_json_structure(json_data)
            
            # Étape 5: Sauvegarde
            return self.save_json_to_file(json_data, selected_browser)
            
        except Exception as e:
            return "ERROR"
    



    @staticmethod
    def generate_json_data(scenario_layout: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Génère les données JSON sans les sauvegarder
        
        Args:
            scenario_layout: Layout des widgets
            
        Returns:
            Données JSON générées
        """
        try:
            # Étape 1: Traitement des widgets
            json_data = JsonManager.process_widget_data(scenario_layout)
            
            # Étape 2: Division en sections
            json_data = JsonManager.split_json_sections(json_data)
            
            # Étape 3: Gestion des derniers éléments
            json_data = JsonManager.handle_last_element(json_data)
            
            # Étape 4: Modification finale
            json_data = JsonManager.modify_json_structure(json_data)
            
            return json_data
            
        except Exception:
            return []
        
    @staticmethod
    def process_complete_pipeline(
        scenario_layout: List[Dict[str, Any]], 
        selected_browser: str
    ) -> str:
        """
        Pipeline complet de traitement des données avec sauvegarde
        
        Args:
            scenario_layout: Layout des widgets
            selected_browser: Navigateur cible
            
        Returns:
            Statut de sauvegarde ("SUCCESS", "SUCCESS_FAMILY", ou "ERROR")
        """
        try:
            # Générer les données JSON
            json_data = JsonManager.generate_json_data(scenario_layout)
            
            # Sauvegarder le fichier
            return JsonManager.save_json_to_file(json_data, selected_browser)
            
        except Exception:
            return "ERROR"


# Singleton pour une utilisation globale
json_manager = JsonManager()