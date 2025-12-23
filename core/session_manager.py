# core/session_manager.py
import os
import json
import datetime
import pytz
from typing import Dict, Optional
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from core.encryption import EncryptionService
    from config import settings
except ImportError as e:
    print(f"Error importing modules: {e}")


class SessionManager:
    def __init__(self):
        self.session_path = settings.SESSION_PATH
        self.encryption_service = EncryptionService
        self.key = settings.KEY

    def check_session(self) -> Dict:
        session_info = {
            "valid": False,
            "username": None,
            "date": None,
            "p_entity": None,
            "error": None
        }

        print(f"[INFO] Chemin du fichier session : {self.session_path}")

        if not os.path.exists(self.session_path):
            print("[AVERTISSEMENT SESSION] ❌ Le fichier session.txt n'existe pas")
            session_info["error"] = "FileNotFound"
            return session_info

        print("[INFO] Le fichier session.txt existe ✅")

        try:
            with open(self.session_path, "r", encoding="utf-8") as f:
                encrypted = f.read().strip()

            print(f"[INFO] Contenu chiffré lu :\n'{encrypted}'")
            print(f"[INFO] Longueur du contenu chiffré : {len(encrypted)} caractères")

            if not encrypted:
                print("[AVERTISSEMENT SESSION] Le fichier session.txt est vide ❌")
                session_info["error"] = "EmptyFile"
                return session_info

            # Tentative de déchiffrement
            try:
                decrypted = self.encryption_service.decrypt_message(encrypted, self.key)
                print(f"[INFO] Contenu déchiffré complet :\n'{decrypted}'")
                print(f"[INFO] Longueur du contenu déchiffré : {len(decrypted)} caractères")
            except Exception as e:
                print(f"[ERREUR DECHIFFREMENT] Erreur lors du déchiffrement : {e}")
                session_info["error"] = f"DecryptError: {e}"
                return session_info

            # Analyse du contenu déchiffré
            parts = decrypted.split("::", 2)
            print(f"[INFO] Contenu découpé en {len(parts)} parties : {parts}")

            if len(parts) != 3:
                print("[ERREUR FORMAT SESSION] ❌ Format invalide (attendu : username::date::p_entity)")
                print(f"[DEBUG] Contenu déchiffré complet : '{decrypted}'")
                session_info["error"] = "InvalidFormat"
                return session_info

            username, date_str, p_entity = [p.strip() for p in parts]

            print(f"[INFO] Nom d'utilisateur : '{username}'")
            print(f"[INFO] Date de session (date_str) : '{date_str}'")
            print(f"[INFO] p_entity : '{p_entity}'")

            try:
                tz = pytz.timezone("Africa/Casablanca")
                print(f"[DEBUG] Conversion de la date '{date_str}' en datetime...")
                last_session = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                last_session = tz.localize(last_session)

                now = datetime.datetime.now(tz)
                print(f"[INFO] Date de la session : {last_session}")
                print(f"[INFO] Date actuelle : {now}")

                if (now - last_session) < datetime.timedelta(days=2):
                    session_info.update({
                        "valid": True,
                        "username": username,
                        "date": last_session,
                        "p_entity": p_entity
                    })
                    print(f"[SESSION] ✅ Session valide pour l'utilisateur '{username}' (p_entity = {p_entity})")
                else:
                    print("[SESSION EXPIRÉE] ⌛ La session a expiré depuis plus de 2 jours")
                    session_info["error"] = "Expired"
            except ValueError as e:
                print(f"[ERREUR FORMAT DATE] ❌ Format de date invalide : {e}")
                print(f"[DEBUG] Contenu complet de date_str : '{date_str}'")
                session_info["error"] = f"InvalidDateFormat: {e}"

        except Exception as e:
            print(f"[ERREUR LECTURE SESSION] ❌ Exception lors de la lecture du fichier : {e}")
            session_info["error"] = f"FileReadError: {e}"

        return session_info

    def create_session(self, username: str, p_entity: str) -> bool:
        try:
            casablanca_time = datetime.datetime.now(pytz.timezone("Africa/Casablanca"))
            session_data = f"{username}::{casablanca_time.strftime('%Y-%m-%d %H:%M:%S')}::{p_entity}"
            
            print(f"[INFO] Création de session avec données : {session_data}")
            encrypted = self.encryption_service.encrypt_message(session_data, self.key)
            print(f"[INFO] Données chiffrées créées (longueur: {len(encrypted)})")
            
            os.makedirs(os.path.dirname(self.session_path), exist_ok=True)
            with open(self.session_path, "w", encoding="utf-8") as f:
                f.write(encrypted)
            
            print(f"[SESSION] ✅ Session créée avec succès pour '{username}'")
            return True
        except Exception as e:
            print(f"[ERREUR CRÉATION SESSION] ❌ Erreur lors de la création de la session : {e}")
            return False

    def clear_session(self):
        if os.path.exists(self.session_path):
            try:
                os.remove(self.session_path)
                print("[SESSION] ✅ Session supprimée avec succès")
            except Exception as e:
                print(f"[ERREUR SUPPRESSION SESSION] ❌ Erreur lors de la suppression : {e}")
        else:
            print("[SESSION] ℹ️ Aucune session à supprimer (fichier non trouvé)")

    def validate_session_with_api(self, username: str, p_entity: str) -> Dict:
        """
        Valide la session via l'API (optionnel)
        
        Args:
            username (str): Nom d'utilisateur
            p_entity (str): Entité
            
        Returns:
            dict: Résultat de la validation API
        """
        # Cette méthode peut être implémentée si vous avez besoin
        # de valider la session avec le serveur API
        print(f"[API VALIDATION] Validation de la session pour '{username}'...")
        # Implémentez ici votre logique API
        return {"valid": True, "message": "Session validée par API"}

    def get_session_summary(self) -> str:
        """
        Retourne un résumé textuel de la session
        
        Returns:
            str: Résumé de la session
        """
        session_info = self.check_session()
        
        if session_info["valid"]:
            return f"Session active - Utilisateur: {session_info['username']}, " \
                   f"Date: {session_info['date'].strftime('%Y-%m-%d %H:%M:%S')}, " \
                   f"Entité: {session_info['p_entity']}"
        elif session_info["error"]:
            return f"Session invalide - Erreur: {session_info['error']}"
        else:
            return "Aucune session active"
        



SessionManager= SessionManager()