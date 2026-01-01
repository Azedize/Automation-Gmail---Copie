import os
import sys
import shutil
import zipfile
import traceback
import importlib
import subprocess
import time
from pathlib import Path
import requests
import json


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)



try:
    from config import Settings
    from utils.validation_utils import ValidationUtils
    from api.base_client import APIManager
except ImportError as e:
    print(f"[ERROR] Import modules failed: {e}")



class UpdateManager:


    @staticmethod
    def is_update_required() -> bool:
        try:
            print("\n" + "=" * 80)
            print("🔍 DÉBUT VÉRIFICATION DES MISES À JOUR")
            print("=" * 80)

            # =========================
            # 🌐 Appel serveur
            # =========================
            print("🌐 Appel API serveur...")
            response = APIManager.make_request(
                "__CHECK_URL_PROGRAMM__",
                method="GET",
                timeout=10
            )

            if not isinstance(response, dict):
                print("❌ Réponse serveur invalide")
                return True

            if response.get("status_code") != 200:
                print(f"❌ Status code incorrect : {response.get('status_code')}")
                return True

            data = response.get("data")
            if not isinstance(data, dict):
                print("❌ Données serveur invalides")
                return True

            # =========================
            # 🔹 Versions serveur
            # =========================
            server_versions = {
                "extensions": data.get("version_extensions"),
                "programm": (
                    data.get("version_programm")
                    or data.get("version_Programm")
                    or data.get("version_program")
                )
            }

            print("\n🌐 Versions serveur :")
            for k, v in server_versions.items():
                print(f"   - {k} : {v}")

            if not all(server_versions.values()):
                print("❌ Version serveur manquante")
                return True

            # =========================
            # 🔹 Versions locales
            # =========================
            local_files = {
                "extensions": Settings.VERSION_LOCAL_EXT,
                "programm": Settings.VERSION_LOCAL_PROGRAMM
            }

            print("\n📁 Vérification des versions locales :")

            for key, file_path in local_files.items():
                print(f"\n📦 {key}")

                if not file_path:
                    print("   ❌ Chemin du fichier non défini")
                    return True

                if not os.path.exists(file_path):
                    print(f"   ❌ Fichier introuvable : {file_path}")
                    return True

                with open(file_path, "r", encoding="utf-8") as f:
                    local_version = f.read().strip()

                if not local_version:
                    print("   ❌ Version locale vide")
                    return True

                print(f"   ✔ Version locale  : {local_version}")
                print(f"   🌐 Version serveur: {server_versions[key]}")

                if local_version != server_versions[key]:
                    print("   🔄 MISE À JOUR REQUISE (versions différentes)")
                    return True

                print("   ✅ Version OK")

            print("\n🎉 Aucune mise à jour requise")
            return False

        except Exception as e:
            print(f"\n🔥 ERREUR CRITIQUE : {e}")
            return True



    @staticmethod
    def DownloadAndExtract(new_versions):
        try:
            if not isinstance(new_versions, dict):
                print("❌ [ERROR] Invalid new_versions (not a dict).")
                return -1

            path_DownloadFile =  os.path.abspath(Settings.PATH_DOWNLOAD_FILE)
            local_zip = os.path.join(path_DownloadFile, "Programme-main.zip")
            extracted_dir = os.path.join(path_DownloadFile, "Programme-main")

            print(f"🗂️ Download path: {path_DownloadFile}")
            print(f"📦 ZIP path: {local_zip}")
            print(f"📂 Extracted folder path: {extracted_dir}")

            need_interface = "version_interface" in new_versions
            need_python = "version_python" in new_versions

            if not need_interface and not need_python:
                print("✅ [INFO] No extension updates required.")
                return 0

        
            if os.path.exists(local_zip):
                print(f"🗑️ Removing old ZIP: {local_zip}")
                os.remove(local_zip)

            # إزالة مجلد الاستخراج القديم
            if os.path.exists(extracted_dir):
                print(f"🗑️ Removing old extracted folder: {extracted_dir}")
                shutil.rmtree(extracted_dir)

            # تحميل ZIP
            print("⬇️ Downloading update ZIP from GitHub...")
            print("🌐 Fetching download URL from API...")

            resp = requests.get(SERVEUR_ZIP_URL_PROGRAMM, stream=True, headers=HEADERS, timeout=60)
            print(f"📡 HTTP status code: {resp.status_code}")
            if resp.status_code != 200:
                print(f"❌ [ERROR] Failed to download ZIP: HTTP {resp.status_code}")
                return -1

            total_size = int(resp.headers.get('content-length', 0))
            print(f"📏 ZIP size: {total_size / 1024:.2f} KB")

            with open(local_zip, "wb") as f:
                downloaded = 0
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                print(f"✅ Downloaded {downloaded / 1024:.2f} KB")


            # التأكد من أن ZIP موجود وحجمه > 0
            if not os.path.exists(local_zip) or os.path.getsize(local_zip) == 0:
                print("❌ ZIP file not downloaded properly!")
                return -1

            # استخراج ZIP
            print("📂 Extracting ZIP file...")
            with zipfile.ZipFile(local_zip, 'r') as zip_ref:
                names = [n for n in zip_ref.namelist() if n.strip()]
                if not names:
                    print("❌ [ERROR] ZIP is empty.")
                    return -1

                top_folder = names[0].split('/')[0]
                print(f"🗃️ Top folder in ZIP: {top_folder}")

                zip_ref.extractall(path_DownloadFile)

            # إذا اسم المجلد الرئيسي في ZIP مختلف عن extracted_dir → إعادة تسمية
            extracted_top_dir = os.path.join(path_DownloadFile, top_folder)
            if extracted_top_dir != extracted_dir:
                if os.path.exists(extracted_dir):
                    shutil.rmtree(extracted_dir)
                print(f"🔀 Renaming extracted folder {extracted_top_dir} → {extracted_dir}")
                os.rename(extracted_top_dir, extracted_dir)

            # إزالة ZIP بعد الاستخراج
            if os.path.exists(local_zip):
                print(f"🗑️ Removing downloaded ZIP file: {local_zip}")
                os.remove(local_zip)

            print("🎉 [SUCCESS] Download and update process completed.")
            return 0

        except Exception as e:
            traceback.print_exc()
            print(f"❌ [EXCEPTION] Unexpected error in DownloadAndExtract: {e}")
            return -1




print("🌐 Appel API serveur...")

# =========================
# 🧪 TEST DIRECT
# =========================

if __name__ == "__main__":
    result = UpdateManager.is_update_required()

    print("\n" + "=" * 80)
    print("📌 RÉSULTAT FINAL")
    print("=" * 80)

    if result:
        print("🔄 UPDATE REQUIRED → True")
    else:
        print("✅ NO UPDATE → False")


