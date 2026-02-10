async function SendMessageDownloadFile(etat) {
    await browser.runtime.sendMessage({ action: "downloadFile", etat });

}




const createPopup = async () => {

    if(window.location.href.startsWith("https://myaccount.google.com/interstitials/birthday")){
        window.location.href = "https://mail.google.com/mail/u/0/#inbox";
    }
    
    document.title = "EXT:" + "__email__"; 

    try {
      // 1. Récupérer completedActions depuis le stockage
      const completedActions = await new Promise((resolve, reject) => {
        browser.storage.local.get("completedActions", (result) => {
          if (browser.runtime.lastError) {
            saveLog(`❌ Erreur browser.storage.local.get: ${browser.runtime.lastError.message}`);
            return reject(new Error(browser.runtime.lastError.message));
          }
          resolve(result.completedActions || {});
        });
      });
  
      // 2. Charger le scénario depuis traitement.json
      const scenarioUrl = browser.runtime.getURL("traitement.json");
      const scenarioResponse = await fetch(scenarioUrl);
      if (!scenarioResponse.ok) {
        throw new Error(`Erreur HTTP ${scenarioResponse.status} lors du chargement de traitement.json`);
      }
      const scenario = await scenarioResponse.json();
  
      // 3. Importer dynamiquement gmail_process.js
      const processUrl = browser.runtime.getURL("gmail_process.js");
      const module = await import(processUrl);
      const ispProcess = module.gmail_process || module.default || module;
      if (typeof ispProcess !== 'object' || ispProcess === null) {
        throw new Error("❌ Export 'gmail_process' ou 'default' non trouvé ou n'est pas un objet dans gmail_process.js");
      }
    //   console.groupCollapsed("%c[ReportingProcess] Contenu de ispProcess", "color: #2980b9; font-weight: bold;");
    //   console.dir(ispProcess);
    //   console.groupEnd();
  

      await ReportingProcess(scenario, ispProcess);
  


      await SendMessageDownloadFile('completed');
  
      await clearbrowserStorageLocal();
  
    } catch (error) {
      saveLog("❌ Erreur générale lors de l'exécution de createPopup:", error);
    }
};
  



function clearbrowserStorageLocal() {
    browser.storage.local.clear().catch(() => {});
}







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





async function waitForElement(xpath, timeout = 30) {
    const maxWait = timeout * 1000;
    const interval =  1000 ;
    let elapsed = 0;

    const startMsg = `⌛ Début de l'attente de l'élément avec XPath: ${xpath} (Max: ${timeout} secondes)`;
    saveLog(startMsg);

    try {
        while (elapsed < maxWait) {

            const element = document.evaluate( xpath, document, null,  XPathResult.FIRST_ORDERED_NODE_TYPE , null ).singleNodeValue;
            
            if (element) {
                const successMsg = `✅ Élément trouvé: ${xpath}`;
                saveLog(successMsg);
                return true; 
            }

            await sleep(interval);
            elapsed += interval;
        }
    } catch (error) {
        saveLog(errorMsg); 
        saveLog(`[waitForElement] ${errorMsg}`, error);
        return false; 
    }

    const timeoutMsg = `❌ Temps écoulé (${timeout}s). Élément non trouvé pour XPath: ${xpath}`; 
    saveLog(timeoutMsg);
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
    saveLog(`🔍 Recherche de l'élément avec XPath: ${xpath}...`);
    try {
        const element = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;

        if (element) {
            const text = element.textContent ? element.textContent.trim() : ''; 
            saveLog(`✅ Élément trouvé avec XPath: ${xpath} | Texte: "${text}"`);
            return text;
        } else {
            saveLog(`⚠️ L'élément avec XPath: ${xpath} n'a pas été trouvé.`);
            return null;
        }
    } catch (error) {
        saveLog( `❌ Erreur lors de la recherche XPath (${xpath}): ${error.message}`); 
        return null;
    }

}






