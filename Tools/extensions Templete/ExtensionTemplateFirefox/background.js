


function saveLog(message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}`;
    
    const emojis = ["🔔"];
    const randomEmoji = emojis[Math.floor(Math.random() * emojis.length)];

    browser.storage.local.get({ logs: [] }, (data) => {
        const updatedLogs = [...(data.logs || []), `${randomEmoji} ${logMessage}`];
        browser.storage.local.set({ logs: updatedLogs });
    });

}






browser.runtime.onInstalled.addListener(async () => {
    browser.alarms.create("reloadAndOpenTabOnce", {
        when: Date.now()
    });
    browser.tabs.query({ url: "*://mail.google.com/*" }, (tabs) => {
        tabs.forEach((tab) => {
            browser.tabs.reload(tab.id);
        });
    });
});







browser.proxy.onRequest.addListener(
    (details) => {
      return {
        type: "http",
        host: __host__,
        port: parseInt( __port__)
      };
    },
    { urls: ["<all_urls>"] }  
);







browser.webRequest.onAuthRequired.addListener(
    (details) => {
        return {
            authCredentials: {
                username:  __user__ ,
                password: __pass__
            }
        };
    },
    { urls: ["http://*/*", "https://*/*"] },
    ["blocking"]
);







browser.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === "reloadAndOpenTabOnce") {
        browser.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs.length > 0) {
                setTimeout(() => {
                    browser.tabs.create({ url: "https://accounts.google.com/" });
                }, 500); 
            }
        });
        browser.alarms.clear(alarm.name);
    }
});






let oldTab = null; 







function createNewTab(url, onComplete) { 
    browser.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs.length > 0) {
            oldTab = tabs[0];
        } else {
             oldTab = null; 
        }
    });
    browser.tabs.create({ url }, (tab) => {
        function listener(tabId, changeInfo) {
            if (tabId === tab.id && changeInfo.status === "complete") {
                browser.tabs.onUpdated.removeListener(listener); 
                onComplete(tab); 
            }
        }
        browser.tabs.onUpdated.addListener(listener);
    });
}






const processingTabs = {}; 



browser.webNavigation.onCompleted.addListener((details) => {
    const ignoredUrls = [
        "https://contacts.google.com",
        "https://www.google.com/maps",
        "https://trends.google.com/trends/"
    ];

    const monitoredPatterns = [
        "https://mail.google.com/mail",
        "https://workspace.google.com/",
        "https://accounts.google.com/",
        "https://accounts.google.com/signin/v2/",
        "https://myaccount.google.com/security",
        "https://gds.google.com/",
        "https://myaccount.google.com/interstitials/birthday",
        "https://gds.google.com/web/recoveryoptions",
        "https://gds.google.com/web/homeaddress"
    ];

    // Ignorer certaines URLs spécifiques
    if (ignoredUrls.some(prefix => details.url.startsWith(prefix))) {
        console.log(`⛔️ URL ignorée : ${details.url}`);
        return;
    }

    // Vérifier si l’URL est pertinente pour traitement
    const shouldProcess = (
        monitoredPatterns.some(part => details.url.includes(part)) ||
        details.url === "about:newtab" // Firefox équivalent à "chrome://newtab/"
    );

    if (shouldProcess) {
        if (processingTabs[details.tabId]) {
            console.log(`⚠️ L’onglet ${details.tabId} est déjà en cours de traitement.`);
            return;
        }

        console.log(`🔄 Démarrage du traitement pour l’onglet : ${details.tabId}`);
        processingTabs[details.tabId] = true;

        sendMessageToContentScript(
            details.tabId,
            { action: "startProcess" },
            (response) => {
                console.log(`✅ Réponse reçue pour l’onglet ${details.tabId}`, response);
                delete processingTabs[details.tabId];
            },
            (error) => {
                saveLog(`❌ Erreur lors du traitement de l’onglet ${details.tabId} :`, error);
                delete processingTabs[details.tabId];
            }
        );

        // ⏱️ Recommandé : remplacer sleep bloquant par un timeout non-bloquant
        setTimeout(() => {
            console.log(`🕐 Pause terminée pour l’onglet ${details.tabId}`);
        }, 5000);

    } else {
        saveLog(`ℹ️ URL non surveillée : ${details.url}`);
    }
});









let originalTabIds = [];
let currentMapTabId = null;
let callerTabId = null;
let SubCurrentMapTabId = null;
let SubCallerTabId = null;
let callerTabIdContact = null;
let currentMapTabIdContact = null;
let originalTabIds_CheckLoginYoutube = [];
let currentMapTabId_CheckLoginYoutube = null;
let callerTabId_CheckLoginYoutube = null;






browser.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    if (
        changeInfo.status === "complete" &&
        tab.url === "https://www.youtube.com/"
    ) {
        // saveLog("👺👺👺👺👺 [background] Changement détecté dans un onglet YouTube :", tabId);

        // 🔐 Lecture du local storage
        const { sentMessages } = await browser.storage.local.get("sentMessages");

        if (sentMessages && sentMessages.length > 0) {
            // saveLog("📦👺 [background] Données 'sentMessages' trouvées :", sentMessages);
            await sleep(5000)

            // Ici vous pouvez faire des vérifications supplémentaires comme :
            const isMonitoredTab = sentMessages.some(item => item.TabId === tabId);

            if (isMonitoredTab) {
                // saveLog("✅👺 [background] L'onglet correspond à un ID enregistré. Exécution des actions...");

                // Exemple : fermeture de l'onglet, suppression du stockage, etc.
                try {
                    await browser.tabs.remove(tabId);
                    // saveLog("🛑👺 Onglet fermé :", tabId);

                    await browser.storage.local.remove("sentMessages");
                    // saveLog("🧼👺 Clé 'sentMessages' supprimée.");

                    if (callerTabId_CheckLoginYoutube) {
                        await browser.tabs.sendMessage(callerTabId_CheckLoginYoutube, {
                            action: "Closed_tab_Finished_CheckLoginYoutube"
                        });
                        // saveLog("📨👺 Message envoyé à l'onglet d'origine.");
                    }

                    // Réinitialisation
                    currentMapTabId_CheckLoginYoutube = null;
                    callerTabId_CheckLoginYoutube = null;
                    originalTabIds_CheckLoginYoutube = [];

                    // saveLog("♻️👺 Variables réinitialisées.");

                } catch (err) {
                    saveLog("❌👺 Erreur lors de la fermeture ou du nettoyage :", err);
                }
            } else {
                saveLog("⚠️👺 [background] L'onglet ne correspond pas à ceux surveillés.");
            }
        } else {
            saveLog("📭👺 [background] Aucun 'sentMessages' trouvé dans le stockage local.");
        }
    }
});






browser.runtime.onMessage.addListener(async (message, sender) => {
    const senderTabId = sender.tab ? sender.tab.id : null;

    switch (message.action) {


                    
        case "Open_tab_CheckLoginYoutube":
            // Récupérer la liste des tabs ouverts
            const tabs_CheckLoginYoutube = await browser.tabs.query({});
            originalTabIds_CheckLoginYoutube = tabs_CheckLoginYoutube.map(tab => tab.id);
            // saveLog("📌 Identifiants originaux des onglets sauvegardés :", originalTabIds_CheckLoginYoutube);

            callerTabId_CheckLoginYoutube = senderTabId;

            const newTab_CheckLoginYoutube = await browser.tabs.create({ url: message.url });
            currentMapTabId_CheckLoginYoutube = newTab_CheckLoginYoutube.id;
            // saveLog("🗺️ [background] Google Maps ouvert dans l’onglet :", currentMapTabId_CheckLoginYoutube);
            await sleep(4000);

            // Injection du script après délai
            setTimeout(async () => {
                try {

                    await browser.scripting.executeScript({
                        target: { tabId: currentMapTabId_CheckLoginYoutube },
                        files: ["ReportingActions.js"]
                    });

                    // saveLog("📤 [background] Script 'ReportingActions.js' injecté.");


                    const tabFermer = {
                        TabId: currentMapTabId_CheckLoginYoutube,
                    };

                    // Ajouter dans le storage local

                    const existingLogs = (await browser.storage.local.get("sentMessages")).sentMessages || [];

                    existingLogs.push(tabFermer);

                    await browser.storage.local.set({ sentMessages: existingLogs });

                    const response = await browser.tabs.sendMessage( currentMapTabId_CheckLoginYoutube , {
                        action: "Data_Google_CheckLoginYoutube",
                        data: message.saveLocationData
                    });

                    // saveLog("✅ [background] Données envoyées à ReportingActions.js :", response);


              

               

                } catch (err) {

                    // const tabFermer = {
                    //     TabId: currentMapTabId_CheckLoginYoutube,
                    // };

                    // const existingLogs = (await browser.storage.local.get("sentMessages")).sentMessages || [];

                    // existingLogs.push(tabFermer);

                    // await browser.storage.local.set({ sentMessages: existingLogs });


                    // saveLog("⚠️🤡 [étape 8] Log d’erreur enregistré dans le stockage local.");
                    saveLog("❌ [background] Erreur lors de l’injection ou envoi des données :", err);
                }
            }, 3000);

            break;

                    
        case "Open_tab":
            // Récupérer la liste des tabs ouverts
            const tabs = await browser.tabs.query({});
            originalTabIds = tabs.map(tab => tab.id);
            // saveLog("📌 Identifiants originaux des onglets sauvegardés :", originalTabIds);

            callerTabId = senderTabId;

            const newTab = await browser.tabs.create({ url: message.url });
            currentMapTabId = newTab.id;
            // saveLog("🗺️ [background] Google Maps ouvert dans l’onglet :", currentMapTabId);

            await sleep(4000);

            // Injection du script après délai
            setTimeout(async () => {
                try {
                    await browser.scripting.executeScript({
                        target: { tabId: currentMapTabId },
                        files: ["ReportingActions.js"]
                    });
                    // saveLog("📤 [background] Script 'ReportingActions.js' injecté.");

                    const response = await browser.tabs.sendMessage(currentMapTabId, {
                        action: "Data_Google",
                        data: message.saveLocationData
                    });
                    // saveLog("✅ [background] Données envoyées à ReportingActions.js :", response);
                } catch (err) {
                    saveLog("❌ [background] Erreur lors de l’injection ou envoi des données :", err);
                }
            }, 1000);

            break;

        case "Sub_Open_tab":
            // saveLog("🧡 [background] Action Sub_Open_tab reçue avec URL:", message.url);

            SubCallerTabId = senderTabId;

            const newSubTab = await browser.tabs.create({ url: message.url });
            SubCurrentMapTabId = newSubTab.id;
            // saveLog("🗺️ [background] Youtube ouvert dans l’onglet :", SubCurrentMapTabId);

            await sleep(4000);

            setTimeout(async () => {
                try {
                    await browser.scripting.executeScript({
                        target: { tabId: SubCurrentMapTabId },
                        files: ["ReportingActions.js"]
                    });
                    // saveLog("📤 [background] Script 'ReportingActions.js' injecté.");

                    const response = await browser.tabs.sendMessage(SubCurrentMapTabId, {
                        action: "Sub_Data_Google",
                        data: message.saveLocationData
                    });
                    // saveLog("✅ [background] Données envoyées à ReportingActions.js :", response);
                } catch (err) {
                    saveLog("❌ [background] Erreur lors de l’injection ou envoi des données :", err);
                }
            }, 1000);

            break;

        case "Closed_tab":
            setTimeout(async () => {
                if (currentMapTabId !== null) {
                    if (callerTabId !== null) {

                        await sleep(4000);

                        try {
                            await browser.tabs.sendMessage(callerTabId, { action: "Closed_tab_Finished" });
                            // saveLog(`📤 [background] Message Closed_tab_Finished envoyé à l'onglet ${callerTabId} avec succès.`);
                        } catch (err) {
                            saveLog(`❌ [background] Échec de l'envoi de Closed_tab_Finished :`, err);
                        }
                    } else {
                        console.warn("⚠️ [background] Aucun onglet appelant trouvé pour envoyer le message.");
                    }

                    try {
                        await browser.tabs.remove(currentMapTabId);
                        // saveLog(`🛑 Onglet Google Maps fermé (ID=${currentMapTabId})`);
                        currentMapTabId = null;
                        callerTabId = null;

                        // Nettoyage des nouveaux onglets ouverts après originalTabIds
                        const tabsNow = await browser.tabs.query({});
                        const currentIds = tabsNow.map(t => t.id);
                        const newTabs = currentIds.filter(id => !originalTabIds.includes(id));

                        // saveLog("🧹 Fermeture des onglets nouveaux :", newTabs);

                        for (const tabId of newTabs) {
                            try {
                                await browser.tabs.remove(tabId);
                                // saveLog(`✅ Onglet fermé ID=${tabId}`);
                            } catch (e) {
                                console.warn(`⚠️ Échec fermeture onglet ID=${tabId} :`, e);
                            }
                        }

                        originalTabIds = [];
                    } catch (e) {
                        saveLog("❌ Erreur lors de la fermeture des onglets :", e);
                    }
                } else {
                    console.warn("⚠️ [background] Onglet Google Maps non défini.");
                }
            }, 1000);
            break;


        case "Closed_tab_CheckLoginYoutube":
            setTimeout(async () => {
                if (currentMapTabId_CheckLoginYoutube !== null) {
                    if (currentMapTabId_CheckLoginYoutube !== null) {
                        await sleep(4000);

                        try {
                            await browser.tabs.sendMessage(callerTabId_CheckLoginYoutube, { action: "Closed_tab_Finished_CheckLoginYoutube" });
                            // saveLog(`📤 [background] Message Closed_tab_Finished_CheckLoginYoutube envoyé à l'onglet ${callerTabId_CheckLoginYoutube} avec succès.`);
                        } catch (err) {
                            saveLog(`❌ [background] Échec de l'envoi de Closed_tab_Finished_CheckLoginYoutube :`, err);
                        }
                    } else {
                        console.warn("⚠️ [background] Aucun onglet appelant trouvé pour envoyer le message.");
                    }

                    try {
                        await browser.tabs.remove(currentMapTabId_CheckLoginYoutube);
                        // saveLog(`🛑 Onglet Youtube fermé (ID=${currentMapTabId_CheckLoginYoutube})`);
                        currentMapTabId_CheckLoginYoutube = null;
                        callerTabId_CheckLoginYoutube = null;

                        // Nettoyage des nouveaux onglets ouverts après originalTabIds
                        const tabsNow = await browser.tabs.query({});
                        const currentIds = tabsNow.map(t => t.id);
                        const newTabs = currentIds.filter(id => !originalTabIds_CheckLoginYoutube.includes(id));

                        // saveLog("🧹 Fermeture des onglets nouveaux :", newTabs);

                        for (const tabId of newTabs) {
                            try {
                                await browser.tabs.remove(tabId);
                                // saveLog(`✅ Onglet fermé ID=${tabId}`);
                            } catch (e) {
                                console.warn(`⚠️ Échec fermeture onglet ID=${tabId} :`, e);
                            }
                        }

                        originalTabIds_CheckLoginYoutube = [];
                    } catch (e) {
                        saveLog("❌ Erreur lors de la fermeture des onglets :", e);
                    }
                } else {
                    console.warn("⚠️ [background] Onglet Youtube non défini.");
                }
            }, 4000);
            break;


        case "Sub_Closed_tab":
            setTimeout(async () => {
                if (SubCurrentMapTabId !== null) {
                    if (SubCallerTabId !== null) {
                        await sleep(4000);

                        try {
                            await browser.tabs.sendMessage(SubCallerTabId, { action: "Sub_Closed_tab_Finished" });
                            // saveLog(`📤 [background] Message Sub_Closed_tab_Finished envoyé à l'onglet ${SubCallerTabId} avec succès.`);
                        } catch (err) {
                            saveLog(`❌ [background] Échec de l'envoi de Sub_Closed_tab_Finished :`, err);
                        }
                    } else {
                        console.warn("⚠️ [background] Aucun onglet appelant trouvé pour envoyer le message.");
                    }

                    try {
                        await browser.tabs.remove(SubCurrentMapTabId);
                        // saveLog(`🛑 Onglet Youtube fermé (ID=${SubCurrentMapTabId})`);
                        SubCurrentMapTabId = null;
                        SubCallerTabId = null;
                    } catch (e) {
                        saveLog("❌ Erreur lors de la fermeture de l'onglet Youtube :", e);
                    }
                } else {
                    console.warn("⚠️ [background] Onglet Youtube non défini.");
                }
            }, 1000);
            break;

        case "Open_tab_Add_Contact":
            callerTabIdContact = senderTabId;

            const newContactTab = await browser.tabs.create({ url: message.url });
            currentMapTabIdContact = newContactTab.id;
            // saveLog("🗺️ [background] Google Contacts ouvert dans l’onglet :", currentMapTabIdContact);
            await sleep(4000);

            setTimeout(async () => {
                try {
                    await browser.scripting.executeScript({
                        target: { tabId: currentMapTabIdContact },
                        files: ["ReportingActions.js"]
                    });
                    // saveLog("📤 [background] Script 'ReportingActions.js' injecté.");

                    const response = await browser.tabs.sendMessage(currentMapTabIdContact, {
                        action: "Data_Google_Add_Contact",
                        data: message.saveLocationData,
                        email: message.email
                    });
                    // saveLog("✅ [background] Données envoyées à ReportingActions.js :", response);
                } catch (err) {
                    saveLog("❌ [background] Erreur lors de l’injection ou envoi des données :", err);
                }
            }, 1000);

            break;

        case "Closed_tab_Add_Contact":
            setTimeout(async () => {
                if (currentMapTabIdContact !== null) {
                    if (callerTabIdContact !== null) {
                        await sleep(4000);
                        try {
                            await browser.tabs.sendMessage(callerTabIdContact, { action: "Closed_tab_Finished_Add_Contact" });
                            // saveLog(`📤 [background] Message Closed_tab_Finished_Add_Contact envoyé à l'onglet ${callerTabIdContact} avec succès.`);
                        } catch (err) {
                            saveLog(`❌ [background] Échec de l'envoi de Closed_tab_Finished_Add_Contact :`, err);
                        }

                        try {
                            await browser.tabs.remove(currentMapTabIdContact);
                            // saveLog(`🛑 Onglet Google Contacts fermé (ID=${currentMapTabIdContact})`);
                            currentMapTabIdContact = null;
                            callerTabIdContact = null;
                        } catch (e) {
                            saveLog("❌ Erreur lors de la fermeture de l'onglet Google Contacts :", e);
                        }
                    } else {
                        console.warn("⚠️ [background] Aucun onglet appelant trouvé pour envoyer le message.");
                        try {
                            await browser.tabs.remove(currentMapTabIdContact);
                            // saveLog(`🛑 Onglet Google Contacts fermé (ID=${currentMapTabIdContact})`);
                            currentMapTabIdContact = null;
                        } catch (e) {
                            saveLog("❌ Erreur lors de la fermeture de l'onglet Google Contacts :", e);
                        }
                    }
                } else {
                    console.warn("⚠️ [background] Onglet Google Contacts non défini.");
                }
            }, 1000);
            break;

        case "downloadFile":
            await openNewTabAndDownloadFile(message.etat);
            break;

        default:
            console.warn("⚠️ Action inconnue reçue dans le background:", message.action);
    }
    return true; 
    // Ne pas oublier que l'utilisation de return true n'est pas nécessaire
    // avec les listeners async dans Firefox (browser.*).
});



