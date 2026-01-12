import sys
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from config import Settings
    from Log import DevLogger
except ImportError as e:
    raise ImportError(f"Error importing Settings: {e}")


class ExtensionManager:


    # =========================
    # PUBLIC API
    # =========================
    @staticmethod
    def create_extension_for_email(    email: str,   password: str, host: str, port: str,  user: str,  passwordP: str, recovry: str,  new_password: str, new_recovry: str,   IDL: str,    selected_browser: str):
        template_dir = ExtensionManager._get_template_directory(selected_browser)
        email_dir = Path(Settings.EXTENTIONS_DIR_FIREFOX if selected_browser.lower() == "firefox" else Settings.EXTENSIONS_DIR_FAMILY_CHROME) / email

        ExtensionManager._prepare_base_directory(email_dir)
        ExtensionManager._copy_template(template_dir, email_dir)

        session = ExtensionManager._read_session()

        js_files = ExtensionManager._build_js_files( email=email, password=password,host=host, port=port,   user=user, passwordP=passwordP,  recovry=recovry, new_password=new_password,  new_recovry=new_recovry,  IDL=IDL,  session=session,  )

        ExtensionManager._apply_js_replacements(email_dir, js_files)
        ExtensionManager._apply_traitement(email_dir)

    # @staticmethod
    # def add_pid_to_text_file( pid: str, Path_DiR: str, email: str, SESSION_ID: str, browser: str):
    #     try:
            
    #         print("🚦 [START] Démarrage de add_pid_to_text_file")
    #         print(f"🧭 [INPUT] browser = {browser}")
    #         print(f"🆔 [INPUT] pid = {pid}")
    #         print(f"🔐 [INPUT] SESSION_ID = {SESSION_ID}")
    #         print(f"📧 [INPUT] email = {email}")

    #         # ------------------ Sélection du chemin ------------------
    #         if browser.lower() == "chrome":
    #             print("🌐 [MODE] Navigateur Chrome détecté")
    #             text_file = Path(Settings.EXTENTION_EX3) / "data.txt"
    #             entry = f"{pid}:{SESSION_ID}"
    #         else:
    #             print("🗂️ [MODE] Navigateur non-Chrome détecté")
    #             text_file = Path(Path_DiR) / email / "data.txt"
    #             print(f"📁 [PATH] Création du dossier : {text_file.parent}")
    #             text_file.parent.mkdir(parents=True, exist_ok=True)
    #             entry = f"{pid}:{email}:{SESSION_ID}"

    #         print(f"📄 [FILE] Chemin du fichier : {text_file}")
    #         print(f"✏️ [WRITE] Contenu à écrire : {entry}")

    #         # ------------------ Nettoyage du fichier ------------------
    #         print("🧹 [CLEAN] Vidage du contenu du fichier")
    #         text_file.write_text("", encoding="utf-8")

    #         # ------------------ Écriture finale ------------------
    #         print("🖊️ [SAVE] Écriture des données dans le fichier")
    #         with open(text_file, "a", encoding="utf-8") as f:
    #             f.write(entry + "\n")

    #         print("🎉 [SUCCESS] Écriture terminée avec succès")
    #         print("🏁 [END] Fonction exécutée sans erreur")

    #     except Exception as e:
    #         print("🔥 [ERROR] Une erreur est survenue !")
    #         print(f"❗ [DETAILS] {type(e).__name__} : {e}")



    # =========================
    # INTERNAL METHODS
    # =========================
    @staticmethod
    def _get_template_directory( browser: str) -> Path:
        return Path(
            Settings.TEMPLATE_DIRECTORY_FIREFOX
            if browser.lower() == "firefox"
            else Settings.TEMPLATE_DIRECTORY_FAMILY_CHROME
        )
    

    @staticmethod
    def _prepare_base_directory( email_dir: Path) -> None:
        email_dir.parent.mkdir(parents=True, exist_ok=True)
        if email_dir.exists():
            shutil.rmtree(email_dir)
        email_dir.mkdir()



    @staticmethod
    def _copy_template( template_dir: Path, destination: Path) -> None:
        for item in template_dir.iterdir():
            target = destination / item.name
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
            else:
                shutil.copy2(item, target)


    @staticmethod
    def _read_session() -> str:
        if Path(Settings.SESSION_PATH).exists():
            return Path(Settings.SESSION_PATH).read_text(encoding="utf-8").strip()
        return ""

    # =========================
    # JS FILES LOGIC
    # =========================

    @staticmethod
    def _build_js_files(**kwargs) -> Dict[str, Dict[str, str]]:
        """
        Construction dynamique des remplacements JS
        """

        return {
            "actions.js": {
                "__IDL__": kwargs["IDL"],
                "__email__": kwargs["email"],
                "___session_user__": kwargs["session"],

            },
            "background.js": {
                "__host__": kwargs["host"],
                "__port__": kwargs["port"],
                "__user__": kwargs["user"],
                "__pass__": kwargs["passwordP"],
                "__IDL__": kwargs["IDL"],
                "__email__": kwargs["email"],
            },
            "gmail_process.js": {
                "__email__": kwargs["email"],
                "__password__": kwargs["password"],
                "__recovry__": kwargs["recovry"],
                "__newPassword__": kwargs["new_password"],
                "__newRecovry__": kwargs["new_recovry"],
            },
            "ReportingActions.js": {
                "__IDL__": kwargs["IDL"],
                "__email__": kwargs["email"],
            },
        }
    


    @staticmethod
    def _apply_js_replacements(  email_dir: Path,   js_files: Dict[str, Dict[str, str]] ):
        for js_file, replacements in js_files.items():
            file_path = email_dir / js_file
            if not file_path.exists():
                continue

            content = file_path.read_text(encoding="utf-8", errors="ignore")

            for placeholder, value in replacements.items():
                content = content.replace(placeholder, str(value))

            file_path.write_text(content, encoding="utf-8")

    # =========================
    # TRAITEMENT LOGIC
    # =========================

    @staticmethod
    def _apply_traitement(email_dir: Path) -> None:
        traitement_file = email_dir / "traitement.json"
        gmail_js_file = email_dir / "gmail_process.js"

        if not traitement_file.exists() or not gmail_js_file.exists():
            return

        try:
            traitement_data = json.loads(traitement_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return

        content = gmail_js_file.read_text(encoding="utf-8", errors="ignore")

        search_map = ExtensionManager._build_search_replacement_map(traitement_data)
        content = ExtensionManager._replace_search_values(content, search_map)
        content = ExtensionManager._replace_reply_messages(traitement_data, content)

        gmail_js_file.write_text(content, encoding="utf-8")


    @staticmethod
    def _build_search_replacement_map(
        data: List[Dict[str, Any]],
    ) -> Dict[str, str]:
        return {
            obj["process"]: obj["search"]
            for obj in data
            if obj.get("process", "").startswith("google") and "search" in obj
        }

    @staticmethod
    def _replace_search_values(
        content: str,
        search_map: Dict[str, str],
    ) -> str:
        for process, value in search_map.items():
            block = ExtensionManager._extract_full_block(content, process)
            if block and "__search_value__" in block:
                content = content.replace(
                    block,
                    block.replace('"__search_value__"', f'"{value}"')
                )
        return content
    
    @staticmethod
    def _extract_full_block( content: str, process_key: str):
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

    @staticmethod
    def _replace_reply_messages(
        data: List[Dict[str, Any]],
        content: str,
    ) -> str:
        for value in ExtensionManager._collect_reply_messages(data):
            content = content.replace("__reply_message__", value, 1)
        return content

    @staticmethod
    def _collect_reply_messages(
        data: List[Dict[str, Any]],
        blocks: List[Dict[str, Any]],
    ) -> List[str]:
        results = []
        for block in blocks:
            if block.get("process") == "reply_message":
                results.append(block.get("value", ""))
            if "sub_process" in block:
                results.extend(ExtensionManager._collect_reply_messages(block["sub_process"]))
        return results




extension_manager = ExtensionManager()