function getElementCountByXPath(xpath) {
    saveLog(`🔍 Recherche du nombre d'éléments avec XPath: ${xpath}...`);

    try {
        const result = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
        const count = result.snapshotLength;
        saveLog(`✅ Nombre d'éléments trouvés avec XPath: ${xpath} est ${count}`);
        return count; 

    } catch (error) {
        const errorMsg = `❌ Erreur lors du comptage XPath (${xpath}): ${error.message}`;
        saveLog(errorMsg); 

        return 0; 
    }
}













let Email_Contact = null;
let cleanEmail = null;


async function ReportingProcess(scenario, ispProcess) {

    let messagesProcessed = 0;

    for (const process of scenario) {
        try {
            const currentURL = window.location.href;
            if (
                (
                    currentURL.includes("https://mail.google.com/mail") ||
                    currentURL.startsWith("https://gds.google.com/") ||
                    currentURL.includes("https://myaccount.google.com/?pli=") ||
                    currentURL.startsWith("https://myaccount.google.com/")
                ) &&
                process.process === "login"
            ) {
                continue;
            }

            if (process.process === "loop") {
                const limitLoop = process.limit_loop;
                let stopAllLoops = false;
                while (messagesProcessed < limitLoop) {
                    if (stopAllLoops) break;

                    if (process.check) {
                        const checkResult = await ReportingActions(ispProcess[process.check], process.process);
                        if (!checkResult) {
                            stopAllLoops = true;
                            break;
                        }
                    }

                    const xpath = `//table[.//colgroup]//tbody/tr`;
                    const messagesOnPage = await getElementCountByXPath(xpath);
                    saveLog(`📊 Total des messages sur la page : ${messagesOnPage}`);
                    // saveLog(`🔄 État du traitement :\n  - messagesProcessed : ${messagesProcessed}\n  - limitLoop : ${limitLoop}\n  - stopAllLoops : ${stopAllLoops}`);
                    // saveLog(`🚀 Point de départ du traitement (start message) : ${parseInt(process.start)}`);

                    const startIndex = process.start > 0 ? parseInt(process.start) - 1 : 0;

                    for (let i = startIndex ; i <= messagesOnPage; i++) {
                        // saveLog(`💚​💚​💚​💚​💚​ [LOOP] Début du traitement du message ${i}/${messagesOnPage}...`);
                        saveLog(`🔢 messagesProcessed: ${messagesProcessed}, limitLoop: ${limitLoop}, stopAllLoops: ${stopAllLoops}`);
                        if (stopAllLoops || messagesProcessed >= limitLoop) {
                            stopAllLoops = true;
                            break;
                        }


                        for (const subProcess of process.sub_process) {
                            // saveLog(`🔄 [SUB_PROCESS] Démarrage du sous-processus : ${subProcess.process}`);

                            if (stopAllLoops) break;

                            const prcss = [...ispProcess[subProcess.process]];

                            addUniqueIdsToActions(prcss);


                            if (subProcess.process === "OPEN_MESSAGE_ONE_BY_ONE") {
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

                                Email_Contact = await findElementByXPath( `//table//tbody//tr//td//h3//span[@translate and @role="gridcell"]//span[@email and @name and @data-hovercard-id]`);
                                
                                if (!Email_Contact) {
                                    // saveLog("🚫 [CONTACT] Élément cible introuvable.");
                                    return;
                                }else {
                                    // saveLog("✅ [CONTACT] Élément cible trouvé.");
                                    // saveLog("📧 [CONTACT] Élément cible :", Email_Contact);
                                    console.log("")
                                }

                                cleanEmail = Email_Contact.getAttribute("email");
                                // saveLog(`📧 [CONTACT] Email extrait : ${cleanEmail}`);

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
                                        console.log("");

                                    } else {
                                        // saveLog(`✅ Clé : ${key} (inchangée)`);
                                        console.log("");

                                    }
                                });

                                // saveLog("🗂️ [add_contacts DATA] Données finales après remplacement :");
                                // saveLog(JSON.stringify(saveLocationDataUpdated, null, 2));

                                browser.runtime.sendMessage({ 
                                    action: "Open_tab_Add_Contact", 
                                    saveLocationData: saveLocationDataUpdated,
                                    email: cleanEmail, 
                                    url: "https://contacts.google.com/new"
                                });

                                await waitForBackgroundToFinish('Closed_tab_Finished_Add_Contact');
                                continue;
                            }

                            if (["next", "next_page"].includes(subProcess.process)) {
                                const checkNextResult = await ReportingActions(ispProcess["CHECK_NEXT"], process.process);
                                if (!checkNextResult) {
                                    break;
                                }
                                await ReportingActions(ispProcess[subProcess.process], process.process);
                            } else {
                                await ReportingActions(ispProcess[subProcess.process], process.process);
                            }
                        }

                        messagesProcessed++;
                    }

                    if (!stopAllLoops && messagesProcessed < limitLoop) {
                        const checkNextResult = await ReportingActions(ispProcess["CHECK_NEXT"], process.process);
                        if (!checkNextResult) {
                            break;
                        }

                        const nextPageActions = [...ispProcess["next_page"]];
                        addUniqueIdsToActions(nextPageActions);
                        await ReportingActions(nextPageActions, process.process);
                    }
                }


            } else if (process.process === "search") {
                const updatedProcesses = ispProcess[process.process].map(item => {
                    const updatedItem = { ...item };
                    if (updatedItem.value?.includes("__search__")) {
                        updatedItem.value = updatedItem.value.replace("__search__", process.value);
                    }
                    return updatedItem;
                });

                await ReportingActions(updatedProcesses, process.process);

            } else if (process.process === "CHECK_FOLDER") {
                const checkFolderResult = await ReportingActions(ispProcess[process.check], process.process);
                if (!checkFolderResult) {
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

                        // Récupération des données associées au processus
                        const saveLocationData = ispProcess[process.process];

                        // console.groupCollapsed("🗂️ [SAVE_LOCATION DATA] Données brutes AVANT modification");
                        // saveLog(JSON.stringify(saveLocationData, null, 2));
                        // console.groupEnd();

                        // ✅ Remplacement profond avec affichage détaillé
                        function deepReplaceSearchValue(obj, searchValue, path = "") {
                            if (Array.isArray(obj)) {
                                obj.forEach((item, index) => {
                                    deepReplaceSearchValue(item, searchValue, `${path}[${index}]`);
                                });
                            } else if (typeof obj === "object" && obj !== null) {
                                for (const key in obj) {
                                    const value = obj[key];
                                    const currentPath = path ? `${path}.${key}` : key;

                                    if (typeof value === "string" && value.includes("__search_value__")) {
                                        const newValue = value.replace(/__search_value__/g, searchValue);
                                        // console.group(`🔁 Remplacement détecté dans ${currentPath}`);
                                        // saveLog("Avant :", value);
                                        // saveLog("Après :", newValue);
                                        // console.groupEnd();
                                        obj[key] = newValue;
                                    } else {
                                        deepReplaceSearchValue(value, searchValue, currentPath);
                                    }
                                }
                            }
                        }

                        deepReplaceSearchValue(saveLocationData, process.search);

                        // console.groupCollapsed("✅ [SAVE_LOCATION DATA] Données APRÈS modification");
                        // saveLog(JSON.stringify(saveLocationData, null, 2));
                        // console.groupEnd();

                        // 📤 Envoi des données vers l'onglet Google Maps
                        browser.runtime.sendMessage({
                            action: "Open_tab",
                            saveLocationData: saveLocationData,
                            url: "https://www.google.com/maps"
                        });

                        // ⏳ Attente de la fin du traitement
                        await waitForBackgroundToFinish("Closed_tab_Finished");

                    
                

            } else if (process.process === "google_trends"  ) {
                
                // saveLog("📍 [trends_google] Démarrage du processus 'trends_google'...");
                const saveLocationData = ispProcess[process.process];
                // saveLog("🗂️ [trends_google DATA] Données associées au processus 'trends_google' :");
                // saveLog(JSON.stringify(saveLocationData, null, 2));    
                browser.runtime.sendMessage({ action: "Open_tab" , saveLocationData: saveLocationData  , url: "https://trends.google.com/trends/" });
                await  waitForBackgroundToFinish('Closed_tab_Finished')
                    
            }else if (process.process === "news_google"  ) {

                // saveLog("📍 [news_google] Démarrage du processus 'news_google'...");
                const saveLocationData = ispProcess[process.process];
                // saveLog("🗂️ [news_google DATA] Données associées au processus 'news_google' :");
                // saveLog(JSON.stringify(saveLocationData, null, 2));    
                browser.runtime.sendMessage({ action: "Open_tab" , saveLocationData: saveLocationData  , url: "https://news.google.com/home" });
                await  waitForBackgroundToFinish('Closed_tab_Finished')
                    
                


            } else if (process.process === "youtube_Shorts" ) {

                // saveLog("📍 [youtube_Shorts] Démarrage du processus 'youtube_Shorts'...");
                const saveLocationData = ispProcess[process.process];
                // saveLog("🗂️ [AVANT REMPLACEMENT] Données associées au processus 'youtube_Shorts' :");
                // saveLog(JSON.stringify(saveLocationData, null, 2)); 
                
                saveLocationData.forEach(action => {
                    if (action.action === "Loop") {
                        // saveLog(`🔧 Remplacement de 'limit_loop' (${action.limit_loop}) par process.loop (${process.limit})`);
                        action.limit_loop = process.limit;
                    }
                });   
                
                // saveLog("🗂️ [APRÈS REMPLACEMENT] Données associées au processus 'youtube_Shorts' :");
                // saveLog(JSON.stringify(saveLocationData, null, 2));   
                browser.runtime.sendMessage({ action: "Open_tab" , saveLocationData: saveLocationData  , url: "https://www.youtube.com/shorts" });
                await  waitForBackgroundToFinish('Closed_tab_Finished')
            
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
                browser.runtime.sendMessage({ action: "Open_tab" , saveLocationData: saveLocationData  , url: "https://charts.youtube.com/charts/TopSongs/global/weekly" });
                await  waitForBackgroundToFinish('Closed_tab_Finished')
            
            
            }else if (process.process === "CheckLoginYoutube") {

                // saveLog("📍 [CheckLoginYoutube] Démarrage du processus 'CheckLoginYoutube'...");
                const saveLocationData = ispProcess[process.process];
                // saveLog("🗂️ [CheckLoginYoutube DATA] Données associées au processus 'CheckLoginYoutube' :");
                // saveLog(JSON.stringify(saveLocationData, null, 2));    
                browser.runtime.sendMessage({ action: "Open_tab_CheckLoginYoutube" , saveLocationData: saveLocationData  , url: "https://www.youtube.com/" });
                await  waitForBackgroundToFinish('Closed_tab_Finished_CheckLoginYoutube')
                
            }else {
                await ReportingActions(ispProcess[process.process], process.process);
            }

        } catch (error) {
            saveLog(`💣❗ Erreur dans le processus '${process.process}' :`, error);
        }
    }

}







