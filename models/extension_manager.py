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
except ImportError as e:
    raise ImportError(f"Error importing Settings: {e}")


class ExtensionManager:


    # =========================
    # PUBLIC API
    # =========================

    def create_extension_for_email(
        self,
        email: str,
        password: str,
        host: str,
        port: str,
        user: str,
        passwordP: str,
        recovry: str,
        new_password: str,
        new_recovry: str,
        IDL: str,
        selected_browser: str,
    ) -> None:
        """
        Création complète de l’extension personnalisée
        """

        template_dir = self._get_template_directory(selected_browser)
        email_dir = Path(Settings.BASE_DIRECTORY) / email

        self._prepare_base_directory(email_dir)
        self._copy_template(template_dir, email_dir)

        session = self._read_session()

        js_files = self._build_js_files(
            email=email,
            password=password,
            host=host,
            port=port,
            user=user,
            passwordP=passwordP,
            recovry=recovry,
            new_password=new_password,
            new_recovry=new_recovry,
            IDL=IDL,
            session=session,
        )

        self._apply_js_replacements(email_dir, js_files)
        self._apply_traitement(email_dir)

    def add_pid_to_text_file(
        self,
        pid: str,
        email: str,
        inserted_id: str,
        SESSION_ID: str,
    ) -> None:
        """
        Ajoute un PID unique dans data.txt
        """

        text_file = Path(Settings.BASE_DIRECTORY) / email / "data.txt"
        text_file.parent.mkdir(parents=True, exist_ok=True)

        existing_entries = set()
        if text_file.exists():
            existing_entries = set(text_file.read_text(encoding="utf-8").splitlines())

        entry = f"{pid}:{email}:{SESSION_ID}:{inserted_id}"

        if entry not in existing_entries:
            text_file.write_text(entry + "\n", encoding="utf-8")

    # =========================
    # INTERNAL METHODS
    # =========================

    def _get_template_directory(self, browser: str) -> Path:
        return Path(
            Settings.TEMPLATE_DIRECTORY_FAMILY_FIREFOX
            if browser.lower() == "firefox"
            else Settings.TEMPLATE_DIRECTORY_FAMILY_CHROME
        )

    def _prepare_base_directory(self, email_dir: Path) -> None:
        email_dir.parent.mkdir(parents=True, exist_ok=True)
        if email_dir.exists():
            shutil.rmtree(email_dir)
        email_dir.mkdir()

    def _copy_template(self, template_dir: Path, destination: Path) -> None:
        for item in template_dir.iterdir():
            target = destination / item.name
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
            else:
                shutil.copy2(item, target)

    def _read_session(self) -> str:
        if Path(Settings.SESSION_PATH).exists():
            return Path(Settings.SESSION_PATH).read_text(encoding="utf-8").strip()
        return ""

    # =========================
    # JS FILES LOGIC
    # =========================

    def _build_js_files(self, **kwargs) -> Dict[str, Dict[str, str]]:
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

    def _apply_js_replacements(
        self,
        email_dir: Path,
        js_files: Dict[str, Dict[str, str]],
    ) -> None:
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

    def _apply_traitement(self, email_dir: Path) -> None:
        traitement_file = email_dir / "traitement.json"
        gmail_js_file = email_dir / "gmail_process.js"

        if not traitement_file.exists() or not gmail_js_file.exists():
            return

        try:
            traitement_data = json.loads(traitement_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return

        content = gmail_js_file.read_text(encoding="utf-8", errors="ignore")

        search_map = self._build_search_replacement_map(traitement_data)
        content = self._replace_search_values(content, search_map)
        content = self._replace_reply_messages(traitement_data, content)

        gmail_js_file.write_text(content, encoding="utf-8")

    def _build_search_replacement_map(
        self,
        data: List[Dict[str, Any]],
    ) -> Dict[str, str]:
        return {
            obj["process"]: obj["search"]
            for obj in data
            if obj.get("process", "").startswith("google") and "search" in obj
        }

    def _replace_search_values(
        self,
        content: str,
        search_map: Dict[str, str],
    ) -> str:
        for process, value in search_map.items():
            block = self._extract_full_block(content, process)
            if block and "__search_value__" in block:
                content = content.replace(
                    block,
                    block.replace('"__search_value__"', f'"{value}"')
                )
        return content

    def _extract_full_block(self, content: str, process_key: str):
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

    def _replace_reply_messages(
        self,
        data: List[Dict[str, Any]],
        content: str,
    ) -> str:
        for value in self._collect_reply_messages(data):
            content = content.replace("__reply_message__", value, 1)
        return content

    def _collect_reply_messages(
        self,
        blocks: List[Dict[str, Any]],
    ) -> List[str]:
        results = []
        for block in blocks:
            if block.get("process") == "reply_message":
                results.append(block.get("value", ""))
            if "sub_process" in block:
                results.extend(self._collect_reply_messages(block["sub_process"]))
        return results


# Instance globale
extension_manager = ExtensionManager()
