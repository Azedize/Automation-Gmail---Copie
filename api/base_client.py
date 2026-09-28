# ==========================================================
# api/safe_api_manager.py
# ApiClient sécurisé avec des journaux détaillés
# ==========================================================

import os
import sys
import json
import time
import traceback
import requests
import re
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter, Retry

# ----------------------------------------------------------
# Détermine la racine du projet.
#
# __file__ représente le chemin du fichier actuel.
# os.path.abspath() transforme ce chemin en chemin absolu.
# Le premier dirname() remonte du dossier "api" vers la racine
# du projet.
#
# Exemple :
#
# Projet/
# ├── api/
# │   └── safe_api_manager.py
# ├── config.py
# └── core/
#
# ROOT_DIR correspondra alors à :
#
# Projet/
#
# Cette racine est ajoutée à sys.path afin de permettre
# les imports absolus comme :
#
# from config import Settings
# from core.encryption import EncryptionService
# ----------------------------------------------------------
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ----------------------------------------------------------
# Vérifie que la racine du projet est disponible dans le
# chemin de recherche de Python.
#
# sys.path contient les répertoires dans lesquels Python
# recherche les modules lors d'un import.
#
# L'utilisation de insert(0, ...) place ROOT_DIR au début
# de la liste afin qu'il soit recherché en priorité.
# ----------------------------------------------------------
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


# ----------------------------------------------------------
# Importation des composants internes nécessaires.
#
# Settings :
# - contient la configuration globale de l'application ;
# - contient notamment les endpoints API ;
# - contient les headers ;
# - contient les paramètres SSL ;
# - contient les clés nécessaires à certaines opérations ;
# - fournit également le système de logging.
#
# EncryptionService :
# - permet de déchiffrer certaines réponses provenant
#   du serveur, notamment la configuration Proxy.
#
# Si l'un de ces modules est indisponible, l'application
# ne peut pas fonctionner correctement.
# ----------------------------------------------------------
try:
    from config import Settings
    from core.encryption import EncryptionService
except ImportError as error:
    # Journalise le traceback si Settings est disponible, sinon utilise la console.
    if "Settings" in globals():
        Settings.write_log_event("api_client_import_failed", "ERROR", file=__file__, exception_type=type(error).__name__, error=str(error), traceback=traceback.format_exc())
    else:
        print(f"❌ Erreur d'importation dans file {__file__}: {error}\n" f"{traceback.format_exc()}")

    # Arrête immédiatement le programme car les dépendances
    # nécessaires au fonctionnement de l'ApiClient sont absentes.
    sys.exit(1)