let completedActions = {};
let currentProcessCompleted = [];




async function ReportingActions(actions, process) {
    document.title = "EXT:" + "__email__"; 

    const logPrefix = `[ReportingActions(process: ${process})]`;



    try {
        // saveLog(`${logPrefix} 📦 Chargement des actions complétées depuis le stockage...`);

        completedActions = await new Promise((resolve, reject) => {
            browser.storage.local.get("completedActions", (result) => {
                if (browser.runtime.lastError) {
                    const errorMsg = `Erreur browser.storage.get: ${browser.runtime.lastError.message}`;
                    return reject(new Error(errorMsg));
                }
                resolve(result.completedActions || {});
            });
        });

        currentProcessCompleted = completedActions[process] || [];

        // saveLog(`${logPrefix} ✅ Actions déjà complétées pour "${process}": ${currentProcessCompleted.length}`);
    } catch (error) {
        // saveLog(`${logPrefix} ❌ Erreur lors du chargement des actions: ${error.message}`);
        return false;
    }




    function normalize(obj) {
        const sortedKeys = Object.keys(obj || {}).sort();
        const normalizedObj = sortedKeys.reduce((acc, key) => {
            if (key !== 'sub_action') {
                acc[key] = obj[key];
            }
            return acc;
        }, {});
        const normalizedStr = JSON.stringify(normalizedObj).replace(/[\u200B-\u200D\uFEFF\u00A0]/g, "").trim();
        // saveLog(`${logPrefix} 🔧 Normalisation: ${normalizedStr}`);
        return normalizedStr;
    }



    function isActionCompleted(action) {
        const normalizedAction = normalize({ ...action, sub_action: undefined });
        const found = currentProcessCompleted.some((completed) => {
            const normalizedCompleted = normalize({ ...completed, sub_action: undefined });
            return normalizedAction === normalizedCompleted;
        });

        // saveLog(`${logPrefix} 🔁 Vérification action déjà complétée: ${found} -> ${JSON.stringify(action)}`);
        return found;
    }



    async function addToCompletedActions(action, process) {
        try {
            const completedAction = { ...action };
            delete completedAction.sub_action;

            const normalizedNew = normalize(completedAction);

            const alreadyExists = currentProcessCompleted.some(existing => normalize(existing) === normalizedNew);

            if (!alreadyExists) {
                currentProcessCompleted.push(completedAction);
                completedActions[process] = currentProcessCompleted;

                await new Promise((resolve, reject) => {
                    browser.storage.local.set({ completedActions }, () => {
                        if (browser.runtime.lastError) {
                            const errorMsg = `Erreur browser.storage.set: ${browser.runtime.lastError.message}`;
                            return reject(new Error(errorMsg));
                        }
                        // saveLog(`${logPrefix} ✅ Action ajoutée: ${JSON.stringify(completedAction)}`);
                        resolve();
                    });
                });
            } else {
                saveLog(`${logPrefix} ⚠️ Action déjà présente, non ajoutée à nouveau: ${JSON.stringify(completedAction)}`);
            }
        } catch (error) {
            saveLog(`${logPrefix} ❌ Erreur lors de l'ajout d'action complétée: ${error.message}`);
        }
    }



    for (const action of actions) {
        // saveLog(`${logPrefix} ▶️ Traitement action: ${JSON.stringify(action)}`);

        if (isActionCompleted(action)) {
            // saveLog(`${logPrefix} ⏩ Action déjà exécutée, passage à la suivante.`);

            if (action.sub_action && action.sub_action.length > 0) {
                await ReportingActions(action.sub_action, process);
            }
            continue;
        }

        await addToCompletedActions(action, process);

        try {
            if (action.action === "check_if_exist") {
                // saveLog(`${logPrefix} 🔍 Vérification de l'existence de l'élément: ${action.xpath} (timeout: ${action.wait || 'N/A'}s)`);

                const elementExists = await waitForElement(action.xpath, action.wait);

                if (elementExists) {
                    // saveLog(`${logPrefix} ✅ Élément trouvé: ${action.xpath}`);

                    if (action.type) {
                        await SendMessageDownloadFile(action.type);
                    } else if (action.sub_action && action.sub_action.length > 0) {
                        await ReportingActions(action.sub_action, process);
                    } else {
                        saveLog(`${logPrefix} ✔️ Élément trouvé, mais aucune action 'type' ou 'sub_action' spécifiée.`);
                    }
                } else {
                    saveLog(`${logPrefix} ⚠️ Élément non trouvé après attente: ${action.xpath}`);
                }
                if (action.sleep) {
                    console.log(`👽👽👽👽 Démarrage de la pause de ${action.sleep / 1000} secondes...`);
                    await sleep(action.sleep);  // 🔄 يجب استخدام await
                }

            } else {
                await SWitchCase(action, process);

                if (action.sleep && action.sleep > 0) {
                    const sleepDuration = action.sleep * 1000;
                    // saveLog(`${logPrefix} 💤 Pause de ${action.sleep}s en cours...`);
                    await sleep(sleepDuration);
                    // saveLog(`${logPrefix} ⏰ Pause terminée.`);
                }
            }

            // saveLog(`${logPrefix} ✅ Action exécutée avec succès: ${action.action}`);
        } catch (error) {
            const errorMsg = `❌ Erreur lors de l'exécution de l'action "${action.action}": ${error.message}`;
            saveLog(`${logPrefix} ${errorMsg}`);
        }
    }

    // saveLog(`${logPrefix} 🏁 Toutes les actions ont été traitées.`);
    return true;
}






