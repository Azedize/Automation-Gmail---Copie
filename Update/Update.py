import os
import sys
import shutil
import tempfile
import zipfile
import requests
import traceback
import json 

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import Settings
from api.base_client import APIManager


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
                "extension": data.get("version_extension"),
                "programme": data.get("version_Programme")
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
                "extension": Settings.VERSION_LOCAL_EXT,
                "programme": Settings.VERSION_LOCAL_PROGRAMM
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
                    print("Local version" + " " + local_version + " " + "server version" + " " + server_versions[key])
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

            # إزالة ZIP القديم
            if os.path.exists(local_zip):
                print(f"🗑️ Removing old ZIP: {local_zip}")
                os.remove(local_zip)

            # إزالة مجلد الاستخراج القديم
            if os.path.exists(extracted_dir):
                print(f"🗑️ Removing old extracted folder: {extracted_dir}")
                shutil.rmtree(extracted_dir)

            # تحميل ZIP
            print("⬇️ Downloading update ZIP from GitHub...")

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


        




    @staticmethod
    def update_from_github_generic(target_dir, zip_name, github_url, remote_version=None):
        try:
            print("📥 Téléchargement de la dernière version depuis GitHub ...")
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, zip_name)
                print(f"📂 Dossier temporaire créé : {tmpdir}")
                print(f"📦 Chemin prévu pour l’archive : {zip_path}")

                # ⬇️ Télécharger l'archive depuis GitHub
                print(f"⬇️ Téléchargement depuis : {github_url}")
                if not download_file(github_url, zip_path):
                    print("❌ Impossible de télécharger le fichier ZIP depuis GitHub.")
                    return False
                else:
                    file_size = os.path.getsize(zip_path)
                    print(f"✅ Fichier ZIP téléchargé ({file_size/1024:.2f} KB) -> {zip_path}")

                # 🗑️ Supprimer l'ancien dossier cible s'il existe
                if os.path.exists(target_dir):
                    print(f"🗑️ Suppression de l'ancien dossier {target_dir} ...")
                    try:
                        shutil.rmtree(target_dir, onerror=remove_readonly)
                        print("✅ Ancien dossier supprimé.")
                    except Exception as e:
                        print(f"⚠️ Impossible de supprimer {target_dir} :", e)

                # 📂 Extraction du fichier ZIP
                print("📂 Extraction du fichier ZIP ...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_content = zip_ref.namelist()
                    print(f"📑 Contenu du ZIP ({len(zip_content)} fichiers) :")
                    for f in zip_content[:10]:  # n’affiche que les 10 premiers
                        print(f"   - {f}")
                    if len(zip_content) > 10:
                        print("   ...")
                    zip_ref.extractall(tmpdir)
                print("✅ Extraction terminée.")

                # 🔎 Chercher le dossier extrait
                extracted_dir = None
                print(f"🔎 Recherche du dossier extrait dans {tmpdir} ...")
                for item in os.listdir(tmpdir):
                    item_path = os.path.join(tmpdir, item)
                    if os.path.isdir(item_path) and item_path != target_dir:
                        extracted_dir = item_path
                        print(f"✅ Dossier extrait trouvé : {extracted_dir}")
                        break

                if extracted_dir is None:
                    print("❌ Impossible de trouver le dossier extrait dans le ZIP.")
                    return False

                # 🚚 Déplacer le dossier extrait vers le chemin final
                print(f"🚚 Déplacement de {extracted_dir} -> {target_dir} ...")
                shutil.move(extracted_dir, target_dir)
                print(f"✅ Mise à jour réussie : {target_dir}")

                if remote_version:
                    print(f"📌 Version installée : {remote_version}")

                return True

        except Exception as e:
            print("❌ Erreur lors de la mise à jour :", e)
            traceback.print_exc()
            return False







    @staticmethod
    def check_version_generic(dropbox_url, manifest_path, version_txt, retries=3, delay=5):
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        attempt = 0
        while attempt < retries:
            try:
                print(f"\n🔎 Tentative de connexion au serveur ({attempt + 1}/{retries}) ...")
                response = requests.get(dropbox_url, headers=headers, verify=False, timeout=20)
                response.raise_for_status()  # Lève une exception pour les codes HTTP >=400
                break  # Si la requête réussit, on sort de la boucle
            except requests.exceptions.ConnectionError as e:
                print(f"❌ Échec de la connexion au serveur. Détail : {e}")
            except requests.exceptions.Timeout as e:
                print(f"⏱️ Délai d'attente dépassé lors de la connexion. Détail : {e}")
            except requests.exceptions.HTTPError as e:
                print(f"⚠️ Erreur HTTP : {e} (code {getattr(response, 'status_code', 'non disponible')})")
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Erreur lors de la requête : {e}")

            attempt += 1
            if attempt < retries:
                print(f"➡️ Nouvelle tentative dans {delay} secondes ...")
                time.sleep(delay)
            else:
                print("❌ Toutes les tentatives de connexion ont échoué. Vérifiez votre connexion Internet ou le serveur.")
                sys.exit(1)

        # Vérification du contenu
        if not response.text.strip():
            print("⚠️ Le serveur n'a renvoyé aucun contenu.")
            sys.exit(1)

        try:
            data = response.json()
        except json.JSONDecodeError:
            print("⚠️ Le contenu reçu n'est pas au format JSON valide.")
            print("📄 Contenu reçu :")
            print(response.text)
            sys.exit(1)

        remote_version = data.get("version_Extention")
        remote_manifest_version = data.get("manifest_version")
        if not remote_version or not remote_manifest_version:
            print("⚠️ Les informations de version sont manquantes dans le fichier distant.")
            sys.exit(1)

        print(f"🌍 Version distante : {remote_version}")
        print(f"🌍 Version manifest distante : {remote_manifest_version}")

        # Vérification des fichiers locaux
        if not os.path.exists(manifest_path) or not os.path.exists(version_txt):
            print(f"⚠️ Les fichiers locaux sont introuvables ({manifest_path} ou {version_txt}). Une mise à jour est requise.")
            return True

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        local_manifest_version = manifest_data.get("version")

        with open(version_txt, "r", encoding="utf-8") as f:
            local_version = f.read().strip()

        print(f"📄 Version locale : {local_version}")
        print(f"📄 Version manifest locale : {local_manifest_version}")

        # Comparaison des versions
        if local_version != remote_version or str(local_manifest_version) != str(remote_manifest_version):
            print("🔄 Une mise à jour est nécessaire !")
            print(f"   ➝ Version locale   : {local_version} (manifest_version={local_manifest_version})")
            print(f"   ➝ Version distante : {remote_version} (manifest_version={remote_manifest_version})")
            return True
        else:
            print("✅ La version locale est à jour.")
            return False





    @staticmethod
    def process_extension(name, folder, dropbox_url, manifest_path, version_file, github_zip_url, zip_name, icon):
        # print(f"\n=== 🚀 Lancement du script de mise à jour {icon} {name} ===")
        print("")

        print(f"\n🔍 Étape 1: Vérification de l'extension locale {name} ...")
        if os.path.exists(folder):
            print(f"📂 Extension trouvée : {folder}")
            remote_version = check_version_generic(dropbox_url, manifest_path, version_file)
            if remote_version:
                print(f"🔄 Une mise à jour est nécessaire (nouvelle version : {remote_version})")
                if update_from_github_generic(folder, zip_name, github_zip_url, remote_version):
                    print(f"✅ Mise à jour réussie : {name} a été mise à jour avec succès !")
                else:
                    print(f"❌ Échec de la mise à jour de {name} depuis GitHub.")
            else:
                print(f"✅ L'extension locale {name} est déjà à jour.")
        else:
            os.makedirs(folder, exist_ok=True)
            print(f"📂 Le dossier '{folder}' a été créé car il n'existait pas.")
            print(f"⚠️ L'extension '{name}' n'existe pas localement.")
            print("📥 Installation de la dernière version ...")

            remote_version = check_version_generic(dropbox_url, manifest_path, version_file)
            if update_from_github_generic(folder, zip_name, github_zip_url, remote_version):
                print(f"✅ Installation de {name} réussie.")
            else:
                print(f"❌ Installation de {name} échouée.")






def download_file(url, dest_path):
    try:
        print(f"⬇️ Téléchargement depuis : {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }

        response = requests.get(url, headers=headers, stream=True, verify=False)
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = (downloaded / total_size) * 100
                        print(f"   → Progression : {percent:.2f}%", end="\r")

        print(f"\n✅ Téléchargement terminé : {dest_path}")
        return True
    except Exception as e:
        print("❌ Erreur lors du téléchargement :", e)
        return False









def process_extension(name, folder, dropbox_url, manifest_path, version_file, github_zip_url, zip_name, icon):
    # print(f"\n=== 🚀 Lancement du script de mise à jour {icon} {name} ===")
    print("")

    print(f"\n🔍 Étape 1: Vérification de l'extension locale {name} ...")
    if os.path.exists(folder):
        print(f"📂 Extension trouvée : {folder}")
        remote_version = check_version_generic(dropbox_url, manifest_path, version_file)
        if remote_version:
            print(f"🔄 Une mise à jour est nécessaire (nouvelle version : {remote_version})")
            if update_from_github_generic(folder, zip_name, github_zip_url, remote_version):
                print(f"✅ Mise à jour réussie : {name} a été mise à jour avec succès !")
            else:
                print(f"❌ Échec de la mise à jour de {name} depuis GitHub.")
        else:
            print(f"✅ L'extension locale {name} est déjà à jour.")
    else:
        os.makedirs(folder, exist_ok=True)
        print(f"📂 Le dossier '{folder}' a été créé car il n'existait pas.")
        print(f"⚠️ L'extension '{name}' n'existe pas localement.")
        print("📥 Installation de la dernière version ...")

        remote_version = check_version_generic(dropbox_url, manifest_path, version_file)
        if update_from_github_generic(folder, zip_name, github_zip_url, remote_version):
            print(f"✅ Installation de {name} réussie.")
        else:
            print(f"❌ Installation de {name} échouée.")

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





