const randomComments = [
  "Super vidéo ! 🔥",
  "Merci pour ce contenu de qualité 🙏",
  "Très enrichissant, j'adore 😃",
  "Excellente explication comme toujours 👌",
  "Continue comme ça, t’es au top 💯",
  "Tu expliques super bien, merci 🙌",
  "Je ne rate aucune de tes vidéos 😍",
  "Toujours un plaisir de regarder tes contenus 🎥",
  "Tu m’apprends tellement de choses, merci ! 🙏",
  "Gros respect pour ton travail 👏",
  "Le montage est propre, bien joué 🎬",
  "Tu mérites plus d’abonnés 🔝",
  "Contenu clair, net et précis ✅",
  "Tu rends les choses compliquées faciles à comprendre 💡",
  "Très bon sujet, j’en voulais justement parler ! 😲",
  "Ton contenu est toujours au top niveau 🎯",
  "J’ai appris quelque chose de nouveau, merci 😊",
  "Encore une pépite comme d’habitude 💎",
  "Bravo pour la qualité de ta chaîne ! 🌟",
  "Je recommande cette vidéo à tout le monde 🔁"
];



window.randomComments = randomComments;  



async function openNewTabAndDownloadFile(etat) {
    try {
        // await downloadLogs();

        if (etat !== 'completed') {
            // console.log("")
            console.log("[Download] Téléchargement des logs avant le fichier d'état...");
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
            // console.log("❌ Impossible d'ouvrir un nouvel onglet.");
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






async function downloadLogs() {
    try {

        chrome.storage.local.get({ logs: [] }, async (data) => {
            const logs = data.logs;

            if (!logs.length) {
                console.log("⚠️ Aucun log disponible pour le téléchargement.");
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
                console.log("❌ Impossible d'ouvrir un nouvel onglet.");
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
        console.log(`❌ Erreur lors du téléchargement des logs : ${error.message}`);
    }
}




async function waitForElement(xpath, timeout = 30) {
    const maxWait = timeout * 1000; 
    const interval = 1000; 
    let elapsed = 0;

    saveLog(`⌛ Début de l'attente de l'élément avec XPath: ${xpath} (Max: ${timeout} secondes)`);

    try {
        while (elapsed < maxWait) {
            const element = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (element) {
                saveLog(`✅ Élément trouvé: ${xpath}`);
                return true;
            }
            await sleep(interval);
            elapsed += interval;
        }
    } catch (error) {
        saveLog(`❌ Erreur lors de la recherche de l'élément: ${error.message}`);
        return false;
    }

    saveLog(`❌ Temps écoulé. Élément non trouvé après ${timeout} secondes.`);
    return false;
}





async function findElementByXPath(xpath, timeout = 10, obligatoire = false, type = undefined) {
    const maxWait = timeout * 1000;
    const interval = 500;
    let elapsed = 0;

    saveLog(`🔍 Recherche de l'élément avec XPath: ${xpath}... (Max: ${timeout} secondes)`);

    try {
        while (elapsed < maxWait) {
            const element = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (element) {
                saveLog(`✅ Élément trouvé avec XPath: ${xpath}`);
                return element;
            }

            await sleep(interval);
            elapsed += interval;
        }
    } catch (error) {
        saveLog(`❌ Erreur lors de la recherche de l'élément: ${error.message}`);
        return null;
    }

    if (obligatoire) {
        saveLog(`❗ L'élément obligatoire n'a pas été trouvé après ${timeout} secondes. XPath: ${xpath}`);
    } else {
        saveLog(`❌ Élément non trouvé après ${timeout} secondes. XPath: ${xpath}`);
    }

    return null;
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
            // console.log(`📥 [AJOUT ACTION COMPLÉTÉE] ${JSON.stringify(completedAction, null, 2)}`);
        } catch (error) {
            console.log(`❌ [ERREUR AJOUT ACTION] ${error.message}`);
        }
    };


    for (const action of actions) {
        console.log(`➡️ Traitement de l'action : ${JSON.stringify(action, null, 2)}`);
        if (process !== "youtube_Shorts" ) {
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
        }    
        await addToCompletedActions(action, process);

        try {

            if (action.action === "check_if_exist") {
                saveLog("🔍 [VÉRIFICATION] Recherche de l'élément...");
                const elementExists = await waitForElement(action.xpath, action.wait);

                if (elementExists) {
                    saveLog(`✅ [ÉLÉMENT TROUVÉ] ${action.xpath}`);
                

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
                if (action.sleep) {
                    console.log(`👽👽👽👽 Démarrage de la pause de ${action.sleep / 1000} secondes...`);
                    await sleep(action.sleep);  // 🔄 يجب استخدام await
                }
            }
            
            
            else if (action.action === "Loop") {
                console.log(`📊 [LOOP START] Démarrage de la boucle (${action.limit_loop + 1} itérations prévues)...`);

                for (let i = 0; i < parseInt(action.limit_loop) ; i++) {
                    console.log(`\n🔄 [ITÉRATION] DÉBUT de l'itération ${i + 1} sur ${action.limit_loop + 1} 🔄`);

                    try {
                        await ReportingActions(action.sub_action,  "youtube_Shorts");
                        console.log(`✅ [ITÉRATION] Itération ${i + 1} terminée avec succès ✅`);
                    } catch (error) {
                        console.error(`🚨 [ERREUR] Problème lors de l'itération ${i + 1} : ${error.message}`);
                        console.error(error); // Détails complets de l’erreur
                    }

                    console.log(`🔚 [ITÉRATION] Fin de l'itération ${i + 1} 📝`);
                }

                console.log(`🏁 [LOOP END] La boucle s'est terminée après ${action.limit_loop + 1} itérations.`);
            }

            
            else {
                await SWitchCase(action, process);
                if (action.sleep) {
                    console.log(`⏱️ [PAUSE] ${action.sleep}s...`);
                    await sleep(action.sleep);
                }
            }

        } catch (error) {
            saveLog(`❌ [ERREUR ACTION] ${action.action} : ${error.message}`);
        }
    }

    console.log(`✅ FIN DU PROCESSUS : '${process}'\n`);
    return true;
}







async function SWitchCase(action, process){
    console.log("%c🔁 Traitement d'une nouvelle action :", "color: #2e86de; font-weight: bold; font-size: 14px");
    console.log(`%c📌 Action : %c${JSON.stringify(action, null, 2)}`, "color: #555; font-weight: bold", "color: #27ae60");
    console.log(`%c🧩 Process : %c${process}`, "color: #555; font-weight: bold", "color: #8e44ad");

    switch (action.action) {


        case "clear":
            let clearElement;
            if (action.obligatoire) {
                clearElement = await findElementByXPath(action.xpath, action.wait , action.obligatoire, action.type);
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
                saveLog(`✅ [DISPATCH EVENT] Événements 'mousedown', 'mouseup' et 'click' envoyés avec succès à l'élément : ${action.xpath}`);
            } else {
                saveLog(`❌ [DISPATCH EVENT] Échec : élément introuvable pour XPath : ${action.xpath}`);
            }
            break;


        case "dispatchEventTwo":
            let elementXpath;
            if (action.obligatoire) {
                elementXpath = await findElementByXPath(action.xpath, action.wait , action.obligatoire, action.type);
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
                saveLog(`✅ [DISPATCH EVENT TWO] Double interaction souris effectuée avec succès sur l'élément : ${action.xpath}`);
            } else {
                saveLog(`❌ [DISPATCH EVENT TWO] Échec : Élément introuvable pour XPath : ${action.xpath}`);
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
    

        case "send_keysHumain":
            let inputElementHumain;

            if (action.obligatoire) {
                inputElementHumain = await findElementByXPath(action.xpath, action.wait , action.obligatoire, action.type);
            } else {
                inputElementHumain = await findElementByXPath(action.xpath ,  action.wait);
            }

            if (inputElementHumain) {
                saveLog(`⌨️ [SEND KEYS HUMAIN] Début de la saisie simulée dans : ${action.xpath}`);

                // Simulation de frappe "humaine"
                for (const char of action.value) {
                    inputElementHumain.value += char;

                    // Déclenchement de l'événement input à chaque caractère (important pour les sites modernes)
                    inputElementHumain.dispatchEvent(new Event("input", { bubbles: true }));

                    await new Promise(resolve => setTimeout(resolve, 100)); // Délai de 100ms entre chaque caractère
                }

                saveLog(`✅ [SEND KEYS HUMAIN] Texte "${action.value}" saisi dans l'élément : ${action.xpath}`);
            } else {
                saveLog(`❌ [SEND KEYS HUMAIN] Échec : Élément introuvable pour XPath "${action.xpath}"`);
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


        case "scroll_to_xpath":
            const scrollElement = await findElementByXPath(action.xpath,);
            if (scrollElement) {
                scrollElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
                console.log(`✅ [SCROLL TO XPATH] Scroll vers l'élément : ${action.xpath}`);
            } else {
                console.log(`❌ [SCROLL TO XPATH] Échec : Élément introuvable pour XPath : ${action.xpath}`);
            }

        
        case "click_random_link":
            try {
                let container = await findElementByXPath(action.container_xpath);
                
                if (!container) {
                    saveLog(`❌ [CLICK RANDOM LINK] Container introuvable pour XPath : ${action.container_xpath}`);
                    break;
                }

                let childElements = Array.from(container.querySelectorAll(action.child_selector));

                if (childElements.length === 0) {
                    // console.log(`❌ [CLICK RANDOM LINK] Aucun élément enfant trouvé avec le sélecteur : ${action.child_selector}`);
                    break;
                }

                let randomIndex = Math.floor(Math.random() * childElements.length);
                let randomLink = childElements[randomIndex];

                if (action.wait) {
                    // console.log(`⏳ [CLICK RANDOM LINK] Attente avant clic: ${action.wait} secondes`);
                    await new Promise(resolve => setTimeout(resolve, action.wait * 1000));
                }

                randomLink.click();


            } catch (error) {
                saveLog(`❌ [CLICK RANDOM LINK] Erreur lors de l'exécution : ${error.message}`);
            }
            break;


        case "insertText":
            let inputElementText;
            if (action.obligatoire) {
                inputElementText = await findElementByXPath(action.xpath, action.wait , action.obligatoire, action.type);
            } else {
                inputElementText = await findElementByXPath(action.xpath ,  action.wait);
            }

            if (inputElementText) {
                // Récupération dynamique de la liste par son nom
                const listName = action.value;
                const list = window[listName];

                if (Array.isArray(list) && list.length > 0) {
                    const randomItem = list[Math.floor(Math.random() * list.length)];

                    inputElementText.focus();
                    saveLog(`🔍 [FOCUS] Focus appliqué sur l'élément : ${action.xpath}`);

                    // Insertion du texte aléatoire depuis la liste
                    document.execCommand('insertText', false, randomItem);
                    saveLog(`✅ [INSERT TEXT] Texte inséré depuis la liste "${listName}" : ${randomItem}`);
                } else {
                    saveLog(`❌ [INSERT TEXT] La liste "${listName}" est introuvable ou vide.`);
                }
            } else {
                saveLog(`❌ [INSERT TEXT] Échec : élément introuvable pour XPath : ${action.xpath}`);
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



        case "scrollTo":
            if (typeof action.value === 'number') {
                window.scrollTo(0, action.value);
                console.log(`✅ [SCROLL] Défilement effectué jusqu'à la position : ${action.value}px`);
            } else {
                console.log("❌ [SCROLL] La valeur de défilement doit être un nombre.");
            }
            break;

            
        case "Sub_Open_Tab":
            console.log("🚀 [ÉTAPE 1] Démarrage du processus Sub_Open_Tab...");
            const containerXPath = "//div[contains(@class, 'chart-table-container') and contains(@class, 'ytmc-chart-table-v2')]";
            const container = await findElementByXPath(containerXPath);
            
            if (!container) {
                saveLog("❌ Conteneur principal introuvable !");
            } else {
                console.log("✅ Conteneur principal trouvé !");
                const rowsXPath = ".//ytmc-entry-row[contains(@class, 'ytmc-chart-table-v2')]";
                const rowsSnapshot = document.evaluate(
                    rowsXPath,
                    container,
                    null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                    null
                );
                const total = rowsSnapshot.snapshotLength;
                console.log(`📋 Total éléments trouvés : ${total}`);

                let titleXPath = null
                let titleResult = null
                let titleDiv = null
                let sharedId = null

                for (let i =0; i < action.limit_loop ; i++) {
                    
                    const row = rowsSnapshot.snapshotItem(i);
                    console.log(`🔸 Élément #${i +1}:`, row);

                    // Étape 3 : rechercher #entity-title par XPath dans chaque ytmc-entry-row
                    titleXPath = ".//div[@id='entity-title']";
                    titleResult = document.evaluate( titleXPath,row,null,XPathResult.FIRST_ORDERED_NODE_TYPE,null );
                    titleDiv = titleResult.singleNodeValue;
                    sharedId = genererIdUnique();

                    if (titleDiv) {
                        // ✅ Extraction de l'attribut endpoint
                        const endpointAttr = titleDiv.getAttribute('endpoint');
                        if (endpointAttr) {
                            try {
                                let  endpointData = JSON.parse(endpointAttr);
                                let urlendpointData = endpointData.urlEndpoint?.url;
                                console.log(`🔗 URL extraite de l'élément #${i +1} : ${urlendpointData}`);
                                console.log(`👒👒 [SUB OPEN TAB] Tentative ${i + 1} de 3 pour ouvrir l'onglet...`);
                                await sleep(3000);
                                console.log("📍 [youtube_Shorts] Démarrage du processus 'youtube_Shorts'...");
                                
                                const saveLocationData =[
                                        {"action": "scroll_to_xpath", "xpath": "(//button[contains(@aria-label, \"J'aime\") or contains(@aria-label, \"like\")])[1]",  "sleep": 1 , id: sharedId},
                                        {"action": "scrollTo",  "value": 600,  "sleep": 1   , id: sharedId},
                                        {"action": "check_if_exist", "xpath": "(//button[contains(@aria-label, \"J'aime\") or contains(@aria-label, \"like\")])[1]", "wait": 3, "sleep": 0  , id: sharedId, "sub_action": [
                                            {"action": "click",  "xpath": "(//button[contains(@aria-label, \"J'aime\") or contains(@aria-label, \"like\")])[1]", "wait": 2, "sleep": 3  , id: sharedId}
                                        ]},
                                        {"action": "check_if_exist", "xpath": "//button[contains(@aria-label, 'commentaires') or contains(@aria-label, 'comments')]", "wait": 3, "sleep": 2 , id: sharedId, "sub_action": [
                                            {"action": "click",  "xpath": "//button[contains(@aria-label, 'commentaires') or contains(@aria-label, 'comments')]", "wait": 2, "sleep": 3  , id: sharedId}
                                        ]},
                                        {"action": "check_if_exist", "xpath": "//*[@id='placeholder-area']", "wait": 3, "sleep": 0  , id: sharedId , "sub_action": [
                                            {"action": "click",  "xpath": "//*[@id='placeholder-area']", "wait": 1, "sleep": 3  , id: sharedId}
                                        ]},
                                        {"action": "check_if_exist", "xpath": "//div[@id='contenteditable-root' and @contenteditable='true']" , "wait": 4, "sleep": 0  , id: sharedId , "sub_action": [
                                            {"action": "focus",  "xpath": "//div[@id='contenteditable-root' and @contenteditable='true']", "wait": 1 , id: sharedId , "sleep": 3 },
                                            {"action": "click",  "xpath": "//div[@id='contenteditable-root' and @contenteditable='true']", "wait": 1  , id: sharedId, "sleep": 3},
                                            {"action": "insertText", "xpath": "//div[@id='contenteditable-root' and @contenteditable='true']", "value" : "randomComments" , "wait": 1  , id: sharedId , "sleep": 5}
                                        ]},
                                        {"action": "check_if_exist", "xpath": "//button[@aria-disabled='false' and (  @aria-label='Commentaire'  or @aria-label='Comment'  or @aria-label='Ajouter un commentaire' or @aria-label='Add a comment')]", "wait": 3, "sleep": 0  , id: sharedId , "sub_action": [
                                            {"action": "click",  "xpath": "//button[@aria-disabled='false' and (  @aria-label='Commentaire'  or @aria-label='Comment'  or @aria-label='Ajouter un commentaire' or @aria-label='Add a comment')]" , "wait": 1  , id: sharedId, "sleep": 3}
                                        ]},
                                    ];
                                console.log("🗂️ [youtube_Shorts DATA] Données associées au processus 'youtube_Shorts' :");
                                console.log(JSON.stringify(saveLocationData, null, 2));    
                                chrome.runtime.sendMessage({ action: "Sub_Open_tab" , saveLocationData: saveLocationData  , url: urlendpointData });
                                await  waitForBackgroundToFinish('Sub_Closed_tab_Finished')  
                                await sleep(4000);


                            } catch (e) {
                                saveLog(`⚠️ Erreur lors du parsing de l'attribut endpoint dans l'élément #${i + 1}`, e);
                            }
                        } else {
                            saveLog(`❌ Aucun attribut 'endpoint' trouvé dans l'élément #${i + 1}`);
                        }



                        // ✅ Clic uniquement sur les 5 premiers éléments
                    
                    } else {
                        saveLog(`❌ Aucun #entity-title trouvé dans l’élément #${i + 1}`);
                    }
                
                }

            }

        default:
            saveLog(`⚠️ Action inconnue : ${action.action}`);
                            
    }
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





// mon besoin apres finis le ReportingActions  send message to background.js chrome.runtime.sendMessage({ action: "Closed_tab" });

// chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
//     if (message.action === "Data_Google") {
//         console.log("📥 Reçu les données :", message.data);

//         setTimeout(async () => {
//             try {
//                 await ReportingActions(message.data);
//                 console.log("✅ ReportingActions terminé");

//                 // ✅ إرسال رسالة إلى background بعد إنهاء العمل
//                 chrome.runtime.sendMessage({ action: "Closed_tab" }, (response) => {
//                     if (chrome.runtime.lastError) {
//                         console.error("❌ Erreur lors de l'envoi de Closed_tab:", chrome.runtime.lastError.message);
//                     } else {
//                         console.log("📤 Message Closed_tab envoyé à background.js");
//                     }
//                 });

//             } catch (err) {
//                 console.error("❌ Erreur dans ReportingActions :", err);
//             }
//         }, 2000);

//         // sendResponse({ received: true }); // يتم إرجاع الاستجابة مباشرة (اختياري)
//         return true; // ضروري إذا كنت تستخدم sendResponse بشكل غير متزامن (هنا ليس ضروريًا، لكنه لا يضر)
//     }
// });



chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {



    if (message.action === "Data_Google_CheckLoginYoutube") {

        // console.log("📥 Données reçues :", message.data);

        // ضروري إرجاع true لإبقاء قناة الاتصال مفتوحة حتى يكتمل الرد
        (async () => {
            try {
                await ReportingActions(message.data);
                // console.log("✅ ReportingActions terminé");

                chrome.runtime.sendMessage({ action: "Closed_tab_CheckLoginYoutube" }, () => {
                    if (chrome.runtime.lastError) {
                        console.error("❌ Erreur lors de l'envoi de 'Closed_tab' :", chrome.runtime.lastError.message);
                    } else {
                        console.log("📤 Message 'Closed_tab_CheckLoginYoutube' envoyé au background");
                    }
                });

            } catch (err) {
                console.error("❌ Erreur dans ReportingActions :", err);
            }
        })();

        sendResponse({ status: "done" });
        return true; // إبقاء القناة مفتوحة لدعم async داخل listener
    }


    // تحقق من نوع الرسالة المستلمة من الخلفية
    if (message.action === "Data_Google") {
        console.log("📥 Reçu les données :", message.data);  // عرض البيانات المستلمة

        // نستخدم setTimeout لتأخير التنفيذ (مثلاً في حال انتظار تحميل العناصر في التاب)
        setTimeout(async () => {
            try {
                // تنفيذ الوظيفة الرئيسية بشكل غير متزامن
                await ReportingActions(message.data);
                console.log("✅ ReportingActions terminé"); // تأكيد إتمام المعالجة

                // بعد الانتهاء، نرسل رسالة إلى background لإعلامه أن المهمة انتهت
                chrome.runtime.sendMessage({ action: "Closed_tab" }, (response) => {
                    if (chrome.runtime.lastError) {
                        console.error("❌ Erreur lors de l'envoi de Closed_tab:", chrome.runtime.lastError.message);
                    } else {
                        console.log("📤 Message Closed_tab envoyé à background.js");
                    }
                });

                // إرسال رد إلى الـ background.js لتجنب إغلاق القناة بدون رد
                sendResponse({ status: "done" });

            } catch (err) {
                // في حالة حصول خطأ أثناء المعالجة
                console.error("❌ Erreur dans ReportingActions :", err);

                // نرسل الخطأ إلى الخلفية أيضًا
                sendResponse({ status: "error", message: err.message });
            }
        }, 0); // تأخير التنفيذ لمدة ثانيتين

        // ضروري لتفادي إغلاق قناة الاتصال قبل وصول sendResponse
        return true;
    }

    // تحقق من نوع الرسالة المستلمة من الخلفية
    if (message.action === "Sub_Data_Google") {
        // console.log("📥 Reçu les données :", message.data);  // عرض البيانات المستلمة

        // نستخدم setTimeout لتأخير التنفيذ (مثلاً في حال انتظار تحميل العناصر في التاب)
        setTimeout(async () => {
            try {
                // تنفيذ الوظيفة الرئيسية بشكل غير متزامن
                await ReportingActions(message.data);
                // console.log("✅ ReportingActions terminé"); // تأكيد إتمام المعالجة

                // بعد الانتهاء، نرسل رسالة إلى background لإعلامه أن المهمة انتهت
                chrome.runtime.sendMessage({ action: "Sub_Closed_tab" }, (response) => {
                    if (chrome.runtime.lastError) {
                        console.error("❌ Erreur lors de l'envoi de Sub_Closed_tab:", chrome.runtime.lastError.message);
                    } else {
                        console.log("📤 Message Sub_Closed_tab envoyé à background.js");
                    }
                });

                // إرسال رد إلى الـ background.js لتجنب إغلاق القناة بدون رد
                sendResponse({ status: "done" });

            } catch (err) {
                // في حالة حصول خطأ أثناء المعالجة
                console.error("❌ Erreur dans ReportingActions :", err);

                // نرسل الخطأ إلى الخلفية أيضًا
                sendResponse({ status: "error", message: err.message });
            }
        }, 0); // تأخير التنفيذ لمدة ثانيتين

        // ضروري لتفادي إغلاق قناة الاتصال قبل وصول sendResponse
        return true;
    }


    if (message.action === "Sub_Closed_tab_Finished") {
        // console.log("✅ [action] تم استقبال رسالة Closed_tab_Finished من background.js");

        // افترض أننا نحتاج وقتًا قبل الرد، مثلاً:
        setTimeout(() => {
            sendResponse({ success: true });  // هذا يُغلق قناة الرسالة بنجاح
        }, 500); // أو أي وقت حسب الحاجة

        return true; // إبلاغ المتصفح أننا سنرد لاحقًا
    }

    
    if (message.action === "Data_Google_Add_Contact") {
        // console.log("📥 [Data_Google_Add_Contact] Reçu les données :", message.data);
        // console.log("📧 [Data_Google_Add_Contact] Email reçu :", message.email);

        setTimeout(async () => {
            try {
                await ReportingActions(message.data, message.email);
                // console.log("✅ [Data_Google_Add_Contact] ReportingActions terminé");

                chrome.runtime.sendMessage({ action: "Closed_tab_Add_Contact" }, (response) => {
                    if (chrome.runtime.lastError) {
                        console.error("❌ Erreur lors de l'envoi de Sub_Closed_tab_Add_Contact:", chrome.runtime.lastError.message);
                    } else {
                        console.log("📤 Message Sub_Closed_tab_Add_Contact envoyé à background.js");
                    }
                });

                sendResponse({ status: "done" });

            } catch (err) {
                console.error("❌ Erreur dans ReportingActions (Add Contact) :", err);
                sendResponse({ status: "error", message: err.message });
            }
        }, 0);

        return true;
    }

});




function waitForBackgroundToFinish(expectedAction) {
  return new Promise((resolve) => {
    let seconds = 0;
    const interval = setInterval(() => {
      seconds++;
    //   console.log(`⏳ [action] انتظر ${seconds} ثانية...`);
    }, 1000);

    const listener = (message, sender, sendResponse) => {
    //   console.log("📥 [action] تم استقبال رسالة من الخلفية:", message);

      if (message.action === expectedAction) {
        // console.log("🎯 [action] تم استلام الرسالة المتوقعة:", expectedAction);
        clearInterval(interval);
        chrome.runtime.onMessage.removeListener(listener);
        resolve();
      }
    };

    chrome.runtime.onMessage.addListener(listener);
  });
}