class ApiClient:
    # ------------------------------------------------------
    # Nombre maximum de tentatives HTTP autorisées.
    #
    # La valeur est centralisée dans Settings afin d'éviter
    # de définir une valeur différente dans chaque méthode.
    #
    # Exemple :
    #
    # MAX_REQUEST_ATTEMPTS = 3
    #
    # Le système pourra alors effectuer :
    #
    # tentative 1
    # tentative 2
    # tentative 3
    #
    # avant de considérer définitivement la requête comme
    # échouée.
    # ------------------------------------------------------
    MAX_REQUEST_ATTEMPTS = Settings.MAX_REQUEST_ATTEMPTS

    def __init__(self):
        # --------------------------------------------------
        # Création d'une Session Requests.
        #
        # Une Session permet de centraliser les paramètres
        # HTTP et de réutiliser certaines ressources réseau
        # entre plusieurs requêtes.
        #
        # Au lieu de créer une nouvelle configuration HTTP
        # pour chaque requête, l'application utilise cette
        # même Session.
        # --------------------------------------------------
        self.session = requests.Session()

        # --------------------------------------------------
        # Configure la vérification SSL.
        #
        # Lorsque VERIFY_SSL vaut True, Requests vérifie
        # le certificat SSL/TLS du serveur.
        #
        # Ce paramètre doit normalement rester activé en
        # environnement de production.
        # --------------------------------------------------
        self.session.verify = Settings.VERIFY_SSL

        # --------------------------------------------------
        # Configure le Retry de l'HTTPAdapter.
        #
        # Ici total=0 signifie que Requests ne réalise pas
        # de retry automatique au niveau de l'adapter.
        #
        # Le système de retry est géré manuellement plus bas
        # dans makeRequest(), ce qui permet de contrôler
        # précisément le nombre de tentatives et le délai
        # entre celles-ci.
        # --------------------------------------------------
        retries = Retry(total=0)

        # --------------------------------------------------
        # Monte l'adapter pour les connexions HTTPS.
        #
        # Toutes les requêtes HTTPS utilisant cette Session
        # passeront par cet adapter.
        # --------------------------------------------------
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

        # --------------------------------------------------
        # Monte le même adapter pour les connexions HTTP.
        # --------------------------------------------------
        self.session.mount("http://", HTTPAdapter(max_retries=retries))

        # --------------------------------------------------
        # Ajoute les headers globaux définis dans Settings.
        #
        # Ces headers seront utilisés par défaut par toutes
        # les requêtes effectuées avec cette Session.
        # --------------------------------------------------
        self.session.headers.update(Settings.HEADER)

        # --------------------------------------------------
        # Journalise l'initialisation du client API.
        #
        # On enregistre uniquement des informations techniques
        # nécessaires au diagnostic :
        #
        # - état de la vérification SSL ;
        # - nombre maximal de tentatives.
        #
        # Le contenu sensible des requêtes n'est pas journalisé.
        # --------------------------------------------------
        Settings.write_log_event("api_client_initialized", "INFO", verify_ssl=self.session.verify, retry_attempts=self.MAX_REQUEST_ATTEMPTS)

    def makeRequest(
        self, endpoint: str, method: str = "POST", data: Optional[Dict] = None, json_data: Optional[Dict] = None, params: Optional[Dict] = None, headers: Optional[Dict] = None, timeout: int = 30
    ) -> Dict[str, Any]:

        # --------------------------------------------------
        # Détermine l'URL réelle qui sera utilisée.
        #
        # Si endpoint commence par "_", il est considéré comme
        # une clé de configuration présente dans :
        #
        # Settings.API_ENDPOINTS
        #
        # Exemple :
        #
        # endpoint = "_SAVE_EMAIL_API"
        #
        # peut correspondre à :
        #
        # https://server.example/api/save-email
        #
        # Si endpoint ne commence pas par "_", sa valeur est
        # considérée directement comme une URL.
        # --------------------------------------------------
        url = Settings.API_ENDPOINTS.get(endpoint, endpoint) if endpoint.startswith("_") else endpoint

        # --------------------------------------------------
        # Crée une copie des headers globaux de la Session.
        #
        # Une copie est utilisée afin de pouvoir ajouter ou
        # modifier des headers pour cette requête sans modifier
        # définitivement les headers globaux de la Session.
        # --------------------------------------------------
        req_headers = self.session.headers.copy()

        # --------------------------------------------------
        # Si des headers spécifiques ont été fournis pour cette
        # requête, ils remplacent ou complètent les headers
        # globaux.
        # --------------------------------------------------
        if headers:
            req_headers.update(headers)

        # --------------------------------------------------
        # Journalise la préparation de la requête.
        #
        # Important :
        # On ne journalise pas directement le contenu de data,
        # json_data ou params.
        #
        # On indique seulement leur présence afin d'éviter
        # d'exposer accidentellement des données sensibles
        # dans les logs.
        # --------------------------------------------------
        Settings.write_log_event(
            "http_request_prepared", "INFO", endpoint=endpoint, method=method.upper(), has_data=bool(data), has_json=bool(json_data), has_params=bool(params), timeout_seconds=timeout
        )

        # --------------------------------------------------
        # Conserve la dernière erreur rencontrée.
        #
        # Cette valeur sera utilisée si toutes les tentatives
        # échouent.
        # --------------------------------------------------
        last_exception = None

        # --------------------------------------------------
        # Effectue les tentatives HTTP.
        #
        # range(1, MAX_REQUEST_ATTEMPTS + 1) permet d'obtenir
        # des numéros de tentative commençant à 1.
        #
        # Exemple avec MAX_REQUEST_ATTEMPTS = 3 :
        #
        # 1
        # 2
        # 3
        # --------------------------------------------------
        for attempt in range(1, self.MAX_REQUEST_ATTEMPTS + 1):
            try:
                # ------------------------------------------
                # Journalise le début de la tentative.
                # ------------------------------------------
                Settings.write_log_event("http_request_started", "INFO", endpoint=endpoint, method=method.upper(), attempt=attempt, max_attempts=self.MAX_REQUEST_ATTEMPTS)

                # ------------------------------------------
                # Envoie réellement la requête HTTP.
                #
                # method :
                #     GET, POST, PUT, DELETE, etc.
                #
                # data :
                #     données classiques envoyées dans la requête.
                #
                # json :
                #     données envoyées comme JSON.
                #
                # params :
                #     paramètres de query string.
                #
                # headers :
                #     headers HTTP.
                #
                # timeout :
                #     temps maximal d'attente.
                # ------------------------------------------
                response = self.session.request(method=method.upper(), url=url, data=data, json=json_data, params=params, headers=req_headers, timeout=timeout)

                # ------------------------------------------
                # Journalise les informations générales de la
                # réponse sans enregistrer son contenu.
                #
                # response_size permet de connaître la taille
                # de la réponse.
                #
                # Content-Type permet de savoir si le serveur
                # a répondu avec du JSON, du texte, etc.
                # ------------------------------------------
                Settings.write_log_event(
                    "http_response_received",
                    "INFO",
                    method=method.upper(),
                    status_code=response.status_code,
                    response_size=len(response.content),
                    content_type=response.headers.get("Content-Type", "unknown"),
                )

                # ------------------------------------------
                # HTTP 200 signifie que la requête a été
                # traitée avec succès au niveau HTTP.
                # ------------------------------------------
                if response.status_code == 200:
                    try:
                        # ----------------------------------
                        # Essaie de convertir la réponse JSON
                        # en objet Python.
                        #
                        # Exemple :
                        #
                        # {"status": true}
                        #
                        # devient :
                        #
                        # {"status": True}
                        # ----------------------------------
                        parsed = response.json()

                        # ----------------------------------
                        # Journalise le type de données obtenu
                        # et éventuellement sa taille.
                        #
                        # Le contenu réel n'est pas enregistré.
                        # ----------------------------------
                        Settings.write_log_event("http_json_parsed", "INFO", response_type=type(parsed).__name__, item_count=(len(parsed) if hasattr(parsed, "__len__") else None))

                        # ----------------------------------
                        # Retourne une structure standardisée.
                        #
                        # status :
                        #     indique que la requête HTTP a réussi.
                        #
                        # data :
                        #     contient les données retournées.
                        #
                        # status_code :
                        #     contient le code HTTP.
                        # ----------------------------------
                        return {"status": "success", "data": parsed, "status_code": 200}

                    except json.JSONDecodeError as json_error:
                        # ----------------------------------
                        # Le serveur a répondu avec HTTP 200,
                        # mais sa réponse n'est pas un JSON valide.
                        #
                        # Ce cas n'est pas forcément une erreur
                        # HTTP : l'API peut volontairement retourner
                        # du texte.
                        # ----------------------------------
                        Settings.write_log_event(
                            "http_json_decode_failed",
                            "WARNING",
                            endpoint=endpoint,
                            status_code=response.status_code,
                            exception_type=type(json_error).__name__,
                            error=str(json_error),
                            traceback=traceback.format_exc(),
                        )

                        # ----------------------------------
                        # Retourne directement le texte reçu.
                        # ----------------------------------
                        return {"status": "success", "data": response.text, "status_code": 200}

                # ------------------------------------------
                # HTTP 401 ou 403 indique généralement un
                # problème d'authentification ou d'autorisation.
                #
                # Ces erreurs ne sont pas considérées ici comme
                # des erreurs réseau temporaires nécessitant
                # plusieurs retries.
                # ------------------------------------------
                elif response.status_code in (401, 403):
                    Settings.write_log_event("http_authentication_failed", "WARNING", endpoint=endpoint, status_code=response.status_code, action="verify credentials or session")

                    # --------------------------------------
                    # Retourne immédiatement une erreur
                    # d'authentification.
                    # --------------------------------------
                    return {"status": "error", "error": (f"HTTP {response.status_code}: " "Access denied / session expired"), "status_code": response.status_code}

                else:
                    # --------------------------------------
                    # Toute autre réponse HTTP est considérée
                    # comme une erreur pour cette tentative.
                    #
                    # Exemple :
                    #
                    # 404
                    # 500
                    # 502
                    # 503
                    # --------------------------------------
                    last_exception = f"HTTP {response.status_code}"

                    Settings.write_log_event(
                        "http_request_failed", "WARNING", endpoint=endpoint, method=method.upper(), attempt=attempt, status_code=response.status_code, response_size=len(response.content)
                    )

            except requests.RequestException as e:
                # ------------------------------------------
                # Capture les exceptions générées par Requests.
                #
                # Exemples :
                #
                # - ConnectionError
                # - Timeout
                # - SSLError
                # - autres erreurs réseau
                #
                # On enregistre le type de l'exception et son
                # message pour faciliter le diagnostic.
                # ------------------------------------------
                Settings.write_log_event("http_request_exception", "ERROR", endpoint=endpoint, attempt=attempt, exception_type=type(e).__name__, error=str(e), traceback=traceback.format_exc())

                # ------------------------------------------
                # Conserve la dernière erreur pour le message
                # final si toutes les tentatives échouent.
                # ------------------------------------------
                last_exception = str(e)

            # ------------------------------------------------
            # Si ce n'était pas la dernière tentative, prépare
            # une nouvelle tentative.
            # ------------------------------------------------
            if attempt < self.MAX_REQUEST_ATTEMPTS:
                Settings.write_log_event("http_request_retry_scheduled", "WARNING", endpoint=endpoint, next_attempt=attempt + 1, delay_seconds=2)

                # ------------------------------------------------
                # Attend deux secondes avant la prochaine tentative.
                #
                # Ce délai évite d'envoyer immédiatement plusieurs
                # requêtes successives vers un serveur temporairement
                # indisponible.
                # ------------------------------------------------
                time.sleep(2)

        # ------------------------------------------------------
        # Toutes les tentatives ont échoué.
        #
        # Cette étape est atteinte uniquement après avoir utilisé
        # toutes les tentatives disponibles.
        # ------------------------------------------------------
        Settings.write_log_event("http_request_failed_final", "ERROR", endpoint=endpoint, attempts=self.MAX_REQUEST_ATTEMPTS, error=last_exception)

        # ------------------------------------------------------
        # Retourne une réponse standardisée indiquant l'échec
        # définitif de la requête.
        # ------------------------------------------------------
        return {"status": "error", "error": (f"Failed after {self.MAX_REQUEST_ATTEMPTS} attempts: {last_exception}"), "status_code": None}

    def handleResponse(self, result: Dict[str, Any], success_default: Any = None, failure_default: Any = None):
        # ------------------------------------------------------
        # Cette méthode centralise le traitement des réponses
        # retournées par makeRequest().
        #
        # makeRequest() retourne normalement une structure :
        #
        # {
        #     "status": "success",
        #     "data": ...,
        #     "status_code": 200
        # }
        #
        # ou :
        #
        # {
        #     "status": "error",
        #     "error": "...",
        #     "status_code": ...
        # }
        #
        # Cette méthode permet aux autres fonctions de récupérer
        # directement les données utiles sans répéter les mêmes
        # vérifications.
        # ------------------------------------------------------
        try:
            # --------------------------------------------------
            # Vérifie que la réponse est bien un dictionnaire.
            # --------------------------------------------------
            if not isinstance(result, dict):
                Settings.write_log_event("api_response_handler_failed", "ERROR", reason="invalid_response_type", response_type=type(result).__name__)

                return failure_default

            # --------------------------------------------------
            # Récupère le statut de la réponse.
            # --------------------------------------------------
            status = result.get("status")

            # --------------------------------------------------
            # Si makeRequest() indique un succès, récupère
            # les données retournées.
            # --------------------------------------------------
            if status == "success":
                data = result.get("data", success_default)

                Settings.write_log_event("api_response_handled", "INFO", status="success", data_type=type(data).__name__)

                return data

            # --------------------------------------------------
            # Tous les autres statuts sont considérés comme
            # des erreurs.
            # --------------------------------------------------
            else:
                Settings.write_log_event("api_response_handled", "ERROR", status="error", status_code=result.get("status_code"), error=result.get("error", "Unknown error"))

                return failure_default

        except Exception as e:
            # --------------------------------------------------
            # Capture toute erreur inattendue lors du traitement
            # de la réponse.
            # --------------------------------------------------
            Settings.write_log_event("api_response_handler_failed", "ERROR", exception_type=type(e).__name__, error=str(e), traceback=traceback.format_exc())

            # --------------------------------------------------
            # En cas d'erreur, retourne la valeur par défaut
            # prévue pour les échecs.
            # --------------------------------------------------
            return failure_default

    def fetchScenarios(self, Url_Api, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:

        # ------------------------------------------------------
        # Journalise le début de la récupération des scénarios.
        # ------------------------------------------------------
        Settings.write_log_event("scenarios_fetch_started", "INFO", method="GET", endpoint=Url_Api, has_params=bool(params))

        try:
            # --------------------------------------------------
            # Effectue une requête GET vers l'API des scénarios.
            # --------------------------------------------------
            result = self.makeRequest(Url_Api, "GET", params=params)

        except Exception as e:
            # --------------------------------------------------
            # Capture une éventuelle erreur inattendue autour
            # de makeRequest().
            # --------------------------------------------------
            Settings.write_log_event("scenarios_fetch_failed", "ERROR", exception_type=type(e).__name__, error=str(e), traceback=traceback.format_exc())

            return {"session": False, "scenarios": []}

        try:
            # --------------------------------------------------
            # Transforme la réponse API en résultat utilisable
            # par l'application.
            #
            # En cas de succès :
            #     {"session": False, "scenarios": []}
            #
            # est utilisé comme valeur par défaut si nécessaire.
            # --------------------------------------------------
            response = self.handleResponse(result, {"session": False, "scenarios": []}, {"session": False, "scenarios": []})

            # --------------------------------------------------
            # Calcule le nombre de scénarios uniquement pour
            # le logging.
            #
            # On vérifie d'abord que response est un dict et
            # que scenarios est bien une liste.
            # --------------------------------------------------
            Settings.write_log_event(
                "scenarios_fetch_completed",
                "INFO",
                response_type=type(response).__name__,
                scenario_count=(len(response.get("scenarios", [])) if (isinstance(response, dict) and isinstance(response.get("scenarios"), list)) else None),
            )

            return response

        except Exception as e:
            # --------------------------------------------------
            # Capture les erreurs pouvant apparaître pendant
            # le traitement de la réponse.
            # --------------------------------------------------
            Settings.write_log_event("scenarios_response_processing_failed", "ERROR", exception_type=type(e).__name__, error=str(e), traceback=traceback.format_exc())

            return {"session": False, "scenarios": []}

    def saveProcess(self, params: Dict[str, Any]) -> int:

        # ------------------------------------------------------
        # Envoie les informations d'un processus vers l'API.
        #
        # json_data indique que params doit être envoyé comme
        # corps JSON de la requête HTTP.
        # ------------------------------------------------------
        result = self.makeRequest("_SAVE_PROCESS_API", "POST", json_data=params)

        # ------------------------------------------------------
        # Extrait les données de la réponse.
        #
        # {} est utilisé comme valeur par défaut en cas d'échec.
        # ------------------------------------------------------
        data = self.handleResponse(result, {})

        # ------------------------------------------------------
        # Vérifie que :
        #
        # 1. la réponse est un dictionnaire ;
        # 2. le champ "status" existe ;
        # 3. sa valeur est exactement True.
        # ------------------------------------------------------
        if isinstance(data, dict) and data.get("status") is True:
            Settings.write_log_event("process_saved", "INFO", has_inserted_id=bool(data.get("inserted_id")))

            # --------------------------------------------------
            # Retourne l'identifiant créé par l'API.
            #
            # Si inserted_id est absent, retourne -1.
            # --------------------------------------------------
            return data.get("inserted_id", -1)

        # ------------------------------------------------------
        # Le serveur n'a pas confirmé l'enregistrement.
        # ------------------------------------------------------
        Settings.write_log_event("process_save_rejected", "WARNING")

        return -1

    def saveEmail(self, params: Dict[str, Any]) -> str:

        # ------------------------------------------------------
        # Envoie les informations d'un email vers l'API.
        # ------------------------------------------------------
        result = self.makeRequest("_SAVE_EMAIL_API", "POST", json_data=params)

        # ------------------------------------------------------
        # Retourne la réponse sous forme de chaîne de caractères.
        #
        # Cela garantit que la fonction respecte son type de
        # retour annoncé : str.
        # ------------------------------------------------------
        return str(self.handleResponse(result, ""))

    def sendStatus(self, params: Dict[str, Any]) -> str:

        # ------------------------------------------------------
        # Journalise la préparation de la requête de statut.
        #
        # On enregistre uniquement le nombre de paramètres,
        # pas leur contenu.
        # ------------------------------------------------------
        Settings.write_log_event("status_request_prepared", "INFO", parameter_count=len(params))

        # ------------------------------------------------------
        # Envoie le statut au serveur.
        # ------------------------------------------------------
        result = self.makeRequest("_SEND_STATUS_API", "POST", json_data=params)

        # ------------------------------------------------------
        # Journalise uniquement le type de résultat reçu.
        # ------------------------------------------------------
        Settings.write_log_event("status_response_received", "INFO", response_type=type(result).__name__)

        # ------------------------------------------------------
        # Traite la réponse et retourne sa valeur sous forme
        # de chaîne.
        # ------------------------------------------------------
        return str(self.handleResponse(result, ""))

    def handleSaveScenario(self, payload: Dict[str, Any], Url_Api) -> Dict[str, Any]:

        # ------------------------------------------------------
        # Journalise le début de l'enregistrement du scénario.
        #
        # Le contenu du payload n'est pas enregistré.
        # Seules des informations générales sont conservées :
        #
        # - type du payload ;
        # - nombre de champs.
        # ------------------------------------------------------
        Settings.write_log_event("scenario_save_started", "INFO", endpoint=Url_Api, payload_type=type(payload).__name__, payload_field_count=len(payload))

        # ------------------------------------------------------
        # Envoie le scénario vers l'API.
        #
        # Ici, le code utilise "data" et non "json_data".
        # Cette différence dépend du format attendu par
        # l'endpoint concerné.
        # ------------------------------------------------------
        result = self.makeRequest(Url_Api, "POST", data=payload)

        # ------------------------------------------------------
        # Journalise les informations générales de la réponse.
        # ------------------------------------------------------
        Settings.write_log_event("save_scenario_response_received", "INFO", status_code=result.get("status_code"), status=result.get("status"), response_type=type(result).__name__)

        # ------------------------------------------------------
        # Transforme la réponse API en résultat standard.
        #
        # En cas de succès, la valeur par défaut est :
        #
        # {"success": True}
        #
        # En cas d'échec :
        #
        # {
        #     "success": False,
        #     "error": "Format de réponse invalide"
        # }
        # ------------------------------------------------------
        response = self.handleResponse(result, {"success": True}, {"success": False, "error": "Format de réponse invalide"})

        # ------------------------------------------------------
        # Journalise le résultat final du traitement.
        # ------------------------------------------------------
        Settings.write_log_event("save_scenario_response_processed", "INFO", success=(response.get("success") if isinstance(response, dict) else None))

        return response

    def fetchProxyConfiguration(self, unique_ips: set, entity_New: str) -> Dict[str, Any]:

        # ------------------------------------------------------
        # Cette méthode récupère une configuration Proxy auprès
        # du serveur.
        #
        # Le flux général est :
        #
        # IPs + Entity
        #       ↓
        # API Proxy
        #       ↓
        # réponse chiffrée
        #       ↓
        # déchiffrement
        #       ↓
        # nettoyage
        #       ↓
        # parsing JSON
        #       ↓
        # validation des IPs
        #       ↓
        # résultat final
        # ------------------------------------------------------
        try:
            Settings.write_log_event("proxy_configuration_fetch_started", "INFO", entity=entity_New, ip_count=len(unique_ips))

            # --------------------------------------------------
            # Vérifie que la collection d'IP n'est pas vide.
            # --------------------------------------------------
            if not unique_ips:
                Settings.write_log_event("proxy_configuration_input_invalid", "ERROR", reason="no_ips_provided")

                return {"valid": False, "data": None, "error": "No IPs provided"}

            # --------------------------------------------------
            # Construit la valeur envoyée au service Proxy.
            #
            # Exemple :
            #
            # unique_ips = {
            #     "1.1.1.1",
            #     "2.2.2.2"
            # }
            #
            # entity_New = "opm74"
            #
            # Résultat possible :
            #
            # 1.1.1.1,2.2.2.2---opm74
            #
            # Le set ne garantit pas un ordre particulier.
            # --------------------------------------------------
            k_proxy = ",".join(unique_ips) + "---" + entity_New

            # --------------------------------------------------
            # Prépare les paramètres nécessaires au service Proxy.
            #
            # IMPORTANT :
            # La valeur de "m" doit être considérée comme
            # potentiellement sensible si elle représente une
            # clé ou un secret d'authentification.
            # Elle devrait idéalement être externalisée dans
            # une configuration sécurisée si nécessaire.
            # --------------------------------------------------
            params = {"m": "5454542z15szsdz4jklhjhdfz", "k": k_proxy}

            Settings.write_log_event("proxy_request_prepared", "INFO", parameter_count=len(params), ip_count=len(unique_ips))

            # --------------------------------------------------
            # Définit un User-Agent spécifique pour cette requête.
            # --------------------------------------------------
            headers = {"User-Agent": "Mozilla/5.0"}

            # --------------------------------------------------
            # Appelle le service Proxy via le client HTTP central.
            #
            # Le résultat passera donc par :
            #
            # makeRequest()
            #
            # et bénéficiera de ses mécanismes :
            #
            # - Session
            # - timeout
            # - logging
            # - gestion HTTP
            # - retry
            # --------------------------------------------------
            result = self.makeRequest(Settings.API_ENDPOINTS["__GET_PROXY_INFO__"], method="POST", data=params, headers=headers, timeout=30)

            # --------------------------------------------------
            # Journalise uniquement les informations générales
            # de la réponse.
            # --------------------------------------------------
            Settings.write_log_event("proxy_response_received", "INFO", status=result.get("status"), status_code=result.get("status_code"), response_type=type(result.get("data")).__name__)

            # --------------------------------------------------
            # Vérifie si makeRequest() considère la requête
            # comme réussie.
            # --------------------------------------------------
            if result.get("status") != "success":
                # ----------------------------------------------
                # Récupère l'erreur fournie par makeRequest().
                # ----------------------------------------------
                error_detail = result.get("error") or "Invalid response status from proxy service"

                Settings.write_log_event("proxy_configuration_fetch_failed", "ERROR", stage="http_response", status=result.get("status"), status_code=result.get("status_code"), error=error_detail)

                return {"valid": False, "data": None, "error": (f"Données API non valides : {error_detail}")}

            # --------------------------------------------------
            # Récupère les données retournées par l'API.
            #
            # À ce stade, elles sont encore chiffrées.
            # --------------------------------------------------
            response_text = result.get("data", "")

            # --------------------------------------------------
            # Calcule la taille de la réponse uniquement pour
            # le logging.
            #
            # Le contenu chiffré lui-même n'est pas enregistré.
            # --------------------------------------------------
            response_size = len(response_text) if isinstance(response_text, str) else 0

            Settings.write_log_event("proxy_response_ready_for_decryption", "INFO", response_size_bytes=response_size)

            try:
                # ----------------------------------------------
                # Déchiffre la réponse du serveur.
                #
                # response_text :
                #     données chiffrées.
                #
                # Settings.API_KEY_PROXY :
                #     clé utilisée par EncryptionService.
                # ----------------------------------------------
                decrypted = EncryptionService.decrypt_message(response_text, Settings.API_KEY_PROXY)

                Settings.write_log_event("proxy_response_decrypted", "INFO", decrypted_size_bytes=len(decrypted))

            except Exception as decrypt_error:
                # ----------------------------------------------
                # Une erreur ici signifie que la réponse n'a pas
                # pu être déchiffrée correctement.
                # ----------------------------------------------
                Settings.write_log_event(
                    "proxy_configuration_fetch_failed", "ERROR", stage="decryption", exception_type=type(decrypt_error).__name__, error=str(decrypt_error), traceback=traceback.format_exc()
                )

                return {"valid": False, "data": None, "error": (f"Decryption error: {str(decrypt_error)}")}

            # --------------------------------------------------
            # Supprime les caractères qui ne font pas partie
            # de la plage ASCII imprimable.
            #
            # Le but est de nettoyer la chaîne avant son parsing
            # JSON.
            #
            # [^\x20-\x7E] signifie :
            #
            # tout caractère qui n'est PAS compris entre
            # 0x20 et 0x7E.
            # --------------------------------------------------
            decrypted = re.sub(r"[^\x20-\x7E]", "", decrypted)

            try:
                # ----------------------------------------------
                # Transforme la chaîne JSON déchiffrée en objet
                # Python.
                #
                # Exemple :
                #
                # '{"1.1.1.1#proxy": {...}}'
                #
                # devient :
                #
                # {
                #     "1.1.1.1#proxy": {...}
                # }
                # ----------------------------------------------
                data = json.loads(decrypted)

                Settings.write_log_event("proxy_json_parsed", "INFO", data_type=type(data).__name__, key_count=(len(data) if isinstance(data, dict) else None))

            except json.JSONDecodeError as json_error:
                # ----------------------------------------------
                # La réponse a été déchiffrée, mais son contenu
                # n'est pas un JSON valide.
                # ----------------------------------------------
                Settings.write_log_event(
                    "proxy_configuration_fetch_failed", "ERROR", stage="json_parse", exception_type=type(json_error).__name__, error=str(json_error), traceback=traceback.format_exc()
                )

                return {"valid": False, "data": None, "error": (f"JSON parsing error: {str(json_error)}")}

            # --------------------------------------------------
            # Vérifie que le JSON obtenu possède la structure
            # attendue : un dictionnaire.
            # --------------------------------------------------
            if not isinstance(data, dict):
                Settings.write_log_event("proxy_configuration_fetch_failed", "ERROR", stage="validation", reason="response_data_not_object", response_type=type(data).__name__)

                return {"valid": False, "data": None, "error": "Invalid proxy response format"}

            # --------------------------------------------------
            # Extrait les IPs présentes dans les clés retournées
            # par l'API.
            #
            # Exemple :
            #
            # {
            #     "1.1.1.1#proxy1": {...},
            #     "2.2.2.2#proxy2": {...}
            # }
            #
            # devient :
            #
            # {
            #     "1.1.1.1",
            #     "2.2.2.2"
            # }
            #
            # split("#")[0] récupère la partie située avant "#".
            # --------------------------------------------------
            api_ips = set(k.split("#")[0] for k in data.keys())

            # --------------------------------------------------
            # Identifie les IPs attendues mais absentes de la
            # réponse API.
            #
            # Exemple :
            #
            # unique_ips :
            # {
            #     "1.1.1.1",
            #     "2.2.2.2",
            #     "3.3.3.3"
            # }
            #
            # api_ips :
            # {
            #     "1.1.1.1",
            #     "2.2.2.2"
            # }
            #
            # missing :
            # {
            #     "3.3.3.3"
            # }
            # --------------------------------------------------
            missing = unique_ips - api_ips

            # --------------------------------------------------
            # Identifie les IPs retournées par l'API mais qui
            # n'étaient pas demandées.
            #
            # Ces IPs sont enregistrées dans les logs mais ne
            # provoquent pas directement un échec dans la logique
            # actuelle.
            # --------------------------------------------------
            extra = api_ips - unique_ips

            Settings.write_log_event(
                "proxy_configuration_compared", "INFO", expected_ip_count=len(unique_ips), returned_ip_count=len(api_ips), missing_ip_count=len(missing), extra_ip_count=len(extra)
            )

            # --------------------------------------------------
            # Si une IP attendue est absente, la configuration
            # reçue est considérée comme invalide.
            # --------------------------------------------------
            if missing:
                Settings.write_log_event(
                    "proxy_configuration_fetch_failed",
                    "ERROR",
                    stage="validation",
                    reason="missing_expected_ips",
                    missing_ip_count=len(missing),
                    response_key_count=(len(data) if isinstance(data, dict) else None),
                )

                return {
                    "valid": False,
                    "data": data,
                    "error": (
                        "Données du service non valides : " "certaines adresses IP attendues sont " "absentes de la réponse. Veuillez " "réessayer ou contacter le support si " "le problème persiste."
                    ),
                }

            # --------------------------------------------------
            # Toutes les IPs attendues sont présentes.
            # La configuration peut donc être considérée comme
            # valide selon les règles actuelles.
            # --------------------------------------------------
            Settings.write_log_event("proxy_configuration_fetch_completed", "INFO", ip_count=len(api_ips))

            return {"valid": True, "data": data, "error": None}

        except Exception as e:
            # --------------------------------------------------
            # Capture toute exception inattendue qui n'a pas été
            # traitée par les blocs précédents.
            #
            # Cela protège l'appelant contre une propagation
            # inattendue de l'exception.
            # --------------------------------------------------
            Settings.write_log_event("proxy_configuration_fetch_failed", "ERROR", stage="unexpected", exception_type=type(e).__name__, error=str(e), traceback=traceback.format_exc())

            return {"valid": False, "data": None, "error": str(e)}


# ==========================================================
# Instance globale
# ==========================================================

# ----------------------------------------------------------
# Création d'une instance unique du client API.
#
# Les autres modules peuvent ensuite importer directement :
#
# from api.safe_api_manager import API_MANAGER
#
# et utiliser :
#
# API_MANAGER.makeRequest(...)
# API_MANAGER.saveEmail(...)
# API_MANAGER.sendStatus(...)
# API_MANAGER.fetchScenarios(...)
#
# Cela évite de recréer un ApiClient et une requests.Session
# dans chaque partie de l'application.
# ----------------------------------------------------------
API_MANAGER = ApiClient()