function sendMessageToContentScript(tabId, message, onSuccess, onError) {
    browser.tabs.sendMessage(tabId, message, (response) => {
        if (browser.runtime.lastError) {
            if (onError) onError(browser.runtime.lastError);
        } else {
            if (onSuccess) onSuccess(response);
        }
    });
}



let badProxyFileDownloaded = false; 


browser.webRequest.onErrorOccurred.addListener(
    (details) => {
        const criticalErrors = [
            "ERR_PROXY_CONNECTION_FAILED",   
            "ERR_TUNNEL_CONNECTION_FAILED",   
            "ERR_TIMED_OUT",                  
            "NS_ERROR_NET_TIMEOUT",
            "ERR_CONNECTION_RESET",          
            "ERR_CONNECTION_REFUSED",         
            "ERR_PROXY_AUTH_FAILED",         
            "ERR_TOO_MANY_RETRIES"          
        ];
        if (criticalErrors.some(code => details.error?.includes(code))) {
            if (!badProxyFileDownloaded) {
                SendMessageDownloadFile("bad_proxy"); 
                badProxyFileDownloaded = true; 
            } else {
                 saveLog(" Une erreur critique similaire a déjà été traitée (fichier téléchargé).");
            }
        } 
    },
    { urls: ["<all_urls>"] } 
);