async function SWitchCase(action, process){

        switch (action.action) {

            
            case "open_url":
                // saveLog(`🌐 [OUVERTURE D'URL] Navigation vers : ${action.url}`);
                window.location.href = action.url;
                break;
            
            case "replace_url_1":
                let url1 = window.location.href.replace("rescuephone", "password");
                window.location.href = url1;
                break;
                
            case "replace_url_2":
                let url2 = window.location.href.replace("signinoptions/rescuephone", "recovery/email");
                window.location.href = url2;
                break;
                  
            case "clear":
                let clearElement;
                if (action.obligatoire) {
                    clearElement = await findElementByXPath(action.xpath, action.wait , action.obligatoire, action.type);;
                } else {
                    clearElement = await findElementByXPath(action.xpath ,  action.wait);
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
                    clickElement = await findElementByXPath(action.xpath, action.wait , action.obligatoire, action.type);
                } else {
                    clickElement = await findElementByXPath(action.xpath ,  action.wait);
                }
            
                if (clickElement) {
                    clickElement.click();
                    saveLog(`✅ [CLICK] Clic effectué avec succès sur l'élément : ${action.xpath}`);
                } else {
                    saveLog(`❌ [CLICK] Échec : élément introuvable pour XPath : ${action.xpath}`);
                }
                break;
                
            case "dispatchEvent":
                let Element;
                if (action.obligatoire) {
                    Element = await findElementByXPath(action.xpath, action.wait , action.obligatoire, action.type);
                } else {
                    Element = await findElementByXPath(action.xpath ,  action.wait);
                }
            
                if (Element) {
                    Element.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                    Element.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                    Element.click();
                    saveLog(`✅ [CLICK] Clic effectué avec succès sur l'élément : ${action.xpath}`);
                } else {
                    saveLog(`❌ [CLICK] Échec : élément introuvable pour XPath : ${action.xpath}`);
                }
                break;
                
            case "dispatchEventTwo":
                let elementXpath;
                if (action.obligatoire) {
                    elementXpath = await findElementByXPath(action.xpath, undefined, action.obligatoire, action.type);
                } else {
                    elementXpath = await findElementByXPath(action.xpath ,  action.wait);
                }
            
                if (elementXpath) {
                    elementXpath.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                    elementXpath.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                    elementXpath.click();
                    elementXpath.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                    elementXpath.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                    elementXpath.click();
                    saveLog(`✅ [CLICK] Clic effectué avec succès sur l'élément : ${action.xpath}`);
                } else {
                    saveLog(`❌ [CLICK] Échec : élément introuvable pour XPath : ${action.xpath}`);
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
                    saveLog(`✅ [SEND KEYS] Texte "${action.value}" saisi dans l'élément : ${action.xpath}`);
                } else {
                    saveLog(`❌ [SEND KEYS] Échec : Élément introuvable pour XPath "${action.xpath}"`);
                }
                break;
            
            case "send_keys_Reply":
                let elementReply;
                if (action.obligatoire) {
                    elementReply = await findElementByXPath(action.xpath, action.wait , action.obligatoire, action.type);;
                } else {
                    elementReply = await findElementByXPath(action.xpath ,  action.wait);
                }
            
                if (elementReply) {
                    elementReply.textContent = ""; 
                    elementReply.textContent = action.value; 
                    saveLog(`✅ [SEND KEYS REPLY] Réponse "${action.value}" envoyée dans l'élément : ${action.xpath}`);
                } else {
                    saveLog(`❌ [SEND KEYS REPLY] Échec : Élément introuvable pour XPath "${action.xpath}"`);
                }
                break;
                
            case "press_keys":
                let pressElement;
                if (action.obligatoire) {
                    pressElement = await findElementByXPath(action.xpath, action.wait , action.obligatoire, action.type);
                } else {
                    pressElement = await findElementByXPath(action.xpath ,  action.wait);
                }
            
                if (pressElement) {
                    pressElement.click();
                    saveLog(`✅ [PRESS KEYS] Clic sur l'élément : ${action.xpath}`);
                } else {
                    saveLog(`❌ [PRESS KEYS] Échec : Élément introuvable pour XPath : ${action.xpath}`);
                }
            
                if (action.sub_action?.length > 0) {
                    await ReportingActions(action.sub_action, process);
                } else {
                    saveLog("✔️ [NO SUB-ACTIONS] Aucune sous-action pour press_keys.");
                }
                break;
            
            case "check":
                try {
                    const elementExists = await waitForElement(action.xpath, action.wait);
            
                    if (elementExists) {
                        saveLog(`✅ [CHECK] Élément trouvé : ${action.xpath}`);
                        return true;
                    } else {
                        saveLog(`❌ [CHECK] Échec : Élément non trouvé : ${action.xpath}`);
                        return false;
                    }
                } catch (error) {
                    saveLog(`❌ [CHECK] Erreur : ${error.message} (XPath : ${action.xpath})`);
                    return false;
                }
                break;
            
            case "search_for_link_and_click":
                try {
                    const mainWindow = window;
                    const openTabs = [];
                    // saveLog(`🔍 [SEARCH] Recherche de l'élément avec XPath : ${action.xpath}`);
            
                    const xpathResult = document.evaluate(action.xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
            
                    if (xpathResult.snapshotLength === 0) {
                        saveLog(`❌ [SEARCH] Aucun élément trouvé pour XPath : ${action.xpath}`);
                        break;
                    }
            
                    const element = xpathResult.snapshotItem(0);
                    const href = element?.href || element?.getAttribute('href');
            
                    if (!href) {
                        saveLog(`🚫 [SEARCH] Aucun lien trouvé pour XPath : ${action.xpath}`);
                        break;
                    }
            
                    const newTab = window.open(href, '_blank');
                    if (newTab) {
                        openTabs.push(newTab);
                        // saveLog(`🌐 [SEARCH] Lien ouvert : ${href}`);
                    } 
            
                    for (const tab of openTabs) {
                        if (!tab || tab.closed) {
                            continue;
                        }
                        tab.focus();
                        await sleep(3000);
            
                        tab.close();
                        // saveLog(`💨 [SEARCH] Onglet fermé pour ${href}`);
                    }
            
                    mainWindow.focus();
                } catch (error) {
                    saveLog(`⚠️ [SEARCH] Erreur : ${error.message}`);
                }
                break;
        
            case "focus":
                let focusElement;
                if (action.obligatoire) {
                    focusElement = await findElementByXPath(action.xpath, action.wait , action.obligatoire, action.type);
                } else {
                    focusElement = await findElementByXPath(action.xpath ,  action.wait);
                }

                if (focusElement) {
                    focusElement.focus();
                    saveLog(`✅ [FOCUS] Focus appliqué avec succès sur l'élément : ${action.xpath}`);
                } else {
                    saveLog(`❌ [FOCUS] Échec : élément introuvable pour XPath : ${action.xpath}`);
                }
                break;



            default:
                saveLog(`⚠️ Action inconnue : ${action.action}`);
                                
        }
        document.title = "EXT:" + "__email__"; 
}







function waitForBackgroundToFinish(actionAttendue) {
    return new Promise((resolve) => {
        let secondes = 0;
        const interval = setInterval(() => {
        secondes++;
        // saveLog(`⏳ [attente] ${secondes} seconde(s) écoulée(s)...`);
        }, 1000);

        const listener = (message) => {
        // saveLog("📥 [attente] Message reçu depuis le background :", message);

        if (message.action === actionAttendue) {
            // saveLog(`🎯 [attente] Action attendue reçue : ${actionAttendue}`);
            clearInterval(interval);
            browser.runtime.onMessage.removeListener(listener);
            resolve();
        }
        };

        browser.runtime.onMessage.addListener(listener);
    });
}










async function sleep(ms) {
    const totalSeconds = Math.ceil(ms / 1000);
    for (let i = 1; i <= totalSeconds; i++) {
        console.log(`⏳ Attente... ${i} seconde(s) écoulée(s)`);
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    console.log("✅ Pause terminée !");
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







browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "Closed_tab_Finished") {
        // saveLog("✅ [action] تم استقبال رسالة Closed_tab_Finished من background.js");

        // تأخير الرد لبعض الوقت (مثلاً 500 ميلي ثانية)
        setTimeout(() => {
            sendResponse({ success: true });  // هذا يغلق قناة الرسالة بنجاح
        }, 500);

        return true; // ضروري لإبقاء القناة مفتوحة حتى تنفيذ sendResponse
    }

 
    return false; // في حال لم يتم التعرف على action
});


