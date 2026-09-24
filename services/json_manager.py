import random
import os
import traceback
from PyQt6.QtWidgets import QCheckBox, QLineEdit, QComboBox
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from config import Settings
except ImportError as e:
    print(f"❌ Erreur d'importation dans file {__file__}: {e}")
    sys.exit(1)


class JsonManager:
    
    @staticmethod
    def parseRandomRange(text: str) -> int:
        try:
            if "," in text:
                a, b = map(int, text.split(","))
                return random.randint(a, b)
            return int(text)
        except Exception:
            Settings.write_log_dev_file(f"Error parsing random range: {text}\n{traceback.format_exc()}", level="ERROR")
            return 0

    @staticmethod
    def getChildWidgets(widget, cls):
        return [c for c in widget.children() if isinstance(c, cls)]


    @staticmethod
    def generateJson(scenario_layout, selected_browser: str):
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

            checkbox = next(iter(JsonManager.getChildWidgets(widget, QCheckBox)), None)
            qlineedits = JsonManager.getChildWidgets(widget, QLineEdit)


            if (  hidden_id  and not show_on_init and not hidden_id.startswith(  (Settings.GOOGLE_PREFIX, Settings.YOUTUBE_PREFIX) ) ):
                if len(qlineedits) > 1:
                    limit = JsonManager.parseRandomRange(qlineedits[0].text())
                    sleep = JsonManager.parseRandomRange(qlineedits[1].text())
                    output_json.append({"process": hidden_id, "limit": limit, "sleep": sleep})
                elif qlineedits:
                    sleep = JsonManager.parseRandomRange(qlineedits[0].text())
                    output_json.append({"process": hidden_id, "sleep": sleep})
                i += 1
                continue


            if ( hidden_id  and not show_on_init and hidden_id.startswith(Settings.YOUTUBE_PREFIX) ):
                limit = JsonManager.parseRandomRange(qlineedits[0].text()) if len(qlineedits) > 1 else 0
                sleep = JsonManager.parseRandomRange(qlineedits[1].text()) if len(qlineedits) > 1 else 0

                output_json.append({"process": "CheckLoginYoutube", "sleep": random.randint(1, 3)})
                output_json.append({"process": hidden_id, "limit": limit, "sleep": sleep})
                i += 1
                continue


            if show_on_init and checkbox:
                output_json.append({"process": hidden_id, "sleep": random.randint(1, 3)})
                if checkbox.isChecked():
                    search_value = qlineedits[-1].text() if qlineedits else ""
                    if hidden_id == "open_spam":
                        search_value = f"in:spam {search_value}"
                    output_json.append({"process": "search", "value": search_value})

                sub_process = []
                i += 1

                while i < scenario_layout.count():
                    sub_widget = scenario_layout.itemAt(i).widget()
                    if not sub_widget:
                        break
                    sub_state = sub_widget.property("full_state") or {}
                    sub_id = sub_state.get("id") or ""
                    if sub_state.get("showOnInit") or sub_id.startswith( (Settings.GOOGLE_PREFIX, Settings.YOUTUBE_PREFIX) ):
                        break
                    sleep_txt = next( (  c.text() for c in JsonManager.getChildWidgets(sub_widget, QLineEdit) ), "0" )
                    sleep = JsonManager.parseRandomRange(sleep_txt)
                    sub_process.append({"process": sub_id, "sleep": sleep})
                    i += 1

                combo = next(iter(JsonManager.getChildWidgets(widget, QComboBox)), None)
                action = "return_back" if combo and combo.currentText() == "Return back" else "next"
                if sub_process:
                    sub_process.append({"process": action})

                limit_loop = JsonManager.parseRandomRange(qlineedits[0].text()) if len(qlineedits) > 1 else 0
                start_loop = JsonManager.parseRandomRange(qlineedits[1].text()) if len(qlineedits) > 1 else 0

                output_json.append({"process": "loop", "check": "is_empty_folder", "limit_loop": limit_loop, "start": start_loop, "sub_process": sub_process})
                continue

            if show_on_init and not checkbox:
                sleep = JsonManager.parseRandomRange(qlineedits[0].text()) if qlineedits else 0
                output_json.append({"process": hidden_id, "sleep": sleep})
                i += 1
                continue


            if hidden_id and hidden_id.startswith((Settings.GOOGLE_PREFIX, Settings.YOUTUBE_PREFIX) ):
                sleep = (  JsonManager.parseRandomRange(qlineedits[0].text()) if qlineedits  else 0 )
                action = {"process": hidden_id, "sleep": sleep}
                if checkbox and checkbox.isChecked():
                    action["search"] = qlineedits[1].text() if len(qlineedits) > 1 else qlineedits[0].text()

                output_json.append(action)
                i += 1
                continue

            i += 1
        output_json = JsonManager.splitJsonIntoProcesses(output_json)
        output_json = JsonManager.handleLastJsonElement(output_json)
        output_json = JsonManager.modifyJsonProcesses(output_json)

        return output_json

 

    @staticmethod
    def splitJsonIntoProcesses(input_json):
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
                allowed = Settings.ALLOWED_ITEMS.get(current, ())
                sub = el["sub_process"]

                if any(s["process"] == "select_all" for s in sub) or any( s["process"] in allowed for s in sub  ):
                    sub = [ s for s in sub if s["process"] not in ("next", "return_back")  ]
                el["sub_process"] = sub
                section.append(el)
                continue
            section.append(el)
        flush()
        return output


    @staticmethod
    def handleLastJsonElement(input_json):
        output = []
        for el in input_json:
            if el.get("process") in Settings.EXCLUDED_PROCESSES:
                continue
            if el.get("process") == "loop":
                sub = el.get("sub_process", [])
                if sub:
                    last = sub[-1]["process"]
                    if last == "next":
                        output.append({"process": "open_message", "sleep": random.randint(1, 3)})
                    elif last not in ("delete", "archive", "not_spam", "report_spam"):
                        for s in sub:
                            if s["process"] == "open_message":
                                s["process"] = "OPEN_MESSAGE_ONE_BY_ONE"
                el["sub_process"] = sub

            output.append(el)

        return output


    @staticmethod
    def modifyJsonProcesses(input_json):
        output, found = [], False

        for el in input_json:
            if el.get("process") == "open_message":
                found = True
            elif el.get("process") == "loop" and found:
                if any(s["process"] == "next" for s in el.get("sub_process", [])):
                    el.pop("check", None)
            output.append(el)

        return output


json_manager = JsonManager()
