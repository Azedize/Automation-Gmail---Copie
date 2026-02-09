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




async function ReportingActions(actions, process) {
    console.log(`▶️ DÉBUT DU PROCESSUS : '${process}'`);
    console.log(`📦 Actions reçues :\n${JSON.stringify(actions, null, 2)}`);

   const { completedActions = {} } = await browser.storage.local.get("completedActions");


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

            // Utilise l'API native Promise
            await browser.storage.local.set({ completedActions });

            console.log(`📥 [AJOUT ACTION COMPLÉTÉE] ${JSON.stringify(completedAction, null, 2)}`);
        } catch (error) {
            console.log(`❌ [ERREUR AJOUT ACTION] ${error.message}`);
        }
    };





    for (const action of actions) {



        console.log(`➡️ Traitement de l'action : ${JSON.stringify(action, null, 2)}`);




        if (process !== "youtube_Shorts" ) {
            if (isActionCompleted(action)) {
                console.log(`⚠️ [ACTION DÉJÀ FAITE] : ${action.action}`);
                console.log(`⚠️ [ACTION DÉJÀ FAITE] : ${action.action}`);
                if (action.sub_action?.length > 0) {
                    console.log("🔁 [RECURSION] Exécution des sous-actions...");
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


                console.log("🔍 [VÉRIFICATION] Recherche de l'élément..."); 
                const elementExists = await waitForElement(action.xpath, action.wait);

                if (elementExists) {
                    console.log(`✅ [ÉLÉMENT TROUVÉ] ${action.xpath}`);
                

                    if (action.type) {
                        console.log(`📁 [DOWNLOAD] Type : ${action.type}`);
                        // await openNewTabAndDownloadFile(action.type);
                        await SendMessageDownloadFile(action.type);

                    } else if (action.sub_action?.length > 0) {
                        console.log("🔄 [SOUS-ACTIONS] Exécution...");
                        await ReportingActions(action.sub_action, process);
                    } else {
                        console.log("✔️ [AUCUNE ACTION] Pas de sous-actions.");
                    }

                } else {
                    console.log(`❌ [ABSENT] Élément introuvable : ${action.xpath}`);
                }
                if (action.sleep) {
                    console.log(`👽👽👽👽 Démarrage de la pause de ${action.sleep / 1000} secondes...`);
                    await sleep(action.sleep);  // 🔄 يجب استخدام await
                }
            }else if (action.action === "Loop") {
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
            }else {
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







async function SWitchCase(action, process){
    // console.log("%c🔁 Traitement d'une nouvelle action :", "color: #2e86de; font-weight: bold; font-size: 14px");
    // console.log(`%c📌 Action : %c${JSON.stringify(action, null, 2)}`, "color: #555; font-weight: bold", "color: #27ae60");
    // console.log(`%c🧩 Process : %c${process}`, "color: #555; font-weight: bold", "color: #8e44ad");

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
                // console.log(`🧹 [CLEAR] Champ vidé : ${action.xpath}`);
            } else {
                console.log(`⚠️ [CLEAR] Échec du vidage du champ, élément introuvable : ${action.xpath}`);
                console.log("");

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
                // console.log(`✅ [CLICK] Clic effectué avec succès sur l'élément : ${action.xpath}`);
            } else {
                // console.log(`❌ [CLICK] Échec : élément introuvable pour XPath : ${action.xpath}`);
                console.log("");
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
                // console.log(`✅ [DISPATCH EVENT] Événements 'mousedown', 'mouseup' et 'click' envoyés avec succès à l'élément : ${action.xpath}`);
            } else {
                // console.log(`❌ [DISPATCH EVENT] Échec : élément introuvable pour XPath : ${action.xpath}`);
                console.log("");

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
                // console.log(`✅ [DISPATCH EVENT TWO] Double interaction souris effectuée avec succès sur l'élément : ${action.xpath}`);
            } else {
                // console.log(`❌ [DISPATCH EVENT TWO] Échec : Élément introuvable pour XPath : ${action.xpath}`);
                console.log("");

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
                // console.log(`✅ [SEND KEYS] Texte "${action.value}" saisi dans l'élément : ${action.xpath}`);
            } else {
                // console.log(`❌ [SEND KEYS] Échec : Élément introuvable pour XPath "${action.xpath}"`);
                console.log("");

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
                // console.log(`⌨️ [SEND KEYS HUMAIN] Début de la saisie simulée dans : ${action.xpath}`);

                // Simulation de frappe "humaine"
                for (const char of action.value) {
                    inputElementHumain.value += char;

                    // Déclenchement de l'événement input à chaque caractère (important pour les sites modernes)
                    inputElementHumain.dispatchEvent(new Event("input", { bubbles: true }));

                    await new Promise(resolve => setTimeout(resolve, 100)); // Délai de 100ms entre chaque caractère
                }

                // console.log(`✅ [SEND KEYS HUMAIN] Texte "${action.value}" saisi dans l'élément : ${action.xpath}`);
            } else {
                // console.log(`❌ [SEND KEYS HUMAIN] Échec : Élément introuvable pour XPath "${action.xpath}"`);
                console.log("");

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
                // console.log(`✅ [PRESS KEYS] Clic sur l'élément : ${action.xpath}`);
            } else {
                // console.log(`❌ [PRESS KEYS] Échec : Élément introuvable pour XPath : ${action.xpath}`);
                console.log("");

            }
        
            if (action.sub_action?.length > 0) {
                await ReportingActions(action.sub_action, process);
            } else {
                // console.log("✔️ [NO SUB-ACTIONS] Aucune sous-action pour press_keys.");
                console.log("");

            }
            break;


        case "scroll_to_xpath":
            const scrollElement = await findElementByXPath(action.xpath,);
            if (scrollElement) {
                scrollElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
                // console.log(`✅ [SCROLL TO XPATH] Scroll vers l'élément : ${action.xpath}`);
            } else {
                // console.log(`❌ [SCROLL TO XPATH] Échec : Élément introuvable pour XPath : ${action.xpath}`);
                console.log("");

            }

        
        case "click_random_link":
            try {
                let container = await findElementByXPath(action.container_xpath);
                
                if (!container) {
                    // console.log(`❌ [CLICK RANDOM LINK] Container introuvable pour XPath : ${action.container_xpath}`);
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
                console.log(`❌ [CLICK RANDOM LINK] Erreur lors de l'exécution : ${error.message}`);
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
                    // console.log(`🔍 [FOCUS] Focus appliqué sur l'élément : ${action.xpath}`);

                    // Insertion du texte aléatoire depuis la liste
                    document.execCommand('insertText', false, randomItem);
                    // console.log(`✅ [INSERT TEXT] Texte inséré depuis la liste "${listName}" : ${randomItem}`);
                } else {
                    console.log(`❌ [INSERT TEXT] La liste "${listName}" est introuvable ou vide.`);
                }
            } else {
                console.log(`❌ [INSERT TEXT] Échec : élément introuvable pour XPath : ${action.xpath}`);
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
                // console.log(`✅ [FOCUS] Focus appliqué avec succès sur l'élément : ${action.xpath}`);
                console.log("");

            } else {
                console.log(`❌ [FOCUS] Échec : élément introuvable pour XPath : ${action.xpath}`);
            }
            break;



        case "scrollTo":
            if (typeof action.value === 'number') {
                window.scrollTo(0, action.value);
                // console.log(`✅ [SCROLL] Défilement effectué jusqu'à la position : ${action.value}px`);
                 console.log("");

            } else {
                console.log("❌ [SCROLL] La valeur de défilement doit être un nombre.");
            }
            break;

            
        case "Sub_Open_Tab":
            // console.log("🚀 [ÉTAPE 1] Démarrage du processus Sub_Open_Tab...");
            const containerXPath = "//div[contains(@class, 'chart-table-container') and contains(@class, 'ytmc-chart-table-v2')]";
            const container = await findElementByXPath(containerXPath);
            
            if (!container) {
                console.warn("❌ Conteneur principal introuvable !");
            } else {
                // console.log("✅ Conteneur principal trouvé !");
                const rowsXPath = ".//ytmc-entry-row[contains(@class, 'ytmc-chart-table-v2')]";
                const rowsSnapshot = document.evaluate(
                    rowsXPath,
                    container,
                    null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                    null
                );
                const total = rowsSnapshot.snapshotLength;
                // console.log(`📋 Total éléments trouvés : ${total}`);
                let titleXPath = null
                let titleResult = null
                let titleDiv = null
                let sharedId = null

                for (let i =0; i < action.limit_loop ; i++) {
                    
                    const row = rowsSnapshot.snapshotItem(i);
                    // console.log(`🔸 Élément #${i +1}:`, row);

                    // Étape 3 : rechercher #entity-title par XPath dans chaque ytmc-entry-row
                    titleXPath = ".//div[@id='entity-title']";
                    titleResult = document.evaluate( titleXPath,row,null,XPathResult.FIRST_ORDERED_NODE_TYPE,null );
                    titleDiv = titleResult.singleNodeValue;

                    if (titleDiv) {
                        // ✅ Extraction de l'attribut endpoint
                        const endpointAttr = titleDiv.getAttribute('endpoint');
                        if (endpointAttr) {
                            try {
                                let  endpointData = JSON.parse(endpointAttr);
                                let urlendpointData = endpointData.urlEndpoint?.url;
                                // console.log(`🔗 URL extraite de l'élément #${i +1} : ${urlendpointData}`);
                                // console.log(`👒👒 [SUB OPEN TAB] Tentative ${i + 1} de 3 pour ouvrir l'onglet...`);
                                await sleep(7000);
                                sharedId = genererIdUnique();

                                // console.log("📍 [youtube_Shorts] Démarrage du processus 'youtube_Shorts'...");
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
                                // console.log("🗂️ [youtube_Shorts DATA] Données associées au processus 'youtube_Shorts' :");
                                // console.log(JSON.stringify(saveLocationData, null, 2));    
                                await browser.runtime.sendMessage({ action: "Sub_Open_tab",  saveLocationData: saveLocationData , url: urlendpointData });
                                await  waitForBackgroundToFinish('Sub_Closed_tab_Finished')  
                                await sleep(4000);


                            } catch (e) {
                                console.warn(`⚠️ Erreur lors du parsing de l'attribut endpoint dans l'élément #${i + 1}`, e);
                            }
                        } else {
                            console.warn(`❌ Aucun attribut 'endpoint' trouvé dans l'élément #${i + 1}`);
                        }



                        // ✅ Clic uniquement sur les 5 premiers éléments
                    
                    } else {
                        console.warn(`❌ Aucun #entity-title trouvé dans l’élément #${i + 1}`);
                    }
                
                }

            }

        default:
            console.log(`⚠️ Action inconnue : ${action.action}`);
                            
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



browser.runtime.onMessage.addListener((message, sender) => {



    if (message.action === "Data_Google_CheckLoginYoutube") {

        // console.log("📥 Données reçues :", message.data);

        return new Promise(async (resolve) => {
            try {
                resolve({ status: "done" });

                await ReportingActions(message.data);
                // console.log("✅ ReportingActions terminé");
                
                try {
                    await browser.runtime.sendMessage({ action: "Closed_tab_CheckLoginYoutube" });
                    // console.log("📤 Message 'Closed_tab_CheckLoginYoutube' envoyé au background");
                } catch (err) {
                    console.error("❌ Erreur lors de l'envoi de 'Closed_tab' :", err);
                }

            } catch (err) {
                console.error("❌ Erreur dans ReportingActions :", err);
                resolve({ status: "error", message: err.message });
            }
        });
    }


    // if (message.action === "Data_Google_CheckLoginYoutube") {

    //     console.log("📥 Données reçues :", message.data);

    //     return new Promise(async (resolve) => {
    //         try {
    //             await ReportingActions(message.data);
    //             console.log("✅ ReportingActions terminé");
                
    //             try {
    //                 await browser.runtime.sendMessage({ action: "Closed_tab_CheckLoginYoutube" });
    //                 console.log("📤 Message 'Closed_tab_CheckLoginYoutube' envoyé au background");
    //             } catch (err) {
    //                 console.error("❌ Erreur lors de l'envoi de 'Closed_tab' :", err);
    //             }

    //             resolve({ status: "done" });
    //         } catch (err) {
    //             console.error("❌ Erreur dans ReportingActions :", err);
    //             resolve({ status: "error", message: err.message });
    //         }
    //     });
    // }



    if (message.action === "Data_Google") {
        console.log("📥 Données reçues :", message.data);

        return new Promise(async (resolve) => {
            try {
                await ReportingActions(message.data);
                console.log("✅ ReportingActions terminé");

                try {
                    await browser.runtime.sendMessage({ action: "Closed_tab" });
                    console.log("📤 Message 'Closed_tab' envoyé au background");
                } catch (err) {
                    console.error("❌ Erreur lors de l'envoi de 'Closed_tab' :", err);
                }

                resolve({ status: "done" });
            } catch (err) {
                console.error("❌ Erreur dans ReportingActions :", err);
                resolve({ status: "error", message: err.message });
            }
        });
    }


    if (message.action === "Sub_Data_Google") {
        // console.log("📥 Données secondaires reçues :", message.data);

        return new Promise(async (resolve) => {
            try {
                await ReportingActions(message.data);
                // console.log("✅ ReportingActions terminé");

                try {
                    await browser.runtime.sendMessage({ action: "Sub_Closed_tab" });
                    // console.log("📤 Message 'Sub_Closed_tab' envoyé au background");
                } catch (err) {
                    console.error("❌ Erreur lors de l'envoi de 'Sub_Closed_tab' :", err);
                }

                resolve({ status: "done" });
            } catch (err) {
                console.error("❌ Erreur dans ReportingActions :", err);
                resolve({ status: "error", message: err.message });
            }
        });
    }


    if (message.action === "Sub_Closed_tab_Finished") {
        // console.log("✅ [action] Message 'Sub_Closed_tab_Finished' reçu depuis le background");

        return new Promise((resolve) => {
            setTimeout(() => {
                resolve({ success: true });
            }, 500);
        });
    }


    if (message.action === "Data_Google_Add_Contact") {
        // console.log("📥 [Ajout de contact] Données reçues :", message.data);
        // console.log("📧 Email à ajouter :", message.email);

        return new Promise(async (resolve) => {
            try {
                await ReportingActions(message.data, message.email);
                // console.log("✅ [Ajout de contact] ReportingActions terminé");

                try {
                    await browser.runtime.sendMessage({ action: "Closed_tab_Add_Contact" });
                    // console.log("📤 Message 'Closed_tab_Add_Contact' envoyé au background");
                } catch (err) {
                    console.error("❌ Erreur lors de l'envoi de 'Closed_tab_Add_Contact' :", err);
                }

                resolve({ status: "done" });
            } catch (err) {
                console.error("❌ Erreur dans ReportingActions (Ajout de contact) :", err);
                resolve({ status: "error", message: err.message });
            }
        });
    }


});



function waitForBackgroundToFinish(expectedAction) {
    return new Promise((resolve) => {
        let seconds = 0;
        const interval = setInterval(() => {
            seconds++;
            // console.log(`⏳ [attente] ${seconds} seconde(s) écoulée(s)...`);
        }, 1000);

        const listener = (message) => {
            // console.log("📥 [attente] Message reçu du background :", message);

            if (message.action === expectedAction) {
                // console.log("🎯 [attente] Action attendue reçue :", expectedAction);
                clearInterval(interval);
                browser.runtime.onMessage.removeListener(listener);
                resolve();
            }
        };

        browser.runtime.onMessage.addListener(listener);
    });
}