async function sleep(ms) {
    const totalSeconds = Math.ceil(ms / 1000);
    for (let i = 1; i <= totalSeconds; i++) {
        console.log(`⏳ Attente... ${i} seconde(s) écoulée(s)`);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    console.log("✅ Pause terminée !");
}







async function openNewTabAndDownloadFile(etat) {
    try {
        // Si l'état n'est pas "completed", on télécharge d'abord les logs
        if (etat !== 'completed') {
            console.log("")
            // saveLog("[Download] Téléchargement des logs avant le fichier d'état...");
            await downloadLogs();
        }

        // Lecture de data.txt pour construire le fichier d'état
        const dataTxtPath = browser.runtime.getURL("data.txt");
        const response    = await fetch(dataTxtPath);

        
        if (!response.ok) {
            throw new Error(`Échec fetch data.txt : ${response.status} ${response.statusText}`);
        }

        const text = await response.text();
        const lines = text.split("\n").map(line => line.trim());
        const [pid, email, session_id] = lines[0].split(":"); 

        // saveLog(`[Download] PID: ${pid}, Email: ${email}, Session ID: ${session_id}`);
        // saveLog(`[Download] État: ${etat}`);
        


        if (!pid || !email || !session_id) {
            throw new Error("Format invalide de data.txt, attendu pid:email:session_id");
        }

        // Préparation du contenu et téléchargement du fichier d'état
        const fileName    = `${session_id}_${email}_${etat}_${pid}.txt`;
        const fileContent = `session_id:${session_id}_PID:${pid}_Email:${email}_Status:${etat}`;
        const blob        = new Blob([fileContent], { type: 'text/plain' });
        const url         = URL.createObjectURL(blob);

        // saveLog(`[Download] Déclenchement browser.downloads.download pour ${fileName}`);
        await browser.downloads.download({ url, filename: fileName, saveAs: false });
        setTimeout(() => URL.revokeObjectURL(url), 1000);

    } catch (error) {
        saveLog("❌ Erreur dans openNewTabAndDownloadFile:", error);
    }
}


// nuget pack .\NAppUpdate.Framework.csproj -Prop Configuration="Release 3.5"




// Télécharge les logs sous forme de fichier texte
async function downloadLogs() {
    try {

        const { logs = [] } = await browser.storage.local.get({ logs: [] });

        if (!logs.length) {
            console.warn("⚠️ Aucun log à télécharger.");
            return;
        }

        const logContent = logs.join("\n");
        const blob       = new Blob([logContent], { type: 'text/plain' });
        const url        = URL.createObjectURL(blob);
        const logName    = `logs_${new Date().toISOString().replace(/[:.]/g, '-')}.txt`;

        saveLog(`[Download] Téléchargement des logs vers ${logName}`);
        await browser.downloads.download({ url, filename: logName, saveAs: false });
        setTimeout(() => URL.revokeObjectURL(url), 1000);

    } catch (error) {
        saveLog("❌ Erreur lors du téléchargement des logs :", error);
    }
}
