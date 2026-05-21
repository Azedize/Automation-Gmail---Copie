#!/usr/bin/env python3
"""
Script de test pour l'API handle_save_scenario
Teste l'endpoint de sauvegarde de scénario
"""

import requests
import json
import urllib3

# Désactiver les avertissements SSL (comme dans votre code)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_save_scenario_api():
    """
    Test de l'API de sauvegarde de scénario
    """

    # 🔗 URL de l'API (avec le paramètre l dans l'URL)
    api_url = "https://reporting.nrb-apps.com/pub/ReportingV4/senario.php?rv4=1&entity=IT&action=add&l=WsWSwmgXwQfGTY89CZQAN1EL5TcHjkxrkiWCkCpbHK1bA8C+ngdEmkCRx0T0FpmieI+CKkgP6hmF3cvE2Ul5+g=="

    # 📦 Payload (form-data)
    payload = {
        "user_id": "3895",
        "encrypted": "WsWSwmgXwQfGTY89CZQAN1EL5TcHjkxrkiWCkCpbHK1bA8C+ngdEmkCRx0T0FpmieI+CKkgP6hmF3cvE2Ul5+g==",
        "name": "eeeeeeeeeee", # name unique pour chaque scénario
        "state": json.dumps({
            "id": "mark_as_important",
            "label": "Mark As Important",
            "actions": ["spamSelectMarkAsRead", "spamSelectAddStar", "spamSelectArchive", "spamSelectNotSpam"],
            "Template": "Template2"
        }),
        "state_stack": json.dumps([
            {
                "id": "open_spam",
                "label": "Open Spam",
                "showOnInit": True,
                "actions": ["spamOpenMessage", "spamSelectAll"],
                "Template": "Template1"
            },
            {
                "id": "select_all",
                "label": "Select All",
                "actions": ["spamSelectMarkAsRead", "spamSelectMarkAsImportant", "spamSelectAddStar", "spamSelectArchive", "spamSelectNotSpam"],
                "Template": "Template2"
            },
            {
                "id": "mark_as_important",
                "label": "Mark As Important",
                "actions": ["spamSelectMarkAsRead", "spamSelectAddStar", "spamSelectArchive", "spamSelectNotSpam"],
                "Template": "Template2"
            }
        ])
    }

    # 📝 Headers
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    # print("🚀 [TEST] Démarrage du test API handle_save_scenario")
    # print(f"🔗 [TEST] URL: {api_url}")
    # print(f"📋 [TEST] Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    # print(f"📝 [TEST] Headers: {headers}")

    settings.WRITE_LOG_DEV_FILE("🚀 [TEST] Démarrage du test API handle_save_scenario", "INFO")
    settings.WRITE_LOG_DEV_FILE(f"🔗 [TEST] URL: {api_url}", "INFO")
    settings.WRITE_LOG_DEV_FILE(f"📋 [TEST] Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}", "INFO")
    settings.WRITE_LOG_DEV_FILE(f"📝 [TEST] Headers: {headers}", "INFO")

    try:
        # 📡 Envoi de la requête
        # print("\n📡 [TEST] Envoi de la requête POST...")
        settings.WRITE_LOG_DEV_FILE("📡 [TEST] Envoi de la requête POST...", "INFO")
        response = requests.post(  api_url, data=payload, headers=headers,  verify=False,  timeout=30 )
        
        # print(json.dumps({
        #     "status_code": response.status_code,
        #     "headers": dict(response.headers),
        #     "text": response.text
        # }, indent=2, ensure_ascii=False))

        settings.WRITE_LOG_DEV_FILE(json.dumps({
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "text": response.text
        }, indent=2, ensure_ascii=False), "INFO")

        # print(f"➡️ [TEST] Status Code: {response.status_code}")
        # print(f"📄 [TEST] Headers Response: {dict(response.headers)}")
        # print(f"📄 [TEST] Response Text: {response.text}")

        settings.WRITE_LOG_DEV_FILE(f"➡️ [TEST] Status Code: {response.status_code}", "INFO")
        settings.WRITE_LOG_DEV_FILE(f"📄 [TEST] Headers Response: {dict(response.headers)}", "INFO")
        settings.WRITE_LOG_DEV_FILE(f"📄 [TEST] Response Text: {response.text}", "INFO")

        # 🔍 Tentative de parsing JSON
        try:
            json_response = response.json()
            # print(f"✅ [TEST] JSON Response: {json.dumps(json_response, indent=2, ensure_ascii=False)}")
            settings.WRITE_LOG_DEV_FILE(f"✅ [TEST] JSON Response: {json.dumps(json_response, indent=2, ensure_ascii=False)}", "INFO")
        except json.JSONDecodeError:
            # print("⚠️ [TEST] Réponse non-JSON")
            settings.WRITE_LOG_DEV_FILE("⚠️ [TEST] Réponse non-JSON", "WARNING")

        # 📊 Analyse du résultat
        if response.status_code == 200:
            # print("✅ [TEST] Requête réussie (HTTP 200)")
            settings.WRITE_LOG_DEV_FILE("✅ [TEST] Requête réussie (HTTP 200)", "INFO")
            if 'status' in response.text.lower():
                if '"status":true' in response.text or '"status":"true"' in response.text:
                    # print("🎉 [TEST] Scénario sauvegardé avec succès !")
                    settings.WRITE_LOG_DEV_FILE("🎉 [TEST] Scénario sauvegardé avec succès !", "INFO")
                elif '"status":false' in response.text or '"status":"false"' in response.text:
                    # print("❌ [TEST] Échec de la sauvegarde du scénario")
                    settings.WRITE_LOG_DEV_FILE("❌ [TEST] Échec de la sauvegarde du scénario", "ERROR")
                else:
                    # print("🤔 [TEST] Statut inconnu dans la réponse")
                    settings.WRITE_LOG_DEV_FILE("🤔 [TEST] Statut inconnu dans la réponse", "WARNING")
        else:
            # print(f"❌ [TEST] Erreur HTTP: {response.status_code}")
            settings.WRITE_LOG_DEV_FILE(f"❌ [TEST] Erreur HTTP: {response.status_code}", "ERROR")

    except requests.RequestException as e:
        # print(f"🔥 [TEST] Exception lors de la requête: {e}")
        settings.WRITE_LOG_DEV_FILE(f"🔥 [TEST] Exception lors de la requête: {e}", "ERROR")
    except Exception as e:
        # print(f"💥 [TEST] Exception générale: {e}")
        settings.WRITE_LOG_DEV_FILE(f"💥 [TEST] Exception générale: {e}", "ERROR")

    # print("\n🏁 [TEST] Fin du test API")
    settings.WRITE_LOG_DEV_FILE("\n🏁 [TEST] Fin du test API", "INFO")

if __name__ == "__main__":
    test_save_scenario_api()
    
    
    