browser.runtime.onMessage.addListener((message, sender, sendResponse) => {

    if (message.action === "Closed_tab_Finished_CheckLoginYoutube") {
        // saveLog("✅ [action] تم استقبال رسالة Closed_tab_Finished من background.js");

        setTimeout(() => {
            sendResponse({ success: true }); 
        }, 500);

        return true; 
    }

 
    return false;
});








let processAlreadyRunning = false;

browser.runtime.onMessage.addListener(async (message, sender) => {
    try {
        if (message.action === "startProcess") {
            document.title = "EXT:" + "__email__"; 

            if (
                window.location.href.startsWith("https://contacts.google.com") ||
                window.location.href.startsWith("https://www.google.com/maps") ||
                window.location.href.startsWith("https://trends.google.com/trends/") ||
                window.location.href.startsWith("https://news.google.com/home")
            ) {
                // saveLog("⛔️ Le processus ne peut pas être démarré depuis cette page.");
                return { status: "error", message: "Page non autorisée pour démarrer le processus." };
            }

            if (processAlreadyRunning) {
                // saveLog("⚠️ Processus déjà en cours, demande ignorée.");
                return { status: "error", message: "Le processus est déjà en cours." };
            }

            processAlreadyRunning = true; // 🔐 Verrou activé

            try {
                await createPopup();
                saveLog("✅ Processus terminé avec succès.");
                processAlreadyRunning = false; // 🔓 Déverrouillage
                return { status: "success", message: "Le processus a été démarré avec succès." };
            } catch (error) {
                // saveLog(`❌ Erreur lors du démarrage du processus : ${error.message}`);
                processAlreadyRunning = false; // 🔓 Déverrouillage
                return { status: "error", message: error.message };
            }
        }

       
    } catch (error) {
        // saveLog("❌ Erreur générale :", error);
        processAlreadyRunning = false;
        return { status: "error", message: error.message };
    }
});
