import sys
import json
import shutil
from pathlib import Path
import os

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from config import Settings
except ImportError as e:
    raise ImportError(f"Error importing Settings: {e}")



class ExtensionManager:

    # =========================
    # PUBLIC API
    # =========================
    @staticmethod
    def create_extension_for_email( email, password, host, port, user, passwordP, recovry,  new_password, new_recovry, IDL, selected_browser ):
        # print("🚀 [START] create_extension_for_email")
        # print(f"🌐 Browser sélectionné : {selected_browser}")
        # print(f"📧 Email : {email}")
        # print(f"🆔 IDL : {IDL}")

        # 1️⃣ Choix du template
        template_directory = (
            Settings.TEMPLATE_DIRECTORY_FIREFOX
            if selected_browser.lower() == "firefox"
            else Settings.TEMPLATE_DIRECTORY_FAMILY_CHROME
        )

        base_directory = (
            Settings.FOLDER_EXTENTIONS_FIREFOX
            if selected_browser.lower() == "firefox"
            else Settings.FOLDER_EXTENTIONS_FAMILY_CHROME
        )

        # print(f"📁 Template directory : {template_directory}")
        # print(f"📁 Base directory : {base_directory}")

        if not os.path.exists(template_directory):
            # print("❌ [ERROR] Template directory introuvable")
            return

        # 2️⃣ Création dossier email
        email_folder = os.path.join(base_directory, email)
        # print(f"📂 Email folder : {email_folder}")

        if os.path.exists(email_folder):
            # print("♻️ Suppression ancien dossier email")
            shutil.rmtree(email_folder)

        os.makedirs(email_folder, exist_ok=True)
        # print("✅ Dossier email créé")

        # 3️⃣ Copie du template
        # print("📦 Copie du template...")
        for item in os.listdir(template_directory):
            src = os.path.join(template_directory, item)
            dst = os.path.join(email_folder, item)

            try:
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                    # print(f"📁 Copied folder : {item}")
                else:
                    shutil.copy2(src, dst)
                    # print(f"📄 Copied file : {item}")
            except Exception as e:
                print(f"❌ Erreur copie {item} : {e}")

        # 4️⃣ Remplacements JS
        # print("✏️ Remplacement actions.js")
        ExtensionManager._replace_actions_js(email_folder, IDL, email)

        # print("✏️ Remplacement background.js")
        ExtensionManager._replace_background_js(
            email_folder, host, port, user, passwordP, IDL, email
        )

        # print("✏️ Remplacement gmail_process.js")
        ExtensionManager._replace_gmail_process_js(
            email_folder, email, password, recovry, new_password, new_recovry
        )

        # print("✏️ Remplacement ReportingActions.js")
        ExtensionManager._replace_reporting_actions_js(email_folder, IDL, email)

        # 5️⃣ Traitement JSON
        # print("🧠 Lancement traitement.json")
        ExtensionManager.modifier_extension_par_traitement(email_folder)

        # print("✅ [END] Extension créée avec succès\n")

    # =========================
    # JS REPLACEMENTS
    # =========================

    @staticmethod
    def _replace_actions_js(email_folder, IDL, email):
        path = os.path.join(email_folder, "actions.js")
        # print(f"🔎 actions.js : {path}")

        if not os.path.exists(path):
            # print("⚠️ actions.js introuvable")
            return

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        content = content.replace("__IDL__", IDL).replace("__email__", email)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        # print("✅ actions.js modifié")

    
    
    
    
    @staticmethod
    def _replace_background_js(email_folder, host, port, user, passwordP, IDL, email):
        path = os.path.join(email_folder, "background.js")
        # print(f"🔎 background.js : {path}")

        if not os.path.exists(path):
            # print("⚠️ background.js introuvable")
            return

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        content = (
            content.replace("__host__", host)
            .replace("__port__", port)
            .replace("__user__", user)
            .replace("__pass__", passwordP)
            .replace("__IDL__", IDL)
            .replace("__email__", email)
        )

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        # print("✅ background.js modifié")

    
    
    
    
    @staticmethod
    def _replace_gmail_process_js(email_folder, email, password, recovry, new_password, new_recovry):
        path = os.path.join(email_folder, "gmail_process.js")
        # print(f"🔎 gmail_process.js : {path}")

        if not os.path.exists(path):
            # print("⚠️ gmail_process.js introuvable")
            return

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        content = (
            content.replace("__email__", email)
            .replace("__password__", password)
            .replace("__recovry__", recovry)
            .replace("__newPassword__", new_password)
            .replace("__newRecovry__", new_recovry)
        )

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        # print("✅ gmail_process.js modifié")

    
    
    
    
    @staticmethod
    def _replace_reporting_actions_js(email_folder, IDL, email):
        path = os.path.join(email_folder, "ReportingActions.js")
        # print(f"🔎 ReportingActions.js : {path}")

        if not os.path.exists(path):
            # print("⚠️ ReportingActions.js introuvable")
            return

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        content = content.replace("__IDL__", IDL).replace("__email__", email)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        # print("✅ ReportingActions.js modifié")

    
    
    
    
    # =========================
    # TRAITEMENT JSON
    # =========================

    
    
    
    
    
    @staticmethod
    def modifier_extension_par_traitement(email_folder):
        traitement_path = os.path.join(email_folder, "traitement.json")
        gmail_process_path = os.path.join(email_folder, "gmail_process.js")

        # print("📂 Vérification traitement.json & gmail_process.js")

        if not os.path.exists(traitement_path):
            # print("❌ traitement.json introuvable")
            return

        if not os.path.exists(gmail_process_path):
            # print("❌ gmail_process.js introuvable")
            return

        with open(traitement_path, "r", encoding="utf-8") as f:
            traitement_data = json.load(f)

        # print("📘 traitement.json chargé")

        remplacement_dict = {}
        for obj in traitement_data:
            process_name = obj.get("process", "")
            if process_name.startswith("google") and "search" in obj:
                remplacement_dict[process_name] = obj["search"]
                # print(f"🔁 Process détecté : {process_name} → {obj['search']}")

        if not remplacement_dict:
            # print("⚠️ Aucun google search trouvé")
            return

        with open(gmail_process_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        for process_key, search_value in remplacement_dict.items():
            # print(f"🧩 Traitement bloc : {process_key}")
            bloc = ExtensionManager.extraire_bloc_complet(content, process_key)

            if not bloc:
                print(f"⚠️ Bloc {process_key} introuvable")
                continue

            if "__search_value__" not in bloc:
                # print(f"⚠️ __search_value__ absent dans {process_key}")
                continue

            bloc_modifie = bloc.replace('"__search_value__"', f'"{search_value}"')
            content = content.replace(bloc, bloc_modifie)
            # print(f"✅ Bloc {process_key} modifié")

        with open(gmail_process_path, "w", encoding="utf-8") as f:
            f.write(content)

        # print("💾 gmail_process.js sauvegardé avec succès")

    
    
    
    
    
    
    
    
    
    
    
    
    @staticmethod
    def extraire_bloc_complet(content, process_key):
        marker = f'"{process_key}": ['
        start = content.find(marker)
        if start == -1:
            return None

        index = start + len(marker)
        depth = 1

        while index < len(content):
            if content[index] == "[":
                depth += 1
            elif content[index] == "]":
                depth -= 1
                if depth == 0:
                    return content[start:index + 1]
            index += 1

        return None




extension_manager = ExtensionManager()
