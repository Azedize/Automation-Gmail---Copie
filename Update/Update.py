import os
import sys
import shutil
import zipfile
import tempfile
import requests
import traceback

from config import Settings
from api.base_client import APIManager


class UpdateManager:
    """
    True  -> Update executed
    False -> No update needed
    """

    # ==========================================================
    # 🔹 UTILITAIRES
    # ==========================================================
    @staticmethod
    def _read_local_version(path):
        if not path or not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return None

    @staticmethod
    def _download_and_extract(zip_url, target_dir):
        print(f"⬇️ Téléchargement depuis : {zip_url}")

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "update.zip")

            r = requests.get(zip_url, stream=True, timeout=60, verify=False)
            r.raise_for_status()

            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)

            print("📦 ZIP téléchargé")

            if os.path.exists(target_dir):
                print(f"🗑️ Suppression ancienne version : {target_dir}")
                # shutil.rmtree(target_dir, ignore_errors=True)

            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(tmpdir)

            extracted = next(
                os.path.join(tmpdir, d)
                for d in os.listdir(tmpdir)
                if os.path.isdir(os.path.join(tmpdir, d))
            )

            shutil.move(extracted, target_dir)
            print(f"✅ Extraction terminée → {target_dir}")

    # ==========================================================
    # 🔥 LOGIQUE PRINCIPALE
    # ==========================================================
    @staticmethod
    def check_and_update() -> bool:
        try:
            print("\n" + "=" * 80)
            print("🔍 DÉMARRAGE DU SYSTÈME DE MISE À JOUR")
            print("=" * 80)

            # -------------------------------
            # 🌐 APPEL SERVEUR
            # -------------------------------
            response = APIManager.make_request(
                "__CHECK_URL_PROGRAMM__", method="GET", timeout=10
            )

            if not isinstance(response, dict) or response.get("status_code") != 200:
                print("❌ Réponse serveur invalide → Update forcé")
                return True

            data = response.get("data", {})

            server_program = data.get("version_Programm")
            server_ext = data.get("version_extensions")

            print(f"🌐 Version programme serveur : {server_program}")
            print(f"🌐 Version extensions serveur : {server_ext}")

            # -------------------------------
            # 📁 VERSIONS LOCALES
            # -------------------------------
            local_program = UpdateManager._read_local_version(
                Settings.VERSION_LOCAL_PROGRAMM
            )
            local_ext = UpdateManager._read_local_version(
                Settings.VERSION_LOCAL_EXT
            )

            print(f"📄 Version programme locale : {local_program}")
            print(f"📄 Version extensions locale : {local_ext}")

            # ======================================================
            # 🟥 PRIORITÉ ABSOLUE : PROGRAMME
            # ======================================================
            if not local_program or local_program != server_program:
                print("\n🟥 MISE À JOUR PROGRAMME REQUISE")
                UpdateManager._download_and_extract(
                    Settings.API_ENDPOINTS["__SERVER_ZIP_URL_PROGRAM__"],
                    Settings.BASE_DIR
                )
                print("⛔ Arrêt après mise à jour programme")
                return True

            # ======================================================
            # 🟨 EXTENSIONS SEULEMENT
            # ======================================================
            if not local_ext or local_ext != server_ext:
                print("\n🟨 MISE À JOUR EXTENSIONS REQUISE")
                UpdateManager._download_and_extract(
                    Settings.API_ENDPOINTS["__SERVER_ZIP_URL_EXTENSIONS__"],
                    Settings.TOOLS_DIR
                )
                print("▶️ Extensions mises à jour, poursuite normale")
                return True

            # ======================================================
            # 🟩 AUCUNE MISE À JOUR
            # ======================================================
            print("\n🟩 APPLICATION À JOUR – AUCUNE ACTION")
            return False

        except Exception as e:
            traceback.print_exc()
            print("🔥 ERREUR CRITIQUE → UPDATE PAR SÉCURITÉ")
            return True


if __name__ == "__main__":
    updated = UpdateManager.check_and_update()

    print("\n" + "=" * 80)
    print("📌 RÉSULTAT FINAL")
    print("=" * 80)

    if updated:
        print("🔄 UPDATE EFFECTUÉ")
    else:
        print("✅ APPLICATION À JOUR")
