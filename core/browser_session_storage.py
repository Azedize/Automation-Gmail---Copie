# ==========================================================
# core/browser_session_storage.py
# Gestion du stockage des sessions navigateur avec support multi-PID
# ==========================================================

import os
import sys
import traceback
from typing import List, Dict, Union

# 🔹 Ajouter chemin racine pour imports
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from config import settings
    from utils.validation_utils import ValidationUtils
except ImportError as e:
    print(f"❌ Erreur d'importation dans {__file__}: {e}")


class BrowserSessionStorage:
    """
    ========================================================
    Gestionnaire de stockage pour sessions navigateur
    ========================================================
    
    Gère l'enregistrement des informations de session au format :
    
    CHROME (un seul PID) :
    5000:test@gmail.com:ABC123:77
    
    FIREFOX (plusieurs PID) :
    12540;12844;13000:test@gmail.com:ABC123:77
    
    Structure générale :
    PID(S):EMAIL:SESSION_ID:INSERTED_ID
    
    Où :
    - PID(S) : "5000" (Chrome) ou "12540;12844;13000" (Firefox)
    - EMAIL : adresse email du compte utilisé
    - SESSION_ID : identifiant de session
    - INSERTED_ID : ID d'enregistrement en base
    """
    
    PID_SEPARATOR = ";"  # Séparateur pour multi-PID Firefox
    FIELD_SEPARATOR = ":"  # Séparateur entre les champs
    
    
    @staticmethod
    def create_session_entry(
        pids: Union[int, str, List[int]],
        email: str,
        session_id: str,
        inserted_id: Union[int, str]
    ) -> str:
        """
        ========================================================
        Créer une entrée de session formatée
        ========================================================
        
        Description :
        Crée une chaîne formatée pour le stockage de session
        compatible avec Chrome (mono-PID) et Firefox (multi-PID).
        
        Paramètres :
        - pids : PID ou liste de PID
          * int : 5000 (Chrome) → "5000"
          * str : "5000" ou "12540;12844;13000" (Firefox)
          * List[int] : [12540, 12844, 13000] → "12540;12844;13000"
        
        - email : adresse email utilisateur (ex: test@gmail.com)
        - session_id : identifiant session (ex: ABC123)
        - inserted_id : ID d'enregistrement (ex: 77)
        
        Processus :
        1. Normaliser le paramètre PID en string
        2. Valider l'email et autres champs
        3. Construire la chaîne formatée
        4. Retourner au format : "PID(S):EMAIL:SESSION_ID:INSERTED_ID"
        
        Exemples :
        
        # Chrome - PID seul
        create_session_entry(
            pids=5000,
            email="test@gmail.com",
            session_id="ABC123",
            inserted_id=77
        )
        # Retour : "5000:test@gmail.com:ABC123:77"
        
        # Firefox - Liste de PID
        create_session_entry(
            pids=[12540, 12844, 13000],
            email="test@gmail.com",
            session_id="ABC123",
            inserted_id=77
        )
        # Retour : "12540;12844;13000:test@gmail.com:ABC123:77"
        
        # Firefox - String de PID
        create_session_entry(
            pids="12540;12844;13000",
            email="test@gmail.com",
            session_id="ABC123",
            inserted_id=77
        )
        # Retour : "12540;12844;13000:test@gmail.com:ABC123:77"
        
        Retour :
        - str : Entrée formatée
        - None en cas d'erreur (log ERROR)
        
        Cas particuliers :
        - Pids vide/None → log ERROR, retour None
        - Email invalide → log WARNING
        ========================================================
        """
        try:
            # Normaliser PID en string
            pids_str = BrowserSessionStorage._normalize_pids(pids)
            
            if not pids_str:
                settings.WRITE_LOG_DEV_FILE(
                    "Erreur: PID(s) invalides pour la session",
                    "ERROR"
                )
                return None
            
            # Construire l'entrée
            entry = f"{pids_str}{BrowserSessionStorage.FIELD_SEPARATOR}{email}{BrowserSessionStorage.FIELD_SEPARATOR}{session_id}{BrowserSessionStorage.FIELD_SEPARATOR}{inserted_id}"
            
            settings.WRITE_LOG_DEV_FILE(
                f"✅ Entrée session créée : {entry}",
                "DEBUG"
            )
            
            return entry
        
        except Exception as e:
            settings.WRITE_LOG_DEV_FILE(
                f"Erreur lors de la création de l'entrée session : {e}\n{traceback.format_exc()}",
                "ERROR"
            )
            return None
    
    
    @staticmethod
    def _normalize_pids(pids: Union[int, str, List[int]]) -> str:
        """
        ========================================================
        Normaliser le paramètre PID en string formaté
        ========================================================
        
        Description :
        Convertit différents formats de PID en string normalisé.
        
        Formats acceptés :
        - int : 5000 → "5000"
        - str : "5000" ou "12540;12844;13000" → inchangé
        - List[int] : [12540, 12844, 13000] → "12540;12844;13000"
        
        Processus :
        1. Déterminer le type de pids
        2. Convertir en string formaté
        3. Valider que ce n'est pas vide
        4. Retourner la string normalisée
        
        Cas particuliers :
        - Liste vide [] → retour ""
        - None → retour ""
        - String vide → retour ""
        
        Retour :
        - str : PID(s) formatés
        - "" (string vide) si invalide
        ========================================================
        """
        try:
            if pids is None:
                return ""
            
            # Cas: int
            if isinstance(pids, int):
                if pids > 0:
                    return str(pids)
                return ""
            
            # Cas: str
            if isinstance(pids, str):
                pids = pids.strip()
                if pids and all(c.isdigit() or c == BrowserSessionStorage.PID_SEPARATOR for c in pids):
                    return pids
                return ""
            
            # Cas: List[int]
            if isinstance(pids, list):
                # Filtrer les PID invalides
                valid_pids = [str(p) for p in pids if isinstance(p, int) and p > 0]
                
                if valid_pids:
                    return BrowserSessionStorage.PID_SEPARATOR.join(valid_pids)
                return ""
            
            # Type non reconnu
            return ""
        
        except Exception as e:
            settings.WRITE_LOG_DEV_FILE(
                f"Erreur lors de la normalisation des PID : {e}",
                "ERROR"
            )
            return ""
    
    
    @staticmethod
    def parse_session_entry(entry: str) -> Dict:
        """
        ========================================================
        Parser une entrée de session formatée
        ========================================================
        
        Description :
        Extrait les informations d'une entrée de session stockée.
        
        Format attendu : PID(S):EMAIL:SESSION_ID:INSERTED_ID
        
        Exemples :
        
        # Chrome - PID seul
        "5000:test@gmail.com:ABC123:77"
        # Retour : {
        #   'pids': [5000],
        #   'email': 'test@gmail.com',
        #   'session_id': 'ABC123',
        #   'inserted_id': 77,
        #   'is_firefox': False,
        #   'is_valid': True
        # }
        
        # Firefox - Multi-PID
        "12540;12844;13000:test@gmail.com:ABC123:77"
        # Retour : {
        #   'pids': [12540, 12844, 13000],
        #   'email': 'test@gmail.com',
        #   'session_id': 'ABC123',
        #   'inserted_id': 77,
        #   'is_firefox': True,
        #   'is_valid': True
        # }
        
        Processus :
        1. Vérifier que l'entrée n'est pas vide
        2. Splitter par FIELD_SEPARATOR (":") en max 4 parties
        3. Extraire les champs : PID(s), email, session_id, inserted_id
        4. Parser les PID (détecter ";" pour multi-PID)
        5. Valider les données
        6. Retourner dictionnaire structuré
        
        Retour :
        - Dict contenant :
          * pids (List[int]) : liste des PID
          * email (str) : email utilisateur
          * session_id (str) : identifiant session
          * inserted_id (int) : ID d'enregistrement
          * is_firefox (bool) : True si multi-PID détecté
          * is_valid (bool) : True si format valide
          * error (str, optional) : message d'erreur si invalide
        
        Cas d'erreur :
        - Format invalide → is_valid=False, error message
        - Nombre de champs incorrect → erreur parsing
        ========================================================
        """
        result = {
            'pids': [],
            'email': None,
            'session_id': None,
            'inserted_id': None,
            'is_firefox': False,
            'is_valid': False,
            'error': None
        }
        
        try:
            if not entry or not isinstance(entry, str):
                result['error'] = "Entrée invalide ou vide"
                return result
            
            entry = entry.strip()
            
            # Splitter par FIELD_SEPARATOR (max 4 parties)
            parts = entry.split(BrowserSessionStorage.FIELD_SEPARATOR, 3)
            
            if len(parts) != 4:
                result['error'] = f"Nombre de champs incorrect (attendu 4, reçu {len(parts)})"
                return result
            
            pids_str, email, session_id, inserted_id_str = parts
            
            # Parser les PID
            if BrowserSessionStorage.PID_SEPARATOR in pids_str:
                # Multi-PID Firefox
                result['is_firefox'] = True
                try:
                    result['pids'] = [int(p) for p in pids_str.split(BrowserSessionStorage.PID_SEPARATOR) if p.strip()]
                except ValueError:
                    result['error'] = f"PID Firefox invalides : {pids_str}"
                    return result
            else:
                # Mono-PID Chrome
                result['is_firefox'] = False
                try:
                    result['pids'] = [int(pids_str.strip())]
                except ValueError:
                    result['error'] = f"PID Chrome invalide : {pids_str}"
                    return result
            
            # Valider les autres champs
            if not result['pids']:
                result['error'] = "Aucun PID valide extrait"
                return result
            
            if not email:
                result['error'] = "Email vide"
                return result
            
            if not session_id:
                result['error'] = "Session ID vide"
                return result
            
            try:
                result['inserted_id'] = int(inserted_id_str)
            except ValueError:
                result['error'] = f"Inserted ID invalide : {inserted_id_str}"
                return result
            
            result['email'] = email
            result['session_id'] = session_id
            result['is_valid'] = True
            
            return result
        
        except Exception as e:
            result['error'] = f"Exception parsing : {e}"
            settings.WRITE_LOG_DEV_FILE(
                f"Erreur lors du parsing de l'entrée session : {e}\n{traceback.format_exc()}",
                "ERROR"
            )
            return result
    
    
    @staticmethod
    def save_to_file(entry: str, file_path: str) -> bool:
        """
        ========================================================
        Sauvegarder une entrée session dans un fichier
        ========================================================
        
        Description :
        Écrit une entrée de session dans un fichier texte.
        
        Paramètres :
        - entry : entrée formatée (ex: "5000:test@gmail.com:ABC123:77")
        - file_path : chemin du fichier de destination
        
        Processus :
        1. Créer les répertoires parents si nécessaires
        2. Ouvrir le fichier en mode écriture
        3. Écrire l'entrée
        4. Fermer le fichier
        5. Log succès
        
        Retour :
        - True : succès
        - False : erreur
        ========================================================
        """
        try:
            # Créer répertoires parents
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Écrire l'entrée
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(entry)
            
            settings.WRITE_LOG_DEV_FILE(
                f"✅ Entrée session sauvegardée : {file_path}",
                "INFO"
            )
            
            return True
        
        except Exception as e:
            settings.WRITE_LOG_DEV_FILE(
                f"Erreur lors de la sauvegarde session : {e}\n{traceback.format_exc()}",
                "ERROR"
            )
            return False
    
    
    @staticmethod
    def load_from_file(file_path: str) -> Union[str, None]:
        """
        ========================================================
        Charger une entrée session depuis un fichier
        ========================================================
        
        Description :
        Lit une entrée de session depuis un fichier texte.
        
        Paramètres :
        - file_path : chemin du fichier source
        
        Retour :
        - str : contenu du fichier (entrée session)
        - None : fichier inexistant ou erreur lecture
        ========================================================
        """
        try:
            if not ValidationUtils.path_exists(file_path):
                settings.WRITE_LOG_DEV_FILE(
                    f"Fichier session inexistant : {file_path}",
                    "WARNING"
                )
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                entry = f.read().strip()
            
            if not entry:
                settings.WRITE_LOG_DEV_FILE(
                    "Fichier session vide",
                    "WARNING"
                )
                return None
            
            return entry
        
        except Exception as e:
            settings.WRITE_LOG_DEV_FILE(
                f"Erreur lors de la lecture session : {e}\n{traceback.format_exc()}",
                "ERROR"
            )
            return None


# ==========================================================
# Instance globale
# ==========================================================
BrowserSessionStorage = BrowserSessionStorage()
