




async function openNewTabAndDownloadFile(etat) {
    try {
        // await downloadLogs();


        if (etat !== 'completed') {
            console.log("")
            // saveLog("[Download] Téléchargement des logs avant le fichier d'état...");
            await downloadLogs();
        }

        const dataTxtPath = chrome.runtime.getURL("data.txt");

        const response = await fetch(dataTxtPath);
        if (!response.ok) {
            throw new Error(`Erreur lors de la lecture de data.txt: ${response.statusText}`);
        }

        const text = await response.text();
        const lines = text.split("\n").map(line => line.trim());



        const [pid, email, session_id] = lines[0].split(":"); 
        const trimmedEmail = email?.trim();

        if (!pid || !trimmedEmail || !session_id) {
            throw new Error("❌ Erreur lors de l'analyse de data.txt : valeurs manquantes.");
        }

    

        const newTab = window.open('https://stackoverflow.com');

        if (!newTab) {
            saveLog("❌ Impossible d'ouvrir un nouvel onglet.");
            return;
        }

        newTab.document.body.innerHTML = `<h1>Téléchargement en cours...</h1><p>PID: ${pid}, Email: ${trimmedEmail}, État: ${etat}</p>`;

        const fileContent = `session_id:${session_id}_PID:${pid}_Email:${trimmedEmail}_Status:${etat}`;
        const blob = new Blob([fileContent], { type: 'text/plain' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `${session_id}_${trimmedEmail}_${etat}_${pid}.txt`;

        newTab.document.body.appendChild(link);

        link.click();
        newTab.document.body.removeChild(link);



    } catch (error) {
        saveLog("❌ Erreur dans le traitement :", error.message);
    }
}






async function downloadLogs() {
    try {

        chrome.storage.local.get({ logs: [] }, async (data) => {
            const logs = data.logs;

            if (!logs.length) {
                saveLog("⚠️ Aucun log disponible pour le téléchargement.");
                return;
            }

            const logContent = logs.join("\n");

            const blob = new Blob([logContent], { type: 'text/plain' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            const fileName = `log_${new Date().toISOString().replace(/[:.]/g, '-')}___email__.txt`;
            link.download = fileName;

            const newTab = window.open('https://stackoverflow.com');
            if (!newTab) {
                saveLog("❌ Impossible d'ouvrir un nouvel onglet.");
                return;
            }

            newTab.document.body.innerHTML = `
                <h1>📥 Téléchargement des logs en cours...</h1>
                <p>Fichier : ${fileName}</p>
            `;
            newTab.document.body.appendChild(link);
            link.click();
            newTab.document.body.removeChild(link);

        });

    } catch (error) {
        saveLog(`❌ Erreur lors du téléchargement des logs : ${error.message}`);
    }
}






const redirectUrls = [
    "https://myaccount.google.com/interstitials/birthday",
    "https://gds.google.com/web/recoveryoptions",
    "https://gds.google.com/web/homeaddress"
];




const createPopup = async () => {
    try {
        await sleep(4000)

        if (redirectUrls.includes(window.location.href)) {
            window.location.href = "https://mail.google.com/mail/u/0/#inbox";
        }
        
        saveLog("🚀 Démarrage du processus ...");


        const completedActions = await new Promise((resolve) => {
            chrome.storage.local.get("completedActions", (result) => {
                resolve(result.completedActions || {});
            });
        });

        const scenario = await fetch(chrome.runtime.getURL("traitement.json"))
            .then(response => response.json())
            .then(data => {
                // Affichage professionnel du JSON
                console.groupCollapsed("%c📦 Contenu de traitement.json", "color: teal; font-weight: bold;");
                saveLog("%c====================", "color: teal;");
                saveLog(JSON.stringify(data, null, 2));  // formatage avec indentation
                saveLog("%c====================", "color: teal;");
                console.groupEnd();
                return data;
            })
            .catch(error => {
                console.log("%c❌ Erreur chargement traitement.json :", "color: red;", error);
                return [];
            });

        const ispProcess = gmail_process;

        await ReportingProcess(scenario, ispProcess);


        clearChromeStorageLocal();

        await openNewTabAndDownloadFile('completed');

    } catch (error) {
        saveLog("%c❌ Erreur lors de la création de la popup :", "color: red;", error.message);
    }
};





function clearChromeStorageLocal() {
    chrome.storage.local.clear(() => {
        if (chrome.runtime.lastError) {
            console.log("❌ Erreur lors de la suppression des données de chrome.storage.local :", chrome.runtime.lastError);
        } 
    });
}







function saveLog(message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}`;
    const emojis = ["🔔"];
    const randomEmoji = emojis[Math.floor(Math.random() * emojis.length)];
    chrome.storage.local.get({ logs: [] }, (data) => {
        const updatedLogs = [...(data.logs || []), `${randomEmoji} ${logMessage}`];
        chrome.storage.local.set({ logs: updatedLogs });
    });
}






async function waitForElement(xpath, timeout = 30) {
    const maxWait = timeout * 1000; 
    const interval = 1000; 
    let elapsed = 0;

    console.log(`⌛ Début de l'attente de l'élément avec XPath: ${xpath} (Max: ${timeout} secondes)`);

    try {
        while (elapsed < maxWait) {
            const element = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (element) {
                console.log(`✅ Élément trouvé: ${xpath}`);
                return true;
            }
            await sleep(interval);
            elapsed += interval;
        }
    } catch (error) {
        console.log(`❌ Erreur lors de la recherche de l'élément: ${error.message}`);
        return false;
    }

    console.log(`❌ Temps écoulé. Élément non trouvé après ${timeout} secondes.`);
    return false;
}





async function findElementByXPath(xpath, timeout = 10, obligatoire = false, type = undefined) {
    const maxWait = timeout * 1000;
    const interval = 500;
    let elapsed = 0;
    let secondsPassed = 0;

    console.log(`🔍 Recherche de l'élément avec XPath: ${xpath}... (Max: ${timeout} secondes)`);

    try {
        while (elapsed < maxWait) {
            const element = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (element) {
                console.log(`✅ Élément trouvé avec XPath: ${xpath}`);
                return element;
            }

            await sleep(interval);
            elapsed += interval;

            if (elapsed >= secondsPassed * 1000) {
                secondsPassed++;
                console.log(`⏳ Recherche... ${secondsPassed} seconde(s) écoulée(s)`);
            }
        }
    } catch (error) {
        console.log(`❌ Erreur lors de la recherche de l'élément: ${error.message}`);
        return null;
    }

    if (obligatoire) {
        console.log(`❗ L'élément obligatoire n'a pas été trouvé après ${timeout} secondes. XPath: ${xpath}`);
    } else {
        console.log(`❌ Élément non trouvé après ${timeout} secondes. XPath: ${xpath}`);
    }

    return null;
}





function getElementTextByXPath(xpath) {
    try {
        console.log(`🔍 Recherche de l'élément avec XPath: ${xpath}...`);

        const element = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;

        if (element) {
            const text = element.textContent.trim();
            console.log(`✅ Élément trouvé avec XPath: ${xpath} | Texte: "${text}"`);
            return text;
        } else {
            console.log(`⚠️ L'élément avec XPath: ${xpath} n'a pas été trouvé.`);
            return null;
        }
    } catch (error) {
        console.log(`❌ Erreur lors de la recherche de l'élément avec XPath: ${xpath} | ${error.message}`);
        return null;
    }
}









function getElementCountByXPath(xpath) {
    try {
        console.log(`🔍 Recherche du nombre d'éléments avec XPath: ${xpath}...`);

        const result = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
        const count = result.snapshotLength;

        console.log(`✅ Nombre d'éléments trouvés avec XPath: ${xpath} est ${count}`);

        return count;
    } catch (error) {
        console.log(`❌ Erreur lors de la recherche des éléments avec XPath: ${xpath} | ${error.message}`);
        return 0;
    }
}






// ✅ دالة لتعديل كل search="__search_value__" بشكل متداخل
function deepReplaceSearchValue(obj, searchValue) {
    if (Array.isArray(obj)) {
        obj.forEach(item => deepReplaceSearchValue(item, searchValue));
    } else if (typeof obj === "object" && obj !== null) {
        for (const key in obj) {
            if (typeof obj[key] === "string" && obj[key].includes("__search_value__")) {
                console.log(`🔁 Remplacement dans [${key}] :`, obj[key], "→", obj[key].replace("__search_value__", searchValue));
                obj[key] = obj[key].replace("__search_value__", searchValue);
            } else {
                deepReplaceSearchValue(obj[key], searchValue);
            }
        }
    }
}





let Email_Contact = null;
let cleanEmail = null;




async function ReportingProcess(scenario, ispProcess) {
    console.log("📝 [ENTRÉE] Démarrage du processus avec les données suivantes :");

    console.log("📚 [SCÉNARIO] Structure du scénario :");
    console.log(JSON.stringify(scenario, null, 2));

    console.log("📦 [ISP PROCESS] Structure du process ISP :");
    console.log(JSON.stringify(ispProcess, null, 2));
    console.log("------------------------------------------------------------");

    let messagesProcessed = 0;
    console.log("🚀 Début du processus de reporting...");

    for (const process of scenario) {
        try {
            console.log(`🚨​🚨​🚨​🚨​🚨​🚨​🚨​ Traitement du processus : '${process.process}'`);

            const currentURL = window.location.href;
            console.log(`🌐 [URL] URL actuelle : ${currentURL}`);

            if (
                (
                    currentURL.includes("https://mail.google.com/mail") ||
                    currentURL.includes("https://myaccount.google.com/?pli=") ||
                    currentURL.startsWith("https://myaccount.google.com/")
                ) &&
                process.process === "login"
            ) {
                console.log("🔐 Page de login détectée. Processus ignoré.");
                continue;
            }

            if (process.process === "loop") {
                const limitLoop = process.limit_loop;
                let stopAllLoops = false;
                // saveLog(`🔁 [LOOP] Début de la boucle avec une limite de ${limitLoop} messages.`);

                // saveLog(`🔁 Début de la boucle (limite: ${limitLoop})`);
                while (messagesProcessed < limitLoop) {
                    if (stopAllLoops) break;

                    if (process.check) {
                        // saveLog(`🧐 [CHECK] Vérification de la condition '${process.check}'...`);
                        const checkResult = await ReportingActions(ispProcess[process.check], process.process);
                        // saveLog(`📋 [RESULT] Résultat de la vérification : ${checkResult}`);
                        if (!checkResult) {
                            // saveLog("❌ Condition échouée. Fin de la boucle.");
                            stopAllLoops = true;
                            break;
                            
                        }
                    }

                    const xpath = `//table[.//colgroup]//tbody/tr`;
                    const messagesOnPage = await getElementCountByXPath(xpath);
                    // saveLog(`📨 [DETECTION] Messages détectés sur la page : ${messagesOnPage}`);
                    saveLog(`📊 Total des messages sur la page : ${messagesOnPage}`);
                    // saveLog(`🔄 État du traitement :\n  - messagesProcessed : ${messagesProcessed}\n  - limitLoop : ${limitLoop}\n  - stopAllLoops : ${stopAllLoops}`);
                    // saveLog(`🚀 Point de départ du traitement (start message) : ${parseInt(process.start)}`);

                    const startIndex = process.start > 0 ? parseInt(process.start) - 1 : 0;
                    for (let i = startIndex ; i < messagesOnPage; i++) {
                        if (stopAllLoops || messagesProcessed >= limitLoop) {
                            stopAllLoops = true;
                            // saveLog("⛔️ [BOUCLE] Limite atteinte ou stop déclenché.");
                            break;
                        }

                        // saveLog(`📩 Traitement de l’email numéro ${messagesProcessed + 1}`);
                        saveLog(`📩 [EMAIL] Traitement de l’email numéro ${messagesProcessed + 1}`);

                        for (const subProcess of process.sub_process) {
                            if (stopAllLoops) break;

                            const prcss = [...ispProcess[subProcess.process]];
                            addUniqueIdsToActions(prcss);

                            // saveLog(`⚙️ [SUBPROCESS] Sous-processus : ${subProcess.process}`);

                            if (subProcess.process === "OPEN_MESSAGE_ONE_BY_ONE") {
                                saveLog("📬 [ACTION] Ouverture du message un par un.");
                                prcss.forEach(p => {
                                    const oldXPath = p.xpath;
                                    p.xpath = p.xpath.replace(/\[(\d+)\]/, `[${i + 1}]`);
                                    // saveLog(`🧬 XPath modifié: ${oldXPath} ➡️ ${p.xpath}`);
                                });



                                // saveLog("🚀 Lancement de ReportingActions pour OPEN_MESSAGE_ONE_BY_ONE...");
                                await ReportingActions(prcss, process.process);
                                // saveLog("✅ Fin de ReportingActions pour OPEN_MESSAGE_ONE_BY_ONE.");
                                continue;
                            }

                            if (subProcess.process === "add_contacts") {

                                saveLog("📍 [add_contacts] Démarrage du processus 'add_contacts'...");

                                let saveLocationData = [...ispProcess[subProcess.process]];;
                                // saveLog("🗂️ [add_contacts DATA] Données associées au processus 'add_contacts' (avant remplacement) :");
                                // saveLog(JSON.stringify(saveLocationData, null, 2));

                                Email_Contact = await findElementByXPath('//table//tbody//tr//td//h3//span[@translate and @role="gridcell"]//span[@email and @name and @data-hovercard-id]');
                                
                                if (!Email_Contact) {
                                    saveLog("🚫 [CONTACT] Élément cible introuvable.");
                                    return;
                                }

                                cleanEmail = Email_Contact.getAttribute("email");
                                saveLog(`📧 [CONTACT] Email extrait : ${cleanEmail}`);

                                // 🔥 Remplacement détaillé avec log clé par clé
                                const saveLocationDataUpdated = JSON.parse(JSON.stringify(saveLocationData).replace(/__Email_Contact__/g, cleanEmail));

                                // saveLog("📊 [REMPLACEMENT] Détails des changements dans saveLocationData :");

                                const keys = Object.keys(saveLocationData);

                                keys.forEach((key) => {
                                    const avant = JSON.stringify(saveLocationData[key]);
                                    const apres = JSON.stringify(saveLocationDataUpdated[key]);
                                    if (avant !== apres) {
                                        // saveLog(`🔄 Clé : ${key}`);
                                        // saveLog(`   Avant : ${avant}`);
                                        // saveLog(`   Après : ${apres}`);
                                    } else {
                                        // saveLog(`✅ Clé : ${key} (inchangée)`);
                                        console.log("");
                                    }
                                });

                                // saveLog("🗂️ [add_contacts DATA] Données finales après remplacement :");
                                // saveLog(JSON.stringify(saveLocationDataUpdated, null, 2));

                                chrome.runtime.sendMessage({ 
                                    action: "Open_tab_Add_Contact", 
                                    saveLocationData: saveLocationDataUpdated,
                                    email: cleanEmail, 
                                    url: "https://contacts.google.com/new"
                                });

                                await waitForBackgroundToFinish('Closed_tab_Finished_Add_Contact');
                                continue;
                            }

                            if (subProcess.process === "next" || subProcess.process === "next_page") {
                                // saveLog("➡️ Vérification de la page suivante...");
                                // saveLog("➡️ [PAGINATION] Vérification s'il existe une page suivante...");
                                const checkNextResult = await ReportingActions(ispProcess["CHECK_NEXT"], process.process);
                                if (!checkNextResult) {
                                    saveLog("🚫 [STOP] Aucune page suivante détectée.");
                                    break;
                                }

                                saveLog("📤 Passage à la page suivante...");
                                saveLog("📤 [NAVIGATION] Passage à la page suivante...");

                                await ReportingActions(ispProcess[subProcess.process], process.process);
                            } else {
                                // saveLog(`🔧 [ACTION] Exécution de l’action '${subProcess.process}'`);
                                await ReportingActions(ispProcess[subProcess.process], process.process);
                            }
                        }

                        messagesProcessed++;
                        saveLog(`✅ Emails traités jusqu'à présent : ${messagesProcessed}`);
                    }

                    if (!stopAllLoops && messagesProcessed < limitLoop) {
                        // saveLog("🔄 Passage manuel à la page suivante...");
                        const checkNextResult = await ReportingActions(ispProcess["CHECK_NEXT"], process.process);
                        if (!checkNextResult) {
                            saveLog("🚫 Aucune page suivante détectée.");
                            break;
                        }

                        const nextPageActions = [...ispProcess["next_page"]];
                        addUniqueIdsToActions(nextPageActions);
                        saveLog("➡️ [PAGE] Passage à la prochaine page de résultats...");
                        await ReportingActions(nextPageActions, process.process);
                    }
                }

                saveLog("✅ Fin de la boucle.");

            } else if (process.process === "search") {
                saveLog(`🔍 Recherche en cours : ${process.value}`);
                const updatedProcesses = ispProcess[process.process].map(item => {
                    const updatedItem = { ...item };
                    if (updatedItem.value && updatedItem.value.includes("__search__")) {
                        updatedItem.value = updatedItem.value.replace("__search__", process.value);
                    }
                    return updatedItem;
                });

                await ReportingActions(updatedProcesses, process.process);

            } else if (process.process === "CHECK_FOLDER") {
                // saveLog("📁 Vérification du dossier...");
                const checkFolderResult = await ReportingActions(ispProcess[process.check], process.process);
                if (!checkFolderResult) {
                    // saveLog("🚫 Le dossier n’existe pas ou la vérification a échoué.");
                    break;
                }
            } else if (process.process === "google_preferred_addresses" || 
                        process.process === "google_travel_projects" ||
                        process.process === "google_places_to_visit" ||
                        process.process === "google_favorite_places" ||
                        process.process === "google_restaurants" || 
                        process.process === "google_attractions"|| 
                        process.process === "google_museums"|| 
                        process.process === "google_transit"|| 
                        process.process === "google_pharmacies"||
                        process.process === "google_atms"

                    ) {



                    // saveLog("📍 [SAVE_LOCATION] Démarrage du processus 'save_location'...");

                    const saveLocationData = ispProcess[process.process];

                    // ✅ Avant modification
                    // saveLog("🧾 [AVANT MODIFICATION] Données brutes :");
                    // saveLog(JSON.stringify(saveLocationData, null, 2));

                    // ✅ Remplacement profond
                    deepReplaceSearchValue(saveLocationData, process.search);

                    // ✅ Après modification
                    // saveLog("✅ [APRÈS MODIFICATION] Données prêtes à l'envoi :");
                    // saveLog(JSON.stringify(saveLocationData, null, 2));

                    // ✅ Envoi au background
                    chrome.runtime.sendMessage({
                        action: "Open_tab",
                        saveLocationData: saveLocationData,
                        url: "https://www.google.com/maps"
                    });

                    // ✅ Attente de fin
                    await waitForBackgroundToFinish('Closed_tab_Finished');


            }else if (process.process === "google_trends"  ) {
                console.log("📍 [trends_google] Démarrage du processus 'trends_google'...");
                const saveLocationData = ispProcess[process.process];
                console.log("🗂️ [trends_google DATA] Données associées au processus 'trends_google' :");
                console.log(JSON.stringify(saveLocationData, null, 2));    
                chrome.runtime.sendMessage({ action: "Open_tab" , saveLocationData: saveLocationData  , url: "https://trends.google.com/trends/" });
                await  waitForBackgroundToFinish('Closed_tab_Finished')
                    
            }else if (process.process === "news_google"  ) {

                // saveLog("📍 [news_google] Démarrage du processus 'news_google'...");
                const saveLocationData = ispProcess[process.process];
                // saveLog("🗂️ [news_google DATA] Données associées au processus 'news_google' :");
                // saveLog(JSON.stringify(saveLocationData, null, 2));    
                chrome.runtime.sendMessage({ action: "Open_tab" , saveLocationData: saveLocationData  , url: "https://news.google.com/home" });
                await  waitForBackgroundToFinish('Closed_tab_Finished')
                    
                


            }else if (process.process === "youtube_Shorts" ) {

                console.log("📍 [youtube_Shorts] Démarrage du processus 'youtube_Shorts'...");
                const saveLocationData = ispProcess[process.process];
                console.log("🗂️ [AVANT REMPLACEMENT] Données associées au processus 'youtube_Shorts' :");
                console.log(JSON.stringify(saveLocationData, null, 2)); 
                
                saveLocationData.forEach(action => {
                    if (action.action === "Loop") {
                        console.log(`🔧 Remplacement de 'limit_loop' (${action.limit_loop}) par process.loop (${process.limit})`);
                        action.limit_loop = process.limit;
                    }
                });   
                
                console.log("🗂️ [APRÈS REMPLACEMENT] Données associées au processus 'youtube_Shorts' :");
                console.log(JSON.stringify(saveLocationData, null, 2));   
                chrome.runtime.sendMessage({ action: "Open_tab" , saveLocationData: saveLocationData  , url: "https://www.youtube.com/shorts" });
                await  waitForBackgroundToFinish('Closed_tab_Finished')
                await sleep(4000)

            }else if (process.process === "youtube_charts") {
            
                // saveLog("📍 [youtube_charts] Démarrage du processus 'youtube_charts'...");
                const saveLocationData = ispProcess[process.process];
                // saveLog("🗂️ [AVANT REMPLACEMENT] Données associées au processus 'youtube_Shorts' :");
                // saveLog(JSON.stringify(saveLocationData, null, 2)); 
                saveLocationData.forEach(action => {
                        // saveLog(`🔧 Remplacement de 'limit_loop' (${action.limit_loop}) par process.loop (${process.limit})`);
                        action.limit_loop = process.limit;
                });   
                // saveLog("🗂️ [APRÈS REMPLACEMENT] Données associées au processus 'youtube_Shorts' :");
                // saveLog(JSON.stringify(saveLocationData, null, 2));    
                chrome.runtime.sendMessage({ action: "Open_tab" , saveLocationData: saveLocationData  , url: "https://charts.youtube.com/charts/TopSongs/global/weekly" });
                await  waitForBackgroundToFinish('Closed_tab_Finished')
                await sleep(4000)

            
            }else if (process.process === "CheckLoginYoutube") {

                console.log("📍 [CheckLoginYoutube] Démarrage du processus 'CheckLoginYoutube'...");
                const saveLocationData = ispProcess[process.process];
                console.log("🗂️ [CheckLoginYoutube DATA] Données associées au processus 'CheckLoginYoutube' :");
                console.log(JSON.stringify(saveLocationData, null, 2));    
                chrome.runtime.sendMessage({ action: "Open_tab_CheckLoginYoutube" , saveLocationData: saveLocationData  , url: "https://www.youtube.com/" });
                await  waitForBackgroundToFinish('Closed_tab_Finished_CheckLoginYoutube')
                await sleep(4000)

                
            }else {
                // saveLog(`▶️ Exécution de l'action '${process.process}'...`);
                await ReportingActions(ispProcess[process.process], process.process);
            }
        } catch (error) {
            saveLog(`❌ [ERREUR] Processus '${process.process}' :`, error);
        }
    }
    saveLog(`🏁 Fin du processus de reporting. Total d’emails traités : ${messagesProcessed}`);
}





async function ReportingActions(actions, process) {

    console.log(`▶️ DÉBUT DU PROCESSUS : '${process}'`);
    console.log(`📦 Actions reçues :\n${JSON.stringify(actions, null, 2)}`);


    const completedActions = await new Promise((resolve) => {
        chrome.storage.local.get("completedActions", (result) => {
            resolve(result.completedActions || {});
        });
    });



    const currentProcessCompleted = completedActions[process] || [];




    const normalize = (obj) => {
        const sortedKeys = Object.keys(obj).sort();
        const normalizedObj = sortedKeys.reduce((acc, key) => {
            acc[key] = obj[key];
            return acc;
        }, {});
        return JSON.stringify(normalizedObj)
            .replace(/[\u200B-\u200D\uFEFF\u00A0]/g, "")
            .trim();
    };





    const isActionCompleted = (action) => {
        const normalizedAction = normalize({ ...action, sub_action: undefined });
        return currentProcessCompleted.some((completed) => {
            const normalizedCompleted = normalize({ ...completed, sub_action: undefined });
            return normalizedAction === normalizedCompleted;
        });
    };





    const addToCompletedActions = async (action, process) => {
        try {
            const completedAction = { ...action };
            delete completedAction.sub_action;
            currentProcessCompleted.push(completedAction);
            completedActions[process] = currentProcessCompleted;
            await new Promise((resolve) => {
                chrome.storage.local.set({ completedActions }, resolve);
            });
            console.log(`📥 [AJOUT ACTION COMPLÉTÉE] ${JSON.stringify(completedAction, null, 2)}`);
        } catch (error) {
            saveLog(`❌ [ERREUR AJOUT ACTION] ${error.message}`);
        }
    };



    
    for (const action of actions) {
        if (redirectUrls.includes(window.location.href)) {
            window.location.href = "https://mail.google.com/mail/u/0/#inbox";
        }
        console.log(`➡️ Traitement de l'action : ${JSON.stringify(action, null, 2)}`);

        if (isActionCompleted(action)) {
            console.log(`⚠️ [ACTION DÉJÀ FAITE] : ${action.action}`);
            if (action.sub_action?.length > 0) {
                console.log("🔁 [RECURSION] Exécution des  sous-actions...");
                await ReportingActions(action.sub_action, process);
            } else {
                console.log("✔️ [AUCUNE ACTION] Aucune sous-action à traiter.");
            }
            continue;
        }

        await addToCompletedActions(action, process);

        try {
            if (action.action === "check_if_exist") {
                console.log("🔍 [VÉRIFICATION] Recherche de l'élément..."); 
                const elementExists = await waitForElement(action.xpath, action.wait);

                if (elementExists) {
                    console.log(`✅ [ÉLÉMENT TROUVÉ] ${action.xpath}`);
                

                    if (action.type) {
                        console.log(`📁 [DOWNLOAD] Type : ${action.type}`);
                        await openNewTabAndDownloadFile(action.type);
                    } else if (action.sub_action?.length > 0) {
                     

                        console.log("🔄 [SOUS-ACTIONS] Exécution...");
                        await ReportingActions(action.sub_action, process);


                    } else {
                        saveLog("✔️ [AUCUNE ACTION] Pas de sous-actions.");
                    }

                } else {
                    saveLog(`❌ [ABSENT] Élément introuvable : ${action.xpath}`);
                }

                // 2
                if (action.sleep) {
                    console.log(`👽👽👽👽 Démarrage de la pause de ${action.sleep / 1000} secondes...`);
                    await sleep(action.sleep);  // 🔄 يجب استخدام await
                }

            } else {
                await SWitchCase(action, process);
                if (action.sleep) {
                    console.log(`⏱️ [PAUSE] ${action.sleep}s...`);
                    await new Promise((resolve) => setTimeout(resolve, action.sleep * 1000));
                }
            }

        } catch (error) {
            console.log(`❌ [ERREUR ACTION] ${action.action} : ${error.message}`);
        }
    }

    // console.log(`✅ FIN DU PROCESSUS : '${process}'\n`);
    return true;
}





async function sleep(ms) {
    const totalSeconds = Math.ceil(ms / 1000);
    for (let i = 1; i <= totalSeconds; i++) {
        console.log(`⏳ Attente... ${i} seconde(s) écoulée(s)`);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    console.log("✅ Pause terminée !");
}









async function SWitchCase(action, process){
      
        switch (action.action) {

            case "open_url":
                console.log(`🌐 [OUVERTURE D'URL] Navigation vers : ${action.url}`);
                await sleep(3000)
                window.location.href = action.url;
                break;
            
            case "replace_url_1":
                let url1 = window.location.href.replace("rescuephone", "password");
                console.log(`🔄 [REMPLACEMENT D'URL] Remplacement de l'URL : ${window.location.href} ➡️ ${url1}`);
                window.location.href = url1;
                break;
                
            case "replace_url_2":
                let url2 = window.location.href.replace("signinoptions/rescuephone", "recovery/email");
                console.log(`🔄 [REMPLACEMENT D'URL] Remplacement de l'URL : ${window.location.href} ➡️ ${url2}`);
                window.location.href = url2;
                break;
                
            
            case "clear":
                let clearElement;
                if (action.obligatoire) {
                    clearElement = await findElementByXPath(action.xpath, undefined, action.obligatoire, action.type);
                } else {
                    clearElement = await findElementByXPath(action.xpath);
                }
            
                if (clearElement) {
                    clearElement.value = "";
                    saveLog(`🧹 [CLEAR] Champ vidé : ${action.xpath}`);
                } else {
                    saveLog(`⚠️ [CLEAR] Échec du vidage du champ, élément introuvable : ${action.xpath}`);
                }
                break;
                

            case "click":
                let clickElement;
                if (action.obligatoire) {
                    clickElement = await findElementByXPath(action.xpath, undefined, action.obligatoire, action.type);
                } else {
                    clickElement = await findElementByXPath(action.xpath);
                }
            
                if (clickElement) {
                    clickElement.click();
                    console.log(`✅ [CLICK] Clic effectué avec succès sur l'élément : ${action.xpath}`);
                } else {
                    console.log(`❌ [CLICK] Échec : élément introuvable pour XPath : ${action.xpath}`);
                }
                break;
                

            case "dispatchEvent":
                let Element;
                if (action.obligatoire) {
                    Element = await findElementByXPath(action.xpath, undefined, action.obligatoire, action.type);
                } else {
                    Element = await findElementByXPath(action.xpath);
                }
            
                if (Element) {
                    Element.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                    Element.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                    Element.click();
                    console.log(`✅ [DISPATCH EVENT] Événements 'mousedown', 'mouseup' et 'click' envoyés avec succès à l'élément : ${action.xpath}`);
                } else {
                    console.log(`❌ [DISPATCH EVENT] Échec : élément introuvable pour XPath : ${action.xpath}`);
                }
                break;
                
            
            case "dispatchEventTwo":
                let elementXpath;
                if (action.obligatoire) {
                    elementXpath = await findElementByXPath(action.xpath, undefined, action.obligatoire, action.type);
                } else {
                    elementXpath = await findElementByXPath(action.xpath);
                }
            
                if (elementXpath) {
                    elementXpath.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                    elementXpath.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                    elementXpath.click();
                    elementXpath.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                    elementXpath.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                    elementXpath.click();
                    console.log(`✅ [DISPATCH EVENT TWO] Double interaction souris effectuée avec succès sur l'élément : ${action.xpath}`);
                } else {
                    console.log(`❌ [DISPATCH EVENT TWO] Échec : Élément introuvable pour XPath : ${action.xpath}`);
                }
                break;
                
            
            case "send_keys":
                let inputElement;
                if (action.obligatoire) {
                    inputElement = await findElementByXPath(action.xpath, action.wait , action.obligatoire, action.type);
                } else {
                    inputElement = await findElementByXPath(action.xpath ,  action.wait);
                }
            
                if (inputElement) {
                    inputElement.value = action.value;
                    console.log(`✅ [SEND KEYS] Texte "${action.value}" saisi dans l'élément : ${action.xpath}`);
                } else {
                    console.log(`❌ [SEND KEYS] Échec : Élément introuvable pour XPath "${action.xpath}"`);
                }
                break;
            
            case "send_keys_Reply":
                let elementReply;
                if (action.obligatoire) {
                    elementReply = await findElementByXPath(action.xpath, undefined, action.obligatoire, action.type);
                } else {
                    elementReply = await findElementByXPath(action.xpath ,  action.wait);
                }
            
                if (elementReply) {
                    elementReply.textContent = ""; 
                    elementReply.textContent = action.value; 
                    console.log(`✅ [SEND KEYS REPLY] Réponse "${action.value}" envoyée dans l'élément : ${action.xpath}`);
                } else {
                    console.log(`❌ [SEND KEYS REPLY] Échec : Élément introuvable pour XPath "${action.xpath}"`);
                }
                break;
                
            
            case "press_keys":
                let pressElement;
                if (action.obligatoire) {
                    pressElement = await findElementByXPath(action.xpath, undefined, action.obligatoire, action.type);
                } else {
                    pressElement = await findElementByXPath(action.xpath ,  action.wait);
                }
            
                if (pressElement) {
                    pressElement.click();
                    console.log(`✅ [PRESS KEYS] Clic sur l'élément : ${action.xpath}`);
                } else {
                    console.log(`❌ [PRESS KEYS] Échec : Élément introuvable pour XPath : ${action.xpath}`);
                }
            
                if (action.sub_action?.length > 0) {
                    await ReportingActions(action.sub_action, process);
                } else {
                    console.log("✔️ [NO SUB-ACTIONS] Aucune sous-action pour press_keys.");
                }
                break;
            
            case "check":
                try {
                    const elementExists = await waitForElement(action.xpath, action.wait);
            
                    if (elementExists) {
                        console.log(`✅ [CHECK] Élément trouvé : ${action.xpath}`);
                        return true;
                    } else {
                        console.log(`❌ [CHECK] Échec : Élément non trouvé : ${action.xpath}`);
                        return false;
                    }
                } catch (error) {
                    console.log(`❌ [CHECK] Erreur : ${error.message} (XPath : ${action.xpath})`);
                    return false;
                }
                break;
             
            case "search_for_link_and_click":
                try {
                    const mainWindow = window;
                    const openTabs = [];
                    console.log(`🔍 [SEARCH] Recherche de l'élément avec XPath : ${action.xpath}`);
            
                    const xpathResult = document.evaluate(action.xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
            
                    if (xpathResult.snapshotLength === 0) {
                        console.log(`❌ [SEARCH] Aucun élément trouvé pour XPath : ${action.xpath}`);
                        break;
                    }
            
                    const element = xpathResult.snapshotItem(0);
                    const href = element?.href || element?.getAttribute('href');
            
                    if (!href) {
                        console.log(`🚫 [SEARCH] Aucun lien trouvé pour XPath : ${action.xpath}`);
                        break;
                    }
            
                    const newTab = window.open(href, '_blank');
                    if (newTab) {
                        openTabs.push(newTab);
                        console.log(`🌐 [SEARCH] Lien ouvert : ${href}`);
                    } 
            
                    for (const tab of openTabs) {
                        if (!tab || tab.closed) {
                            continue;
                        }
                        tab.focus();
                        await sleep(3000);
            
                        tab.close();
                        console.log(`💨 [SEARCH] Onglet fermé pour ${href}`);
                    }
            
                    mainWindow.focus();
                } catch (error) {
                    saveLog(`⚠️ [SEARCH] Erreur : ${error.message}`);
                }
                break;
        

            case "focus":
                let focusElement;
                if (action.obligatoire) {
                    focusElement = await findElementByXPath(action.xpath, undefined, action.obligatoire, action.type);
                } else {
                    focusElement = await findElementByXPath(action.xpath ,  action.wait);
                }

                if (focusElement) {
                    focusElement.focus();
                    console.log(`✅ [FOCUS] Focus appliqué avec succès sur l'élément : ${action.xpath}`);
                } else {
                    console.log(`❌ [FOCUS] Échec : élément introuvable pour XPath : ${action.xpath}`);
                }
                break;



            default:
                console.log(`⚠️ Action inconnue : ${action.action}`);
                                
        }
}







function waitForBackgroundToFinish(expectedAction) {
    return new Promise((resolve) => {
        let seconds = 0;
        const interval = setInterval(() => {
        seconds++;
        console.log(`⏳ [action] En attente depuis ${seconds} seconde(s)...`);
        }, 1000);

        const listener = (message, sender, sendResponse) => {
            console.log("📥 [action] Message reçu depuis l’arrière-plan :", message);

            if (message.action === expectedAction) {
                console.log("🎯 [action] Action attendue reçue :", expectedAction);
                clearInterval(interval);
                chrome.runtime.onMessage.removeListener(listener);
                resolve();
            }
        };

        chrome.runtime.onMessage.addListener(listener);
    });
}





function genererIdUnique() {
    const timestamp = Date.now().toString(36); 
    const random = Math.random().toString(36).substring(2, 10); 
    const uniqueId = `${timestamp}-${random}`;
    return uniqueId;
}







function addUniqueIdsToActions(actions) {
    actions.forEach(action => {
        action.id = genererIdUnique();
        if (action.sub_action && Array.isArray(action.sub_action)) {
            addUniqueIdsToActions(action.sub_action); 
        }
    });
}









chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {

    if (message.action === "Closed_tab_Finished") {
        console.log("✅ [action] تم استقبال رسالة Closed_tab_Finished من background.js");

        // افترض أننا نحتاج وقتًا قبل الرد، مثلاً:
        setTimeout(() => {
            sendResponse({ success: true });  // هذا يُغلق قناة الرسالة بنجاح
        }, 500); // أو أي وقت حسب الحاجة

        return true; // إبلاغ المتصفح أننا سنرد لاحقًا
    }



    if (message.action === "Closed_tab_Finished_CheckLoginYoutube") {
        console.log("✅ [action] تم استقبال رسالة Closed_tab_Finished من background.js");

        setTimeout(() => {
            sendResponse({ success: true }); 
        }, 500);

        return true; 
    }

 
    return false;


    
});






let processAlreadyRunning = false;




chrome.runtime.onMessage.addListener(async (message, sender, sendResponse) => {
    try {
        if (message.action === "startProcess") {
            if (
                window.location.href.startsWith("https://contacts.google.com") ||
                window.location.href.startsWith("https://www.google.com/maps") ||
                window.location.href.startsWith("https://trends.google.com/trends/") ||
                window.location.href.startsWith("https://news.google.com/home") 
            ) {
                console.log("⛔️ Le processus ne peut pas être démarré depuis cette page.");
                return;
            }

            if (processAlreadyRunning) {
                console.log("⚠️ Processus déjà en cours, demande ignorée.");
                sendResponse({ status: "error", message: "Le processus est déjà en cours." });
                return;
            }

            processAlreadyRunning = true;  // 🔐 Verrou activé

            createPopup()
                .then(() => {
                    console.log("✅ Processus terminé avec succès.");
                    processAlreadyRunning = false;  // 🔓 Déverrouillage
                    sendResponse({ status: "success", message: "Le processus a été démarré avec succès." });
                })
                .catch((error) => {
                    console.log(`❌ Erreur lors du démarrage du processus : ${error.message}`);
                    processAlreadyRunning = false;  // 🔓 Déverrouillage même en cas d'erreur
                    sendResponse({ status: "error", message: error.message });
                });
        }
    } catch (error) {
        console.log("❌ Erreur générale :", error);
        processAlreadyRunning = false;  // 🔓 Sécurité en cas d'erreur
        sendResponse({ status: "error", message: error.message });
    }
    return true; // Obligatoire pour les appels asynchrones
});
