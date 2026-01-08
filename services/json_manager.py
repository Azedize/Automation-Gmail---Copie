import json
import random
import os
from PyQt6.QtWidgets import QCheckBox, QLineEdit, QComboBox
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from config import Settings
except ImportError as e:
    print(f"Error importing modules: {e}")


class JsonManager:

    GOOGLE_PREFIX = "google"
    YOUTUBE_PREFIX = "youtube"

    EXCLUDED_PROCESSES = {
        "google_maps_actions",
        "save_location",
        "search_activities"
    }

    ALLOWED_ITEMS = {
        "open_inbox": ["report_spam", "delete", "archive"],
        "open_spam": ["not_spam", "delete", "report_spam"]
    }

    # ==============================
    # Utils
    # ==============================
    @staticmethod
    def parse_random_range(text: str) -> int:
        try:
            if ',' in text:
                a, b = map(int, text.split(','))
                return random.randint(a, b)
            return int(text)
        except Exception:
            return 0

    @staticmethod
    def get_children(widget, cls):
        return [c for c in widget.children() if isinstance(c, cls)]

    # ==============================
    # MAIN PIPELINE
    # ==============================
    @staticmethod
    def generate(scenario_layout, selected_browser: str):

        output_json = [{"process": "login", "sleep": 1}]

        if scenario_layout.count() == 0:
            return []

        i = 0
        while i < scenario_layout.count():
            widget = scenario_layout.itemAt(i).widget()
            if not widget:
                i += 1
                continue

            full_state = widget.property("full_state") or {}
            hidden_id = full_state.get("id")
            show_on_init = full_state.get("showOnInit", False)

            checkbox = next(iter(JsonManager.get_children(widget, QCheckBox)), None)
            qlineedits = JsonManager.get_children(widget, QLineEdit)

            # ==========================
            # CASE 1: NORMAL ACTION (NO showOnInit, NO google/youtube)
            # ==========================
            if (
                hidden_id
                and not show_on_init
                and not hidden_id.startswith((JsonManager.GOOGLE_PREFIX, JsonManager.YOUTUBE_PREFIX))
            ):
                if len(qlineedits) > 1:
                    limit = JsonManager.parse_random_range(qlineedits[0].text())
                    sleep = JsonManager.parse_random_range(qlineedits[1].text())
                    output_json.append({
                        "process": hidden_id,
                        "limit": limit,
                        "sleep": sleep
                    })
                elif qlineedits:
                    sleep = JsonManager.parse_random_range(qlineedits[0].text())
                    output_json.append({
                        "process": hidden_id,
                        "sleep": sleep
                    })
                i += 1
                continue

            # ==========================
            # CASE 2: YOUTUBE ACTION
            # ==========================
            if (
                hidden_id
                and not show_on_init
                and hidden_id.startswith(JsonManager.YOUTUBE_PREFIX)
            ):
                limit = JsonManager.parse_random_range(qlineedits[0].text()) if len(qlineedits) > 1 else 0
                sleep = JsonManager.parse_random_range(qlineedits[1].text()) if len(qlineedits) > 1 else 0

                output_json.append({
                    "process": "CheckLoginYoutube",
                    "sleep": random.randint(1, 3)
                })
                output_json.append({
                    "process": hidden_id,
                    "limit": limit,
                    "sleep": sleep
                })
                i += 1
                continue

            # ==========================
            # CASE 3: showOnInit + checkbox (Inbox / Spam)
            # ==========================
            if show_on_init and checkbox:
                output_json.append({
                    "process": hidden_id,
                    "sleep": random.randint(1, 3)
                })

                if checkbox.isChecked():
                    search_value = qlineedits[-1].text() if qlineedits else ""
                    if hidden_id == "open_spam":
                        search_value = f"in:spam {search_value}"
                    output_json.append({
                        "process": "search",
                        "value": search_value
                    })

                sub_process = []
                i += 1

                while i < scenario_layout.count():
                    sub_widget = scenario_layout.itemAt(i).widget()
                    if not sub_widget:
                        break

                    sub_state = sub_widget.property("full_state") or {}
                    sub_id = sub_state.get("id")

                    if sub_state.get("showOnInit") or sub_id.startswith((JsonManager.GOOGLE_PREFIX, JsonManager.YOUTUBE_PREFIX)):
                        break

                    sleep_txt = next((c.text() for c in JsonManager.get_children(sub_widget, QLineEdit)), "0")
                    sleep = JsonManager.parse_random_range(sleep_txt)

                    sub_process.append({
                        "process": sub_id,
                        "sleep": sleep
                    })
                    i += 1

                combo = next(iter(JsonManager.get_children(widget, QComboBox)), None)
                action = "return_back" if combo and combo.currentText() == "Return back" else "next"
                if sub_process:
                    sub_process.append({"process": action})

                limit_loop = JsonManager.parse_random_range(qlineedits[0].text()) if len(qlineedits) > 1 else 0
                start_loop = JsonManager.parse_random_range(qlineedits[1].text()) if len(qlineedits) > 1 else 0

                output_json.append({
                    "process": "loop",
                    "check": "is_empty_folder",
                    "limit_loop": limit_loop,
                    "start": start_loop,
                    "sub_process": sub_process
                })
                continue

            # ==========================
            # CASE 4: showOnInit WITHOUT checkbox
            # ==========================
            if show_on_init and not checkbox:
                sleep = JsonManager.parse_random_range(qlineedits[0].text()) if qlineedits else 0
                output_json.append({
                    "process": hidden_id,
                    "sleep": sleep
                })
                i += 1
                continue

            # ==========================
            # CASE 5: GOOGLE / YOUTUBE with search
            # ==========================
            if hidden_id and hidden_id.startswith((JsonManager.GOOGLE_PREFIX, JsonManager.YOUTUBE_PREFIX)):
                sleep = JsonManager.parse_random_range(qlineedits[0].text()) if qlineedits else 0
                action = {"process": hidden_id, "sleep": sleep}

                if checkbox and checkbox.isChecked():
                    action["search"] = qlineedits[1].text() if len(qlineedits) > 1 else qlineedits[0].text()

                output_json.append(action)
                i += 1
                continue

            i += 1

        # ==============================
        # POST PROCESSING
        # ==============================
        output_json = JsonManager.process_and_split_json(output_json)
        output_json = JsonManager.process_and_handle_last_element(output_json)
        output_json = JsonManager.process_and_modify_json(output_json)

        return output_json

    # ==============================
    # SPLIT JSON
    # ==============================
    @staticmethod
    def process_and_split_json( input_json):
        output, section, current = [], [], None

        def flush():
            if section:
                output.extend(section)

        for el in input_json:
            if el.get("process") == "loop" and not el.get("sub_process"):
                continue

            if el.get("process") in ("open_inbox", "open_spam"):
                flush()
                section = [el]
                current = el["process"]
                continue

            if el.get("process") == "loop":
                allowed = JsonManager.ALLOWED_ITEMS.get(current, [])
                sub = el["sub_process"]

                if any(s["process"] == "select_all" for s in sub) or any(s["process"] in allowed for s in sub):
                    sub = [s for s in sub if s["process"] not in ("next", "return_back")]

                el["sub_process"] = sub
                section.append(el)
                continue

            section.append(el)

        flush()
        return output

    # ==============================
    # HANDLE LAST ELEMENT
    # ==============================
    @staticmethod
    def process_and_handle_last_element( input_json):
        output = []

        for el in input_json:
            if el.get("process") in JsonManager.EXCLUDED_PROCESSES:
                continue

            if el.get("process") == "loop":
                sub = el.get("sub_process", [])
                if sub:
                    last = sub[-1]["process"]
                    if last == "next":
                        output.append({
                            "process": "open_message",
                            "sleep": random.randint(1, 3)
                        })
                    elif last not in ("delete", "archive", "not_spam", "report_spam"):
                        for s in sub:
                            if s["process"] == "open_message":
                                s["process"] = "OPEN_MESSAGE_ONE_BY_ONE"
                el["sub_process"] = sub

            output.append(el)

        return output

    # ==============================
    # MODIFY JSON
    # ==============================
    @staticmethod
    def process_and_modify_json( input_json):
        output, found = [], False

        for el in input_json:
            if el.get("process") == "open_message":
                found = True
            elif el.get("process") == "loop" and found:
                if any(s["process"] == "next" for s in el.get("sub_process", [])):
                    el.pop("check", None)
            output.append(el)

        return output

    # ==============================
    # SAVE FILE
    # ==============================
    @staticmethod
    def save_json_to_file(json_data, browser):
        try:
            browser_lower = browser.lower()

            if browser_lower == "firefox":
                path = Settings.TEMPLATE_DIRECTORY_FIREFOX
            elif browser_lower == "chrome":
                path = Settings.EXTENTION_EX3
            else:
                path = Settings.TEMPLATE_DIRECTORY_FAMILY_CHROME

            # إنشاء المجلد إذا لم يكن موجودًا
            os.makedirs(path, exist_ok=True)

            file_path = os.path.join(path, "traitement.json")

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)

            return "SUCCESS"

        except Exception as e:
            print("❌ Error while saving JSON file")
            print(f"❌ Exception: {e}")
            return "ERROR"

# Singleton pour une utilisation globale
json_manager = JsonManager()



